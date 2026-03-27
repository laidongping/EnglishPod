import os
from pathlib import Path
from bs4 import BeautifulSoup

# ── 配置 ──────────────────────────────────────────────────
INPUT_DIR  = Path("input")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

LONG_SPK_THRESHOLD = 3
# ──────────────────────────────────────────────────────────


def is_long(name: str) -> bool:
    return len(name.strip()) > LONG_SPK_THRESHOLD


def wrap_pages(soup: BeautifulSoup) -> None:
    """
    把每组 h1 + tags + dialogue-block + vocab 包进 div.script-page
    """
    body = soup.find("body")
    if not body:
        return

    children = list(body.children)
    groups = []
    current = []

    for node in children:
        if isinstance(node, str):
            current.append(node)
            continue
        if node.name == "h1":
            if current:
                groups.append(current)
            current = [node]
        else:
            current.append(node)
    if current:
        groups.append(current)

    body.clear()

    for group in groups:
        # 跳过全是空白文本的组
        real = [n for n in group if not (isinstance(n, str) and not n.strip())]
        if not real:
            continue
        page = soup.new_tag("div", attrs={"class": "script-page"})
        for node in group:
            page.append(node)
        body.append(page)


def convert_dialogue(soup: BeautifulSoup) -> None:
    for block in soup.select("div.dialogue-block"):
        lines = block.select("div.line")
        if not lines:
            continue

        has_long = any(
            is_long(line.select_one(".speaker").get_text())
            for line in lines
            if line.select_one(".speaker")
        )

        dl_class = "dialogue-block long" if has_long else "dialogue-block"
        dl = soup.new_tag("dl", attrs={"class": dl_class})

        for line in lines:
            spk_el  = line.select_one(".speaker")
            text_el = line.select_one(".text")
            if not spk_el or not text_el:
                continue

            dt = soup.new_tag("dt")
            dt.string = spk_el.get_text(strip=True)

            dd = soup.new_tag("dd")
            for child in list(text_el.children):
                dd.append(child)

            dl.append(dt)
            dl.append(dd)

        block.replace_with(dl)


def convert_vocab(soup: BeautifulSoup) -> None:
    for block in soup.select("div.vocab-block"):
        items = block.select("div.vocab-item")
        if not items:
            continue

        table = soup.new_tag("table", attrs={"class": "vocab-block"})

        colgroup = soup.new_tag("colgroup")
        for cls in ("col-word", "col-type", "col-def"):
            col = soup.new_tag("col", attrs={"class": cls})
            colgroup.append(col)
        table.append(colgroup)

        tbody = soup.new_tag("tbody")

        for item in items:
            word_el = item.select_one(".word")
            type_el = item.select_one(".type")
            def_el  = item.select_one(".definition")

            tr = soup.new_tag("tr")

            th = soup.new_tag("th")
            th.string = word_el.get_text(strip=True) if word_el else ""

            td_type = soup.new_tag("td", attrs={"class": "type"})
            td_type.string = type_el.get_text(strip=True) if type_el else ""

            td_def = soup.new_tag("td", attrs={"class": "definition"})
            if def_el:
                for child in list(def_el.children):
                    td_def.append(child)

            tr.append(th)
            tr.append(td_type)
            tr.append(td_def)
            tbody.append(tr)

        table.append(tbody)
        block.replace_with(table)


def update_head(soup: BeautifulSoup) -> None:
    for tag in soup.find_all("style"):
        tag.decompose()

    head = soup.find("head")
    if not head:
        return

    existing = head.find("link", rel="stylesheet")
    if existing:
        existing["href"] = "styles.css"
    else:
        link = soup.new_tag("link", rel="stylesheet", href="styles.css")
        head.append(link)


def process_file(src: Path, dst: Path) -> None:
    html = src.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    convert_dialogue(soup)
    convert_vocab(soup)
    wrap_pages(soup)
    update_head(soup)

    dst.write_text(str(soup), encoding="utf-8")
    print(f"OK  {src.name}")


def main():
    files = sorted(INPUT_DIR.glob("*.html"))
    if not files:
        print("input 文件夹中没有找到 html 文件")
        return
    for src in files:
        dst = OUTPUT_DIR / src.name
        try:
            process_file(src, dst)
        except Exception as e:
            print(f"ERR {src.name}: {e}")
    print(f"\n完成，共处理 {len(files)} 个文件，输出至 {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
