# 🗣️ Voice-Powered Google Calendar Agent

A voice-driven AI assistant that acts as your personal scheduler. Built with **Streamlit**, **LangChain**, and **Google Gemini**, it lets you manage Google Calendar events through natural, conversational voice commands.

---

## ✨ Key Features

- **Voice-to-Voice interaction:** Speak a command; the agent replies with synthesized voice.
- **Context-aware agent core:** Powered by Google Gemini and LangChain; handles clarifying questions and tool calls.
- **Full Calendar CRUD:** Create, read, update, delete events via natural language.
- **Secure authentication:** OAuth 2.0 flow with Google; user tokens stored securely (Firestore for this project).
- **Persistent conversation memory:** Summarization + memory so the agent remembers context across a session.
- **Streamlit Cloud compatible:** Use Streamlit secrets manager or a local `.streamlit/secrets.toml` file.

---

## 📁 Repository Overview

- `app.py` — Streamlit app (UI, auth handling, voice recorder)
- `agent.py` — Scheduling agent orchestration
- `speech_to_text.py` — STT pipeline (e.g., Eleven Labs)
- `text_to_speech.py` — TTS pipeline (e.g., Eleven Labs)
- `calenderTool.py` — Calendar tool functions (create/find/update/delete events)
- `prompt.txt` — System prompt for the agent
- `.streamlit/secrets.toml` — **(not included in repo)** — store your credentials locally or via Streamlit Cloud secrets

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.9+
- Google Cloud project with Google Calendar API enabled
- Firebase project with Firestore (optional, used for token/session storage in this project)
- Eleven Labs (or other) account for STT/TTS (if you use those services)

### 1. Clone the repo

```bash
git clone https://github.com/5ah1lKhan/Voice-Chatbot.git
cd Voice-Chatbot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure secrets

Create a folder named `.streamlit` in the project root and add a `secrets.toml` file. **Do not commit this file to git** — it contains sensitive credentials.

**Important:** Use fenced code blocks in this README (and in your docs) so the TOML is displayed correctly on GitHub. Below is a ready-to-copy template. Paste it into `.streamlit/secrets.toml` and replace the placeholder values.

```toml
# .streamlit/secrets.toml

# For local desktop (installed app) Google OAuth 2.0 credentials
[google_credentials]
installed = {
  client_id = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com",
  project_id = "your-gcp-project-id",
  auth_uri = "https://accounts.google.com/o/oauth2/auth",
  token_uri = "https://oauth2.googleapis.com/token",
  auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs",
  client_secret = "YOUR_GOOGLE_CLIENT_SECRET",
  redirect_uris = ["http://localhost:8501"]
}

# If you deploy on Streamlit Cloud, you might use the `web` client config instead:
# [google_credentials]
# web = { client_id = "...", client_secret = "...", project_id = "...", auth_uri = "...", token_uri = "...", redirect_uris = ["https://your-streamlit-app.streamlitapp.com/"] }

[firebase_service_account]
# Copy fields from your Firebase service account JSON. IMPORTANT: the private_key is multi-line — use triple quotes.
type = "service_account"
project_id = "your-firebase-project-id"
private_key_id = "..."
private_key = """-----BEGIN PRIVATE KEY-----\n...your...key...\n-----END PRIVATE KEY-----\n"""
client_email = "service-account-email@your-firebase-project.iam.gserviceaccount.com"
client_id = "..."
# ...copy the rest of the fields from your Firebase JSON (if needed)

[gemini]
api_key = "YOUR_GEMINI_API_KEY"

[elevenlabs]
api_key = "YOUR_ELEVENLABS_API_KEY"
```

> **Reminder:** Wrap multi-line private keys with triple quotes exactly as shown. The `\n` sequences preserve newlines inside the TOML file.

---

### 4. Run locally

```bash
streamlit run app.py
```

### 5. Deployed on Streamlit Cloud
Visit the app : [Voice Chatbot](https://voice-chatbot-next.streamlit.app/)