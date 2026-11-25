"""Tests for the Qwen -> Gemini LLM fallback in Da Qalam AI."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient

import server
from demo import SAMPLE_POEM
from server import app

client = TestClient(app)

FAKE_ANALYSIS = {
    "meaning": "Fake meaning from the test double.",
    "translation_urdu": "جعلي اردو ترجمہ",
    "translation_english": "Fake English translation.",
    "difficult_words": [
        {"word": "ګل", "meaning_ur": "پھول", "meaning_en": "flower", "note": ""}
    ],
    "emotions": ["hope"],
    "themes": ["goodness"],
    "message": "Fake message.",
    "summary": "Fake summary.",
}


class FakeClient:
    def __init__(self, available=True, fail=False):
        self._available = available
        self._fail = fail

    def is_available(self):
        return self._available

    def complete(self, messages):
        if self._fail:
            raise RuntimeError("fake provider failure")
        return {"content": json.dumps(FAKE_ANALYSIS), "model": "fake-model"}


def test_status_reports_gemini_when_only_gemini_configured(monkeypatch):
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "live"
    assert data["qwen_configured"] is False
    assert data["gemini_configured"] is True
    assert data["provider"] == "gemini"


def test_status_prefers_qwen_when_both_configured(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    resp = client.get("/api/status")
    assert resp.json()["mode"] == "live"
    assert resp.json()["provider"] == "qwen"


def test_analyze_falls_back_to_gemini_when_qwen_fails(monkeypatch):
    monkeypatch.setattr(server, "get_client", lambda: FakeClient(fail=True))
    monkeypatch.setattr(server, "get_gemini_client", lambda: FakeClient())
    resp = client.post("/api/analyze", json={"poem": SAMPLE_POEM, "language": "en"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "live"
    assert data["provider"] == "gemini"
    assert data["translation_english"] == "Fake English translation."
    assert data["model"] == "fake-model"


def test_analyze_falls_back_to_demo_when_both_providers_fail(monkeypatch):
    monkeypatch.setattr(server, "get_client", lambda: FakeClient(fail=True))
    monkeypatch.setattr(server, "get_gemini_client", lambda: FakeClient(fail=True))
    resp = client.post("/api/analyze", json={"poem": SAMPLE_POEM, "language": "en"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "demo"
    assert "live_error" in data
