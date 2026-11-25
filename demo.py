"""Demo analysis engine for Da Qalam AI.

Honest, rule-based analysis used whenever no Qwen API key is configured.
It NEVER pretends to be live AI: for the built-in sample poem (a verified
Rahman Baba couplet) it returns hand-written explanations; for any other
poem it returns a structural reading (line/word counts, glossary matches,
theme and emotion signals) and says plainly that full interpretation
needs live AI. Translations of non-sample poems are NOT invented — the
translation fields carry a clear demo-limitation note instead.
"""

from __future__ import annotations

import re

LANGUAGES = ("ps", "ur", "en")

# ---------------------------------------------------------------- sample poem
# Verified Rahman Baba couplet, from the Diwan ("Sow Flowers" / کر د ګلو کړه).
# Sources: dastar.org (Diwan, English by Fayez M. Sahibzada) and
# Poetry Chaikhana (English by Robert Sampson & Momin Khan). Both agree on
# the Pashto wording; the transliteration in theragblog.com matches too.
# Rahman Baba (1632–1706), public domain.
SAMPLE_POEM = (
    "کر د ګلو کړه چې سیمه دې ګلزار شي\n"
    "اغزي مه کره په پښو کې به دې خار شي"
)
SAMPLE_POET = "Rahman Baba (رحمان بابا, 1632–1706)"

# ---------------------------------------------------------------- glossary
# word -> (meaning_ur, meaning_en, note)
GLOSSARY: dict[str, tuple[str, str, str]] = {
    "ګل": ("پھول", "flower", "The most common nature image in Pashto poetry."),
    "ګلزار": ("گلزار، پھولوں کا باغ", "flower garden", "A place full of flowers; a symbol of a beautiful life."),
    "ګلشن": ("گلشن، پھولوں کا باغ", "flower garden", "Like ګلزار — a garden in bloom."),
    "اغزی": ("کانٹے", "thorns", "Sharp thorns; a symbol of harm or bad deeds."),
    "خار": ("کانٹے کی چبھن", "a thorn's prick", "The sting of a thorn — the pain a bad deed causes."),
    "سیمه": ("علاقہ، زمین", "region, surroundings", "The land around you; your neighbourhood and world."),
    "پښې": ("پاؤں", "feet", "Your own feet — what you walk on, what gets hurt."),
    "کره": ("کرو", "do / make (imperative)", "A command: do it."),
    "مینه": ("محبت", "love", "Love — the central theme of much Pashto poetry."),
    "عشق": ("عشق", "passionate love", "Deep, burning love; often divine love in Sufi poetry."),
    "جانان": ("محبوب", "beloved", "The beloved — a person, or God in Sufi verse."),
    "یار": ("یار، دوست", "friend, lover", "A dear friend or lover."),
    "زړه": ("دل", "heart", "The heart — seat of feeling in Pashto poetry."),
    "دنیا": ("دنیا", "world", "The world and its passing nature."),
    "ژوند": ("زندگی", "life", "Life, and how it is lived."),
    "سترګې": ("آنکھیں", "eyes", "Eyes — often the beloved's eyes, or the way we see."),
    "شپه": ("رات", "night", "Night — often a time of longing or prayer."),
    "ورځ": ("دن", "day", "Day — light, clarity, a new beginning."),
    "سپوږمۍ": ("چاند", "moon", "The moon — beauty and light in the dark."),
    "ستوری": ("ستارہ", "star", "A star — guidance, hope, distance."),
    "غم": ("غم", "sorrow", "Sorrow and grief."),
    "درد": ("درد", "pain", "Pain — of the heart or of separation."),
    "اوښکې": ("آنسو", "tears", "Tears — the visible sign of sorrow or love."),
    "خوشحالي": ("خوشی", "happiness", "Joy and contentment."),
    "صبر": ("صبر", "patience", "Patience — a prized virtue in Pashto ethics."),
    "خدای": ("خدا", "God", "God — the addressee of much Sufi poetry."),
    "رب": ("رب", "Lord", "The Lord."),
    "دعا": ("دعا", "prayer", "Prayer, supplication."),
    "بڼ": ("باغ", "garden", "A garden — peace, beauty, paradise."),
    "چمن": ("چمن", "meadow", "A green meadow; a place of rest and beauty."),
    "بلبل": ("بلبل", "nightingale", "The nightingale — the singer of love in the garden."),
    "هیله": ("امید", "hope", "Hope."),
    "رڼا": ("روشنی", "light", "Light — truth, guidance, morning."),
    "صبح": ("صبح", "morning", "Morning — a fresh start."),
    "سندره": ("گیت", "song", "A song."),
    "وطن": ("وطن", "homeland", "The homeland — a deep theme in Pashto poetry."),
    "ملګری": ("دوست", "friend", "A companion, a friend."),
    "ازادي": ("آزادی", "freedom", "Freedom."),
    "پښتون": ("پختون", "Pashtun", "A Pashtun — the people and their code of honour."),
    "قلم": ("قلم", "pen", "The pen — the poet's tool."),
    "ښه": ("اچھا", "good", "Good — a good deed or a good person."),
    "بد": ("برا", "bad", "Bad — a bad deed or a bad person."),
    # Inflected forms that appear in the sample poem.
    "ګلو": ("پھولوں (کی)", "of flowers", "Flowers — the oblique form of ګل."),
    "پښو": ("پاؤں (میں)", "feet (in)", "Feet — the oblique form of پښې."),
    "کړه": ("کرو", "do / make (imperative)", "A command: do it (with ړ)."),
    "شي": ("ہونا، بننا", "becomes", "Becomes — the verb that completes the line."),
}

