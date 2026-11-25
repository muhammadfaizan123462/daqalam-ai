"""Da Qalam AI — FastAPI server.

Serves the static frontend (index.html, styles.css, app.js) and
POST /api/analyze {poem, language}:

- If QWEN_API_KEY is set, the poem is sent to Qwen (DashScope) with the
  Da Qalam system prompt and the JSON answer is returned with
  mode="live". If Qwen is unavailable or fails, the server tries Gemini
  (Google AI Studio) with the same prompt and contract, returning
  mode="live" with provider="gemini".
- Otherwise (or if both LLM calls fail), the honest rule-based demo
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
from gemini_client import GeminiUnavailable, get_client as get_gemini_client
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


def _parse_llm_json(content: str) -> dict | None:
    """Extract a JSON object from an LLM reply (tolerates ```json fences)."""
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


def _build_live_result(
    poem: str, language: str, data: dict, provider: str, model: str
) -> dict:
    """Shape one provider's parsed JSON into the /api/analyze response."""
    stats_lines = len([ln for ln in poem.splitlines() if ln.strip()])
    return {
        "mode": "live",
        "provider": provider,
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
        "model": model,
    }


def _try_provider(
    provider: str, poem: str, language: str, messages: list[dict]
) -> dict:
    """Ask one provider for a structured analysis. Raises on any failure."""
    if provider == "qwen":
        client = get_client()
        if not client.is_available():
            raise QwenUnavailable("No Qwen API key configured.")
    else:
        client = get_gemini_client()
        if not client.is_available():
            raise GeminiUnavailable("No Gemini API key configured.")
    result = client.complete(messages)
    data = _parse_llm_json(result["content"])
    if data is None:
        raise RuntimeError(f"{provider} did not return valid JSON.")
    missing = [k for k in ANALYSIS_KEYS if k not in data]
    if missing:
        raise RuntimeError(f"{provider} JSON missing keys: {missing}")
    return _build_live_result(poem, language, data, provider, result["model"])


def analyze_live(poem: str, language: str) -> dict:
    """Ask Qwen first, then Gemini, for a structured analysis.

    Raises on any failure, so the caller can fall back to demo mode.
    """
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
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    last_exc: Exception | None = None
    for provider in ("qwen", "gemini"):
        try:
            return _try_provider(provider, poem, language, messages)
        except Exception as exc:  # noqa: BLE001 - try the next provider
            last_exc = exc
    raise RuntimeError(f"All LLM providers failed: {last_exc}")


@app.get("/api/status")
def status() -> dict:
    """Which mode the server is in (live Qwen/Gemini vs demo)."""
    qwen = get_client().is_available()
    gemini = get_gemini_client().is_available()
    provider = "qwen" if qwen else ("gemini" if gemini else None)
    return {
        "mode": "live" if provider else "demo",
        "qwen_configured": qwen,
        "gemini_configured": gemini,
        "provider": provider,
    }


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
