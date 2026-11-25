/* Da Qalam AI — frontend.
 *
 * Pure demo logic lives at the top (no DOM access) so it can be tested
 * under Node. DOM wiring is inside init(), run on DOMContentLoaded.
 * The app tries POST /api/analyze first; when the server is absent
 * (e.g. opening index.html directly) it falls back to the built-in
 * demo analysis. The mode badge ALWAYS shows which one answered.
 */
"use strict";

/* ------------------------------------------------------------------ data */
var SAMPLE_POEM =
  "کر د ګلو کړه چې سیمه دې ګلزار شي\nاغزي مه کره په پښو کې به دې خار شي";
var SAMPLE_POET = "Rahman Baba (رحمان بابا, 1632–1706)";

/* word -> [meaning_ur, meaning_en, note] — mirrors demo.py GLOSSARY */
var GLOSSARY = {
  "ګل": ["پھول", "flower", "The most common nature image in Pashto poetry."],
  "ګلزار": ["گلزار، پھولوں کا باغ", "flower garden", "A place full of flowers; a symbol of a beautiful life."],
  "ګلشن": ["گلشن، پھولوں کا باغ", "flower garden", "Like ګلزار — a garden in bloom."],
  "اغزی": ["کانٹے", "thorns", "Sharp thorns; a symbol of harm or bad deeds."],
  "خار": ["کانٹے کی چبھن", "a thorn's prick", "The sting of a thorn — the pain a bad deed causes."],
  "سیمه": ["علاقہ، زمین", "region, surroundings", "The land around you; your neighbourhood and world."],
  "پښې": ["پاؤں", "feet", "Your own feet — what you walk on, what gets hurt."],
  "کره": ["کرو", "do / make (imperative)", "A command: do it."],
  "مینه": ["محبت", "love", "Love — the central theme of much Pashto poetry."],
  "عشق": ["عشق", "passionate love", "Deep, burning love; often divine love in Sufi poetry."],
  "جانان": ["محبوب", "beloved", "The beloved — a person, or God in Sufi verse."],
  "یار": ["یار، دوست", "friend, lover", "A dear friend or lover."],
  "زړه": ["دل", "heart", "The heart — seat of feeling in Pashto poetry."],
  "دنیا": ["دنیا", "world", "The world and its passing nature."],
  "ژوند": ["زندگی", "life", "Life, and how it is lived."],
  "سترګې": ["آنکھیں", "eyes", "Eyes — often the beloved's eyes, or the way we see."],
  "شپه": ["رات", "night", "Night — often a time of longing or prayer."],
  "ورځ": ["دن", "day", "Day — light, clarity, a new beginning."],
  "سپوږمۍ": ["چاند", "moon", "The moon — beauty and light in the dark."],
  "ستوری": ["ستارہ", "star", "A star — guidance, hope, distance."],
  "غم": ["غم", "sorrow", "Sorrow and grief."],
  "درد": ["درد", "pain", "Pain — of the heart or of separation."],
  "اوښکې": ["آنسو", "tears", "Tears — the visible sign of sorrow or love."],
  "خوشحالي": ["خوشی", "happiness", "Joy and contentment."],
  "صبر": ["صبر", "patience", "Patience — a prized virtue in Pashto ethics."],
  "خدای": ["خدا", "God", "God — the addressee of much Sufi poetry."],
  "رب": ["رب", "Lord", "The Lord."],
  "دعا": ["دعا", "prayer", "Prayer, supplication."],
  "بڼ": ["باغ", "garden", "A garden — peace, beauty, paradise."],
  "چمن": ["چمن", "meadow", "A green meadow; a place of rest and beauty."],
  "بلبل": ["بلبل", "nightingale", "The nightingale — the singer of love in the garden."],
  "هیله": ["امید", "hope", "Hope."],
  "رڼا": ["روشنی", "light", "Light — truth, guidance, morning."],
  "صبح": ["صبح", "morning", "Morning — a fresh start."],
  "سندره": ["گیت", "song", "A song."],
  "وطن": ["وطن", "homeland", "The homeland — a deep theme in Pashto poetry."],
  "ملګری": ["دوست", "friend", "A companion, a friend."],
  "ازادي": ["آزادی", "freedom", "Freedom."],
  "پښتون": ["پختون", "Pashtun", "A Pashtun — the people and their code of honour."],
  "قلم": ["قلم", "pen", "The pen — the poet's tool."],
  "ښه": ["اچھا", "good", "Good — a good deed or a good person."],
  "بد": ["برا", "bad", "Bad — a bad deed or a bad person."],
  "ګلو": ["پھولوں (کی)", "of flowers", "Flowers — the oblique form of ګل."],
  "پښو": ["پاؤں (میں)", "feet (in)", "Feet — the oblique form of پښې."],
  "کړه": ["کرو", "do / make (imperative)", "A command: do it (with ړ)."],
  "شي": ["ہونا، بننا", "becomes", "Becomes — the verb that completes the line."]
};

