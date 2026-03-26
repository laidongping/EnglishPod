from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
import re

INPUT_DIR   = Path("output")
OUTPUT_HTML = Path("output") / "index.xhtml"
OUTPUT_CSS  = Path("output") / "index.css"

PREFIX_TO_LEVEL = {
    "B": "Elementary",
    "C": "Intermediate",
    "D": "Upper-Intermediate",
    "E": "Advanced",
    "F": "Advanced Media",
}
LEVEL_ORDER    = ["Elementary", "Intermediate", "Upper-Intermediate", "Advanced", "Advanced Media"]
CATEGORY_ORDER = ["Daily Life", "The Weekend", "The Office", "Global View", "Other"]


def parse_level(code):
    return PREFIX_TO_LEVEL.get(code[0].upper(), "Other") if code else "Other"


def strip_category_prefix(title, cat):
    prefix = cat + " - "
    if title.startswith(prefix):
        return title[len(prefix):]
    return title


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
        h1  = page.find("h1")
        raw = h1.get_text(strip=True) if h1 else src.stem
        m   = re.match(r"^([A-Fa-f]\d+)\s+(.*)", raw)
        code  = m.group(1).upper() if m else ""
        title = m.group(2).strip()  if m else raw
        ct    = page.select_one(".tag-category")
        cat   = ct.get_text(strip=True) if ct else "Other"
        title = strip_category_prefix(title, cat)
        results.append({
            "file"  : src.name,
            "anchor": code.lower() if code else re.sub(r"\W+", "-", title.lower()),
            "code"  : code,
            "title" : title,
            "level" : parse_level(code),
            "category": cat,
        })
    return results


def r(s, **kw):
    for k, v in kw.items():
        s = s.replace("<<" + k + ">>", str(v))
    return s


def build_entry(e):
    return r(
        '<li><a class="idx-entry-link" href="<<href>>">'
        '<span class="idx-code"><<code>></span>'
        '<span class="idx-entry-title"><<title>></span>'
        '</a></li>',
        href  = e["file"] + "#" + e["anchor"],
        code  = e["code"],
        title = e["title"],
    )


def build_subgroup(name, entries):
    items = "".join(build_entry(e) for e in sorted(entries, key=lambda x: x["code"]))
    return r(
        '<details class="idx-subgroup">'
        '<summary class="idx-subgroup-title">'
        '<<name>> <span class="idx-subcount"><<cnt>></span>'
        '<span class="idx-chevron"></span>'
        '</summary>'
        '<ul class="idx-list"><<items>></ul>'
        '</details>',
        name=name, cnt=len(entries), items=items,
    )


def build_panel(group_val, entries, sub_key, sub_order):
    """一个二级芯片对应的面板，内含三级子分组"""
    sub_grouped = defaultdict(list)
    for e in entries:
        sub_grouped[e[sub_key]].append(e)

    subgroups = "".join(
        build_subgroup(name, sub_grouped[name])
        for name in sub_order if name in sub_grouped
    )
    safe_id = re.sub(r"\W+", "-", group_val.lower())
    return r(
        '<div class="idx-panel" id="panel-<<id>>" style="display:none">'
        '<<subgroups>>'
        '</div>',
        id=safe_id, subgroups=subgroups,
    )


def build_view(view_id, all_entries, group_key, group_order, sub_key, sub_order):
    grouped = defaultdict(list)
    for e in all_entries:
        grouped[e[group_key]].append(e)

    chips_html  = ""
    panels_html = ""
    first = True
    for val in group_order:
        if val not in grouped:
            continue
        safe_id   = re.sub(r"\W+", "-", val.lower())
        active_cls = " active" if first else ""
        chips_html += r(
            '<button class="idx-chip<<active>>" '
            'data-panel="panel-<<id>>" '
            'onclick="selectChip(this,\'<<vid>>\')">'
            '<<val>> <span class="chip-count"><<cnt>></span>'
            '</button>',
            active=active_cls, id=safe_id,
            vid=view_id, val=val, cnt=len(grouped[val]),
        )
        display = "block" if first else "none"
        panels_html += r(
            '<div class="idx-panel" id="panel-<<id>>" style="display:<<disp>>">'
            '<<subgroups>>'
            '</div>',
            id=safe_id, disp=display,
            subgroups="".join(
                build_subgroup(name, [e for e in grouped[val] if e[sub_key] == name])
                for name in sub_order
                if any(e[sub_key] == name for e in grouped[val])
            ),
        )
        first = False

    controls = (
        '<span class="idx-reset"    onclick="resetView(\'<<vid>>\')" >&#215; Reset</span>'
        '<span class="idx-toggle-all" onclick="toggleAll(\'<<vid>>\')" >Expand All</span>'
    ).replace("<<vid>>", view_id)

    return r(
        '<div id="<<vid>>" class="idx-view" style="display:none">'
        '<div class="idx-chip-row" id="<<vid>>-chips"><<chips>></div>'
        '<div class="idx-controls"><<controls>></div>'
        '<div class="idx-panels" id="<<vid>>-panels"><<panels>></div>'
        '</div>',
        vid=view_id, chips=chips_html,
        controls=controls, panels=panels_html,
    )


