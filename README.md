🗣️ Voice-Powered Google Calendar Agent
This project is a sophisticated, voice-driven AI assistant that acts as your personal scheduler. Built with Streamlit, LangChain, and Google Gemini, it allows you to manage your Google Calendar events through a natural, conversational voice interface.

The agent is designed to be stateful and secure, remembering your conversation history and managing authentication gracefully. It connects directly to your Google Calendar to create, find, update, and delete events, all guided by your voice commands.

Demo
A picture is worth a thousand words, and a video is worth a million! Here is a short demonstration of the agent in action.

(--> IMPORTANT: REPLACE THIS LINE with your GIF or Video <--)

To create a GIF for your README, you can use a tool like Giphy, EZgif, or Kapwing. Record your screen, convert the video to a GIF, and then upload the GIF to your GitHub repository. You can then embed it here using the following Markdown syntax:
![Demo GIF](link_to_your_gif_in_the_repo.gif)

✨ Key Features
🎙️ Voice-to-Voice Interaction: A complete hands-free experience. Speak your command, and the agent responds with a synthesized voice.

🧠 Intelligent Agent Core: Powered by Google Gemini and a custom LangChain agent, it understands context, asks clarifying questions, and manages a tool-calling loop.

🛠️ Full Calendar Management (CRUD):

Create: "Schedule a meeting with the design team tomorrow at 10 AM."

Read: "What do I have scheduled for Friday?"

Update: "Change my 10 AM meeting to 11 AM."

Delete: "Cancel my project sync meeting."

🔐 Secure Authentication: Implements a robust OAuth 2.0 flow with Google, securely storing user tokens in Google Firestore. User sessions are managed with unique IDs to ensure privacy.

💾 Persistent Memory: The agent remembers your conversations in the session. Allowing more contextual answers

☁️ Streamlit Cloud Ready: Designed for easy deployment, with all API key and secret management handled through Streamlit's secrets manager.

🔑 Flexible API Key Management: Use the default API keys or provide your own directly in the UI.

🚀 How It Works (System Architecture)
User Interface (Streamlit): The app.py script creates a web interface with a voice recorder. It manages user authentication, chat display, and API key inputs.

Authentication & Session Management:

The app first prompts for a unique User ID to namespace all data.

It then initiates a Google OAuth 2.0 flow. The app state and User ID are temporarily stored in Firestore to survive the redirect.

Upon successful login, the user's API token is securely saved to a Firestore document tied to their User ID.

Voice Processing:

Speech-to-Text (speech_to_text.py): The user's recorded audio is sent to the Eleven Labs model to be transcribed into text.

Text-to-Speech (text_to_speech.py): The agent's final text response is sent to the Eleven Labs model to be synthesized into audio, which is then played back automatically in the browser.

Agent Core (agent.py):

The transcribed text is passed to the SchedulingAgent.

The agent uses Google Gemini, a detailed system prompt (prompt.txt), and a set of tools to decide on the next action.

It maintains a conversation history (memory).

It handles long conversations by memory summarization by llm(gemini)

Calendar Tools (calenderTool.py):

These are the functions the agent can call. They interact directly with the Google Calendar API using the user's stored credentials to perform actions like creating, finding, or deleting events.

🛠️ Setup and Installation
Follow these steps to run the project locally or deploy it to Streamlit Community Cloud.

Prerequisites
Python 3.9+

A Google Cloud Platform project with the Google Calendar API enabled.

An Eleven Labs account for STT/TTS.

A Google Firebase project with Firestore enabled.

1. Clone the Repository
git clone https://github.com/5ah1lKhan/Voice-Chatbot.git
cd Voice-Chatbot

2. Install Dependencies
Install all the required Python packages from the requirements.txt file.

pip install -r requirements.txt

3. Configure Your Secrets
This is the most important step. Create a folder named .streamlit in your project root and, inside it, create a file named secrets.toml.

Voice-Chatbot/
└── .streamlit/
    └── secrets.toml

Populate secrets.toml with your credentials. Use the following template:

# In .streamlit/secrets.toml

#for web application
#[google_credentials]
#web = { client_id = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com", project_id = "your-gcp-project-id", auth_uri = "...", token_uri = "...", auth_provider_x509_cert_url = "...", client_secret = "YOUR_GOOGLE_CLIENT_SECRET", redirect_uris =  }

#for local desktop
[google_credentials]
installed = { client_id = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com", project_id = "your-gcp-project-id", auth_uri = "...", token_uri = "...", auth_provider_x509_cert_url = "...", client_secret = "YOUR_GOOGLE_CLIENT_SECRET", redirect_uris = ["http://localhost:8501"] }


[firebase_service_account]
type = "service_account"
project_id = "your-firebase-project-id"
private_key_id = "..."
# REMEMBER: Use triple quotes for the multi-line private key
private_key = """-----BEGIN PRIVATE KEY-----\n...your...key...\n-----END PRIVATE KEY-----\n"""
client_email = "..."
client_id = "..."
# ... (copy the rest of the fields from your Firebase service account JSON)

[gemini]
api_key = "YOUR_GEMINI_API_KEY"

[elevenlabs]
api_key = "YOUR_ELEVENLABS_API_KEY"

4. Run the Application Locally
Once your secrets are configured, you can run the app with a single command:

streamlit run app.py

5. Deploy to Streamlit Cloud
To deploy, follow the official Streamlit deployment guide. During the advanced setup, you will copy the entire contents of your local secrets.toml file into the Streamlit Cloud secrets manager.