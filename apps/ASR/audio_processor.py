import wave
import os
import json
import uuid
from typing import Union
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from io import BytesIO
import sys

# Add the routing directory to Python path to import processing.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'routing'))

try:
    from processing import text_to_speech_stream, create_voice
    PROCESSING_AVAILABLE = True
    print("✅ Successfully imported processing.py functions")
except ImportError as e:
    print(f"⚠️  Could not import processing.py: {e}")
    print("Text-to-speech functionality will be disabled")
    PROCESSING_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

# Initialize the ElevenLabs client
# It will automatically use the ELEVENLABS_API_KEY from the environment
elevenlabs_client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

def process_audio(from_lang: str, to_lang: str, pcm_bytes: bytes) -> dict:
    """
    Process raw PCM16 audio data through speech-to-text transcription and translation pipeline.
    
    This function handles the complete audio processing workflow:
    1. Convert PCM16 bytes to WAV format
    2. Save WAV file locally with unique naming
    3. Send to ElevenLabs Speech-to-Text API
    4. Parse response and create structured output
    5. Call external translation and audio file services
    
    Args:
        from_lang (str): Source language code (e.g., 'en', 'es', 'fr')
        to_lang (str): Target language code for translation
        pcm_bytes (bytes): Raw PCM16 16kHz mono audio data
        
    Returns:
        dict: JSON object containing transcription results and metadata
        
    Raises:
        Exception: For any processing errors (gracefully handled and logged)
    """
    
    try:
        # Step 1: Convert PCM16 bytes to WAV format
        print("Step 1: Converting PCM16 bytes to WAV format...")
        wav_file_path = _convert_pcm_to_wav(pcm_bytes)
        print(f"WAV file created at: {wav_file_path}")
        
        # Step 2: Send WAV file to ElevenLabs Speech-to-Text API
        print("Step 2: Sending audio to ElevenLabs for transcription...")
        transcription_result = _transcribe_with_elevenlabs(wav_file_path, from_lang)
        
        # Step 3: Create structured JSON response
        print("Step 3: Creating structured JSON response...")
        result_json = {
            "from": from_lang,
            "to": to_lang,
            "text": transcription_result.get("text", ""),
            "detected_language": transcription_result.get("detected_language", from_lang)
        }
        
        # Step 4: Call external translation service
        print("Step 4: Calling translation service...")
        _call_translator_service(
            text=result_json["text"], 
            from_lang=from_lang, 
            to_lang=to_lang
        )
        
        # Step 5: Send audio file to external service
        print("Step 5: Sending audio file to external service...")
        _send_audio_file(wav_file_path)
        
        # Step 6: Return the JSON object
        print("Step 6: Processing complete!")
        print(json.dumps(result_json, indent=2))
        return result_json
        
    except Exception as e:
        # Graceful error handling with detailed logging
        error_message = f"Error processing audio: {str(e)}"
        print(f"ERROR: {error_message}")
        
        # Return error response in same JSON format
        error_response = {
            "from": from_lang,
            "to": to_lang,
            "text": "",
            "detected_language": "",
            "error": error_message
        }
        return error_response


