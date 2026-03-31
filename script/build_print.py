# build_print.py  v2
import pathlib
import re
import sys

from bs4 import BeautifulSoup

CATEGORY_DISPLAY = {
    "TheWeekend": "The Weekend",
    "DailyLife": "Daily Life",
    "TheOffice": "The Office",
    "GlobalView": "Global View",
    "Other": "Other",
}


def get_meta(soup, name):
    tag = soup.find("meta", attrs={"name": name})
    return tag["content"].strip() if tag else ""


def get_title_text(soup):
    h1 = soup.find("h1")
    if not h1:
        return ""
    code_span = h1.find("span", class_="tag-code")
    cat_span = h1.find("span", class_="tag-category")
    code = code_span.get_text().strip() if code_span else ""
    cat = cat_span.get_text().strip() if cat_span else ""
    for s in h1.find_all("span"):
        s.decompose()
    name = re.sub(r"\s+", " ", h1.get_text(" ")).strip().strip("-").strip()
    if cat and name.startswith(cat):
        name = name[len(cat) :].strip().lstrip("-").strip()
    return f"{code} {name}" if code else name


def get_dialogue(soup):
    dl = soup.find("dl")
    return str(dl) if dl else ""


def build_lesson_article(soup):
    code = get_meta(soup, "ep-code")
    level = get_meta(soup, "ep-level")
    category = get_meta(soup, "ep-category")
    title = get_title_text(soup)
    dialogue = get_dialogue(soup)
    cat_disp = CATEGORY_DISPLAY.get(category, category)
    if not dialogue:
        return "", None
    name_only = title.replace(code, "").strip().lstrip("-").strip()
    art = (
        f'<article class="lesson" data-code="{code}" '
        f'data-level="{level}" data-category="{category}" id="{code}">\n'
        f'  <h2 class="lesson-heading">'
        f'<span class="lh-code">{code}</span>'
        f'<span class="lh-name">{name_only}</span>'
        f'<span class="lh-badges">'
        f'<span class="lbadge lbadge-level" data-level="{level}">{level}</span>'
        f'<span class="lbadge lbadge-cat" data-cat="{category}">{cat_disp}</span>'
        f"</span></h2>\n"
        f"  {dialogue}\n"
        f"</article>\n"
    )
    toc = (
        f'<li class="toc-item" data-level="{level}" data-category="{category}">'
        f'<a href="#{code}"><span class="toc-code">{code}</span>'
        f'<span class="toc-name">{name_only}</span></a></li>'
    )
    return art, toc


def main():
    if len(sys.argv) < 3:
        print("用法: python build_print.py <output_dir> <print.html>")
        sys.exit(1)
    src_dir = pathlib.Path(sys.argv[1])
    out_file = pathlib.Path(sys.argv[2])
    files = sorted(src_dir.glob("*.html"))
    articles, toc_items = [], []
    for f in files:
        if f.name in ("index.html", "print.html"):
            continue
        soup = BeautifulSoup(f.read_text(encoding="utf-8"), "html.parser")
        art, toc = build_lesson_article(soup)
        if art:
            articles.append(art)
            toc_items.append(toc)
    print(f"共处理 {len(articles)} 篇")
    tmpl = TEMPLATE.replace("%%TOC%%", "\n".join(toc_items))
    tmpl = tmpl.replace("%%ARTICLES%%", "\n".join(articles))
    tmpl = tmpl.replace("%%TOTAL%%", str(len(articles)))
    out_file.write_text(tmpl, encoding="utf-8")
    print(f"已写入 {out_file}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Print — All Lessons</title>
<style>
/* ── Reset ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

/* ── Variables ── */
:root{
  --font-mono:  "Courier Prime","Courier New",monospace;
  --font-serif: "Georgia","Times New Roman",serif;
  --font-sans:  "Helvetica Neue",Arial,sans-serif;
  --body-font:  var(--font-mono);
  --fs:         9.5pt;
  --lh:         1.5;
  --col-gap:    1.2em;
  --page-w:     210mm;
  --page-pad:   12mm;
  --ctrl-h:     40px;
  --a4-h:       297mm;
}

html{ font-size:var(--fs); }
body{
  font-family: var(--body-font);
  line-height: var(--lh);
  background: #888;
  color: #111;
  margin: 0;
}
body.font-mono  { --body-font: var(--font-mono);  }
body.font-serif { --body-font: var(--font-serif); }
body.font-sans  { --body-font: var(--font-sans);  }

/* ── Control Bar ── */
#ctrl{
  position:fixed; top:0; left:0; right:0;
  height:var(--ctrl-h);
  background:#1a1a1a; color:#eee;
  display:flex; align-items:center;
  gap:0.4rem; padding:0 0.75rem;
  z-index:1000; overflow-x:auto;
  font-family:var(--font-sans); font-size:11px;
}
#ctrl button,#ctrl select{
  font-family:var(--font-sans); font-size:10.5px;
  padding:0.2em 0.55em;
  border:1px solid #444; background:#2a2a2a; color:#ddd;
  border-radius:2px; cursor:pointer; white-space:nowrap;
}
#ctrl button:hover,#ctrl select:hover{ background:#3a3a3a; }
#ctrl button.active{ background:#1768b4; border-color:#1768b4; color:#fff; }
#ctrl select{ padding:0.15em 0.3em; max-width:160px; }

