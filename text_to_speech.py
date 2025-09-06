from google import genai
from google.genai import types
# from google.genai.types import GenerateContentConfig, Tool
# from IPython.display import display, HTML, Markdown
# import io
# import json
# import re
from dotenv import load_dotenv
import os
from pydub import AudioSegment
load_dotenv()

def opus_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """
    Converts raw PCM audio bytes to an Opus file using pydub.
    
    Args:
        filename (str): The name of the output .opus file.
        pcm (bytes): The raw PCM audio data.
        channels (int): The number of audio channels (e.g., 1 for mono).
        rate (int): The sample rate in Hz.
        sample_width (int): The sample width in bytes (e.g., 2 for 16-bit).
    """
    # Create an AudioSegment from the raw PCM data
    audio_segment = AudioSegment(
        data=pcm,
        sample_width=sample_width,
        frame_rate=rate,
        channels=channels
    )

    # Export the AudioSegment to an Opus file
    audio_segment.export(filename, format="opus")
    print(f"Audio content written to file '{filename}'")


def generate_tts(PROMPT, VOICE='Kore', file_name="output_audio"):

    client = genai.Client(
        api_key=os.environ.get("gemini")
    )
# 
    response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=PROMPT,
    config=types.GenerateContentConfig(
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=VOICE,
                )
            )
        ),
    )
    )

    data = response.candidates[0].content.parts[0].inline_data.data
    # set the sample rate
    rate = 24000
    file_name = f'{file_name}.opus'

    # print(f"\nSaving sample rate: {rate}")
    opus_file(file_name, data, rate=rate)

    return file_name

if __name__ == "__main__":
    voice = 'Kore'
    # voice = 'Zephyr'
    # text  = "sing: Me hu jiyan, mera gala h bhut sureela"
    # text = "Natural, friendly, professional tone: Hello, how are you doing today? I hope you're having a great day!"
    # text = '''Yes, you have two meetings today:

    #         "Discussion - Sahil (Python - Delhi)" from 09:30 AM to 10:00 AM.
    #         "Meet - AI & Simulations" from 08:00 PM to 09:00 PM.'''
    text = "Hello, I am your voice assistant. How can I help you today?"
    generate_tts(text, voice, "output_audio")
