import re
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup

INPUT_DIR = Path("input")
OUTPUT_HTML = Path("output") / "index.xhtml"
OUTPUT_CSS = Path("output") / "index.css"

PREFIX_TO_LEVEL = {
    "B": "Elementary",
    "C": "Intermediate",
    "D": "Upper-Intermediate",
    "E": "Advanced",
    "F": "Advanced Media",
}

LEVEL_LABEL = {
    "Elementary": "B·Elementary",
    "Intermediate": "C·Intermediate",
    "Upper-Intermediate": "D·Upper-Intermediate",
    "Advanced": "E·Advanced",
    "Advanced Media": "F·Advanced Media",
}

LEVEL_COLOR = {
    "Elementary": ("lv-b", "#fff0f0", "#c0392b"),
    "Intermediate": ("lv-c", "#ffe0e0", "#a93226"),
    "Upper-Intermediate": ("lv-d", "#ffc8c8", "#922b21"),
    "Advanced": ("lv-e", "#ffaaaa", "#7b241c"),
    "Advanced Media": ("lv-f", "#ff8888", "#641e16"),
}

CATEGORY_COLOR = {
    "Daily Life": ("cat-dl", "#e0f7fa", "#006064"),
    "The Weekend": ("cat-tw", "#f9fbe7", "#558b2f"),
    "The Office": ("cat-to", "#fff8e1", "#f57f17"),
    "Global View": ("cat-gv", "#e8eaf6", "#3a3a8a"),
    "Other": ("cat-ot", "#f5f5f5", "#555555"),
}

LEVEL_ORDER = [
    "Elementary",
    "Intermediate",
    "Upper-Intermediate",
    "Advanced",
    "Advanced Media",
]
CATEGORY_ORDER = ["Daily Life", "The Weekend", "The Office", "Global View", "Other"]


def parse_level(code):
    return PREFIX_TO_LEVEL.get(code[0].upper(), "Other") if code else "Other"


def strip_category_prefix(title, cat):
    prefix = cat + " - "
    return title[len(prefix) :] if title.startswith(prefix) else title


def extract_meta(src):
    soup = BeautifulSoup(src.read_text(encoding="utf-8"), "html.parser")
    results = []
    pages = soup.select("div.script-page")
    if not pages:
        b = soup.find("body")
        pages = [b] if b else []
    for page in pages:
        if not page:
            continue
        h1 = page.find("h1")
        raw = h1.get_text(strip=True) if h1 else src.stem
        m = re.match(r"^([A-Fa-f]\d+)\s+(.*)", raw)
        code = m.group(1).upper() if m else ""
        title = m.group(2).strip() if m else raw
        ct = page.select_one(".tag-category")
        cat = ct.get_text(strip=True) if ct else "Other"
        title = strip_category_prefix(title, cat)
        results.append(
            {
                "file": src.name,
                "anchor": code.lower() if code else re.sub(r"\W+", "-", title.lower()),
                "code": code,
                "title": title,
                "level": parse_level(code),
                "category": cat,
            }
        )
    return results


def r(s, **kw):
    for k, v in kw.items():
        s = s.replace("<<" + k + ">>", str(v))
    return s


def chip_style(bg, fg):
    return 'style="background:' + bg + ";border-color:" + fg + ";color:" + fg + '"'


def build_level_chips(counts):
    parts = []
    for lv in LEVEL_ORDER:
        if lv not in counts:
            continue
        cls, bg, fg = LEVEL_COLOR.get(lv, ("", "#eee", "#333"))
        label = LEVEL_LABEL.get(lv, lv)
        parts.append(
            r(
                '<button class="idx-chip <<cls>>" data-dim="level" data-val="<<val>>" <<sty>> onclick="toggleChip(this)">'
                '<<label>> <span class="chip-count"><<cnt>></span>'
                "</button>",
                cls=cls,
                val=lv,
                cnt=counts[lv],
                sty=chip_style(bg, fg),
                label=label,
            )
        )
    return "".join(parts)


def build_category_chips(counts):
    parts = []
    for cat in CATEGORY_ORDER:
        if cat not in counts:
            continue
        cls, bg, fg = CATEGORY_COLOR.get(cat, ("", "#eee", "#333"))
        parts.append(
            r(
                '<button class="idx-chip <<cls>>" data-dim="category" data-val="<<val>>" <<sty>> onclick="toggleChip(this)">'
                '#<<val>> <span class="chip-count"><<cnt>></span>'
                "</button>",
                cls=cls,
                val=cat,
                cnt=counts[cat],
                sty=chip_style(bg, fg),
            )
        )
    return "".join(parts)


