"""Audio processing pipeline for converting a recorded WAV file into text,
translating it, and preparing a cloned voice for TTS output.

Responsibilities implemented here (as requested):
1. Accept a path to an incoming .wav file (captured from mic by another system).
2. Persist (copy) that file into a local `recordings` folder under `apps/`.
3. Perform Speech-to-Text (STT) using ElevenLabs Speech-to-Text.
4. Translate the transcribed text using Gemini translator (`translate_text`).
5. Create (clone) a voice via `create_voice` (from `processing.py`) using the saved WAV.
6. Return structured data including transcript, translation, language codes, saved path, and voice_id.

NOTE:
 - This module does not itself perform Text-To-Speech playback; that remains in `processing.text_to_speech_stream`.
 - Voice cloning on every call can be expensive & slow; a simple cache mechanism is provided so the same
   cloned voice isn't created redundantly for identical (voice_name, source file hash) pairs during a run.
 - The ElevenLabs Python SDK interface for STT may evolve; adjust the function `_run_speech_to_text` if needed.

Environment Variables Expected:
 - ELEVENLABS_API_KEY : for ElevenLabs SDK
 - GEMINI_API_KEY      : required indirectly by translator module

Public Entry Points:
 - process_recording(...)
 - transcribe_and_translate(...)

"""

from __future__ import annotations

import os
import hashlib
import shutil
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Local imports (relative paths based on repository structure)
from apps.gemini_api.translator import translate_text  # translation


# ---------------------------------------------------------------------------
# Environment & Client Initialization
# ---------------------------------------------------------------------------
load_dotenv()  # Load .env in current or parent directories

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVEN_API_KEY:
	raise RuntimeError(
		"ELEVENLABS_API_KEY is not set. Please add it to your .env file."  # noqa: E501
	)

eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY)


# ---------------------------------------------------------------------------
# Configuration Constants
# ---------------------------------------------------------------------------
DEFAULT_STT_MODEL = "eleven_multilingual_v2"  # Adjust if product naming differs
RECORDINGS_DIR_NAME = "recordings"
ALLOWED_EXT = {".wav"}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
@dataclass
class ProcessingResult:
	"""Represents the outcome of a full processing cycle."""

	saved_wav_path: str
	original_text: str
	translated_text: str
	from_lang: str
	to_lang: str
	voice_id: str
	audio_stream: Any
	meta: Dict[str, Any]

	def to_dict(self) -> Dict[str, Any]:
		return {
			"saved_wav_path": self.saved_wav_path,
			"original_text": self.original_text,
			"translated_text": self.translated_text,
			"from_lang": self.from_lang,
			"to_lang": self.to_lang,
			"voice_id": self.voice_id,
			"audio_stream": self.audio_stream,
			"meta": self.meta,
		}


# ---------------------------------------------------------------------------
# Utility Helpers
# ---------------------------------------------------------------------------
def _ensure_recordings_dir() -> str:
	"""Ensure the recordings directory exists under `apps/` and return its path."""
	# This file lives at: apps/ASR/audio_processor.py -> parent of parent is repo root? parent is ASR, parent of that is apps.
	apps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
	recordings_dir = os.path.join(apps_dir, RECORDINGS_DIR_NAME)
	os.makedirs(recordings_dir, exist_ok=True)
	return recordings_dir


def _hash_file(path: str) -> str:
	"""Compute a short SHA256 hash of a file for caching key purposes."""
	h = hashlib.sha256()
	with open(path, "rb") as f:
		for chunk in iter(lambda: f.read(8192), b""):
			h.update(chunk)
	return h.hexdigest()[:16]


def _copy_into_recordings(src_wav_path: str) -> str:
	"""Copy the provided WAV into the recordings directory with a timestamped filename."""
	if not os.path.isfile(src_wav_path):
		raise FileNotFoundError(f"Input file not found: {src_wav_path}")

	ext = os.path.splitext(src_wav_path)[1].lower()
	if ext not in ALLOWED_EXT:
		raise ValueError(f"Unsupported file extension '{ext}'. Expected one of {ALLOWED_EXT}")

	recordings_dir = _ensure_recordings_dir()
	base_name = os.path.splitext(os.path.basename(src_wav_path))[0]
	ts = int(time.time() * 1000)
	dest_name = f"{base_name}_{ts}.wav"
	dest_path = os.path.join(recordings_dir, dest_name)
	shutil.copy2(src_wav_path, dest_path)
	return dest_path


# ---------------------------------------------------------------------------
# Speech-to-Text via ElevenLabs
# ---------------------------------------------------------------------------
def _run_speech_to_text(wav_path: str, model_id: str = DEFAULT_STT_MODEL) -> str:
	"""Perform speech-to-text. Adjust this if ElevenLabs SDK updates.

	Currently assumes a method `speech_to_text.convert` returning an object/dict with a `text` field.
	Fallback strategies provided to extract the transcript robustly.
	"""
	with open(wav_path, "rb") as f:
		# Attempt primary API call; update if SDK uses a different namespace.
		try:
			response = eleven_client.speech_to_text.convert(
				file=f,  # type: ignore[arg-type]
				model_id=model_id,
			)
		except AttributeError as e:
			raise RuntimeError(
				"ElevenLabs SDK interface for STT seems different. "
				"Verify the method name (expected speech_to_text.convert)."
			) from e
		except Exception as e:  # noqa: BLE001
			raise RuntimeError(f"Speech-to-Text conversion failed: {e}") from e

	# Try to extract the transcript text gracefully
	if response is None:
		raise RuntimeError("Empty response from STT API")

	if isinstance(response, str):
		return response.strip()

	# Object with .text
	text_val = getattr(response, "text", None)
	if text_val:
		return str(text_val).strip()

	# Dict-like
	if isinstance(response, dict):
		for key in ("text", "transcript", "transcription"):
			if key in response and response[key]:
				return str(response[key]).strip()

	# Fallback to repr
	return repr(response)