JS = """
function switchView(v) {
    document.querySelectorAll('.idx-view').forEach(function(el) {
        el.style.display = 'none';
    });
    document.getElementById(v).style.display = 'block';
    document.querySelectorAll('.idx-view-btn').forEach(function(b) {
        b.classList.toggle('active', b.dataset.view === v);
    });
    updateCounter(v);
}

function selectChip(chip, viewId) {
    var row = document.getElementById(viewId + '-chips');
    row.querySelectorAll('.idx-chip').forEach(function(c) {
        c.classList.remove('active');
    });
    chip.classList.add('active');
    var panelsEl = document.getElementById(viewId + '-panels');
    panelsEl.querySelectorAll('.idx-panel').forEach(function(p) {
        p.style.display = 'none';
    });
    document.getElementById(chip.dataset.panel).style.display = 'block';
    updateCounter(viewId);
}

function resetView(viewId) {
    var row   = document.getElementById(viewId + '-chips');
    var first = row.querySelector('.idx-chip');
    if (first) selectChip(first, viewId);
}

function toggleAll(viewId) {
    var panels = document.getElementById(viewId + '-panels');
    var active = panels.querySelector('.idx-panel[style*="block"]');
    if (!active) return;
    var details = active.querySelectorAll('details');
    var anyOpen = false;
    details.forEach(function(d) { if (d.open) anyOpen = true; });
    details.forEach(function(d) { d.open = !anyOpen; });
    var btn = document.querySelector(
        '[onclick="toggleAll(\\'' + viewId + '\\')"]'
    );
    if (btn) btn.textContent = anyOpen ? 'Expand All' : 'Collapse All';
}

function updateCounter(viewId) {
    var panels = document.getElementById(viewId + '-panels');
    var active = panels ? panels.querySelector('.idx-panel[style*="block"]') : null;
    var count  = active ? active.querySelectorAll('li').length : 0;
    var total  = document.getElementById('idx-total').textContent;
    document.getElementById('idx-visible').textContent = count;
}

switchView('idx-by-level');
"""


