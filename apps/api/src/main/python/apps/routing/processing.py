import base64
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Initialize the ElevenLabs client
# It will automatically use the ELEVENLABS_API_KEY from the environment
elevenlabs_client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# --- Core Functions (callable from other Python files) ---

# def create_voice(name: str, description: str, audio_b64: str) -> str:
#     """
#     Creates a new voice clone from one or more audio files.

#     Args:
#         name (str): The name for the new voice.
#         description (str): A description for the new voice.
#         file_paths (list[str]): A list of absolute paths to the audio files.

#     Returns:
#         str: The newly created voice_id.
#     """
    
#     data_bytes = base64.b64decode(audio_b64)
#     buf = BytesIO(data_bytes)
#     buf.name = "voice.wav"  # ElevenLabs SDK expects file-like objects to have a 'name' attribute

#     voice = elevenlabs_client.voices.ivc.create(
#         name=name,
#         description=description,
#         files=[buf],
#     )
#     return voice.voice_id

# def text_to_speech_stream(text: str, voice_id: str, model_id: str = "eleven_multilingual_v2"):
#     """
#     Converts text to speech and streams the audio.

#     Args:
#         text (str): The text to convert.
#         voice_id (str): The ID of the voice to use.
#         model_id (str, optional): The model to use. Defaults to "eleven_multilingual_v2".

#     Yields:
#         bytes: Audio chunks from the API.
#     """
#     audio_stream = elevenlabs_client.text_to_speech.convert(
#         text=text,
#         voice_id=voice_id,
#         model_id=model_id,
#         output_format="mp3_44100_128",
#     )

#     for chunk in audio_stream:
#         yield chunk

def clone_and_speak(
    audio_b64: str,
    text: str,
    model_id: str = "eleven_multilingual_v2",
    output_format: str = "mp3_44100_128",
    name: str = "a",
    description: str = "b",
):
    
    data_bytes = base64.b64decode(audio_b64)
    buf = BytesIO(data_bytes)
    buf.name = "voice.wav"  # ElevenLabs expects 'name' attribute on file-like objects

    voice = elevenlabs_client.voices.ivc.create(
        name=name,
        description=description,
        files=[buf],
    )
    
    voice_id = getattr(voice, "voice_id", None)
    if voice_id is None and isinstance(voice, dict):
        voice_id = voice.get("voice_id")
    if not voice_id:
        raise RuntimeError("Failed to obtain voice_id from ElevenLabs IVC response")

    # Generate speech using the cloned voice
    audio_stream = elevenlabs_client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model_id,
        output_format=output_format,
    )

    # Stream audio chunks
    # for chunk in audio_stream:
    #     yield chunk
    with open("out.wav", "wb") as f:
        for chunk in audio_stream: f.write(chunk); yield chunk
    return audio_stream

# --- Example Usage ---
# This block demonstrates how you would import and use the functions above
# in another Python file, for example, in your main application logic.

# def main():
#     """Main function to demonstrate API usage."""
#     print("--- ElevenLabs API Example ---")

#     # --- 1. Create a Voice ---
#     # We will use the voice.mp3 file in the current directory.
#     audio_files = [os.path.join(os.path.dirname(__file__), "voice.mp3")]
#     try:
#         print("Creating a new voice...")
#         new_voice_id = create_voice(
#             name="MyClonedVoice",
#             description="A voice cloned from voice.mp3.",
#             file_paths=audio_files
#         )
#         print(f"New voice created with ID: {new_voice_id}")
#         voice_to_use = new_voice_id
#     except Exception as e:
#         print(f"Could not create voice: {e}")
#         print("Falling back to a default voice.")
#         voice_to_use = "JBFqnCBsd6RMkjVDRZzb" # Default voice
    

#     # --- 2. Generate and Save Audio ---
#     translated_text = "This is an example of how to call the API from another Python file."
#     output_filename = "example_output.mp3"

#     print(f"\nGenerating speech for the text: '{translated_text}'")
#     print(f"Using voice ID: {voice_to_use}")

#     try:
#         audio_generator = text_to_speech_stream(
#             text=translated_text,
#             voice_id=voice_to_use
#         )

#         with open(output_filename, "wb") as f:
#             for i, chunk in enumerate(audio_generator):
#                 print(f"Received chunk {i+1}")
#                 f.write(chunk)
        
#         print(f"\nSuccessfully saved audio to '{output_filename}'")

#     except Exception as e:
#         print(f"An error occurred: {e}")

# if __name__ == "__main__":
#     main()