# ---------------------------------------------------------------- signals
# keyword (or substring) -> theme / emotion, per language label.
THEME_SIGNALS: dict[str, dict[str, str]] = {
    "love": {"ps": "مینه", "ur": "محبت", "en": "Love"},
    "nature": {"ps": "طبیعت", "ur": "فطرت", "en": "Nature"},
    "spirituality": {"ps": "روحانیت", "ur": "روحانیت", "en": "Spirituality"},
    "morality": {"ps": "اخلاق", "ur": "اخلاق", "en": "Morality & good deeds"},
    "sorrow": {"ps": "غم", "ur": "غم", "en": "Sorrow"},
    "life": {"ps": "ژوند او دنیا", "ur": "زندگی اور دنیا", "en": "Life & the world"},
    "hope": {"ps": "هیله", "ur": "امید", "en": "Hope"},
    "homeland": {"ps": "وطن", "ur": "وطن", "en": "Homeland"},
}
THEME_KEYWORDS: dict[str, list[str]] = {
    "love": ["مینه", "عشق", "جانان", "یار", "زړه"],
    "nature": ["ګل", "ګلزار", "بڼ", "چمن", "بلبل", "ګلشن", "ستوری", "سپوږمۍ"],
    "spirituality": ["خدای", "رب", "دعا", "صبر"],
    "morality": ["اغزی", "خار", "ښه", "بد"],
    "sorrow": ["غم", "درد", "اوښکې"],
    "life": ["دنیا", "ژوند"],
    "hope": ["هیله", "رڼا", "صبح", "خوشحالي"],
    "homeland": ["وطن", "پښتون", "ازادي"],
}
EMOTION_SIGNALS: dict[str, dict[str, str]] = {
    "love": {"ps": "مینه", "ur": "محبت", "en": "Love"},
    "longing": {"ps": "ارمان", "ur": "اشتیاق", "en": "Longing"},
    "peace": {"ps": "سکون", "ur": "سکون", "en": "Peace"},
    "sorrow": {"ps": "غم", "ur": "غم", "en": "Sorrow"},
    "devotion": {"ps": "عقیدت", "ur": "عقیدت", "en": "Devotion"},
    "hope": {"ps": "هیله", "ur": "امید", "en": "Hope"},
    "reflection": {"ps": "فکر", "ur": "غور و فکر", "en": "Moral reflection"},
}
EMOTION_KEYWORDS: dict[str, list[str]] = {
    "love": ["مینه", "عشق", "جانان"],
    "longing": ["یار", "زړه", "سترګې"],
    "peace": ["صبر", "رڼا", "صبح", "خوشحالي"],
    "sorrow": ["غم", "درد", "اوښکې"],
    "devotion": ["خدای", "رب", "دعا"],
    "hope": ["هیله", "خوشحالي", "رڼا"],
    "reflection": ["اغزی", "خار", "ښه", "بد"],
}

