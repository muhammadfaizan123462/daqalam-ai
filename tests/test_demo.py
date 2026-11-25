"""Tests for the Da Qalam AI demo engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from demo import (
    GLOSSARY,
    SAMPLE_POEM,
    analyze_demo,
    find_difficult_words,
)


def test_sample_analysis_has_all_sections():
    result = analyze_demo(SAMPLE_POEM, "en")
    assert result["mode"] == "demo"
    for key in (
        "meaning", "translation_urdu", "translation_english",
        "difficult_words", "emotions", "themes", "message", "summary",
    ):
        assert key in result, f"missing section: {key}"
        assert result[key], f"empty section: {key}"
    assert result["poet"] == "Rahman Baba (رحمان بابا, 1632–1706)"


def test_sample_translations_present_and_real():
    result = analyze_demo(SAMPLE_POEM, "ps")
    assert "گلزار" in result["translation_urdu"]
    assert "Sow flowers" in result["translation_english"]
    assert result["translation_urdu"] != SAMPLE_POEM
    assert result["translation_english"] != SAMPLE_POEM


def test_sample_difficult_words_include_gulzar_and_thorns():
    words = [w["word"] for w in analyze_demo(SAMPLE_POEM, "en")["difficult_words"]]
    assert "ګلزار" in words
    assert "اغزی" in words
    assert "خار" in words
    assert "سیمه" in words


def test_sample_meaning_differs_by_language():
    ps = analyze_demo(SAMPLE_POEM, "ps")["meaning"]
    ur = analyze_demo(SAMPLE_POEM, "ur")["meaning"]
    en = analyze_demo(SAMPLE_POEM, "en")["meaning"]
    assert ps != ur != en
    assert "ګلان" in ps or "ګل" in ps
    assert "پھول" in ur
    assert "garden" in en


def test_empty_poem_rejected():
    with pytest.raises(ValueError):
        analyze_demo("   ", "en")
    with pytest.raises(ValueError):
        analyze_demo("", "ps")


def test_bad_language_rejected():
    with pytest.raises(ValueError):
        analyze_demo(SAMPLE_POEM, "fr")


def test_glossary_lookup():
    found = find_difficult_words("زما زړه کې مینه ده")
    words = [w["word"] for w in found]
    assert "زړه" in words and "مینه" in words
    assert found[0]["meaning_en"]  # every entry has meanings
    assert find_difficult_words("hello world") == []


def test_glossary_covers_common_words():
    for word in ("ګل", "مینه", "خدای", "دنیا", "زړه", "غم"):
        assert word in GLOSSARY


def test_arbitrary_poem_demo_is_honest():
    poem = "زما زړه کې مینه ده\nد دنیا غم مې نه دی هېر"
    result = analyze_demo(poem, "en")
    assert result["mode"] == "demo"
    assert "demo" in result["demo_note"].lower()
    # Demo must NOT invent a translation for an unseen poem.
    assert "cannot translate" in result["translation_english"]
    assert "connect Qwen" in result["translation_english"]
    assert result["poet"] is None


def test_arbitrary_poem_detects_love_theme():
    result = analyze_demo("مینه او جانان زما زړه کې دي", "en")
    assert "Love" in result["themes"]
    assert "Love" in result["emotions"]


def test_stats_count_lines_and_words():
    result = analyze_demo("یوه کرښه\nبله کرښه ده", "en")
    assert result["stats"]["lines"] == 2
    assert result["stats"]["words"] == 5