.ctrl-sep{ width:1px; height:20px; background:#444; flex-shrink:0; margin:0 0.15rem; }
.ctrl-label{ font-size:9.5px; color:#888; letter-spacing:0.08em; text-transform:uppercase; white-space:nowrap; }

#fz-display{
  font-size:10px; color:#aaa; min-width:2.8em;
  text-align:center; white-space:nowrap;
}
#btn-print{
  margin-left:auto;   /* 贴最右 */
  background:#1768b4 !important;
  border-color:#1768b4 !important;
  color:#fff !important;
}

/* ── Layout ── */
#layout{ display:flex; margin-top:var(--ctrl-h); }

/* ── TOC ── */
#toc{
  width:190px; min-width:190px;
  height:calc(100vh - var(--ctrl-h));
  position:sticky; top:var(--ctrl-h);
  overflow-y:auto; background:#222; color:#ccc;
  padding:0.5rem 0;
  font-family:var(--font-sans); font-size:10px;
  transition:width 0.2s,min-width 0.2s;
}
#toc.collapsed{ width:0; min-width:0; overflow:hidden; padding:0; }
.toc-item{ border-bottom:1px solid #2a2a2a; }
.toc-item.hidden{ display:none; }
.toc-item a{
  display:flex; gap:0.35rem; padding:0.3rem 0.65rem;
  color:#bbb; text-decoration:none; line-height:1.3;
}
.toc-item a:hover{ background:#2e2e2e; color:#fff; }
.toc-code{ color:#555; flex-shrink:0; }
.toc-name{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

/* ── Main ── */
#main{ flex:1; padding:1.2rem var(--page-pad); min-width:0; }

/* ── A4 page wrap ── */
.page-wrap{
  max-width:var(--page-w);
  margin:0 auto;
  background:#fff;
  box-shadow:0 2px 16px rgba(0,0,0,0.25);
  padding:var(--page-pad);
  position:relative;       /* for page-rule pseudo positioning */
}
.page-wrap.cols-2{ columns:2; column-gap:var(--col-gap); }
.page-wrap.cols-1{ columns:1; }

/* ── A4 page-break rules (每297mm一条线) ── */
/* 用 repeating-linear-gradient 在背景上画水平线 */
.page-wrap{
  background-image: repeating-linear-gradient(
    to bottom,
    transparent 0,
    transparent calc(var(--a4-h) - 1px),
    #c0c8d8 calc(var(--a4-h) - 1px),
    #c0c8d8 var(--a4-h)
  );
  background-attachment: local;
}

/* ── Lesson ── */
.lesson{
  break-inside: avoid-column;   /* 整篇不跨栏 */
  margin-bottom: 0.7em;
}
.lesson.hidden{ display:none; }

/* ── Lesson heading ── */
.lesson-heading{
  font-size: 1em;              /* 与正文一致或略大，由 em 继承 */
  font-weight: 800;
  line-height: 1.3;
  margin-bottom: 0.2em;
  column-span: none;           /* 绝不横跨两栏 */
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.3em;
  border-bottom: 1px solid #111;  /* 标题下边框不减弱 */
  padding-bottom: 0.1em;
}
.lh-code{
  font-size: 0.8em;
  font-weight: 700;
  color: #888;
  letter-spacing: 0.06em;
  font-family: var(--font-mono);
  flex-shrink: 0;
}
.lh-name{ flex:1; min-width:0; }
.lh-badges{ display:flex; gap:0.2em; flex-shrink:0; }

.lbadge{
  font-size:0.6em; font-weight:700;
  padding:0.05em 0.35em; border-radius:2px;
  white-space:nowrap; font-family:var(--font-sans);
}
.lbadge-level[data-level="Elementary"]         {background:#dbeeff;color:#1a5fa8;}
.lbadge-level[data-level="Intermediate"]       {background:#d4edda;color:#1a6e38;}
.lbadge-level[data-level="Upper-Intermediate"] {background:#fff3cd;color:#856404;}
.lbadge-level[data-level="Advanced"]           {background:#fde0d0;color:#a03010;}
.lbadge-level[data-level="Advanced Media"]     {background:#e8d5f5;color:#5a1a8a;}
.lbadge-cat[data-cat="TheWeekend"] {background:#fde8f0;color:#9c1a50;}
.lbadge-cat[data-cat="DailyLife"]  {background:#e0f4f4;color:#1a6e6e;}
.lbadge-cat[data-cat="TheOffice"]  {background:#fff0d8;color:#8a4a00;}
.lbadge-cat[data-cat="GlobalView"] {background:#e8edf8;color:#1a3a8a;}
.lbadge-cat[data-cat="Other"]      {background:#f0f0ee;color:#888;}

/* ── Dialogue ── */

/* 短说话人（≤3字母）：双列网格 */
dl.dialogue-block{
  display:grid;
  grid-template-columns: 2.2em 1fr;
  gap:0;
  font-size:0.92em;
  line-height:var(--lh);
}

/* 长说话人：堆叠 */
dl.dialogue-block.long{
  display:block;
}

/* 短说话人 dt */
dl.dialogue-block:not(.long) dt{
  font-weight:700;
  text-align:right;
  padding-right:0.1em;
  align-self:start;
  padding-top:0.02em;
  white-space:nowrap;
  color:#111;
}
/* 冒号灰色 */
dl.dialogue-block:not(.long) dt::after{
  content:":";
  color:#bbb;
  font-weight:400;
}

/* 长说话人 dt */
dl.dialogue-block.long dt{
  font-weight:700;
  color:#111;
  margin-top:0.3em;
  margin-bottom:0.05em;
}
dl.dialogue-block.long dt::after{
  content:":";
  color:#bbb;
  font-weight:400;
}

/* dd 通用 */
dl.dialogue-block dt,
dl.dialogue-block dd{
  font-size:1em;   /* 说话人与对话字号一致 */
}

dl.dialogue-block dd{
  margin-bottom:0.15em;
  word-break:break-all;
  overflow-wrap:anywhere;
  hyphens:auto;
  -webkit-hyphens:auto;
  text-align:justify;
  text-justify:inter-word;
}
dl.dialogue-block.long dd{
  margin-bottom:0.3em;
  padding-left:0.5em;
}

/* 旁白（无说话人，dd 包含 i）*/
dl.dialogue-block dd i{
  font-style:italic;
  color:#777;
}

/* ── Print ── */
@media print{
  #ctrl,#toc{ display:none !important; }
  #layout{ margin-top:0; }
  #main{ padding:0; }
  body{ background:white; }
  .page-wrap{
    box-shadow:none; max-width:100%;
    padding:10mm 12mm;
    /* 打印时去掉背景线，用真实分页 */
    background-image:none;
  }
  .lesson.hidden{ display:none !important; }
}
</style>
</head>
<body class="font-mono">

<!-- ── Control Bar ── -->
<div id="ctrl">

  <button id="btn-toc" class="active">☰ TOC</button>
  <div class="ctrl-sep"></div>

  <span class="ctrl-label">Cols</span>
  <button id="btn-col1">▌</button>
  <button id="btn-col2" class="active">▌▌</button>
  <div class="ctrl-sep"></div>

  <span class="ctrl-label">Font</span>
  <button class="btn-font active" data-font="font-mono">Mono</button>
  <button class="btn-font" data-font="font-serif">Serif</button>
  <button class="btn-font" data-font="font-sans">Sans</button>
  <div class="ctrl-sep"></div>

  <button id="btn-fz-down">A−</button>
  <span id="fz-display">9.5pt</span>
  <button id="btn-fz-up">A+</button>
  <div class="ctrl-sep"></div>

  <!-- 筛选下拉 -->
  <span class="ctrl-label">Level</span>
  <select id="sel-level">
    <option value="all">All Levels</option>
    <option value="Elementary">Elementary</option>
    <option value="Intermediate">Intermediate</option>
    <option value="Upper-Intermediate">Upper-Int.</option>
    <option value="Advanced">Advanced</option>
    <option value="Advanced Media">Adv. Media</option>
  </select>

  <span class="ctrl-label">Cat</span>
  <select id="sel-cat">
    <option value="all">All Categories</option>
    <option value="TheWeekend">The Weekend</option>
    <option value="DailyLife">Daily Life</option>
    <option value="TheOffice">The Office</option>
    <option value="GlobalView">Global View</option>
    <option value="Other">Other</option>
  </select>

  <span id="count-display" style="font-size:10px;color:#aaa;white-space:nowrap">
    — / %%TOTAL%%
  </span>

  <button id="btn-print">⎙ Print</button>
</div>

<!-- ── Layout ── -->
<div id="layout">
  <nav id="toc"><ul style="list-style:none">%%TOC%%</ul></nav>
  <div id="main">
    <div class="page-wrap cols-2" id="pageWrap">
      %%ARTICLES%%
    </div>
  </div>
</div>

<script>
(function(){
  var activeLevel = "all", activeCategory = "all";
  var fontSize = 9.5;
  var body     = document.body;
  var pageWrap = document.getElementById("pageWrap");
  var toc      = document.getElementById("toc");
  var countEl  = document.getElementById("count-display");
  var fzEl     = document.getElementById("fz-display");
  var total    = parseInt("%%TOTAL%%", 10);
  var lessons  = document.getElementsByClassName("lesson");
  var tocItems = document.getElementsByClassName("toc-item");

  function applyFilter(){
    var v = 0;
    for(var i=0;i<lessons.length;i++){
      var el=lessons[i];
      var ok=(activeLevel==="all"||el.getAttribute("data-level")===activeLevel)&&
             (activeCategory==="all"||el.getAttribute("data-category")===activeCategory);
      el.classList.toggle("hidden",!ok);
      if(ok) v++;
    }
    for(var j=0;j<tocItems.length;j++){
      var ti=tocItems[j];
      var tok=(activeLevel==="all"||ti.getAttribute("data-level")===activeLevel)&&
              (activeCategory==="all"||ti.getAttribute("data-category")===activeCategory);
      ti.classList.toggle("hidden",!tok);
    }
    if(countEl) countEl.textContent = v+" / "+total;
  }

  document.getElementById("sel-level").addEventListener("change",function(){
    activeLevel=this.value; applyFilter();
  });
  document.getElementById("sel-cat").addEventListener("change",function(){
    activeCategory=this.value; applyFilter();
  });

  document.getElementById("btn-toc").addEventListener("click",function(){
    toc.classList.toggle("collapsed");
    this.classList.toggle("active");
  });

  document.getElementById("btn-col1").addEventListener("click",function(){
    pageWrap.className="page-wrap cols-1";
    this.classList.add("active");
    document.getElementById("btn-col2").classList.remove("active");
  });
  document.getElementById("btn-col2").addEventListener("click",function(){
    pageWrap.className="page-wrap cols-2";
    this.classList.add("active");
    document.getElementById("btn-col1").classList.remove("active");
  });

  var fontBtns=document.querySelectorAll(".btn-font");
  for(var i=0;i<fontBtns.length;i++){
    (function(btn){
      btn.addEventListener("click",function(){
        for(var k=0;k<fontBtns.length;k++) fontBtns[k].classList.remove("active");
        btn.classList.add("active");
        body.className=body.className.replace(/font-\S+/g,"").trim();
        body.classList.add(btn.getAttribute("data-font"));
      });
    })(fontBtns[i]);
  }

  function setFz(v){
    fontSize=Math.round(v*10)/10;
    document.documentElement.style.fontSize=fontSize+"pt";
    if(fzEl) fzEl.textContent=fontSize+"pt";
  }
  document.getElementById("btn-fz-down").addEventListener("click",function(){
    if(fontSize>6) setFz(fontSize-0.5);
  });
  document.getElementById("btn-fz-up").addEventListener("click",function(){
    if(fontSize<16) setFz(fontSize+0.5);
  });

  document.getElementById("btn-print").addEventListener("click",function(){
    window.print();
  });

  applyFilter();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