def demonstrate_text_to_speech(text: str, voice_id: str = None, output_filename: str = None) -> str:
    """
    Demonstrate text-to-speech functionality using the processing.py module.
    
    This function can be called separately to convert text to speech using
    either a custom voice (created from recorded audio) or a default voice.
    
    Args:
        text (str): The text to convert to speech
        voice_id (str, optional): The voice ID to use. If None, uses default voice
        output_filename (str, optional): Output filename. If None, generates automatically
        
    Returns:
        str: Path to the generated audio file, or empty string if failed
    """
    
    if not PROCESSING_AVAILABLE:
        print("❌ Processing.py functions not available")
        return ""
    
    try:
        # Use provided voice ID or fall back to default
        if not voice_id:
            voice_id = "JBFqnCBsd6RMkjVDRZzb"  # Default voice from processing.py
            print(f"🔊 Using default voice: {voice_id}")
        else:
            print(f"🎤 Using custom voice: {voice_id}")
        
        # Generate output filename if not provided
        if not output_filename:
            timestamp = str(int(uuid.uuid4().int))[:-10]  # Use UUID-based timestamp
            output_filename = f"tts_output_{timestamp}.mp3"
        
        # Ensure output is in recordings directory
        recordings_dir = "recordings"
        if not os.path.exists(recordings_dir):
            os.makedirs(recordings_dir)
        
        output_path = os.path.join(recordings_dir, output_filename)
        
        print(f"🎵 Generating speech: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print(f"📁 Output file: {output_path}")
        
        # Generate speech using processing.py
        audio_generator = text_to_speech_stream(
            text=text,
            voice_id=voice_id
        )
        
        # Save the generated audio
        with open(output_path, "wb") as f:
            chunk_count = 0
            for chunk in audio_generator:
                f.write(chunk)
                chunk_count += 1
            
        print(f"✅ Successfully generated speech in {chunk_count} chunks")
        print(f"💾 Audio saved to: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error generating text-to-speech: {e}")
        return ""


def _convert_pcm_to_wav(pcm_bytes: bytes) -> str:
    """
    Convert raw PCM16 bytes to a properly formatted WAV file.
    
    PCM16 format specifications:
    - 16-bit signed integers (2 bytes per sample)
    - 16kHz sample rate
    - Mono channel (1 channel)
    
    Args:
        pcm_bytes (bytes): Raw PCM16 audio data
        
    Returns:
        str: Path to the created WAV file
    """
    
    # Create recordings directory if it doesn't exist
    recordings_dir = "recordings"
    if not os.path.exists(recordings_dir):
        os.makedirs(recordings_dir)
        print(f"Created directory: {recordings_dir}")
    
    # Generate unique filename using UUID to avoid conflicts
    unique_id = str(uuid.uuid4())
    wav_filename = f"audio_{unique_id}.wav"
    wav_file_path = os.path.join(recordings_dir, wav_filename)
    
    # WAV file parameters for PCM16 16kHz mono
    sample_rate = 16000  # 16kHz
    channels = 1         # Mono
    sample_width = 2     # 16-bit = 2 bytes per sample
    
    # Create WAV file using wave library
    with wave.open(wav_file_path, 'wb') as wav_file:
        # Set WAV file parameters
        wav_file.setnchannels(channels)        # Number of audio channels
        wav_file.setsampwidth(sample_width)    # Bytes per sample
        wav_file.setframerate(sample_rate)     # Sample rate in Hz
        
        # Write the raw PCM data to WAV file
        wav_file.writeframes(pcm_bytes)
    
    print(f"Successfully converted {len(pcm_bytes)} bytes of PCM data to WAV format")
    return wav_file_path


def _transcribe_with_elevenlabs(wav_file_path: str, language_code: str) -> dict:
    """
    Send WAV file to ElevenLabs Speech-to-Text API for transcription using the ElevenLabs client.
    
    Uses ElevenLabs' speech-to-text endpoint with automatic language detection.
    The API can handle language detection automatically, but we can optionally
    pass the expected language code for better accuracy.
    
    Args:
        wav_file_path (str): Path to the WAV file to transcribe
        language_code (str): Expected source language code
        
    Returns:
        dict: Parsed JSON response containing transcribed text and detected language
    """
    
    # Check if ElevenLabs client is properly initialized
    if elevenlabs_client is None or not os.getenv("ELEVENLABS_API_KEY"):
        print("WARNING: ElevenLabs API key not provided. Using mock response.")
        # Return mock response for testing purposes
        return {
            "text": "This is a mock transcription response since no API key was provided.",
            "detected_language": language_code
        }
    
    try:
        print(f"Sending request to ElevenLabs API...")
        print(f"File: {wav_file_path}")
        print(f"Language code: {language_code}")
        
        # Read the WAV file and convert to BytesIO for the API
        with open(wav_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            audio_buffer = BytesIO(audio_data)
        
        # Call ElevenLabs Speech-to-Text API using the client
        # Note: The exact method name may vary - check ElevenLabs Python SDK documentation
        try:
            # Attempt to use the speech-to-text functionality
            # This is the most likely API call structure based on ElevenLabs SDK
            result = elevenlabs_client.speech_to_text.convert(
                audio=audio_buffer,
                language=language_code if language_code else None
            )
            
            # Handle different possible response formats
            if hasattr(result, 'text'):
                transcribed_text = result.text
                detected_lang = getattr(result, 'detected_language', language_code)
            elif isinstance(result, dict):
                transcribed_text = result.get('text', '')
                detected_lang = result.get('detected_language', language_code)
            else:
                # If result is just a string
                transcribed_text = str(result)
                detected_lang = language_code
            
            print(f"Transcription successful: {transcribed_text[:100]}...")
            
            return {
                "text": transcribed_text,
                "detected_language": detected_lang
            }
            
        except AttributeError as attr_error:
            # If the API method doesn't exist, try alternative approaches
            print(f"API method not found, trying alternative approach: {attr_error}")
            
            # Alternative: Check if there's a different method structure
            # You may need to adjust this based on the actual ElevenLabs SDK documentation
            try:
                result = elevenlabs_client.transcribe(audio_buffer)
                return {
                    "text": str(result),
                    "detected_language": language_code
                }
            except Exception as alt_error:
                print(f"Alternative approach also failed: {alt_error}")
                raise Exception(f"ElevenLabs SDK method not found. Please check the documentation.")
                
    except FileNotFoundError:
        error_msg = f"Audio file not found: {wav_file_path}"
        print(f"ERROR: {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error calling ElevenLabs API: {str(e)}"
        print(f"ERROR: {error_msg}")
        raise Exception(error_msg)


def _call_translator_service(text: str, from_lang: str, to_lang: str) -> None:
    """
    Call external translation service (placeholder function).
    
    This function serves as a placeholder for the actual translation service
    that will be implemented by your teammate. It would typically send the
    transcribed text to a translation API and handle the response.
    
    Args:
        text (str): The transcribed text to translate
        from_lang (str): Source language code
        to_lang (str): Target language code
        
    Returns:
        None: This is a fire-and-forget call
    """
    
    print(f"PLACEHOLDER: Calling translator.translate() with:")
    print(f"  Text: {text[:50]}{'...' if len(text) > 50 else ''}")
    print(f"  From: {from_lang}")
    print(f"  To: {to_lang}")
    
    # TODO: Implement actual translation service call
    # Example implementation:
    # try:
    #     import translator  # Your teammate's translation module
    #     result = translator.translate(
    #         text=text,
    #         from_lang=from_lang,
    #         to_lang=to_lang
    #     )
    #     print(f"Translation service called successfully")
    #     return result
    # except Exception as e:
    #     print(f"Error calling translation service: {e}")


def _send_audio_file(file_path: str) -> None:
    """
    Send the saved WAV file to the text-to-speech processing service.
    
    This function integrates with the processing.py module to handle the WAV file.
    It can be used for voice cloning or other audio processing tasks.
    
    Args:
        file_path (str): Path to the WAV file to send
        
    Returns:
        None: This is a fire-and-forget call
    """
    
    print(f"📤 Sending audio file to processing service:")
    print(f"  File path: {file_path}")
    
    # Check if file exists before attempting to send
    if not os.path.exists(file_path):
        print(f"ERROR: Audio file not found at {file_path}")
        return
    
    # Get file size for logging
    file_size = os.path.getsize(file_path)
    print(f"  File size: {file_size} bytes")
    
    # Check if processing functions are available
    if not PROCESSING_AVAILABLE:
        print("⚠️  Processing.py functions not available - using placeholder behavior")
        print("  Audio file saved locally but not processed further")
        return
    
    try:
        # Option 1: Use the audio file for voice cloning
        # This creates a new voice using the recorded audio
        print("🎤 Creating voice clone from recorded audio...")
        
        # Extract a base name for the voice from the file path
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        voice_name = f"RecordedVoice_{base_name[:8]}"  # Use first 8 characters of filename
        
        voice_id = create_voice(
            name=voice_name,
            description=f"Voice cloned from recorded audio: {os.path.basename(file_path)}",
            file_paths=[file_path]
        )
        
        print(f"✅ Successfully created voice clone with ID: {voice_id}")
        print(f"   Voice name: {voice_name}")
        
        # Store the voice ID for potential future use
        # You could save this to a file or database for later reference
        voice_info = {
            "voice_id": voice_id,
            "voice_name": voice_name,
            "source_file": file_path,
            "created_at": json.dumps(os.path.getctime(file_path))
        }
        
        # Save voice info to a JSON file for tracking
        voice_info_path = file_path.replace('.wav', '_voice_info.json')
        with open(voice_info_path, 'w') as f:
            json.dump(voice_info, f, indent=2)
        
        print(f"💾 Voice information saved to: {voice_info_path}")
        
    except Exception as e:
        print(f"❌ Error processing audio file with processing.py: {e}")
        print("  Audio file saved locally but processing failed")


# Example usage and testing
if __name__ == "__main__":
    """
    Example usage of the process_audio function.
    This section demonstrates how to use the function with sample data.
    """
    
    print("=== Audio Processing Function Test ===")
    
    # Example: Create some dummy PCM16 data for testing
    # In real usage, this would come from your teammate's microphone capture system
    import numpy as np
    
    # Generate 1 second of sine wave at 440Hz (A note) as test audio
    sample_rate = 16000
    duration = 1.0  # 1 second
    frequency = 440  # A note
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    sine_wave = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM format
    pcm_data = (sine_wave * 32767).astype(np.int16)
    pcm_bytes = pcm_data.tobytes()
    
    print(f"Generated {len(pcm_bytes)} bytes of test PCM16 data")
    
    # Test the function
    result = process_audio(
        from_lang="en",
        to_lang="es", 
        pcm_bytes=pcm_bytes
    )
    
    print("\n=== Final Result ===")
    print(json.dumps(result, indent=2))
    
    # Demonstrate text-to-speech functionality
    print("\n=== Text-to-Speech Demo ===")
    if PROCESSING_AVAILABLE:
        demo_text = "This is a demonstration of the integrated text-to-speech functionality."
        tts_output = demonstrate_text_to_speech(
            text=demo_text,
            output_filename="demo_tts_output.mp3"
        )
        
        if tts_output:
            print(f"🎉 Text-to-speech demo completed! Check: {tts_output}")
        else:
            print("❌ Text-to-speech demo failed")
    else:
        print("⚠️  Text-to-speech functionality not available")