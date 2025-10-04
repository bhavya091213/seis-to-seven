import wave
import os
import json
import uuid
import requests
from typing import Union

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
    Send WAV file to ElevenLabs Speech-to-Text API for transcription.
    
    Uses ElevenLabs' speech-to-text endpoint with automatic language detection.
    The API can handle language detection automatically, but we can optionally
    pass the expected language code for better accuracy.
    
    Args:
        wav_file_path (str): Path to the WAV file to transcribe
        language_code (str): Expected source language code
        
    Returns:
        dict: Parsed JSON response containing transcribed text and detected language
    """
    
    # ElevenLabs Speech-to-Text API endpoint
    api_url = "https://api.elevenlabs.io/v1/speech-to-text"
    
    # TODO: Replace with your actual ElevenLabs API key
    # You can get this from: https://elevenlabs.io/docs/api-reference/getting-started
    # api_key = "your_elevenlabs_api_key_here"
    api_key = None  # COMMENTED OUT - Replace with actual API key
    
    if api_key is None:
        print("WARNING: ElevenLabs API key not provided. Using mock response.")
        # Return mock response for testing purposes
        return {
            "text": "This is a mock transcription response since no API key was provided.",
            "detected_language": language_code
        }
    
    # Prepare headers with API key authentication
    headers = {
        "xi-api-key": api_key
    }
    
    # Prepare the audio file for upload
    try:
        with open(wav_file_path, 'rb') as audio_file:
            # Prepare multipart form data
            files = {
                'audio': ('audio.wav', audio_file, 'audio/wav')
            }
            
            # Optional: Include language code for better accuracy
            data = {}
            if language_code:
                data['language_code'] = language_code
            
            print(f"Sending request to ElevenLabs API...")
            print(f"File: {wav_file_path}")
            print(f"Language code: {language_code}")
            
            # Make POST request to ElevenLabs API
            response = requests.post(
                api_url, 
                headers=headers, 
                files=files, 
                data=data,
                timeout=30  # 30 second timeout
            )
            
            # Check if request was successful
            if response.status_code == 200:
                # Parse JSON response
                result = response.json()
                print(f"Transcription successful: {result.get('text', '')[:100]}...")
                return result
            else:
                # Handle API errors
                error_msg = f"ElevenLabs API error: {response.status_code} - {response.text}"
                print(f"ERROR: {error_msg}")
                raise Exception(error_msg)
                
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error calling ElevenLabs API: {str(e)}"
        print(f"ERROR: {error_msg}")
        raise Exception(error_msg)
    except FileNotFoundError:
        error_msg = f"Audio file not found: {wav_file_path}"
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
    Send the saved WAV file to another team's service (placeholder function).
    
    This function serves as a placeholder for sending the audio file to
    another team's service. This could be via HTTP upload, file system copy,
    message queue, etc., depending on the integration architecture.
    
    Args:
        file_path (str): Path to the WAV file to send
        
    Returns:
        None: This is a fire-and-forget call
    """
    
    print(f"PLACEHOLDER: Calling send_audio_file() with:")
    print(f"  File path: {file_path}")
    
    # Check if file exists before attempting to send
    if not os.path.exists(file_path):
        print(f"ERROR: Audio file not found at {file_path}")
        return
    
    # Get file size for logging
    file_size = os.path.getsize(file_path)
    print(f"  File size: {file_size} bytes")
    
    # TODO: Implement actual file sending logic
    # Example implementations:
    
    # Option 1: HTTP upload to another service
    # try:
    #     with open(file_path, 'rb') as audio_file:
    #         files = {'audio': audio_file}
    #         response = requests.post('http://other-team-service/upload', files=files)
    #         print(f"File sent successfully: {response.status_code}")
    # except Exception as e:
    #     print(f"Error sending file via HTTP: {e}")
    
    # Option 2: Copy to shared directory
    # try:
    #     import shutil
    #     shared_dir = "/shared/audio_files/"
    #     shutil.copy2(file_path, shared_dir)
    #     print(f"File copied to shared directory: {shared_dir}")
    # except Exception as e:
    #     print(f"Error copying file: {e}")
    
    # Option 3: Message queue notification
    # try:
    #     import pika  # RabbitMQ example
    #     connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    #     channel = connection.channel()
    #     channel.basic_publish(
    #         exchange='',
    #         routing_key='audio_files',
    #         body=file_path
    #     )
    #     connection.close()
    #     print(f"File path sent to message queue")
    # except Exception as e:
    #     print(f"Error sending to message queue: {e}")


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