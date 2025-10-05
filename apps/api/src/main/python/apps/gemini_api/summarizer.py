from __future__ import annotations
import os, json
from typing import List, Dict, Literal
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")
genai.configure(api_key=api_key)

ModelName = Literal["gemini-1.5-flash", "gemini-2.5-flash"]

def _length_hint(entries: List[Dict]) -> str:
    words = sum(len((e.get("text") or "").split()) for e in entries)
    if words < 400:
        return "Keep it brief: 4–6 bullets and a 2–3 sentence overview."
    elif words < 1500:
        return "Aim for 7–10 bullets and a concise 3–4 sentence overview."
    else:
        return "Aim for 10–15 bullets and a concise 4–6 sentence overview."

def summarize_conversation(
    entries: List[Dict],
    target_lang: str,
    model_name: ModelName = "gemini-1.5-flash",
) -> str:
    clean = [
        {
            "t": float(e.get("t", 0.0)),
            "speaker": str(e.get("speaker", ""))[:20],
            "lang": str(e.get("lang", ""))[:10],
            "text": str(e.get("text", "")),
        }
        for e in entries if e.get("text")
    ]
    transcript_json = json.dumps(clean, ensure_ascii=False)
    rules = (
        f"You are an expert meeting summarizer. Summarize in {target_lang}.\n"
        "Output 3 sections:\n"
        "1) Summary — 2–6 sentences.\n"
        "2) Key Topics — 4–10 bullets (main ideas/themes).\n"
        "3) Action Items — bullets (owner — task — due date if mentioned). If none, say 'None stated.'\n\n"
        "Rules: Be concise. Do not invent facts. Keep names/dates. "
        f"{_length_hint(clean)} Write the entire output in {target_lang}.\n\n"
        "Transcript as JSON lines with fields: t, speaker, lang, text:\n"
        f"{transcript_json}"
    )
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(rules)
    return (getattr(resp, "text", "") or "").strip()