# ---------------------------------------------------------------------------
# Translation Wrapper
# ---------------------------------------------------------------------------
def _translate_text(transcribed_text: str, from_lang: str, to_lang: str, saved_wav_path: str, voice_name: Optional[str] = None, voice_description: Optional[str] = None) -> Dict[str, any]:
	"""Delegate to Gemini translator; normalizes input."""
	return translate_text(to_lang=to_lang, from_lang=from_lang, text=transcribed_text, saved_wav_path=saved_wav_path, voice_name=voice_name, voice_description=voice_description)


# ---------------------------------------------------------------------------
# Voice Creation moved to translator.py for proper sequential flow
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Public Orchestration Functions
# ---------------------------------------------------------------------------
def transcribe_and_translate(
	wav_path: str,
	from_lang: str,
	to_lang: str,
	*,
	voice_name: Optional[str] = None,
	voice_description: Optional[str] = None,
	model_id: str = DEFAULT_STT_MODEL,
) -> Dict[str, any]:
	"""Convenience: run STT then translation with TTS. Returns translator result dict augmented with 'original_text'."""
	saved_path = _copy_into_recordings(wav_path)
	original_text = _run_speech_to_text(saved_path, model_id=model_id)
	
	translation = _translate_text(original_text, from_lang=from_lang, to_lang=to_lang, saved_wav_path=saved_path, voice_name=voice_name, voice_description=voice_description)
	return {
		"original_text": original_text,
		**translation,
		"saved_wav_path": saved_path,
	}


def process_recording(
	wav_path: str,
	from_lang: str,
	to_lang: str,
	*,
	voice_name: Optional[str] = None,
	voice_description: Optional[str] = None,
	stt_model_id: str = DEFAULT_STT_MODEL,
	create_voice_flag: bool = True,
) -> ProcessingResult:
	"""Full pipeline: save -> STT -> translate -> (optionally) clone voice.

	Args:
		wav_path: Path to source .wav file produced by the mic capture system.
		from_lang: Source language code/name.
		to_lang: Target language code/name.
		voice_name: Optional custom name for the cloned voice.
		voice_description: Optional description for the cloned voice.
		stt_model_id: ElevenLabs STT model id.
		create_voice_flag: If False, skip cloning and use fallback voice id.

	Returns:
		ProcessingResult with all relevant fields.
	"""
	saved_wav_path = _copy_into_recordings(wav_path)
	original_text = _run_speech_to_text(saved_wav_path, model_id=stt_model_id)
	
	translation_result = _translate_text(
		original_text, 
		from_lang=from_lang, 
		to_lang=to_lang, 
		saved_wav_path=saved_wav_path,
		voice_name=voice_name if create_voice_flag else None,
		voice_description=voice_description if create_voice_flag else None
	)
	translated_text = translation_result.get("translated_text", "")

	result = ProcessingResult(
		saved_wav_path=saved_wav_path,
		original_text=original_text,
		translated_text=translated_text,
		from_lang=translation_result.get("from_lang", from_lang),
		to_lang=translation_result.get("to_lang", to_lang),
		voice_id=translation_result.get("voice_id", "JBFqnCBsd6RMkjVDRZzb"),
		audio_stream=translation_result.get("audio_stream"),
		meta={
			"stt_model_id": stt_model_id,
			"created_voice": create_voice_flag,
		},
	)
	return result


# ---------------------------------------------------------------------------
# CLI / Manual Test Harness
# ---------------------------------------------------------------------------
def _demo():  # pragma: no cover - convenience manual runner
	import argparse

	parser = argparse.ArgumentParser(description="Process a WAV through STT + translation + voice clone.")
	parser.add_argument("wav", help="Path to input WAV file")
	parser.add_argument("from_lang", help="Source language code or name (e.g., en or English)")
	parser.add_argument("to_lang", help="Target language code or name (e.g., es or Spanish)")
	parser.add_argument("--voice-name", dest="voice_name", default=None)
	parser.add_argument("--voice-desc", dest="voice_description", default=None)
	parser.add_argument("--no-clone", dest="no_clone", action="store_true", help="Skip voice cloning step")
	args = parser.parse_args()

	result = process_recording(
		wav_path=args.wav,
		from_lang=args.from_lang,
		to_lang=args.to_lang,
		voice_name=args.voice_name,
		voice_description=args.voice_description,
		create_voice_flag=not args.no_clone,
	)
	print("\n--- Processing Result ---")
	print(result.to_dict())


if __name__ == "__main__":  # pragma: no cover
	_demo()

