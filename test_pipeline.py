#!/usr/bin/env python3
"""
Test script to verify the complete audio processing pipeline.
"""

import json
import subprocess
import tempfile
import wave
import numpy as np

def create_test_wav(duration=2, frequency=440, sample_rate=44100):
    """Create a simple test WAV file with a sine wave."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave_data = np.sin(frequency * 2 * np.pi * t) * 0.3
    
    # Convert to 16-bit integers
    wave_data = (wave_data * 32767).astype(np.int16)
    
    # Create temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = temp_file.name
    
    with wave.open(temp_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())
    
    return temp_path

def test_pipeline():
    """Test the complete pipeline via main.py stdin/stdout interface."""
    print("Creating test WAV file...")
    test_wav = create_test_wav()
    print(f"Test WAV created: {test_wav}")
    
    # Prepare input for the pipeline
    input_data = {
        "wav_path": test_wav,
        "from_lang": "en",
        "to_lang": "es",
        "voice_name": "TestVoice",
        "voice_description": "Test voice for pipeline verification"
    }
    
    input_json = json.dumps(input_data)
    print(f"Input JSON: {input_json}")
    
    try:
        # Run the main.py pipeline
        print("\nRunning pipeline...")
        result = subprocess.run(
            ["python3", "main.py"],
            input=input_json,
            capture_output=True,
            text=True,
            cwd="/Users/aaryanb/seis-to-seven/apps"
        )
        
        print(f"\nReturn code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                if output.get("success"):
                    print("\n✅ Pipeline test PASSED!")
                    print(f"Original text: {output.get('original_text', 'N/A')}")
                    print(f"Translated text: {output.get('translated_text', 'N/A')}")
                    print(f"Audio output: {output.get('audio_file_path', 'N/A')}")
                else:
                    print(f"\n❌ Pipeline test FAILED: {output.get('error')}")
            except json.JSONDecodeError:
                print(f"\n❌ Pipeline test FAILED: Invalid JSON output")
        else:
            print(f"\n❌ Pipeline test FAILED: Non-zero exit code")
    
    except Exception as e:
        print(f"\n❌ Pipeline test FAILED: {e}")
    
    finally:
        # Cleanup
        import os
        try:
            os.unlink(test_wav)
            print(f"Cleaned up test file: {test_wav}")
        except:
            pass

if __name__ == "__main__":
    test_pipeline()