var THEME_SIGNALS = {
  love: { ps: "مینه", ur: "محبت", en: "Love" },
  nature: { ps: "طبیعت", ur: "فطرت", en: "Nature" },
  spirituality: { ps: "روحانیت", ur: "روحانیت", en: "Spirituality" },
  morality: { ps: "اخلاق", ur: "اخلاق", en: "Morality & good deeds" },
  sorrow: { ps: "غم", ur: "غم", en: "Sorrow" },
  life: { ps: "ژوند او دنیا", ur: "زندگی اور دنیا", en: "Life & the world" },
  hope: { ps: "هیله", ur: "امید", en: "Hope" },
  homeland: { ps: "وطن", ur: "وطن", en: "Homeland" }
};
var THEME_KEYWORDS = {
  love: ["مینه", "عشق", "جانان", "یار", "زړه"],
  nature: ["ګل", "ګلزار", "بڼ", "چمن", "بلبل", "ګلشن", "ستوری", "سپوږمۍ"],
  spirituality: ["خدای", "رب", "دعا", "صبر"],
  morality: ["اغزی", "خار", "ښه", "بد"],
  sorrow: ["غم", "درد", "اوښکې"],
  life: ["دنیا", "ژوند"],
  hope: ["هیله", "رڼا", "صبح", "خوشحالي"],
  homeland: ["وطن", "پښتون", "ازادي"]
};
var EMOTION_SIGNALS = {
  love: { ps: "مینه", ur: "محبت", en: "Love" },
  longing: { ps: "ارمان", ur: "اشتیاق", en: "Longing" },
  peace: { ps: "سکون", ur: "سکون", en: "Peace" },
  sorrow: { ps: "غم", ur: "غم", en: "Sorrow" },
  devotion: { ps: "عقیدت", ur: "عقیدت", en: "Devotion" },
  hope: { ps: "هیله", ur: "امید", en: "Hope" },
  reflection: { ps: "فکر", ur: "غور و فکر", en: "Moral reflection" }
};
var EMOTION_KEYWORDS = {
  love: ["مینه", "عشق", "جانان"],
  longing: ["یار", "زړه", "سترګې"],
  peace: ["صبر", "رڼا", "صبح", "خوشحالي"],
  sorrow: ["غم", "درد", "اوښکې"],
  devotion: ["خدای", "رب", "دعا"],
  hope: ["هیله", "خوشحالي", "رڼا"],
  reflection: ["اغزی", "خار", "ښه", "بد"]
};

