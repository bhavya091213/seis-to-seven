# src/main/python/apps/main.py
import sys
import json
from apps.ASR.audio_processor import receive_data
from apps.gemini_api.translator import translate_text
from apps.routing.processing import clone_and_speak


def processAudio(from_lang: str, to_lang: str, audio_b64: str):
    """
    In: base64 16-bit 16kHz WAV (mono recommended)
    Out: generator yielding audio bytes (MP3/WAV) from TTS
    """
    print(f"[main.py] STT from '{from_lang}' -> '{to_lang}'", file=sys.stderr, flush=True)
    print(f"[main.py] audio_b64 len={len(audio_b64)}", file=sys.stderr, flush=True)

    # 1) ASR: returns dict with keys: to_lang, from_lang, transcription, audio_data
    response_asr = receive_data(from_lang, to_lang, audio_b64)

    # 2) Translate
    response_trans = translate_text(
        response_asr.get("to_lang"),
        response_asr.get("from_lang"),
        response_asr.get("transcription"),
        response_asr.get("audio_data"),
    )

    # 3) TTS: returns an iterator of bytes
    return clone_and_speak(
        response_trans.get("file"),
        response_trans.get("translated_text")
    )


if __name__ == "__main__":
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            raise ValueError("No JSON on stdin")

        data = json.loads(raw_input)
        from_lang = data.get("from_lang")
        to_lang   = data.get("to_lang")
        audio_b64 = data.get("audio_b64")

        if not all([from_lang, to_lang, audio_b64]):
            raise ValueError("Missing fields: from_lang, to_lang, audio_b64")

        audio_stream = processAudio(from_lang, to_lang, audio_b64)

        for chunk in audio_stream:
            if isinstance(chunk, (bytes, bytearray)):
                sys.stdout.buffer.write(chunk)
                sys.stdout.flush()  # make Java see it immediately
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
