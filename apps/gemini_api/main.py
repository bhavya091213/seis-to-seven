# main.py

# If main.py is at the project root and your translator is in gemini_api/translator.py:
from gemini_api.translator import (
    translate_text_ordered,          # (to_lang, from_lang, text) -> dict
    translate_text_stream_ordered,   # (to_lang, from_lang, text) -> generator
)

def aaryan_to_simir(to_lang: str, from_lang: str, text: str) -> dict:
    """
    Aaryan calls this with exactly three strings:
      - to_lang   (listener language, e.g., "es" or "Spanish")
      - from_lang (speaker language, e.g., "en" or "English")
      - text      (ASR output from Aaryan)
    Returns a dict: {translated_text, from_lang, to_lang, source_text}
    """
    return translate_text_ordered(to_lang, from_lang, text)

def aaryan_to_simir_stream(to_lang: str, from_lang: str, text: str):
    """
    Streaming variant that yields partial translation chunks.
    """
    return translate_text_stream_ordered(to_lang, from_lang, text)

# ---- Demo runner (local smoke test) ----
if __name__ == "__main__":
    # One-shot example (simulate Aaryan -> Simir)
    res = aaryan_to_simir("es", "en", "We can begin in five minutes.")
    print("Non-streaming result:")
    print(res)  # {'translated_text': '...', 'from_lang': 'en', 'to_lang': 'es', 'source_text': '...'}

    # Streaming example (simulate partials for live UI)
    print("\nStreaming result:")
    for part in aaryan_to_simir_stream("es", "en", "Please review the document by EOD."):
        print(part, end="", flush=True)
    print()