def inline_tag(val, dim):
    if dim == "level":
        _, bg, fg = LEVEL_COLOR.get(val, ("", "#eee", "#333"))
    else:
        _, bg, fg = CATEGORY_COLOR.get(val, ("", "#eee", "#333"))
    return (
        '<span class="entry-tag" style="background:'
        + bg
        + ";color:"
        + fg
        + '">'
        + val
        + "</span>"
    )


def build_entries(all_entries):
    parts = []
    for e in sorted(all_entries, key=lambda x: x["code"]):
        cat_tag = inline_tag(e["category"], "category")
        parts.append(
            r(
                '<li data-level="<<lv>>" data-category="<<cat>>">'
                '<a class="idx-entry-link" href="<<href>>">'
                '<span class="idx-code"><<code>></span>'
                '<span class="idx-entry-title"><<title>></span>'
                "</a>"
                '<span class="entry-tags"><<cattag>></span>'
                "</li>",
                lv=e["level"],
                cat=e["category"],
                href=e["file"] + "#" + e["anchor"],
                code=e["code"],
                title=e["title"],
                cattag=cat_tag,
            )
        )
    return "\n".join(parts)


JS = """
var allEntries = [];

function init() {
    document.querySelectorAll('#idx-list li').forEach(function(li) {
        allEntries.push(li);
    });
    updateCounter();
}

function toggleChip(chip) {
    chip.classList.toggle('active');
    applyFilters();
}

function resetAll() {
    document.querySelectorAll('.idx-chip').forEach(function(c) {
        c.classList.remove('active');
    });
    applyFilters();
}

function applyFilters() {
    var activeLevels = [];
    var activeCats   = [];
    document.querySelectorAll('.idx-chip.active').forEach(function(c) {
        if (c.dataset.dim === 'level')    activeLevels.push(c.dataset.val);
        if (c.dataset.dim === 'category') activeCats.push(c.dataset.val);
    });
    allEntries.forEach(function(li) {
        var lv    = li.dataset.level;
        var cat   = li.dataset.category;
        var lvOk  = activeLevels.length === 0 || activeLevels.indexOf(lv)  !== -1;
        var catOk = activeCats.length   === 0 || activeCats.indexOf(cat)   !== -1;
        li.hidden = !(lvOk && catOk);
    });
    updateCounter();
}

function updateCounter() {
    var vis = 0;
    allEntries.forEach(function(li) { if (!li.hidden) vis++; });
    document.getElementById('idx-visible').textContent = vis;
}

init();
"""

INDEX_CSS = """\
/* ── Index page ─────────────────────────────────────────── */
.idx-header { text-align: center; margin-bottom: 1em; }
.idx-header h1 {
    border: none; text-align: center;
    letter-spacing: 0.12em; margin-bottom: 0.15em;
}
.idx-counter { font-size: 0.88em; color: #999; }

/* ── Filter card ── */
.idx-filter-card {
    border: 1px solid #ddd; border-radius: 6px;
    padding: 0.9em 1em; margin-bottom: 1.4em;
    background: #fafafa;
}
.idx-filter-label {
    font-size: 0.82em; color: #888; margin-bottom: 0.6em;
}
.idx-dim-row {
    display: flex; flex-wrap: wrap;
    align-items: center; gap: 0.4em; margin-bottom: 0.5em;
}
.idx-dim-label {
    font-size: 0.8em; color: #aaa;
    white-space: nowrap; min-width: 4.5em;
}

/* ── Chips ── */
.idx-chip {
    display: inline-flex; align-items: center; gap: 0.25em;
    padding: 0.22em 0.75em; border: 1.5px solid #ccc;
    border-radius: 999px; font-size: 0.82em; cursor: pointer;
    background: transparent; color: #bbb; font-family: inherit;
    opacity: 0.45;
    transition: opacity 0.15s, transform 0.1s, box-shadow 0.15s;
    user-select: none;
}
.idx-chip.active {
    opacity: 1;
    transform: scale(1.05);
    box-shadow: 0 1px 5px rgba(0,0,0,0.2);
}
.chip-count { font-size: 0.8em; opacity: 0.85; }

/* ── Controls ── */
.idx-controls {
    display: flex; gap: 0.5em;
    margin-top: 0.6em; align-items: center;
}
.idx-reset {
    display: inline-flex; align-items: center; gap: 0.3em;
    padding: 0.22em 0.75em; border: 1.5px solid #ccc;
    border-radius: 999px; font-size: 0.82em; cursor: pointer;
    background: transparent; color: #aaa; font-family: inherit;
    user-select: none; transition: color 0.15s, border-color 0.15s;
}
.idx-reset:hover { color: #555; border-color: #888; }

/* ── Entry list: two-column ── */
#idx-list {
    list-style: none; margin: 0; padding: 0;
    display: grid; grid-template-columns: 1fr 1fr;
}
#idx-list li {
    display: flex; align-items: baseline; gap: 0.4em;
    padding: 0.38em 0.6em; border-bottom: 1px solid #f0f0f0;
    min-width: 0;
}
#idx-list li:nth-child(4n+1),
#idx-list li:nth-child(4n+2) { background: #fff; }
#idx-list li:nth-child(4n+3),
#idx-list li:nth-child(4n+4) { background: #f9f8f6; }
#idx-list li:hover { background: #eef2f8; }
#idx-list li[hidden] { display: none !important; }

.idx-entry-link {
    display: inline-flex; align-items: baseline; gap: 0.45em;
    text-decoration: none; flex: 1; min-width: 0;
}
.idx-code {
    font-weight: bold; color: #1a3a6a;
    white-space: nowrap; flex-shrink: 0; min-width: 5ch;
}
.idx-entry-title {
    color: #222; overflow: hidden;
    text-overflow: ellipsis; white-space: nowrap;
}
.idx-entry-link:hover .idx-entry-title {
    text-decoration: underline; color: #1a3a6a;
}
.entry-tags {
    display: inline-flex; gap: 0.3em;
    flex-shrink: 0; margin-left: auto;
}
.entry-tag {
    font-size: 0.72em; padding: 0.1em 0.45em;
    border-radius: 3px; white-space: nowrap;
}

@media screen and (max-width: 540px) {
    #idx-list { grid-template-columns: 1fr; }
    .entry-tags { display: none; }
}
"""


