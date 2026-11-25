# Da Qalam AI — Pashto Poetry Assistant

> **Why it can impress judges:** It connects AI with regional culture, language
> accessibility and a real educational problem — most Pashto students can read
> poetry but cannot *understand* it. Da Qalam AI explains Pashto poetry in
> simple Pashto, Urdu or English, translates it, unpacks difficult words, and
> reveals the emotions, themes and message behind the verse.

A beautiful, modern web app that helps people understand Pashto poetry and
literature. Dark navy + gold premium design, full RTL support, Pashto
typography (Noto Nastaliq Urdu), mobile-first and responsive.

## Features

1. Large textarea to paste Pashto poetry
2. Language selection: Pashto, Urdu, English (the explanation language)
3. Simple-language explanation of the poem
4. Translation into Urdu and English
5. Difficult Pashto words explained individually (glossary)
6. Emotions, themes and the poet's message identified
7. Short summary
8. Copy results button (copies the full formatted analysis)
9. Clear / reset button
10. Sample poem button — a verified Rahman Baba couplet

The UI **always** shows a visible badge: **● Live AI (Qwen)** when Qwen
answers, or **● Demo mode — sample explanations** when it does not.
Demo responses are never presented as live AI.

## Sample poem (verified)

> کر د ګلو کړه چې سیمه دې ګلزار شي
> اغزي مه کره په پښو کې به دې خار شي
> — **Rahman Baba** (1632–1706), from the Diwan, *"Sow Flowers"*

Wording verified against two independent sources: dastar.org (Diwan,
English by Fayez M. Sahibzada) and Poetry Chaikhana (English by Robert
Sampson & Momin Khan); the transliteration matches theragblog.com.
Rahman Baba is public domain. The poet is only attributed when certain —
the app never invents a poet's identity.

## Run it

### Demo mode (no key needed — open and use)

```bash
# Option A: just open the file
open index.html        # or double-click it

# Option B: serve it locally
python3 -m http.server 8000 --directory .
# then open http://127.0.0.1:8000
```

Demo mode gives a hand-written analysis of the sample poem and an honest
structural reading (glossary matches, themes, emotions) for any other poem.
It says plainly that full interpretation needs live AI, and it does not
invent translations for poems it has not seen.

### Live mode (Qwen)

```bash
pip install -r requirements.txt
QWEN_API_KEY=your-dashscope-key python server.py
# open http://127.0.0.1:8000
```

The server sends the poem to Qwen (Alibaba DashScope, OpenAI-compatible
endpoint) with the Da Qalam system prompt and returns structured JSON.
The key lives **only** in the `QWEN_API_KEY` environment variable on the
server — never in the frontend or in source code.

## Project structure

| File | What it is |
|---|---|
| `index.html` | Page structure (header, hero, input, results, empty state) |
| `styles.css` | Dark navy + gold design, RTL, mobile-first responsive |
| `app.js` | UI logic + standalone demo engine (JS mirror of `demo.py`) |
| `server.py` | FastAPI: serves the site + `POST /api/analyze`, `GET /api/status` |
| `demo.py` | Honest rule-based demo engine (glossary, themes, sample analysis) |
| `qwen_client.py` | Qwen/DashScope client (httpx), key from env only |
| `requirements.txt` | fastapi, uvicorn, httpx |
| `tests/` | pytest suite (demo engine + API) |

## API

- `GET /` — the app
- `GET /api/status` — `{"mode": "demo"|"live", "qwen_configured": bool}`
- `POST /api/analyze` — body `{"poem": "...", "language": "ps"|"ur"|"en"}`.
  Returns `mode`, `meaning`, `translation_urdu`, `translation_english`,
  `difficult_words[]`, `emotions[]`, `themes[]`, `message`, `summary`,
  `stats`. Empty poem → 400. If Qwen fails, the server falls back to the
  demo engine and says so in `live_error`.

## Tests

```bash
python -m pytest tests/ -q
```

## Limitations (honest)

- Demo mode cannot translate or deeply interpret poems other than the
  sample — it gives structure + glossary matches and says so.
- Live mode needs a DashScope API key and network access; Qwen answers
  are the model's interpretation, not scholarly fact — the app says so
  when meaning is uncertain.
- Glossary covers ~40 common poetry words; it is a starter, not a
  dictionary.
