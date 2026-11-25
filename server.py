"""Da Qalam AI — FastAPI server.

Serves the static frontend (index.html, styles.css, app.js) and
POST /api/analyze {poem, language}:

- If QWEN_API_KEY is set, the poem is sent to Qwen (DashScope) with the
  Da Qalam system prompt and the JSON answer is returned with
  mode="live".
- Otherwise (or if the Qwen call fails), the honest rule-based demo
  engine answers with mode="demo" — clearly labelled, never pretending
  to be live AI.

Run:  python server.py          (http://127.0.0.1:8000)
Live:  QWEN_API_KEY=... python server.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from demo import LANGUAGES, analyze_demo
from qwen_client import SYSTEM_PROMPT, QwenUnavailable, get_client

BASE_DIR = Path(__file__).resolve().parent
MAX_POEM_CHARS = 5000

app = FastAPI(title="Da Qalam AI", version="1.0.0")

ANALYSIS_KEYS = (
    "meaning",
    "translation_urdu",
    "translation_english",
    "difficult_words",
    "emotions",
    "themes",
    "message",
    "summary",
)


class AnalyzeRequest(BaseModel):
    poem: str = Field(..., min_length=1, max_length=MAX_POEM_CHARS)
    language: str = "ps"


def _parse_qwen_json(content: str) -> dict | None:
    """Extract a JSON object from Qwen's reply (tolerates ```json fences)."""
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def analyze_live(poem: str, language: str) -> dict:
    """Ask Qwen for a structured analysis. Raises on any failure."""
    client = get_client()
    if not client.is_available():
        raise QwenUnavailable("No Qwen API key configured.")
    lang_name = {"ps": "Pashto", "ur": "Urdu", "en": "English"}[language]
    user_message = (
        f"Poem (Pashto):\n{poem}\n\n"
        f"Give the explanation in {lang_name}. "
        "Respond with valid JSON only, no other text, using exactly these keys: "
        "meaning (string), translation_urdu (string), translation_english (string), "
        "difficult_words (array of objects with word, meaning_ur, meaning_en, note), "
        "emotions (array of strings), themes (array of strings), "
        "message (string), summary (string)."
    )
    result = client.complete(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
    )
    data = _parse_qwen_json(result["content"])
    if data is None:
        raise RuntimeError("Qwen did not return valid JSON.")
    missing = [k for k in ANALYSIS_KEYS if k not in data]
    if missing:
        raise RuntimeError(f"Qwen JSON missing keys: {missing}")
    stats_lines = len([ln for ln in poem.splitlines() if ln.strip()])
    return {
        "mode": "live",
        "poem": poem,
        "language": language,
        "stats": {
            "lines": stats_lines,
            "words": len(poem.split()),
            "difficult_words_found": len(data.get("difficult_words") or []),
        },
        "meaning": data["meaning"],
        "translation_urdu": data["translation_urdu"],
        "translation_english": data["translation_english"],
        "difficult_words": data["difficult_words"],
        "emotions": data["emotions"],
        "themes": data["themes"],
        "message": data["message"],
        "summary": data["summary"],
        "model": result["model"],
    }


@app.get("/api/status")
def status() -> dict:
    """Which mode the server is in (live Qwen vs demo)."""
    configured = get_client().is_available()
    return {"mode": "live" if configured else "demo", "qwen_configured": configured}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> JSONResponse:
    poem = (req.poem or "").strip()
    if not poem:
        raise HTTPException(status_code=400, detail="Poem is empty")
    if req.language not in LANGUAGES:
        raise HTTPException(
            status_code=400, detail=f"Unsupported language: {req.language}"
        )
    try:
        return JSONResponse(analyze_live(poem, req.language))
    except Exception as exc:  # noqa: BLE001 - fall back to honest demo mode
        result = analyze_demo(poem, req.language)
        result["live_error"] = f"Live AI unavailable ({exc}); showing demo analysis."
        return JSONResponse(result)


# Static frontend last: serves index.html at / and the assets.
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port)
