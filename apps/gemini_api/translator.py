from __future__ import annotations
import os
from typing import Generator, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Common language mapping
LANG_MAP = {
    "en": "English",
    "es": "Spanish",
    "hi": "Hindi",
    "zh": "Chinese",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
}


def _normalize_lang(lang: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Accepts 'en' or 'English' and returns (code, display_name)."""
    if not lang:
        return None, None
    l = lang.strip().lower()

    if l in LANG_MAP:
        return l, LANG_MAP[l]

    for code, name in LANG_MAP.items():
        if l == name.lower():
            return code, name

    return l, lang.strip()


def _build_system_prompt(source_disp: Optional[str], target_disp: str) -> str:
    """Builds the system instruction for Gemini."""
    src_part = (
        f"Source language is {source_disp}."
        if source_disp
        else "If unclear, auto-detect the source language."
    )
    return (
        "You are a low-latency meeting interpreter. "
        f"{src_part} Translate to {target_disp}. "
        "Preserve tone and intent. Prefer short, simple sentences. "
        "If the source is incomplete, translate the best-guess fragment without adding new facts. "
        "Only output the translation, nothing else."
    )


class StreamingTranslator:
    """
    Stateless per-call translator that takes:
      - from_lang (speaker language)
      - to_lang   (listener language)
      - text      (ASR text from Aaryan)
    Returns only the translated text.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model = genai.GenerativeModel(model_name)

    # ---------- One-shot (returns a single translated string) ----------
    def translate_once(self, text: str, from_lang: Optional[str], to_lang: str) -> str:
        from_code, from_disp = _normalize_lang(from_lang)
        to_code, to_disp = _normalize_lang(to_lang)

        system_prompt = _build_system_prompt(from_disp, to_disp or to_lang)
        prompt = f"{system_prompt}\n\nSource text: {text}"

        resp = self.model.generate_content(prompt)
        translated = (getattr(resp, "text", "") or "").strip()

        return translated

    # ---------- Streaming (yields partial translated chunks) ----------
    def translate_stream(
        self, text: str, from_lang: Optional[str], to_lang: str
    ) -> Generator[str, None, None]:
        from_code, from_disp = _normalize_lang(from_lang)
        _, to_disp = _normalize_lang(to_lang)

        system_prompt = _build_system_prompt(from_disp, to_disp or to_lang)
        prompt = f"{system_prompt}\n\nSource text: {text}"

        try:
            stream = self.model.generate_content(prompt, stream=True)
            for chunk in stream:
                piece = getattr(chunk, "text", "")
                if piece:
                    if not piece.endswith((" ", "\n")):
                        piece += " "
                    yield piece
        except Exception as e:
            yield f"[translation_error]: {type(e).__name__}: {e}\n"


# ---------- Singleton Instance ----------
_translator_singleton = StreamingTranslator()


# ---------- Wrappers for Aaryan's order (to_lang, from_lang, text) ----------
def translate_text_ordered(to_lang: str, from_lang: Optional[str], text: str) -> str:
    """
    Aaryan calls this with (to_lang, from_lang, text).
    Returns: translated_text (string only)
    """
    return _translator_singleton.translate_once(text, from_lang, to_lang)


def translate_text_stream_ordered(
    to_lang: str, from_lang: Optional[str], text: str
) -> Generator[str, None, None]:
    """
    Streaming variant for Aaryan's order.
    Yields translated text fragments.
    """
    return _translator_singleton.translate_stream(text, from_lang, to_lang)


# ---------- Local Test ----------
if __name__ == "__main__":
    print("One-shot (Aaryan order):")
    translation = translate_text_ordered("es", "en", "We can begin in five minutes.")
    print("Translated:", translation)

    print("\nStreaming (Aaryan order):")
    for part in translate_text_stream_ordered("es", "en", "Please review the document by EOD."):
        print(part, end="", flush=True)
    print()
