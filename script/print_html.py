import os
from pathlib import Path

from bs4 import BeautifulSoup

INPUT_DIR = Path("input")  # 365 个 HTML 文件目录
OUTPUT_FILE = Path("output/print.html")

# ── 读取所有 episode 文件 ──────────────────────────────────────
episodes = []
for html_file in sorted(INPUT_DIR.glob("englishpod_*.html")):
    with open(html_file, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # 取 episode id（如 englishpod_0001）
    ep_id = html_file.stem  # "englishpod_0001"

    # 取标题（假设你的文件里有 <h1> 或 <title>）
    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ep_id

    # 取正文内容（整个 body 内部，或你指定的容器）
    body = soup.find("body") or soup
    content_html = body.decode_contents()  # 内部 HTML 字符串

    episodes.append(
        {
            "id": ep_id,
            "title": title,
            "content": content_html,
        }
    )

# ── 生成目录 ──────────────────────────────────────────────────
toc_items = "\n".join(
    f'<li><a href="#{ep["id"]}">{i + 1}. {ep["title"]}</a></li>'
    for i, ep in enumerate(episodes)
)


# ── 生成每篇 A4 页 ────────────────────────────────────────────
pages_html = "\n".join(
    f'<div class="print-page" id="{ep["id"]}">\n{ep["content"]}\n</div>'
    for ep in episodes
)

# ── 工具栏 ────────────────────────────────────────────────────
toolbar = """<div id="print-toolbar">
  <button id="btn-toc" onclick="toggleToc()">&#9776; TOC</button>
  <span class="sep"></span>
  <label>栏：</label>
  <button id="btn-col1" class="active" onclick="setCol(1)">单栏</button>
  <button id="btn-col2" onclick="setCol(2)">双栏</button>
  <span class="sep"></span>
  <label>词汇：</label>
  <button id="btn-vocab-show" class="active" onclick="setVocab(true)">显示</button>
  <button id="btn-vocab-hide" onclick="setVocab(false)">隐藏</button>
  <span class="sep"></span>
  <label>字体：</label>
  <button id="btn-font-mono" class="active" onclick="setFont('mono')">等宽</button>
  <button id="btn-font-serif" onclick="setFont('serif')">衬线</button>
  <button id="btn-font-sans" onclick="setFont('sans')">无衬线</button>
  <span class="sep"></span>
  <button class="btn-print" onclick="window.print()">&#128438; 打印 / PDF</button>
</div>"""

# ── TOC 侧边栏 ────────────────────────────────────────────────
sidebar_items = "\n".join(
    f'<li><a href="#{ep["id"]}" onclick="closeToc()">{i + 1}. {ep["title"]}</a></li>'
    for i, ep in enumerate(episodes)
)

sidebar = f"""<div id="toc-overlay" onclick="closeToc()"></div>
<nav id="toc-sidebar">
  <h2>目录</h2>
  <ol>{sidebar_items}</ol>
</nav>"""

# ── JS ────────────────────────────────────────────────────────
js = """<script>
function toggleToc() {
    var open = document.getElementById('toc-sidebar').classList.toggle('open');
    document.getElementById('toc-overlay').classList.toggle('active', open);
    document.body.classList.toggle('toc-open', open);
}
function closeToc() {
    document.getElementById('toc-sidebar').classList.remove('open');
    document.getElementById('toc-overlay').classList.remove('active');
    document.body.classList.remove('toc-open');
}
function setActive(nodes, id) {
    nodes.forEach(function(b) { b.classList.remove('active'); });
    document.getElementById(id).classList.add('active');
}
function setCol(n) {
    document.body.classList.remove('col-1','col-2');
    document.body.classList.add('col-'+n);
    setActive(document.querySelectorAll('#btn-col1,#btn-col2'), 'btn-col'+n);
}
function setVocab(show) {
    document.body.classList.toggle('hide-vocab', !show);
    setActive(
        document.querySelectorAll('#btn-vocab-show,#btn-vocab-hide'),
        show ? 'btn-vocab-show' : 'btn-vocab-hide'
    );
}
function setFont(f) {
    document.body.classList.remove('font-mono','font-serif','font-sans');
    document.body.classList.add('font-'+f);
    setActive(
        document.querySelectorAll('#btn-font-mono,#btn-font-serif,#btn-font-sans'),
        'btn-font-'+f
    );
}
</script>"""

# ── 拼装完整 HTML ─────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EnglishPod — Print Edition</title>
  <link rel="stylesheet" href="print.css">
</head>
<body class="col-1 font-mono">
{toolbar}
{sidebar}
<div id="page-container">

{pages_html}
</div>
{js}
</body>
</html>"""

OUTPUT_FILE.write_text(html, encoding="utf-8")
print(f"Done: {OUTPUT_FILE}  ({len(episodes)} episodes)")
