#!/usr/bin/env python3
"""
Setup and test script for the ASR (Automatic Speech Recognition) module.
This script installs dependencies and runs a basic test of the audio processing function.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required Python packages."""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Successfully installed all requirements!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of the audio processor."""
    print("\n🧪 Testing basic audio processing functionality...")
    
    try:
        # Import the audio processor
        from audio_processor import process_audio
        import numpy as np
        
        # Generate test PCM16 data (1 second of sine wave)
        print("Generating test audio data...")
        sample_rate = 16000
        duration = 1.0
        frequency = 440  # A note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        sine_wave = np.sin(2 * np.pi * frequency * t)
        pcm_data = (sine_wave * 32767).astype(np.int16)
        pcm_bytes = pcm_data.tobytes()
        
        print(f"Generated {len(pcm_bytes)} bytes of test PCM16 data")
        
        # Test the function
        print("Testing process_audio function...")
        result = process_audio(
            from_lang="en",
            to_lang="es", 
            pcm_bytes=pcm_bytes
        )
        
        print("✅ Audio processing function executed successfully!")
        print("📄 Result structure:")
        import json
        print(json.dumps(result, indent=2))
        
        # Check if WAV file was created
        recordings_dir = "recordings"
        if os.path.exists(recordings_dir):
            wav_files = [f for f in os.listdir(recordings_dir) if f.endswith('.wav')]
            if wav_files:
                print(f"✅ WAV file created: {wav_files[-1]}")
            else:
                print("⚠️  No WAV files found in recordings directory")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def check_environment():
    """Check if environment variables are properly set."""
    print("\n🔍 Checking environment configuration...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
        
        # Try to load and check API key
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if api_key:
                # Don't print the full key for security
                masked_key = api_key[:8] + "..." + api_key[-8:] if len(api_key) > 16 else "***"
                print(f"✅ ELEVENLABS_API_KEY found: {masked_key}")
                return True
            else:
                print("❌ ELEVENLABS_API_KEY not found in environment")
                return False
                
        except ImportError:
            print("⚠️  python-dotenv not installed yet")
            return False
    else:
        print("❌ .env file not found")
        print("Please make sure the .env file exists with your ELEVENLABS_API_KEY")
        return False

def main():
    """Main setup and test function."""
    print("🚀 ASR Module Setup and Test")
    print("=" * 40)
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    
    # Step 1: Install requirements
    if not install_requirements():
        print("❌ Setup failed during package installation")
        return False
    
    # Step 2: Check environment
    if not check_environment():
        print("⚠️  Environment check failed - API functionality may be limited")
    
    # Step 3: Test basic functionality
    if not test_basic_functionality():
        print("❌ Basic functionality test failed")
        return False
    
    print("\n🎉 Setup and testing completed successfully!")
    print("\n📋 Next steps:")
    print("1. Your ASR module is ready to use")
    print("2. Call process_audio(from_lang, to_lang, pcm_bytes) from your code")
    print("3. Check the 'recordings' directory for saved WAV files")
    print("4. Update the placeholder functions for translation and audio file services")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)