import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from translator import StreamingTranslator

app = FastAPI(
    title="Translation Service API",
    description="API for real-time text translation using Gemini.",
    version="1.0.0"
)

translator = StreamingTranslator(target_lang='es')

class TranslationRequest(BaseModel):
    text: str
    session_id: str | None = None

@app.post("/translate/stream")
async def handle_translation(request: TranslationRequest):
    """
    Receives text and streams the translation back in real-time.
    """

    return StreamingResponse(translator.translate_streaming(request.text), media_type="text/plain")

@app.get("/")
def read_root():
    return {"status": "Translation server is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