var SAMPLE_ANALYSIS = {
  ps: {
    meaning: "دا شعر موږ ته وايي چې خپل ژوند کې ښېګڼې وکړه — لکه ګلان کرل — نو ستا چاپېریال به ښکلی او خوشبوداره شي. که بدي وکړې، لکه اغزي کرل، نو هماغه بدي به تا ته خپل زیان ورسوي. هر عمل خپل انجام لري.",
    translation_urdu: "پھول بو، تاکہ تیری زمین گلزار بن جائے\nکانٹے مت بو، ورنہ تیرے پاؤں کو زخم لگیں گے",
    translation_english: "Sow flowers to make a garden bloom around you,\nThe thorns you sow will prick your own feet.",
    message: "نېکي وکړه او له بدۍ ځان وساته. چې څه کوې، هماغه به تا ته بېرته راشي — ښه عمل ښه انجام لري او بد عمل بد.",
    summary: "د طبیعت په ژبه یو اخلاقي درس: زموږ عملونه زموږ شاوخوا داسې وده کوي لکه باغ یا لکه اغزي.",
    emotions: ["هیله", "فکر", "سکون"],
    themes: ["اخلاق", "طبیعت", "ژوند او دنیا"]
  },
  ur: {
    meaning: "یہ شعر ہمیں سکھاتا ہے کہ زندگی میں نیکی کرو — جیسے پھول بونا — تو تمہارا ماحول خوبصورت اور خوشبودار ہو جائے گا۔ اگر برائی کرو گے، جیسے کانٹے بونا، تو وہی برائی تمہیں نقصان پہنچائے گی۔ ہر عمل کا اپنا انجام ہوتا ہے۔",
    translation_urdu: "پھول بو، تاکہ تیری زمین گلزار بن جائے\nکانٹے مت بو، ورنہ تیرے پاؤں کو زخم لگیں گے",
    translation_english: "Sow flowers to make a garden bloom around you,\nThe thorns you sow will prick your own feet.",
    message: "نیکی کرو اور برائی سے بچو۔ جو کچھ تم کرتے ہو، وہی تمہارے پاس لوٹ کر آتا ہے — اچھا عمل اچھا انجام لاتا ہے، برا عمل برا۔",
    summary: "فطرت کی زبان میں ایک اخلاقی سبق: ہمارے اعمال ہمارے اردگرد ایسے اگتے ہیں جیسے باغ یا جیسے کانٹے۔",
    emotions: ["امید", "غور و فکر", "سکون"],
    themes: ["اخلاق", "فطرت", "زندگی اور دنیا"]
  },
  en: {
    meaning: "This couplet teaches that the good we do shapes the world around us — plant flowers, and your surroundings become a garden. Plant thorns, and they will prick your own feet. Every action returns to the one who did it.",
    translation_urdu: "پھول بو، تاکہ تیری زمین گلزار بن جائے\nکانٹے مت بو، ورنہ تیرے پاؤں کو زخم لگیں گے",
    translation_english: "Sow flowers to make a garden bloom around you,\nThe thorns you sow will prick your own feet.",
    message: "Do good, and keep away from harm. Whatever you do comes back to you — a good deed brings a good end, and a bad deed brings a bad one.",
    summary: "A moral lesson in the language of nature: our deeds grow around us like a garden — or like thorns.",
    emotions: ["Hope", "Moral reflection", "Peace"],
    themes: ["Morality & good deeds", "Nature", "Life & the world"]
  }
};

