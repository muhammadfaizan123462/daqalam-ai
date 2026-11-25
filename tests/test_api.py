"""Tests for the Da Qalam AI FastAPI server (demo mode, no Qwen key)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient

from demo import SAMPLE_POEM
from server import app

client = TestClient(app)


def test_root_serves_app():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Da Qalam AI" in resp.text
    assert "Pashto Poetry Assistant" in resp.text
    assert 'id="poem-input"' in resp.text


def test_status_reports_demo_without_key(monkeypatch):
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    resp = client.get("/api/status")
    assert resp.status_code == 200
    assert resp.json()["mode"] == "demo"
    assert resp.json()["qwen_configured"] is False


def test_analyze_sample_returns_all_sections():
    resp = client.post("/api/analyze", json={"poem": SAMPLE_POEM, "language": "en"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "demo"
    for key in (
        "meaning", "translation_urdu", "translation_english",
        "difficult_words", "emotions", "themes", "message", "summary",
    ):
        assert key in data and data[key], f"missing/empty: {key}"
    assert "Sow flowers" in data["translation_english"]


def test_analyze_empty_poem_400():
    resp = client.post("/api/analyze", json={"poem": "   ", "language": "en"})
    assert resp.status_code == 400


def test_analyze_bad_language_400():
    resp = client.post("/api/analyze", json={"poem": SAMPLE_POEM, "language": "fr"})
    assert resp.status_code == 400


def test_analyze_arbitrary_poem_is_demo_and_honest():
    resp = client.post(
        "/api/analyze", json={"poem": "زما زړه کې مینه ده", "language": "ur"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "demo"
    assert "ڈیمو" in data["demo_note"]  # Urdu demo note, not Latin "demo"
    assert "محبت" in data["themes"] or "مینه" in data["themes"]


def test_analyze_in_pashto_language():
    resp = client.post("/api/analyze", json={"poem": SAMPLE_POEM, "language": "ps"})
    assert resp.status_code == 200
    assert resp.json()["language"] == "ps"
    assert "ګلان" in resp.json()["meaning"] or "ګل" in resp.json()["meaning"]
