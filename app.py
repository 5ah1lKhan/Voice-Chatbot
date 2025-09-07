import streamlit as st
import json
import os
# from text_to_speech import generate_tts
from text_to_speech import generate_tts
from speech_to_text import transcribe_audio
# from agent_from_scratch import agent
from audio_recorder_streamlit import audio_recorder
from streamlit_float import *
from streamlit_js_eval import streamlit_js_eval
import base64
import re
import firebase_admin
from firebase_admin import credentials, firestore
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.cloud.firestore_v1.transforms import SERVER_TIMESTAMP
# --- Basic App Configuration ---
st.set_page_config(page_title="Google Calendar Agent", layout="wide")
st.title("🗓️ Google Calendar Agent")

# --- Load API Keys and Set Environment Variables ---
st.sidebar.header("API Keys (Optional)")
# --- Gemini API Key ---
# Use session_state to remember the key entered by the user
if 'gemini_api_key' not in st.session_state:
    st.session_state['gemini_api_key'] = ""

gemini_input = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    value=st.session_state['gemini_api_key']
)
st.session_state['gemini_api_key'] = gemini_input

# Logic: Prioritize user-input key, then fallback to secrets
if st.session_state['gemini_api_key']:
    os.environ["GOOGLE_API_KEY"] = st.session_state['gemini_api_key']
    st.sidebar.success("Using user-provided Gemini key.", icon="🔑")
elif "gemini" in st.secrets and "api_key" in st.secrets.gemini:
    os.environ["GOOGLE_API_KEY"] = st.secrets.gemini.api_key
    st.sidebar.info("Using default Gemini key")
else:
    st.sidebar.warning("Gemini API key is not configured.")

# --- Eleven Labs API Key ---
if 'elevenlabs_api_key' not in st.session_state:
    st.session_state['elevenlabs_api_key'] = ""

elevenlabs_input = st.sidebar.text_input(
    "Eleven Labs API Key",
    type="password",
    value=st.session_state['elevenlabs_api_key']
)
st.session_state['elevenlabs_api_key'] = elevenlabs_input

# Logic: Prioritize user-input key, then fallback to secrets
if st.session_state['elevenlabs_api_key']:
    os.environ["ELEVENLABS_API_KEY"] = st.session_state['elevenlabs_api_key']
    st.sidebar.success("Using user-provided Eleven Labs key.", icon="🔑")
elif "elevenlabs" in st.secrets and "api_key" in st.secrets.elevenlabs:
    os.environ["ELEVENLABS_API_KEY"] = st.secrets.elevenlabs.api_key
    st.sidebar.info("Using default ElevenLabs key.")
else:
    st.sidebar.warning("Eleven Labs API key is not configured.")


