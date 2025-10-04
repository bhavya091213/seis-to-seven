from translator import StreamingTranslator

if __name__ == "__main__":
    translator = StreamingTranslator(target_lang='es')

    result = translator.translate_chunk("Hello, how are you today?")
    print("Non-streaming:", result)

    print("\nStreaming:")
    for partial in translator.translate_streaming("Let's start the meeting now"):
        print(partial, end='', flush=True)
    print()