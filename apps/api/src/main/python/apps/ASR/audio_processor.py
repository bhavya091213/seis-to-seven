# example.py
import os
from dotenv import load_dotenv
from io import BytesIO
import base64
import requests
from elevenlabs.client import ElevenLabs

load_dotenv()

elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)

def receive_data(from_lang: str, to_lang: str, audio_file: str) -> dict:
    # encode audio to b64
    audio_data = BytesIO(base64.b64decode(audio_file))
    transcription = elevenlabs.speech_to_text.convert(
        file=audio_data,
        model_id="scribe_v1", # Model to use, for now only "scribe_v1" is supported
        tag_audio_events=True, # Tag audio events like laughter, applause, etc.
        language_code=from_lang, # Language of the audio file. If set to None, the model will detect the language automatically.
        diarize=False, # Whether to annotate who is speaking
    )
    
    onlytext = transcription.text
    return {"transcription": onlytext, "from_lang": from_lang, "to_lang": to_lang, "audio_data": audio_file} # comes in as a string, needs to be decoded, and then bytes in mihirs thing

# data_bytes = base64.b64decode(b64) 

