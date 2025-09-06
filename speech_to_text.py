# example.py
import os
from dotenv import load_dotenv
from io import BytesIO
from elevenlabs.client import ElevenLabs

load_dotenv()

elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)

def transcribe_audio(audio_path = "/Users/sahilkhan/VOICE_REPOS/Voice-to-text-and-voice-chatbot/output_audio.opus"):
    with open(audio_path, "rb") as f:
        audio_data = BytesIO(f.read())

    transcription = elevenlabs.speech_to_text.convert(
        file=audio_data,
        model_id="scribe_v1", # Model to use, for now only "scribe_v1" is supported
        tag_audio_events=True, # Tag audio events like laughter, applause, etc.
        language_code="eng", # Language of the audio file. If set to None, the model will detect the language automatically.
        diarize=True, # Whether to annotate who is speaking
    )

    return transcription.text

if __name__ == "__main__":
    audio_path = "/Users/sahilkhan/VOICE_REPOS/Voice-to-text-and-voice-chatbot/output_audio.opus"
    transcribe_audio(audio_path)