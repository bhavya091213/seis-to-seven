from __future__ import annotations
import os
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
from processing import text_to_speech_stream  # call Mihir's code

# ── Load API key ──────────────────────────────────────────────
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")
genai.configure(api_key=api_key)

# ── Supported language mappings ───────────────────────────────
LANG_MAP: Dict[str, str] = {
    "en": "English", "es": "Spanish", "zh": "Chinese", "hi": "Hindi",
    "fr": "French", "de": "German", "pt": "Portuguese", "ru": "Russian",
    "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "bn": "Bengali",
    "it": "Italian", "tr": "Turkish", "vi": "Vietnamese", "ta": "Tamil",
    "ur": "Urdu", "fa": "Persian (Farsi)", "pl": "Polish", "id": "Indonesian",
    "ms": "Malay", "th": "Thai", "sw": "Swahili", "nl": "Dutch", "uk": "Ukrainian",
}

def _norm_lang(lang: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not lang: return None, None
    l = lang.strip().lower()
    if l in LANG_MAP: return l, LANG_MAP[l]
    for code, name in LANG_MAP.items():
        if l == name.lower(): return code, name
    return l, lang.strip()

def _prompt(src_disp: Optional[str], tgt_disp: str) -> str:
    src = f"Source language is {src_disp}." if src_disp else "If unclear, auto-detect the source language."
    return (
        "You are a low-latency meeting interpreter. "
        f"{src} Translate to {tgt_disp}. "
        "Preserve tone and intent. Prefer short, simple sentences. "
        "If the source is incomplete, translate the best-guess fragment without adding new facts. "
        "Only output the translation, nothing else."
    )

# ── Core translator ───────────────────────────────────────────
class Translator:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model = genai.GenerativeModel(model_name)

    def translate(self, to_lang: str, from_lang: str, text: str, b64file: str ) -> dict:
        text = (text or "").strip()
        if not text:
            return {"translated_text": "", "from_lang": from_lang or "", "to_lang": to_lang or ""}
        if from_lang and to_lang and from_lang.lower() == to_lang.lower():
            return {"translated_text": text, "from_lang": from_lang, "to_lang": to_lang}

        from_code, from_disp = _norm_lang(from_lang)
        to_code, to_disp = _norm_lang(to_lang)
        prompt = f"{_prompt(from_disp, to_disp or to_lang)}\n\nSource text: {text}"

        resp = self.model.generate_content(prompt)
        translated = (getattr(resp, "text", "") or "").strip()
        return {"translated_text": translated, "from_lang": from_code or from_lang or "", "to_lang": to_code or to_lang or "", "file": b64file}

_translator = Translator()

def translate_text(to_lang: str, from_lang: str, text: str, b64file: str) -> Dict[str, str]:
    """Called by Aaryan — returns only translated text and langs."""
    return _translator.translate(to_lang, from_lang, text, b64file)

# def translate_and_send_to_mihir(to_lang: str, from_lang: str, text: str):
#     """
#     Translates the text, then calls Mihir's TTS function.
#     Your file no longer saves or manages audio — Mihir’s does.
#     """
#     result = translate_text(to_lang, from_lang, text)
#     translated = result["translated_text"]

#     # hand it directly to Mihir’s function
#     audio_stream = text_to_speech_stream(text=translated, voice_id=None)

#     # return both so the rest of the system can handle them
#     return {
#         "translated_text": translated,
#         "from_lang": result["from_lang"],
#         "to_lang": result["to_lang"],
#         "audio_stream": audio_stream
#     }