var DEMO_NOTE = {
  ps: "ډیمو حالت: دا تحلیل د نمونې پر بنسټ دی، نه د ژوندۍ مصنوعي ذهانت. د بشپړ تشریح لپاره Qwen سره وصل شئ.",
  ur: "ڈیمو موڈ: یہ تجزیہ نمونے پر مبنی ہے، زندہ AI پر نہیں۔ مکمل تشریح کے لیے Qwen سے جڑیں۔",
  en: "Demo mode: this analysis is rule-based sample work, not live AI. Connect Qwen for full interpretation."
};
var GENERIC_MEANING = {
  ps: "ډیمو حالت کې، دا شعر په بشپړ ډول نه شي ژباړل کېدای. لاندې یې جوړښت او هغه سخت ټکي ښودل شوي چې په لغت کې موندل شوي. د شعر ژور مطلب لپاره ژوندۍ AI ته اړتیا ده.",
  ur: "ڈیمو موڈ میں اس شعر کی مکمل تشریح نہیں کی جا سکتی۔ نیچے اس کی ساخت اور وہ مشکل الفاظ دکھائے گئے ہیں جو لغت میں ملے۔ گہرے مطلب کے لیے زندہ AI چاہیے۔",
  en: "In demo mode this poem cannot be fully interpreted. Below is its structure and the difficult words found in the glossary. A deeper reading needs live AI."
};
var GENERIC_MESSAGE = {
  ps: "د دې شعر دقیق پیغام په ډیمو حالت کې نه شو ټاکلای — ژوندۍ AI به یې وپوهېږي.",
  ur: "اس شعر کا درست پیغام ڈیمو موڈ میں طے نہیں کیا جا سکتا — زندہ AI اسے سمجھے گا۔",
  en: "The exact message of this poem cannot be fixed in demo mode — live AI would read it."
};
var NO_TRANSLATION_UR = "ڈیمو موڈ اس شعر کا اردو ترجمہ نہیں کر سکتا — مکمل ترجمے کے لیے Qwen سے جڑیں۔";
var NO_TRANSLATION_EN = "Demo mode cannot translate this poem into English — connect Qwen for a full translation.";

var HEADINGS = {
  ps: { meaning: "مطلب", translation_urdu: "اردو ژباړه", translation_english: "انګلیسي ژباړه", difficult_words: "سخت ټکي", emotions: "جذبات", themes: "موضوعات", message: "د شاعر پیغام", summary: "لنډیز" },
  ur: { meaning: "مطلب", translation_urdu: "اردو ترجمہ", translation_english: "انگریزی ترجمہ", difficult_words: "مشکل الفاظ", emotions: "جذبات", themes: "موضوعات", message: "شاعر کا پیغام", summary: "خلاصہ" },
  en: { meaning: "Meaning", translation_urdu: "Urdu translation", translation_english: "English translation", difficult_words: "Difficult words", emotions: "Emotions", themes: "Themes", message: "Poet's message", summary: "Summary" }
};