def main():
    files = sorted(INPUT_DIR.glob("*.html"))
    if not files:
        print("input 文件夹中没有找到 html 文件")
        return

    all_entries = []
    for src in files:
        if src.stem == "index":
            continue
        try:
            entries = extract_meta(src)
            all_entries.extend(entries)
            print("OK  " + src.name + "  (" + str(len(entries)) + " 条)")
        except Exception as ex:
            print("ERR " + src.name + ": " + str(ex))

    total = len(all_entries)

    lv_counts = defaultdict(int)
    cat_counts = defaultdict(int)
    for e in all_entries:
        lv_counts[e["level"]] += 1
        cat_counts[e["category"]] += 1

    lv_chips = build_level_chips(lv_counts)
    cat_chips = build_category_chips(cat_counts)
    entries = build_entries(all_entries)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!DOCTYPE html>",
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">',
        "<head>",
        '  <meta charset="UTF-8"/>',
        "  <title>EnglishPod Index</title>",
        '  <link rel="stylesheet" href="styles.css"/>',
        '  <link rel="stylesheet" href="index.css"/>',
        "</head>",
        '<body><div class="script-page">',
        "",
        '<div class="idx-header">',
        "  <h1>Index</h1>",
        '  <div class="idx-counter">',
        '    <span id="idx-visible">' + str(total) + "</span>",
        '    / <span id="idx-total">' + str(total) + "</span> episodes",
        "  </div>",
        "</div>",
        "",
        '<div class="idx-filter-card">',
        '  <div class="idx-filter-label">Select episodes:</div>',
        '  <div class="idx-dim-row">',
        '    <span class="idx-dim-label">Level:</span>',
        lv_chips,
        "  </div>",
        '  <div class="idx-dim-row">',
        '    <span class="idx-dim-label">Category:</span>',
        cat_chips,
        "  </div>",
        '  <div class="idx-controls">',
        '    <span class="idx-reset" onclick="resetAll()">&#215; Reset</span>',
        "  </div>",
        "</div>",
        "",
        '<ul id="idx-list">',
        entries,
        "</ul>",
        "",
        "<script>//<![CDATA[",
        JS,
        "//]]></script>",
        "",
        "</div></body></html>",
    ]

    OUTPUT_HTML.write_text("\n".join(lines), encoding="utf-8")
    print("\n完成，共 " + str(total) + " 条 → " + str(OUTPUT_HTML.resolve()))

    OUTPUT_CSS.write_text(INDEX_CSS, encoding="utf-8")
    print("CSS → " + str(OUTPUT_CSS.resolve()))


if __name__ == "__main__":
    main()