# ------------------------------------------------------- hand-written sample
# Written by the builder from the verified translations (Sahibzada via
# dastar.org; Sampson & Momin Khan via Poetry Chaikhana). The poet's
# identity is certain: Rahman Baba, Diwan, "Sow Flowers".
SAMPLE_ANALYSIS: dict[str, dict] = {
    "ps": {
        "meaning": (
            "دا شعر موږ ته وايي چې خپل ژوند کې ښېګڼې وکړه — لکه ګلان کرل — نو ستا "
            "چاپېریال به ښکلی او خوشبوداره شي. که بدي وکړې، لکه اغزي کرل، نو هماغه "
            "بدي به تا ته خپل زیان ورسوي. هر عمل خپل انجام لري."
        ),
        "translation_urdu": (
            "پھول بو، تاکہ تیری زمین گلزار بن جائے\n"
            "کانٹے مت بو، ورنہ تیرے پاؤں کو زخم لگیں گے"
        ),
        "translation_english": (
            "Sow flowers to make a garden bloom around you,\n"
            "The thorns you sow will prick your own feet."
        ),
        "message": (
            "نېکي وکړه او له بدۍ ځان وساته. چې څه کوې، هماغه به تا ته بېرته "
            "راشي — ښه عمل ښه انجام لري او بد عمل بد."
        ),
        "summary": (
            "د طبیعت په ژبه یو اخلاقي درس: زموږ عملونه زموږ شاوخوا داسې وده کوي "
            "لکه باغ یا لکه اغزي."
        ),
        "emotions": ["هیله", "فکر", "سکون"],
        "themes": ["اخلاق", "طبیعت", "ژوند او دنیا"],
    },
    "ur": {
        "meaning": (
            "یہ شعر ہمیں سکھاتا ہے کہ زندگی میں نیکی کرو — جیسے پھول بونا — تو "
            "تمہارا ماحول خوبصورت اور خوشبودار ہو جائے گا۔ اگر برائی کرو گے، جیسے "
            "کانٹے بونا، تو وہی برائی تمہیں نقصان پہنچائے گی۔ ہر عمل کا اپنا انجام ہوتا ہے۔"
        ),
        "translation_urdu": (
            "پھول بو، تاکہ تیری زمین گلزار بن جائے\n"
            "کانٹے مت بو، ورنہ تیرے پاؤں کو زخم لگیں گے"
        ),
        "translation_english": (
            "Sow flowers to make a garden bloom around you,\n"
            "The thorns you sow will prick your own feet."
        ),
        "message": (
            "نیکی کرو اور برائی سے بچو۔ جو کچھ تم کرتے ہو، وہی تمہارے پاس لوٹ کر "
            "آتا ہے — اچھا عمل اچھا انجام لاتا ہے، برا عمل برا۔"
        ),
        "summary": (
            "فطرت کی زبان میں ایک اخلاقی سبق: ہمارے اعمال ہمارے اردگرد ایسے اگتے ہیں "
            "جیسے باغ یا جیسے کانٹے۔"
        ),
        "emotions": ["امید", "غور و فکر", "سکون"],
        "themes": ["اخلاق", "فطرت", "زندگی اور دنیا"],
    },
    "en": {
        "meaning": (
            "This couplet teaches that the good we do shapes the world around "
            "us — plant flowers, and your surroundings become a garden. Plant "
            "thorns, and they will prick your own feet. Every action returns "
            "to the one who did it."
        ),
        "translation_urdu": (
            "پھول بو، تاکہ تیری زمین گلزار بن جائے\n"
            "کانٹے مت بو، ورنہ تیرے پاؤں کو زخم لگیں گے"
        ),
        "translation_english": (
            "Sow flowers to make a garden bloom around you,\n"
            "The thorns you sow will prick your own feet."
        ),
        "message": (
            "Do good, and keep away from harm. Whatever you do comes back to "
            "you — a good deed brings a good end, and a bad deed brings a bad one."
        ),
        "summary": (
            "A moral lesson in the language of nature: our deeds grow around us "
            "like a garden — or like thorns."
        ),
        "emotions": ["Hope", "Moral reflection", "Peace"],
        "themes": ["Morality & good deeds", "Nature", "Life & the world"],
    },
}

