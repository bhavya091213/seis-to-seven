from __future__ import annotations
import os
from typing import Dict, Generator, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

LANG_MAP: Dict[str, str] = {
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
    """
    Accept 'en' or 'English' and return (code, display_name).
    Unknowns pass through as (normalized_input, original_titlecase).
    """
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
    """
    Build a clear, low-latency interpreter instruction with explicit source/target.
    """
    src_part = (
        f"Source language is {source_disp}."
        if source_disp else
        "If unclear, auto-detect the source language."
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
    and returns translated text (or streams partials).
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model = genai.GenerativeModel(model_name)

    # ---------- One-shot (returns a dict Mihir can use directly) ----------
    def translate_once(self, text: str, from_lang: Optional[str], to_lang: str) -> Dict[str, str]:
        from_code, from_disp = _normalize_lang(from_lang)
        to_code,   to_disp   = _normalize_lang(to_lang)

        system_prompt = _build_system_prompt(from_disp, to_disp or to_lang)
        prompt = f"{system_prompt}\n\nSource text: {text}"

        resp = self.model.generate_content(prompt)
        translated = (getattr(resp, "text", "") or "").strip()

        return {
            "from_lang": from_code or (from_lang or ""),
            "to_lang":   to_code   or (to_lang   or ""),
            "translated_text": translated,
            "source_text": text,
        }

    def translate_stream(self, text: str, from_lang: Optional[str], to_lang: str) -> Generator[str, None, None]:
        from_code, from_disp = _normalize_lang(from_lang)
        _,        to_disp    = _normalize_lang(to_lang)

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

_translator_singleton = StreamingTranslator()

def translate_text(text: str, from_lang: Optional[str], to_lang: str) -> Dict[str, str]:
    """One-shot; returns dict with translated_text, from_lang, to_lang, source_text."""
    return _translator_singleton.translate_once(text, from_lang, to_lang)

def translate_text_stream(text: str, from_lang: Optional[str], to_lang: str):
    """Streaming generator; yields partial strings."""
    return _translator_singleton.translate_stream(text, from_lang, to_lang)

if __name__ == "__main__":
    print("One-shot:")
    print(translate_text("Let's start the meeting now.", "en", "es"))

    print("\nStreaming:")
    for part in translate_text_stream("Please send the summary after the call.", "English", "Spanish"):
        print(part, end="", flush=True)
    print()
