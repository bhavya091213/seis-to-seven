import os
import sys
from dotenv import load_dotenv

# Add the subdirectories to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "gemini_api"))
sys.path.append(os.path.join(os.path.dirname(__file__), "routing"))

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "gemini_api", ".env"))

from translator import StreamingTranslator
from processing import text_to_speech_stream, create_voice


def main():
    """Main function to test the translation and text-to-speech pipeline."""
    print("--- Translation and Text-to-Speech Test ---")

    # --- 1. Translate Text ---
    translator = StreamingTranslator(target_lang="es")
    text_to_translate = "Hi my name is gemini."
    print(f"Original text: {text_to_translate}")

    translated_text = ""
    print("\nStreaming translation:")
    for partial in translator.translate_streaming(text_to_translate):
        print(partial, end="", flush=True)
        translated_text += partial
    print()

    # --- 2. Generate and Save Audio ---
    output_filename = "test_output.mp3"
    # Using a default voice for simplicity
    voice_to_use = "JBFqnCBsd6RMkjVDRZzb"

    print(f"\nGenerating speech for the translated text: '{translated_text}'")
    print(f"Using voice ID: {voice_to_use}")

    try:
        audio_generator = text_to_speech_stream(
            text=translated_text, voice_id=voice_to_use
        )

        with open(output_filename, "wb") as f:
            for i, chunk in enumerate(audio_generator):
                print(f"Received chunk {i + 1}")
                f.write(chunk)

        print(f"\nSuccessfully saved audio to '{output_filename}'")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
