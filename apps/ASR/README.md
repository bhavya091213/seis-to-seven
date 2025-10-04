# ASR (Automatic Speech Recognition) Module

This module provides speech-to-text transcription functionality using ElevenLabs API, designed to process PCM16 audio data from microphone input.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
Your `.env` file is already configured with the ElevenLabs API key.

### 3. Test the Module
```bash
python setup_and_test.py
```

## 📋 Usage

### Basic Function Call
```python
from audio_processor import process_audio

# Your PCM16 audio data (from microphone capture)
pcm_bytes = b"..."  # Raw PCM16 16kHz mono audio data

# Process the audio
result = process_audio(
    from_lang="en",    # Source language
    to_lang="es",      # Target language for translation
    pcm_bytes=pcm_bytes
)

print(result)
# Output:
# {
#   "from": "en",
#   "to": "es", 
#   "text": "Hello, how are you?",
#   "detected_language": "en"
# }
```

## 🔧 Function Details

### `process_audio(from_lang: str, to_lang: str, pcm_bytes: bytes) -> dict`

**Purpose**: Convert PCM16 audio data to text using ElevenLabs Speech-to-Text API

**Parameters**:
- `from_lang` (str): Source language code (e.g., 'en', 'es', 'fr')
- `to_lang` (str): Target language for translation
- `pcm_bytes` (bytes): Raw PCM16 16kHz mono audio data

**Returns**: JSON object with transcription results:
```json
{
    "from": "source_language",
    "to": "target_language", 
    "text": "transcribed_text",
    "detected_language": "detected_language"
}
```

## 📁 File Structure

```
apps/ASR/
├── audio_processor.py      # Main processing function
├── requirements.txt        # Python dependencies
├── setup_and_test.py      # Installation and testing script
├── .env                   # Environment variables (API key)
├── recordings/            # Directory for saved WAV files
└── README.md             # This file
```

## 🔄 Processing Pipeline

1. **PCM16 to WAV**: Convert raw audio bytes to WAV format
2. **File Storage**: Save WAV file with unique UUID filename
3. **Transcription**: Send to ElevenLabs Speech-to-Text API
4. **JSON Response**: Create structured response
5. **External Calls**: Call translation and audio file services (placeholders)

## ⚙️ Configuration

### Environment Variables
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key (already set in `.env`)

### Audio Format Requirements
- **Format**: PCM16 (16-bit signed integers)
- **Sample Rate**: 16kHz
- **Channels**: Mono (1 channel)
- **Encoding**: Little-endian

## 🔗 Integration Points

### Text-to-Speech Service (✅ IMPLEMENTED)
```python
# Integrated with ../routing/processing.py
from processing import text_to_speech_stream, create_voice

# Creates voice clones from recorded WAV files
voice_id = create_voice(name="MyVoice", description="Custom voice", file_paths=["audio.wav"])

# Generates speech using custom or default voices
demonstrate_text_to_speech(text="Hello world", voice_id=voice_id)
```

### Translation Service (Placeholder)
```python
# TODO: Implement in _call_translator_service()
translator.translate(text="Hello", from_lang="en", to_lang="es")
```

## 🧪 Testing

The module includes comprehensive testing:

### Basic Setup Test
```bash
python setup_and_test.py
```
- **Dependency Check**: Verifies all packages are installed
- **Environment Check**: Confirms API key is configured
- **Functionality Test**: Generates test audio and processes it
- **Output Validation**: Checks WAV file creation and JSON response

### Integration Test  
```bash
python test_integration.py
```
- **Import Validation**: Tests processing.py integration
- **Text-to-Speech**: Validates voice generation functionality
- **Voice Cloning**: Tests custom voice creation from audio files
- **File Management**: Verifies recording and output file handling

## 📝 Error Handling

- **Graceful Degradation**: Uses mock responses when API key is missing
- **Detailed Logging**: Step-by-step processing information
- **Exception Management**: Catches and logs all errors
- **Structured Errors**: Returns error information in same JSON format

## 🔐 Security

- **API Key Protection**: Stored in `.env` file (gitignored)
- **No Hardcoded Secrets**: All sensitive data in environment variables
- **Safe Error Messages**: No API keys exposed in logs

## 📈 Next Steps

1. **Test with Real Audio**: Replace test sine wave with actual microphone data
2. **Integration**: Connect with teammate's microphone capture system
3. **Translation Service**: Implement actual translation API calls
4. **Audio File Service**: Set up file transfer to other team's service
5. **Voice Activity Detection**: Add autonomous speech detection (future enhancement)

## 🆘 Troubleshooting

### Common Issues

**Import Errors**: Run `pip install -r requirements.txt`

**API Key Issues**: Check `.env` file contains `ELEVENLABS_API_KEY=your_key_here`

**Audio Format Problems**: Ensure PCM16 16kHz mono format

**Permission Errors**: Check write permissions for `recordings/` directory

### Debug Mode
Set environment variable for detailed logging:
```bash
export DEBUG=1
python audio_processor.py
```