import sys, json
from apps.gemini_api.summarizer import summarize_conversation

if __name__ == "__main__":
    """
    STDIN JSON:
    { "entries":[{"t":0.0,"speaker":"A","lang":"en","text":"..."}, ...],
      "target_lang":"en" }

    STDOUT JSON:
    { "status":"ok", "summary_text":"..." }  OR  { "status":"error", "message":"..." }
    """
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        entries = payload.get("entries") or []
        target = payload.get("target_lang") or "en"
        text = summarize_conversation(entries, target_lang=target)
        sys.stdout.write(json.dumps({"status":"ok","summary_text":text}, ensure_ascii=False))
        sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(json.dumps({"status":"error","message":str(e)}))
        sys.stdout.flush()
        sys.exit(1)
