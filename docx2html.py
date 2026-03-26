import re
import sys

from bs4 import BeautifulSoup, NavigableString

CSS_BLANK = """
  .blank {
    display: inline-block;
    min-width: calc(var(--chars) * 0.55em);
    border-bottom: 1.5px solid #000;
    vertical-align: bottom;
    margin: 0 1px;
  }
"""


def make_blank_tag(soup, chars):
    """创建一个 blank span 标签"""
    tag = soup.new_tag("span")
    tag["class"] = "blank"
    tag["style"] = f"--chars:{chars}"
    return tag


def replace_blanks_in_node(node, soup):
    """递归处理文本节点，将连续下划线替换为 span"""
    if isinstance(node, NavigableString):
        text = str(node)
        if "_" not in text:
            return

        # 按连续下划线分割
        parts = re.split(r"(_+)", text)
        if len(parts) <= 1:
            return

        new_nodes = []
        for part in parts:
            if re.fullmatch(r"_+", part):
                new_nodes.append(make_blank_tag(soup, len(part)))
            elif part:
                new_nodes.append(NavigableString(part))

        # 替换原文本节点
        parent = node.parent
        idx = list(parent.children).index(node)
        node.extract()
        for i, new_node in enumerate(new_nodes):
            parent.insert(idx + i, new_node)

    elif hasattr(node, "children"):
        # 先收集子节点，避免遍历时修改
        for child in list(node.children):
            replace_blanks_in_node(child, soup)


def process_html(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    # 注入 CSS（如果还没有 .blank 样式）
    style_tag = soup.find("style")
    if style_tag and ".blank" not in style_tag.string:
        style_tag.string += CSS_BLANK
    elif not style_tag:
        head = soup.find("head")
        if head:
            new_style = soup.new_tag("style")
            new_style.string = CSS_BLANK
            head.append(new_style)

    # 只处理 dd 标签内的文本（对话内容区域）
    for dd in soup.find_all("dd"):
        replace_blanks_in_node(dd, soup)

    return str(soup)


def main():
    if len(sys.argv) < 2:
        print("请将 .html 文件拖拽到本脚本上运行。")
        input("按 Enter 退出...")
        return

    for path in sys.argv[1:]:
        if not path.lower().endswith(".html"):
            print(f"跳过非 .html 文件: {path}")
            continue
        print(f"处理中: {path}")
        try:
            result = process_html(path)
            out = path.replace(".html", "_blanks.html")
            with open(out, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"已生成: {out}")
        except Exception as e:
            print(f"失败: {e}")

    input("\n全部完成，按 Enter 退出...")


if __name__ == "__main__":
    main()
