# Audio Processing Pipeline

## Overview

This pipeline processes audio files through the following stages:
1. **Speech-to-Text (STT)** - Convert .wav audio to text using ElevenLabs
2. **Translation + Voice Cloning** - Translate text using Google Gemini API and create voice clone
3. **Text-to-Speech (TTS)** - Convert translated text to speech using the cloned voice

## Pipeline Flow

```
.wav file → audio_processor.py → translator.py → processing.py → main.py
    ↓              ↓                    ↓              ↓           ↓
  STT +         Translation +      Voice Clone +   TTS Stream →  JSON Output
 Save file      Voice Creation     TTS Generation                
```

## Files and Responsibilities

### `audio_processor.py`
- Accepts .wav file, from_lang, to_lang
- Converts speech to text using ElevenLabs STT
- Saves .wav file to `apps/recordings/` folder
- Calls `translate_text()` from translator.py
- Passes saved WAV path to translator for voice creation

### `translator.py` 
- Translates text using Google Gemini API
- **Creates voice clone** from saved WAV file
- Calls `text_to_speech_stream()` from processing.py
- Returns translation + voice_id + audio stream

### `processing.py`
- Provides voice cloning functionality via ElevenLabs
- Provides TTS streaming functionality
- Returns audio chunks

### `main.py`
- Stdin/stdout interface for clean integration
- Coordinates the entire pipeline
- Saves final audio to temporary file
- Returns JSON response

## Usage

### Programmatic (Direct Function Calls)
```python
from ASR.audio_processor import process_recording

result = process_recording(
    wav_path="input.wav",
    from_lang="en", 
    to_lang="es",
    voice_name="MyVoice"
)

# Save audio stream to file
with open("output.mp3", "wb") as f:
    for chunk in result.audio_stream:
        f.write(chunk)
```

### CLI Interface (Stdin/Stdout)
```bash
echo '{"wav_path":"input.wav","from_lang":"en","to_lang":"es"}' | python3 apps/main.py
```

**Input JSON Format:**
```json
{
    "wav_path": "/path/to/audio.wav",
    "from_lang": "en",
    "to_lang": "es", 
    "voice_name": "optional_name",
    "voice_description": "optional_description"
}
```

**Output JSON Format:**
```json
{
    "success": true,
    "original_text": "transcribed text",
    "translated_text": "translated text",
    "from_lang": "en",
    "to_lang": "es", 
    "saved_wav_path": "/path/to/saved.wav",
    "voice_id": "voice_id_string",
    "audio_file_path": "/path/to/output.mp3",
    "meta": {...}
}
```

## Environment Setup

Required environment variables:
```bash
ELEVENLABS_API_KEY=your_elevenlabs_key
GEMINI_API_KEY=your_gemini_key
```

Install dependencies:
```bash
pip install -r apps/ASR/requirements.txt
pip install -r apps/gemini_api/requirements.txt
```

## Directory Structure

```
apps/
├── main.py                 # Main stdin/stdout interface
├── recordings/             # Auto-created for saved .wav files
├── ASR/
│   ├── audio_processor.py  # STT + orchestration
│   └── requirements.txt
├── gemini_api/
│   ├── translator.py       # Translation + TTS call
│   └── requirements.txt  
└── routing/
    └── processing.py       # Voice cloning + TTS streaming
```

## Testing

Run the test script to verify the complete pipeline:
```bash
python3 test_pipeline.py
```

This creates a test WAV file and runs it through the entire pipeline to verify all components work together.

## Notes

- Voice cloning happens on first use and is cached to avoid redundant API calls
- Audio output is streamed and saved to temporary files
- Error handling provides fallback voices if cloning fails
- Pipeline preserves original .wav files in recordings folder for reference