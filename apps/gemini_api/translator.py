import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class StreamingTranslator:
    def __init__(self, target_lang='es'):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.target_lang = target_lang
        self.system_prompt = self.build_system_prompt()

    def build_system_prompt(self):
        lang_names = {
            'es': 'Spanish',
            'en': "English",
            'hi': 'Hindi',
            "zh": "Chinese",
        }
        target = lang_names.get(self.target_lang, 'Spanish')

        return f"""You are a low-latency meeting interpreter.
        Translate the following text to {target}
        I want you to preserve tone and intent. Use short, simple sentences.
        If the source is incomplete, translate the best-guess fragment without adding new facts.
        Only output the translation, nothing else."""

    def translate_chunk(self, text_chunk):
        """Translate a single chunk of text"""
        prompt = f"{self.system_prompt}\n\nSource text: {text_chunk}"

        response = self.model.generate_content(prompt)
        return response.text.strip()

    def translate_streaming(self, text_chunk):
        """Translate with streaming response (yields partial translations)"""
        prompt = f"{self.system_prompt}\n\nSource text: {text_chunk}"

        response = self.model.generate_content(prompt, stream=True)

        for chunk in response:
            if chunk.text:
                yield chunk.text
            
    def set_target_language(self, lang_code):
        """Change target language"""
        self.target_lang = lang_code
        self.system_prompt = self.build_system_prompt()

if __name__ == "__main__":
    translator = StreamingTranslator(target_lang='es')

    result = translator.translate_chunk("Hello, how are you today?")
    print("Non-streaming:", result)

    print("\nStreaming:")
    for partial in translator.translate_streaming("Let's start the meeting now"):
        print(partial, end='', flush=True)
    print()
        
        