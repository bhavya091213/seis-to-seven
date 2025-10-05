#!/usr/bin/env python3
"""
Main entry point for the audio processing pipeline.
Reads input from stdin and writes output to stdout for clean integration.

Expected stdin format (JSON):
{
    "wav_path": "/path/to/audio.wav",
    "from_lang": "en",
    "to_lang": "es",
    "voice_name": "optional_voice_name",
    "voice_description": "optional_description"
}

Output format (JSON):
{
    "success": true/false,
    "original_text": "transcribed text",
    "translated_text": "translated text", 
    "from_lang": "en",
    "to_lang": "es",
    "saved_wav_path": "/path/to/saved.wav",
    "voice_id": "voice_id_string",
    "audio_file_path": "/path/to/output.mp3",
    "error": "error message if success=false"
}
"""

import sys
import json
import os
import tempfile
from typing import Dict, Any

# Import our processing pipeline
from ASR.audio_processor import process_recording


def process_audio_pipeline(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process audio through the complete pipeline."""
    try:
        # Extract input parameters
        wav_path = input_data.get("wav_path")
        from_lang = input_data.get("from_lang")
        to_lang = input_data.get("to_lang")
        voice_name = input_data.get("voice_name")
        voice_description = input_data.get("voice_description")
        
        # Validate required parameters
        if not wav_path or not from_lang or not to_lang:
            return {
                "success": False,
                "error": "Missing required parameters: wav_path, from_lang, to_lang"
            }
        
        if not os.path.exists(wav_path):
            return {
                "success": False,
                "error": f"Audio file not found: {wav_path}"
            }
        
        # Run the processing pipeline
        result = process_recording(
            wav_path=wav_path,
            from_lang=from_lang,
            to_lang=to_lang,
            voice_name=voice_name,
            voice_description=voice_description,
        )
        
        # Save the audio stream to a temporary file
        output_audio_path = None
        if result.audio_stream:
            # Create a temporary file for the output audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                output_audio_path = temp_file.name
                for chunk in result.audio_stream:
                    temp_file.write(chunk)
        
        # Return success response
        return {
            "success": True,
            "original_text": result.original_text,
            "translated_text": result.translated_text,
            "from_lang": result.from_lang,
            "to_lang": result.to_lang,
            "saved_wav_path": result.saved_wav_path,
            "voice_id": result.voice_id,
            "audio_file_path": output_audio_path,
            "meta": result.meta
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Pipeline error: {str(e)}"
        }


def main():
    """Main function that handles stdin/stdout communication."""
    try:
        # Read JSON from stdin
        input_line = sys.stdin.read().strip()
        if not input_line:
            output = {
                "success": False,
                "error": "No input provided"
            }
        else:
            try:
                input_data = json.loads(input_line)
                output = process_audio_pipeline(input_data)
            except json.JSONDecodeError as e:
                output = {
                    "success": False,
                    "error": f"Invalid JSON input: {str(e)}"
                }
        
        # Write JSON to stdout
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        # Fallback error output
        error_output = {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
        print(json.dumps(error_output, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