INDEX_CSS = """\
/* ── Index page ─────────────────────────────────────────── */
.idx-header { text-align: center; margin-bottom: 1.2em; }
.idx-header h1 {
    border: none; text-align: center;
    letter-spacing: 0.12em; margin-bottom: 0.2em;
}
.idx-counter { font-size: 0.9em; color: #999; }

/* ── Level 1: view toggle ── */
.idx-toolbar {
    display: flex; gap: 0.6em;
    justify-content: center; margin-bottom: 1.6em;
}
.idx-view-btn {
    font-family: inherit; font-size: 0.9em; font-weight: bold;
    padding: 0.38em 1.2em; border: 2px solid #333;
    background: transparent; color: #333; cursor: pointer;
    letter-spacing: 0.06em; text-transform: uppercase;
    border-radius: 2px; transition: background 0.15s, color 0.15s;
}
.idx-view-btn.active {
    background: #1a3a6a; border-color: #1a3a6a; color: #fff;
}

/* ── Level 2: group chips (single-select) ── */
.idx-chip-row {
    display: flex; flex-wrap: wrap; gap: 0.5em; margin-bottom: 0.8em;
}
.idx-chip {
    display: inline-flex; align-items: center; gap: 0.3em;
    padding: 0.28em 0.85em; border: 1.5px solid #bbb;
    border-radius: 999px; font-size: 0.85em; cursor: pointer;
    background: transparent; color: #666; font-family: inherit;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
    user-select: none;
}
.idx-chip.active {
    background: #b8b8e0; border-color: #7070c0; color: #1a1a5a;
}
.chip-count { font-size: 0.82em; color: #999; }
.idx-chip.active .chip-count { color: #444; }

/* ── Controls row ── */
.idx-controls {
    display: flex; gap: 0.5em;
    margin-bottom: 1.2em; align-items: center;
}
.idx-reset, .idx-toggle-all {
    display: inline-flex; align-items: center; gap: 0.3em;
    padding: 0.25em 0.8em; border: 1.5px solid #ccc;
    border-radius: 999px; font-size: 0.82em; cursor: pointer;
    background: transparent; color: #888; font-family: inherit;
    user-select: none; transition: color 0.15s, border-color 0.15s;
}
.idx-reset:hover, .idx-toggle-all:hover {
    color: #333; border-color: #888;
}

/* ── Level 3: subgroups ── */
.idx-subgroup { border-bottom: 1px solid #ddd; }
.idx-subgroup-title {
    display: flex; align-items: center; list-style: none;
    cursor: pointer; padding: 0.5em 0.8em;
    font-weight: bold; text-transform: uppercase;
    letter-spacing: 0.06em; font-size: 10pt;
    background: #f0f0ee; user-select: none;
}
.idx-subgroup-title::-webkit-details-marker { display: none; }
.idx-subgroup-title::marker { content: none; }
.idx-subgroup[open] .idx-subgroup-title { background: #e4e2dc; }
.idx-subcount {
    font-weight: normal; font-size: 0.82em; color: #aaa;
    margin-left: 0.4em;
}
.idx-chevron { margin-left: auto; }
.idx-chevron::after { content: "+"; color: #aaa; font-weight: normal; }
.idx-subgroup[open] .idx-chevron::after { content: "\\2212"; }

/* ── Entries: two-column grid ── */
.idx-list {
    list-style: none; margin: 0; padding: 0.2em 0;
    display: grid; grid-template-columns: 1fr 1fr;
}
.idx-list li {
    display: flex; align-items: baseline; gap: 0.5em;
    padding: 0.38em 0.8em; border-bottom: 1px solid #f0f0f0;
    min-width: 0;
}
.idx-list li:nth-child(4n+1),
.idx-list li:nth-child(4n+2) { background: #fff; }
.idx-list li:nth-child(4n+3),
.idx-list li:nth-child(4n+4) { background: #f9f8f6; }
.idx-list li:hover { background: #eef2f8; }

.idx-entry-link {
    display: inline-flex; align-items: baseline; gap: 0.5em;
    text-decoration: none; min-width: 0; flex: 1;
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

@media screen and (max-width: 540px) {
    .idx-list { grid-template-columns: 1fr; }
}
"""


def main():
    files = sorted(INPUT_DIR.glob("*.html"))
    if not files:
        print("output 文件夹中没有找到 html 文件")
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

    by_level    = build_view("idx-by-level",    all_entries,
                             "level",    LEVEL_ORDER,
                             "category", CATEGORY_ORDER)
    by_category = build_view("idx-by-category", all_entries,
                             "category", CATEGORY_ORDER,
                             "level",    LEVEL_ORDER)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE html>',
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">',
        '<head>',
        '  <meta charset="UTF-8"/>',
        '  <title>EnglishPod Index</title>',
        '  <link rel="stylesheet" href="styles.css"/>',
        '  <link rel="stylesheet" href="index.css"/>',
        '</head>',
        '<body><div class="script-page">',
        '<div class="idx-header">',
        '  <h1>Index</h1>',
        '  <div class="idx-counter">',
        '    <span id="idx-visible">' + str(total) + '</span>',
        '    / <span id="idx-total">' + str(total) + '</span> episodes',
        '  </div>',
        '</div>',
        '<div class="idx-toolbar">',
        '  <button class="idx-view-btn active" data-view="idx-by-level"'
        '    onclick="switchView(\'idx-by-level\')">By Level</button>',
        '  <button class="idx-view-btn" data-view="idx-by-category"'
        '    onclick="switchView(\'idx-by-category\')">By Category</button>',
        '</div>',
        by_level,
        by_category,
        '<script>//<![CDATA[',
        JS,
        '//]]></script>',
        '</div></body></html>',
    ]

    OUTPUT_HTML.write_text("\n".join(lines), encoding="utf-8")
    print("\n完成，共 " + str(total) + " 条 → " + str(OUTPUT_HTML.resolve()))

    OUTPUT_CSS.write_text(INDEX_CSS, encoding="utf-8")
    print("CSS → " + str(OUTPUT_CSS.resolve()))


if __name__ == "__main__":
    main()