# --- Firebase Firestore Setup ---
try:
    if "firebase_service_account" in st.secrets:
        creds_dict = dict(st.secrets["firebase_service_account"])
        firebase_creds = credentials.Certificate(creds_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(firebase_creds)
        db = firestore.client()
    else:
        st.warning("Firebase service account not found. App cannot save tokens.")
        db = None
except Exception as e:
    st.error(f"Failed to initialize Firebase: {e}")
    db = None

# --- Google API Configuration ---
if "google_credentials" not in st.secrets:
    st.error("Google credentials not found in Streamlit Secrets. Authentication will fail.")
    st.stop()

CLIENT_CONFIG = st.secrets["google_credentials"]
SCOPES = ['https://www.googleapis.com/auth/calendar']

try:
    # Attempt to get the full URL for Streamlit Community Cloud
    # from streamlit.web.server.server import Server
    # server = Server.get_current()
    # REDIRECT_URI = server.get_full_url("/")
    REDIRECT_URI = st.secrets["google_credentials"]['web']['redirect_uris'][0]
except (ImportError, AttributeError):
    # Fallback for local development
    print("Could not determine full URL, defaulting to localhost.")
    REDIRECT_URI = "http://localhost:8501/"
st.sidebar.info(f"Using Redirect URI: `{REDIRECT_URI}`. Please ensure this is authorized in your Google Cloud Console.")

# --- Helper Functions ---

def get_auth_url(user_id):
    """Generates a Google OAuth URL, saving the user_id with the state."""
    flow = Flow.from_client_config(
        CLIENT_CONFIG, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline', include_granted_scopes='true'
    )
    # Store the state and the user_id in Firestore for robust verification
    if db:
        db.collection('oauth_states').document(state).set({
            'timestamp': SERVER_TIMESTAMP,
            'user_id': user_id
        })
    else:
        st.error("Database connection not available. Cannot store OAuth state.")
    return authorization_url, flow

def exchange_code_for_creds(code, flow):
    """Exchanges an authorization code for credentials."""
    flow.fetch_token(code=code)
    return flow.credentials

def save_creds_to_firestore(user_id, creds):
    """Saves credentials to Firestore."""
    if db and user_id:
        creds_json = creds.to_json()
        db.collection('user_tokens').document(user_id).set({'token_json': creds_json})

def load_creds_from_firestore(user_id):
    """Loads credentials from Firestore."""
    if db and user_id:
        doc = db.collection('user_tokens').document(user_id).get()
        if doc.exists:
            token_json = doc.to_dict().get('token_json')
            return Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    return None

def verify_state_and_restore_user_id(state):
    """
    Verifies the state from Firestore, restores the user_id to the session,
    and deletes the state document. Returns the user_id on success.
    """
    if not db:
        st.error("Database connection not available for state verification.")
        return None
    try:
        state_ref = db.collection('oauth_states').document(state)
        state_doc = state_ref.get()
        if state_doc.exists:
            user_id = state_doc.to_dict().get('user_id')
            st.session_state['user_id'] = user_id
            state_ref.delete() # State is single-use for security
            return user_id
        return None
    except Exception as e:
        st.error(f"Error verifying OAuth state from Firestore: {e}")
        return None

def delete_creds_from_firestore(user_id):
    """Deletes a user's credentials from Firestore."""
    if db and user_id:
        try:
            db.collection('user_tokens').document(user_id).delete()
            st.info("Your credentials have been securely deleted from the server.")
        except Exception as e:
            st.warning(f"Could not delete credentials from Firestore: {e}")

# --- Main Application Logic & UI Display ---

# Initialize session state
if 'credentials' not in st.session_state:
    st.session_state['credentials'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# Step 1: Handle OAuth redirect immediately. This may restore the user_id.
query_params = st.query_params
if "code" in query_params and "state" in query_params:
    code = query_params["code"]
    state = query_params["state"]
    
    restored_user_id = verify_state_and_restore_user_id(state)
    if restored_user_id:
        flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        creds = exchange_code_for_creds(code, flow)
        if creds:
            st.session_state['credentials'] = creds
            save_creds_to_firestore(restored_user_id, creds)
            st.success("Authentication successful and token saved!")
            st.query_params.clear()
            st.rerun()
    else:
        st.error("OAuth state mismatch or expired. This could be a security risk. Please try authenticating again.")
        st.query_params.clear()
        st.rerun()

# Step 2: Get User ID if not present in session state
if not st.session_state.get('user_id'):
    st.header("Welcome to the Calendar Agent")
    st.write("To keep your Google Calendar connection private, please create a unique User ID. Your access token will be stored securely under this ID.")
    
    with st.form("user_id_form"):
        username = st.text_input("Enter your unique User ID")
        submitted = st.form_submit_button("Continue")
        if submitted and username:
            st.session_state['user_id'] = username.strip()
            st.rerun()
    # Stop further execution until user_id is provided
    st.stop() 

# If we've reached this point, a user_id exists in the session state
user_id = st.session_state['user_id']
st.sidebar.success(f"Logged in as: **{user_id}**")

# Attempt to load credentials for the logged-in user
st.session_state['credentials'] = load_creds_from_firestore(user_id)

# Display content based on whether the user has authenticated with Google
if not st.session_state['credentials']:
    st.header("Google Login Required")
    st.write(f"Hi **{user_id}**, please log in with your Google account to grant calendar access.")
    auth_url, _ = get_auth_url(user_id) # Pass user_id to the function
    # st.link_button("Login with Google", auth_url)
    if st.button("Login with Google", use_container_width=True):
        streamlit_js_eval(f'window.location.href = "{auth_url}"', key="google_auth_redirect")
    # button_html = f"""
    # <a href="{auth_url}" target="_self" style="
    #     display: inline-block;
    #     padding: 0.5em 1em;
    #     color: white;
    #     background-color: #FF4B4B;
    #     border-radius: 0.5rem;
    #     text-decoration: none;
    #     font-weight: bold;">
    #     Login with Google
    # </a>
    # """
    # st.markdown(button_html, unsafe_allow_html=True)
else:
    from agent import agent
    # This section is shown only after the user is fully logged in and authenticated
    st.sidebar.info("✅ You are connected to your Google Calendar.")
    st.sidebar.header("Account")
    if st.sidebar.button("Logout and Revoke Access"):
        delete_creds_from_firestore(st.session_state.get('user_id'))
        st.session_state['credentials'] = None
        st.session_state['user_id'] = None # Clear user_id to force re-entry
        st.rerun()

    float_init()

    def autoplay_audio(wav_bytes):
        b64 = base64.b64encode(wav_bytes).decode("utf-8")
        md = f"""
        <audio autoplay>
        <source src="data:audio/wav;base64,{b64}" type="audio/wav">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)

    # Initialize session state for managing chat messages
    def initialize_session_state():
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Hi! How may I assist you today?"}]

    initialize_session_state()


    # st.title("Voice Chatbot 🤖")

    # Create a container for the microphone and audio recording
    footer_container = st.container()
    with footer_container:
        audio_bytes = audio_recorder(pause_threshold=2.0)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if audio_bytes:
        with st.spinner("Transcribing..."):
            transcript = transcribe_audio(audio_bytes)
            if transcript:
                st.session_state.messages.append({"role": "user", "content": transcript})
                with st.chat_message("user"):
                    st.write(transcript)
                
                
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking🤔..."):
                final_response = agent(st.session_state.messages[-1]["content"])
                final_response = re.sub(r"[^a-zA-Z0-9 ,.!?'-]", '', final_response)
            with st.spinner("Generating audio response..."):
                audio_bytes = generate_tts(final_response)
                autoplay_audio(audio_bytes)
            st.write(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response})
            

    # Float the footer container and provide CSS to target it with
    footer_container.float("bottom: 0rem;")