/* ------------------------------------------------------------ pure logic */
function normYeh(s) { return s.replace(/ي/g, "ی"); }
function normalize(text) { return text.trim().split(/\s+/).join(" "); }
function isSample(poem) { return normYeh(normalize(poem)) === normYeh(normalize(SAMPLE_POEM)); }
function tokenize(poem) { return poem.trim().split(/\s+/).filter(Boolean); }
function stripPunct(token) { return token.replace(/^[،؛؟.!؟"'()[\]«»—-]+|[،؛؟.!؟"'()[\]«»—-]+$/g, ""); }

/* Normalised glossary for lookup (Yeh variants unified). */
var GLOSSARY_NORM = {};
Object.keys(GLOSSARY).forEach(function (k) { GLOSSARY_NORM[normYeh(k)] = GLOSSARY[k]; });

function findDifficultWords(poem) {
  var found = [], seen = {};
  tokenize(poem).forEach(function (token) {
    var word = normYeh(stripPunct(token));
    if (GLOSSARY_NORM[word] && !seen[word]) {
      seen[word] = true;
      found.push({ word: word, meaning_ur: GLOSSARY_NORM[word][0], meaning_en: GLOSSARY_NORM[word][1], note: GLOSSARY_NORM[word][2] });
    }
  });
  return found;
}

function detect(poem, keywords, labels, language) {
  var hits = [];
  var poemN = normYeh(poem);
  Object.keys(keywords).forEach(function (key) {
    if (keywords[key].some(function (kw) { return poemN.indexOf(normYeh(kw)) !== -1; })) {
      hits.push(labels[key][language]);
    }
  });
  return hits;
}

function analyzeDemoLocal(poem, language) {
  if (!poem || !poem.trim()) throw new Error("Poem is empty");
  if (["ps", "ur", "en"].indexOf(language) === -1) throw new Error("Unsupported language: " + language);
  poem = poem.trim();
  var lines = poem.split("\n").filter(function (ln) { return ln.trim(); });
  var words = tokenize(poem);
  var difficult = findDifficultWords(poem);
  var base = {
    mode: "demo", poem: poem, language: language,
    stats: { lines: lines.length, words: words.length, difficult_words_found: difficult.length },
    demo_note: DEMO_NOTE[language]
  };
  if (isSample(poem)) {
    var s = SAMPLE_ANALYSIS[language];
    return Object.assign(base, {
      meaning: s.meaning, translation_urdu: s.translation_urdu,
      translation_english: s.translation_english, difficult_words: difficult,
      emotions: s.emotions, themes: s.themes, message: s.message,
      summary: s.summary, poet: SAMPLE_POET
    });
  }
  var summaryTpl = {
    ps: "یو شعر چې " + lines.length + " کرښې او " + words.length + " ټکي لري. په لغت کې " + difficult.length + " سخت ټکي وموندل شول.",
    ur: "ایک شعر جس میں " + lines.length + " مصرعے اور " + words.length + " الفاظ ہیں۔ لغت میں " + difficult.length + " مشکل الفاظ ملے۔",
    en: "A poem of " + lines.length + " lines and " + words.length + " words. " + difficult.length + " difficult words were found in the glossary."
  };
  return Object.assign(base, {
    meaning: GENERIC_MEANING[language],
    translation_urdu: NO_TRANSLATION_UR,
    translation_english: NO_TRANSLATION_EN,
    difficult_words: difficult,
    emotions: detect(poem, EMOTION_KEYWORDS, EMOTION_SIGNALS, language),
    themes: detect(poem, THEME_KEYWORDS, THEME_SIGNALS, language),
    message: GENERIC_MESSAGE[language],
    summary: summaryTpl[language],
    poet: null
  });
}

function formatResultText(result) {
  var h = HEADINGS[result.language] || HEADINGS.en;
  var out = ["Da Qalam AI — Pashto Poetry Assistant", "", result.poem, ""];
  if (result.poet) out.push("Poet: " + result.poet, "");
  out.push(h.meaning + ":", result.meaning, "");
  out.push(h.translation_urdu + ":", result.translation_urdu, "");
  out.push(h.translation_english + ":", result.translation_english, "");
  out.push(h.difficult_words + ":");
  if (result.difficult_words.length === 0) {
    out.push("—");
  } else {
    result.difficult_words.forEach(function (w) {
      out.push("- " + w.word + " — " + w.meaning_ur + " / " + w.meaning_en);
    });
  }
  out.push("", h.emotions + ": " + (result.emotions.join(", ") || "—"));
  out.push(h.themes + ": " + (result.themes.join(", ") || "—"));
  out.push("", h.message + ":", result.message, "");
  out.push(h.summary + ":", result.summary);
  if (result.mode === "demo") out.push("", result.demo_note);
  return out.join("\n");
}

/* ------------------------------------------------------------ DOM wiring */
var state = { language: "ps", lastPoem: "", lastResult: null };

function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function setBadge(mode) {
  var badge = document.getElementById("mode-badge");
  if (!badge) return;
  if (mode === "live") {
    badge.textContent = "● Live AI (Qwen)";
    badge.className = "mode-badge mode-live";
  } else {
    badge.textContent = "● Demo mode — sample explanations";
    badge.className = "mode-badge mode-demo";
  }
}

function card(icon, title, innerHtml, extraClass) {
  return '<article class="result-card' + (extraClass ? " " + extraClass : "") + '">' +
    '<h3><span class="card-icon" aria-hidden="true">' + icon + '</span>' + esc(title) + '</h3>' +
    innerHtml + '</article>';
}

function renderResult(result) {
  var h = HEADINGS[result.language] || HEADINGS.en;
  var grid = document.getElementById("results-grid");
  var html = "";
  html += '<div class="stats-row">' +
    '<span class="stat"><strong>' + result.stats.lines + '</strong> lines</span>' +
    '<span class="stat"><strong>' + result.stats.words + '</strong> words</span>' +
    '<span class="stat"><strong>' + result.stats.difficult_words_found + '</strong> difficult words</span>' +
    '</div>';
  if (result.poet) {
    html += '<p class="poet-line">Poet: <strong>' + esc(result.poet) + '</strong></p>';
  }
  html += card("❝", h.meaning, '<p>' + esc(result.meaning) + '</p>', "wide");
  html += card("⇄", h.translation_urdu, '<p class="urdu-text" lang="ur" dir="rtl">' + esc(result.translation_urdu) + '</p>');
  html += card("⇄", h.translation_english, '<p class="en-text">' + esc(result.translation_english) + '</p>');
  var wordsHtml;
  if (result.difficult_words.length === 0) {
    wordsHtml = "<p>No difficult words from the glossary were found in this poem.</p>";
  } else {
    wordsHtml = '<div class="table-wrap"><table class="word-table"><thead><tr><th>Word</th><th>Urdu</th><th>English</th><th>Note</th></tr></thead><tbody>' +
      result.difficult_words.map(function (w) {
        return "<tr><td>" + esc(w.word) + "</td><td>" + esc(w.meaning_ur) + "</td><td>" + esc(w.meaning_en) + "</td><td>" + esc(w.note) + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }
  html += card("✎", h.difficult_words, wordsHtml, "wide");
  html += card("♥", h.emotions, '<div class="tag-row">' +
    (result.emotions.length ? result.emotions.map(function (e) { return '<span class="tag">' + esc(e) + '</span>'; }).join("") : "<p>—</p>") + '</div>');
  html += card("✦", h.themes, '<div class="tag-row">' +
    (result.themes.length ? result.themes.map(function (t) { return '<span class="tag cool">' + esc(t) + '</span>'; }).join("") : "<p>—</p>") + '</div>');
  html += card("✉", h.message, '<p>' + esc(result.message) + '</p>', "wide");
  html += card("≡", h.summary, '<p>' + esc(result.summary) + '</p>', "wide");
  grid.innerHTML = html;

  document.getElementById("results-title").textContent =
    result.language === "ps" ? "تحلیل" : result.language === "ur" ? "تجزیہ" : "Analysis";
  document.getElementById("results-sub").textContent =
    result.mode === "live" ? "Answered by live AI (Qwen)." : "Demo analysis — sample explanations, not live AI.";
  var note = document.getElementById("demo-note");
  if (result.mode === "demo") {
    note.textContent = result.demo_note || DEMO_NOTE[result.language] || DEMO_NOTE.en;
    note.hidden = false;
  } else {
    note.hidden = true;
  }
  document.getElementById("empty-state").hidden = true;
  document.getElementById("loading").hidden = true;
  document.getElementById("results").hidden = false;
  setBadge(result.mode);
}

function showLoading(show) {
  document.getElementById("loading").hidden = !show;
  if (show) {
    document.getElementById("empty-state").hidden = true;
    document.getElementById("results").hidden = true;
  }
}

function analyzeCurrent() {
  var textarea = document.getElementById("poem-input");
  var poem = textarea.value.trim();
  var analyzeBtn = document.getElementById("analyze-btn");
  if (!poem) {
    textarea.focus();
    textarea.style.borderColor = "#e02424";
    setTimeout(function () { textarea.style.borderColor = ""; }, 1600);
    return;
  }
  state.lastPoem = poem;
  showLoading(true);
  analyzeBtn.disabled = true;
  var controller = null, timedOut = false;
  try { controller = new AbortController(); } catch (e) { controller = null; }
  var timer = null;
  if (controller) timer = setTimeout(function () { timedOut = true; controller.abort(); }, 10000);
  var done = function (result) {
    if (timer) clearTimeout(timer);
    analyzeBtn.disabled = false;
    state.lastResult = result;
    renderResult(result);
    document.getElementById("results").scrollIntoView({ behavior: "smooth", block: "start" });
  };
  fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ poem: poem, language: state.language }),
    signal: controller ? controller.signal : undefined
  })
    .then(function (resp) { if (!resp.ok) throw new Error("HTTP " + resp.status); return resp.json(); })
    .then(function (result) { done(result); })
    .catch(function () {
      /* Server absent or failed: honest local demo fallback. */
      try { done(analyzeDemoLocal(poem, state.language)); }
      catch (e) {
        showLoading(false);
        analyzeBtn.disabled = false;
        document.getElementById("empty-state").hidden = false;
      }
    });
}

function copyResults() {
  var btn = document.getElementById("copy-btn");
  if (!state.lastResult) return;
  var text = formatResultText(state.lastResult);
  var done = function () {
    var old = btn.textContent;
    btn.textContent = "✓ Copied";
    setTimeout(function () { btn.textContent = old; }, 1800);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
  } else {
    fallbackCopy(text); done();
  }
}

function fallbackCopy(text) {
  var ta = document.createElement("textarea");
  ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
  document.body.appendChild(ta); ta.select();
  try { document.execCommand("copy"); } catch (e) { /* ignore */ }
  document.body.removeChild(ta);
}

function clearAll() {
  var textarea = document.getElementById("poem-input");
  textarea.value = "";
  state.lastPoem = "";
  state.lastResult = null;
  updateCounter();
  document.getElementById("results").hidden = true;
  document.getElementById("loading").hidden = true;
  document.getElementById("empty-state").hidden = false;
  textarea.focus();
}

function updateCounter() {
  var n = document.getElementById("poem-input").value.length;
  document.getElementById("char-count").textContent = n + " characters";
}

function setLanguage(lang) {
  state.language = lang;
  document.querySelectorAll(".lang-btn").forEach(function (b) {
    b.classList.toggle("is-active", b.getAttribute("data-lang") === lang);
  });
  if (state.lastPoem && state.lastResult) analyzeCurrent();
}

function init() {
  var textarea = document.getElementById("poem-input");
  textarea.addEventListener("input", updateCounter);
  document.getElementById("analyze-btn").addEventListener("click", analyzeCurrent);
  document.getElementById("clear-btn").addEventListener("click", clearAll);
  document.getElementById("copy-btn").addEventListener("click", copyResults);
  document.querySelectorAll(".lang-btn").forEach(function (b) {
    b.addEventListener("click", function () { setLanguage(b.getAttribute("data-lang")); });
  });
  var fillSample = function () {
    textarea.value = SAMPLE_POEM;
    updateCounter();
    analyzeCurrent();
  };
  document.getElementById("sample-btn").addEventListener("click", fillSample);
  document.querySelectorAll('[data-action="sample"]').forEach(function (b) {
    b.addEventListener("click", fillSample);
  });
  updateCounter();
  /* Ask the server which mode it is in; stay on demo if unreachable. */
  fetch("/api/status")
    .then(function (resp) { return resp.json(); })
    .then(function (s) { setBadge(s.mode === "live" ? "live" : "demo"); })
    .catch(function () { setBadge("demo"); });
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", init);
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    SAMPLE_POEM: SAMPLE_POEM, SAMPLE_POET: SAMPLE_POET, GLOSSARY: GLOSSARY,
    analyzeDemoLocal: analyzeDemoLocal, formatResultText: formatResultText,
    findDifficultWords: findDifficultWords, isSample: isSample
  };
}
