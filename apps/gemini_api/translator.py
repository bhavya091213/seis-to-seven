from __future__ import annotations
import os
import hashlib
from typing import Dict, Optional, Tuple, Generator
from dotenv import load_dotenv
import google.generativeai as genai
from apps.routing.processing import text_to_speech_stream, create_voice

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

# Voice Creation Cache (avoid re-cloning identical sources repeatedly)
_voice_cache: dict[tuple[str, str], str] = {}


def _hash_file(path: str) -> str:
    """Compute a short SHA256 hash of a file for caching key purposes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _create_or_get_voice(saved_wav_path: str, voice_name: Optional[str], description: Optional[str]) -> str:
    """Create a cloned voice unless we already cached one for (voice_name, file_hash)."""
    if not voice_name:
        # Provide deterministic fallback name
        voice_name = "ClonedVoice"
    if not description:
        description = "Auto-generated cloned voice from recording."

    file_hash = _hash_file(saved_wav_path)
    cache_key = (voice_name, file_hash)

    if cache_key in _voice_cache:
        return _voice_cache[cache_key]

    try:
        voice_id = create_voice(
            name=voice_name,
            description=description,
            file_paths=[saved_wav_path],
        )
    except Exception as e:  # noqa: BLE001
        # Provide a static default voice id fallback (same as processing.py example).
        # In production, you might look up an existing stable voice.
        voice_id = "JBFqnCBsd6RMkjVDRZzb"
        # For observability you might log this; printing for now.
        print(f"[translator] Voice creation failed, using fallback. Error: {e}")

    _voice_cache[cache_key] = voice_id
    return voice_id

# Function Aaryan will call directly
def translate_text(to_lang: str, from_lang: str, text: str, saved_wav_path: str, voice_name: Optional[str] = None, voice_description: Optional[str] = None) -> Dict[str, any]:
    """
    Called by Aaryan.
    Receives: (to_lang, from_lang, text, saved_wav_path, voice_name, voice_description)
    Returns: {'translated_text', 'from_lang', 'to_lang', 'voice_id', 'audio_stream'}
    """
    translation_result = _translator_singleton.translate(to_lang, from_lang, text)
    
    # Create or get voice from the saved WAV file
    voice_id = _create_or_get_voice(
        saved_wav_path=saved_wav_path,
        voice_name=voice_name,
        description=voice_description
    )
    
    # Call text_to_speech_stream with translated text
    audio_stream = text_to_speech_stream(
        text=translation_result['translated_text'],
        voice_id=voice_id
    )
    
    return {
        **translation_result,
        'voice_id': voice_id,
        'audio_stream': audio_stream
    }