from apps.ASR.audio_processor import receive_data
from apps.gemini_api.translator import translate_text
import sys
import json
import base64
from apps.routing.processing import clone_and_speak

def processAudio(from_lang: str, to_lang: str, audio_b64: str):
    """
    Processes an incoming 16-bit 16kHz WAV audio file (in bytes),
    along with the source and target languages.

    Args:
        from_lang (str): The language the speaker is speaking in.
        to_lang (str): The language to translate the speech into.
        audio_bytes (bytes): Raw audio data (16-bit, 16kHz WAV) from API input.
    """
    # Placeholder for future logic
    print(f"Processing audio from '{from_lang}' to '{to_lang}'...", file=sys.stderr)
    print(f"Received audio data size: {len(audio_b64)} bytes", file=sys.stderr)

    response_asr = receive_data(from_lang, to_lang, audio_b64)
    response_trans = translate_text(response_asr.get("to_lang"), response_asr.get("from_lang"), response_asr.get("transcription"), response_asr.get("audio_data"))


    # Later, you’ll call Aaryan’s STT, your Translator, Mihir’s TTS, etc.
    # For now, we’ll just echo back the audio for testing.
    return clone_and_speak(response_trans.get("file"), response_trans.get("translated_text"))


if __name__ == "__main__":
    """
    Expected STDIN input format (JSON):
    {
        "from_lang": "en",
        "to_lang": "es",
        "audio_b64": "<base64-encoded WAV bytes>"
    }

    STDOUT output format (JSON):
    {
        "status": "success",
        "processed_audio_b64": "<base64-encoded WAV bytes>"
    }
    """
    try:
        # Read JSON from stdin
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            raise ValueError("No input provided on stdin")

        data = json.loads(raw_input)
        from_lang = data.get("from_lang")
        to_lang = data.get("to_lang")
        audio_b64 = data.get("audio_b64")

        if not all([from_lang, to_lang, audio_b64]):
            raise ValueError("Missing one or more required fields: from_lang, to_lang, audio_b64")


        # Process the audio (your future pipeline)
        # processed_audio = processAudio(from_lang, to_lang, audio_b64)

        # # Flush raw audio bytes to STDOUT (important!)
        # sys.stdout.buffer.write(processed_audio)
        # sys.stdout.flush()

        audio_stream = processAudio(from_lang, to_lang, audio_b64)

        for chunk in audio_stream:
            if isinstance(chunk, (bytes, bytearray)):
                sys.stdout.buffer.write(chunk)
        sys.stdout.flush()

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