DEMO_NOTE = {
    "ps": (
        "ډیمو حالت: دا تحلیل د نمونې پر بنسټ دی، نه د ژوندۍ مصنوعي ذهانت. "
        "د بشپړ تشریح لپاره Qwen سره وصل شئ."
    ),
    "ur": (
        "ڈیمو موڈ: یہ تجزیہ نمونے پر مبنی ہے، زندہ AI پر نہیں۔ مکمل تشریح کے لیے Qwen سے جڑیں۔"
    ),
    "en": (
        "Demo mode: this analysis is rule-based sample work, not live AI. "
        "Connect Qwen for full interpretation."
    ),
}

GENERIC_MEANING = {
    "ps": (
        "ډیمو حالت کې، دا شعر په بشپړ ډول نه شي ژباړل کېدای. لاندې یې جوړښت "
        "او هغه سخت ټکي ښودل شوي چې په لغت کې موندل شوي. د شعر ژور مطلب "
        "لپاره ژوندۍ AI ته اړتیا ده."
    ),
    "ur": (
        "ڈیمو موڈ میں اس شعر کی مکمل تشریح نہیں کی جا سکتی۔ نیچے اس کی ساخت اور "
        "وہ مشکل الفاظ دکھائے گئے ہیں جو لغت میں ملے۔ گہرے مطلب کے لیے زندہ AI چاہیے۔"
    ),
    "en": (
        "In demo mode this poem cannot be fully interpreted. Below is its "
        "structure and the difficult words found in the glossary. A deeper "
        "reading needs live AI."
    ),
}
GENERIC_MESSAGE = {
    "ps": "د دې شعر دقیق پیغام په ډیمو حالت کې نه شو ټاکلای — ژوندۍ AI به یې وپوهېږي.",
    "ur": "اس شعر کا درست پیغام ڈیمو موڈ میں طے نہیں کیا جا سکتا — زندہ AI اسے سمجھے گا۔",
    "en": "The exact message of this poem cannot be fixed in demo mode — live AI would read it.",
}
GENERIC_SUMMARY = {
    "ps": "یو شعر چې {lines} کرښې او {words} ټکي لري. په لغت کې {n} سخت ټکي وموندل شول.",
    "ur": "ایک شعر جس میں {lines} مصرعے اور {words} الفاظ ہیں۔ لغت میں {n} مشکل الفاظ ملے۔",
    "en": "A poem of {lines} lines and {words} words. {n} difficult words were found in the glossary.",
}
NO_TRANSLATION_UR = "ڈیمو موڈ اس شعر کا اردو ترجمہ نہیں کر سکتا — مکمل ترجمے کے لیے Qwen سے جڑیں۔"
NO_TRANSLATION_EN = "Demo mode cannot translate this poem into English — connect Qwen for a full translation."


