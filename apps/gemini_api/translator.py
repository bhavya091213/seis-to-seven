from __future__ import annotations
import os
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Supported language mappings
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
    """Builds the Gemini system prompt for translation."""
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


class Translator:
    """
    Handles a single translation request:
    - Receives: to_lang, from_lang, text
    - Returns: translated_text, from_lang, to_lang
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model = genai.GenerativeModel(model_name)

    def translate(self, to_lang: str, from_lang: Optional[str], text: str) -> Dict[str, str]:
        """Translate a full text string once."""
        from_code, from_disp = _normalize_lang(from_lang)
        to_code, to_disp = _normalize_lang(to_lang)

        system_prompt = _build_system_prompt(from_disp, to_disp or to_lang)
        prompt = f"{system_prompt}\n\nSource text: {text}"

        # Call Gemini
        response = self.model.generate_content(prompt)
        translated_text = (getattr(response, "text", "") or "").strip()

        # Return the structured result
        return {
            "translated_text": translated_text,
            "from_lang": from_code or from_lang or "",
            "to_lang": to_code or to_lang or "",
        }


# Singleton instance
_translator_singleton = Translator()

# Function Aaryan will call directly
def translate_text(to_lang: str, from_lang: str, text: str) -> Dict[str, str]:
    """
    Called by Aaryan.
    Receives: (to_lang, from_lang, text)
    Returns: {'translated_text', 'from_lang', 'to_lang'}
    """
    return _translator_singleton.translate(to_lang, from_lang, text)