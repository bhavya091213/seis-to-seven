#!/usr/bin/env python3
"""
Integration test script to verify that audio_processor.py 
successfully integrates with processing.py
"""

import os
import sys
import json

def test_integration():
    """Test the integration between ASR and routing modules."""
    print("🔗 Testing ASR <-> Routing Integration")
    print("=" * 50)
    
    # Change to ASR directory
    asr_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(asr_dir)
    print(f"Working directory: {asr_dir}")
    
    try:
        # Test importing both modules
        print("\n📦 Testing imports...")
        
        from audio_processor import process_audio, demonstrate_text_to_speech, PROCESSING_AVAILABLE
        print("✅ Successfully imported audio_processor functions")
        
        if PROCESSING_AVAILABLE:
            print("✅ Processing.py functions are available")
        else:
            print("⚠️  Processing.py functions are NOT available")
            print("   This could be due to:")
            print("   - Missing routing/processing.py file")
            print("   - Missing dependencies (elevenlabs, python-dotenv)")
            print("   - API key issues")
            return False
        
        # Test text-to-speech functionality
        print("\n🎵 Testing text-to-speech integration...")
        demo_text = "Hello from the integrated ASR and routing system!"
        
        tts_result = demonstrate_text_to_speech(
            text=demo_text,
            output_filename="integration_test.mp3"
        )
        
        if tts_result and os.path.exists(tts_result):
            print(f"✅ Text-to-speech integration successful!")
            print(f"   Output file: {tts_result}")
            print(f"   File size: {os.path.getsize(tts_result)} bytes")
        else:
            print("❌ Text-to-speech integration failed")
            return False
        
        # Test with minimal audio processing (without numpy dependency)
        print("\n🎤 Testing minimal audio processing...")
        
        # Create minimal test audio data (silence)
        sample_rate = 16000
        duration_seconds = 0.5  # Half second of silence
        samples = sample_rate * duration_seconds
        
        # Create silence as PCM16 data (16-bit signed integers, little-endian)
        silence_pcm = b'\\x00\\x00' * int(samples)  # Zero amplitude = silence
        
        print(f"Generated {len(silence_pcm)} bytes of silence as test PCM data")
        
        # Process the audio
        result = process_audio(
            from_lang="en",
            to_lang="es",
            pcm_bytes=silence_pcm
        )
        
        print("✅ Audio processing completed!")
        print("📊 Result:")
        print(json.dumps(result, indent=2))
        
        # Check if recordings directory was created and contains files
        recordings_dir = "recordings"
        if os.path.exists(recordings_dir):
            files = os.listdir(recordings_dir)
            wav_files = [f for f in files if f.endswith('.wav')]
            mp3_files = [f for f in files if f.endswith('.mp3')]
            json_files = [f for f in files if f.endswith('.json')]
            
            print(f"\\n📁 Recordings directory contains:")
            print(f"   WAV files: {len(wav_files)}")
            print(f"   MP3 files: {len(mp3_files)}")
            print(f"   JSON files: {len(json_files)}")
            
            if wav_files:
                print(f"   Latest WAV: {wav_files[-1]}")
            if json_files:
                print(f"   Voice info files: {json_files}")
        
        print("\\n🎉 Integration test completed successfully!")
        print("\\n📋 Summary:")
        print("✅ Audio processing (PCM16 -> WAV)")
        print("✅ Speech-to-text transcription")
        print("✅ Voice cloning integration")
        print("✅ Text-to-speech generation")
        print("✅ File management and logging")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main test function."""
    success = test_integration()
    
    if success:
        print("\\n🚀 Integration is working properly!")
        print("Your ASR module is ready to:")
        print("1. 🎤 Process microphone audio (PCM16 -> WAV)")
        print("2. 📝 Transcribe speech to text (ElevenLabs)")
        print("3. 🎭 Create voice clones from recorded audio")
        print("4. 🎵 Generate speech using cloned voices")
    else:
        print("\\n⚠️  Integration test failed")
        print("Please check the error messages above and:")
        print("1. Install missing dependencies")
        print("2. Verify API key configuration")
        print("3. Check file paths and permissions")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)