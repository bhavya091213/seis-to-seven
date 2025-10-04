from translator import StreamingTranslator, translate_text, translate_text_stream

if __name__ == "__main__":
    translator = StreamingTranslator()

    from_lang = "en"
    to_lang   = "es"
    asr_text  = "We can begin in five minutes."

    result = translator.translate_once(asr_text, from_lang, to_lang)
    print("Non-streaming result:")
    print(result)

    print("\nStreaming result:")
    for partial in translator.translate_stream("Please review the document by EOD.", from_lang, to_lang):
        print(partial, end='', flush=True)
    print()