def _norm_yeh(s: str) -> str:
    """Map Arabic Yeh (U+064A) to Farsi Yeh (U+06CC).

    Pashto writers interchange the two look-alike letters, and web
    sources mix them (the sample poem itself uses U+064A in اغزي while
    the glossary was written with U+06CC). Normalising makes matching
    work regardless of which Yeh the user pastes.
    """
    return s.replace("\u064a", "\u06cc")


def _normalize(text: str) -> str:
    """Collapse whitespace for comparison."""
    return " ".join(text.strip().split())


def _is_sample(poem: str) -> bool:
    return _norm_yeh(_normalize(poem)) == _norm_yeh(_normalize(SAMPLE_POEM))


def _tokenize(poem: str) -> list[str]:
    return [t for t in re.split(r"\s+", poem.strip()) if t]


def _strip_punct(token: str) -> str:
    return token.strip("،؛؟.!؟\"'()[]«»—-")


# Normalised glossary for lookup (Yeh variants unified).
_GLOSSARY_NORM = {_norm_yeh(k): v for k, v in GLOSSARY.items()}


def find_difficult_words(poem: str) -> list[dict]:
    """Glossary entries whose word appears in the poem (order of appearance)."""
    found: list[dict] = []
    seen: set[str] = set()
    for token in _tokenize(poem):
        word = _norm_yeh(_strip_punct(token))
        if word in _GLOSSARY_NORM and word not in seen:
            seen.add(word)
            ur, en, note = _GLOSSARY_NORM[word]
            found.append({"word": word, "meaning_ur": ur, "meaning_en": en, "note": note})
    return found


def _detect(poem: str, signals: dict[str, list[str]], labels: dict[str, dict[str, str]], language: str) -> list[str]:
    hits: list[str] = []
    poem_n = _norm_yeh(poem)
    for key, keywords in signals.items():
        if any(_norm_yeh(kw) in poem_n for kw in keywords):
            hits.append(labels[key][language])
    return hits


def analyze_demo(poem: str, language: str = "ps") -> dict:
    """Rule-based demo analysis. Never pretends to be live AI.

    Raises ValueError on empty input or unsupported language.
    """
    if not poem or not poem.strip():
        raise ValueError("Poem is empty")
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    poem = poem.strip()
    lines = [ln for ln in poem.splitlines() if ln.strip()]
    words = _tokenize(poem)
    difficult = find_difficult_words(poem)
    stats = {
        "lines": len(lines),
        "words": len(words),
        "difficult_words_found": len(difficult),
    }
    base = {
        "mode": "demo",
        "poem": poem,
        "language": language,
        "stats": stats,
        "demo_note": DEMO_NOTE[language],
    }
    if _is_sample(poem):
        s = SAMPLE_ANALYSIS[language]
        return {
            **base,
            "meaning": s["meaning"],
            "translation_urdu": s["translation_urdu"],
            "translation_english": s["translation_english"],
            "difficult_words": difficult,
            "emotions": s["emotions"],
            "themes": s["themes"],
            "message": s["message"],
            "summary": s["summary"],
            "poet": SAMPLE_POET,
        }
    emotions = _detect(poem, EMOTION_KEYWORDS, EMOTION_SIGNALS, language)
    themes = _detect(poem, THEME_KEYWORDS, THEME_SIGNALS, language)
    return {
        **base,
        "meaning": GENERIC_MEANING[language],
        "translation_urdu": NO_TRANSLATION_UR,
        "translation_english": NO_TRANSLATION_EN,
        "difficult_words": difficult,
        "emotions": emotions,
        "themes": themes,
        "message": GENERIC_MESSAGE[language],
        "summary": GENERIC_SUMMARY[language].format(
            lines=len(lines), words=len(words), n=len(difficult)
        ),
        "poet": None,
    }
