import datetime
import uuid
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup

# =============================================================
# 配置
# =============================================================

PROJECT_DIR = Path(__file__).parent
OEBPS_DIR = PROJECT_DIR / "OEBPS"
META_DIR = PROJECT_DIR / "META-INF"

BOOK_TITLE = "EnglishPod Complete Collection"
BOOK_AUTHOR = "EnglishPod"
BOOK_LANG = "en"
OUTPUT_FILE = PROJECT_DIR / "EnglishPod.epub"


# 自动找封面图片
def find_cover():
    images_dir = OEBPS_DIR / "images"
    if not images_dir.exists():
        return None
    for f in sorted(images_dir.iterdir()):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            return f
    return None


COVER_IMAGE = find_cover()

# =============================================================
# 工具
# =============================================================


def get_html_files():
    exclude = {
        "index.xhtml",
        "intro.xhtml",
        "nav.xhtml",
        "cover.xhtml",
        "titlepage.xhtml",
    }
    return sorted(
        [
            f
            for f in OEBPS_DIR.iterdir()
            if f.suffix in (".html", ".xhtml") and f.name not in exclude
        ]
    )


def extract_title(path):
    try:
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else path.stem
    except Exception:
        return path.stem


def mt(path):
    return {
        ".html": "application/xhtml+xml",
        ".xhtml": "application/xhtml+xml",
        ".css": "text/css",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }.get(path.suffix.lower(), "application/octet-stream")


# =============================================================
# 生成 mimetype
# =============================================================


def ensure_mimetype():
    (PROJECT_DIR / "mimetype").write_text("application/epub+zip", encoding="utf-8")


# =============================================================
# 生成 META-INF/container.xml
# =============================================================


def ensure_container():
    META_DIR.mkdir(exist_ok=True)
    (META_DIR / "container.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0"\n'
        ' xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        "  <rootfiles>\n"
        '    <rootfile full-path="OEBPS/content.opf"\n'
        '     media-type="application/oebps-package+xml"/>\n'
        "  </rootfiles>\n"
        "</container>\n",
        encoding="utf-8",
    )


# =============================================================
# 生成封面 cover.xhtml（符合 EPUB3 规范）
# =============================================================


def generate_cover():
    if not COVER_IMAGE:
        print("⚠️  未找到封面图片，跳过")
        return False

    rel = "Images/" + COVER_IMAGE.name
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE html>\n"
        '<html xmlns="http://www.w3.org/1999/xhtml"\n'
        '      xmlns:epub="http://www.idpf.org/2007/ops">\n'
        "<head>\n"
        '<meta charset="UTF-8"/>\n'
        "<title>Cover</title>\n"
        "<style>\n"
        "html, body { margin: 0; padding: 0; height: 100%; }\n"
        "img { display: block; width: 100%; height: 100%; object-fit: contain; }\n"
        "</style>\n"
        "</head>\n"
        '<body epub:type="cover">\n'
        '<img src="' + rel + '" alt="Cover"/>\n'
        "</body>\n"
        "</html>\n"
    )
    (OEBPS_DIR / "cover.xhtml").write_text(content, encoding="utf-8")
    return True


# =============================================================
# 生成 nav.xhtml
# =============================================================


def generate_nav(html_files, has_cover):
    items = []
    if has_cover:
        items.append('    <li><a href="cover.xhtml">Cover</a></li>')
    if (OEBPS_DIR / "intro.xhtml").exists():
        items.append('    <li><a href="intro.xhtml">Introduction</a></li>')
    if (OEBPS_DIR / "index.xhtml").exists():
        items.append('    <li><a href="index.xhtml">Index</a></li>')
    for f in html_files:
        title = extract_title(f)
        items.append('    <li><a href="' + f.name + '">' + title + "</a></li>")

    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE html>\n"
        '<html xmlns="http://www.w3.org/1999/xhtml"\n'
        '      xmlns:epub="http://www.idpf.org/2007/ops">\n'
        '<head><meta charset="UTF-8"/><title>Contents</title></head>\n'
        "<body>\n"
        '<nav epub:type="toc" id="toc">\n'
        "<h1>Contents</h1>\n"
        "<ol>\n" + "\n".join(items) + "\n"
        "</ol>\n"
        "</nav>\n"
        "</body>\n"
        "</html>\n"
    )
    (OEBPS_DIR / "nav.xhtml").write_text(content, encoding="utf-8")


# =============================================================
# 生成 content.opf
# =============================================================


def generate_opf(html_files, has_cover):
    book_id = str(uuid.uuid4())
    date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest = []
    spine = []

    # nav — 必须在 manifest，不进 spine
    manifest.append(
        '    <item id="nav" href="nav.xhtml"'
        ' media-type="application/xhtml+xml" properties="nav"/>'
    )

    # 封面图片 — properties="cover-image"，只注册图片，不进 spine
    if has_cover and COVER_IMAGE:
        manifest.append(
            '    <item id="cover-image" href="images/' + COVER_IMAGE.name + '"'
            ' media-type="' + mt(COVER_IMAGE) + '" properties="cover-image"/>'
        )
        # cover.xhtml 进 spine，linear="yes"，放第一位
        manifest.append(
            '    <item id="cover" href="cover.xhtml"'
            ' media-type="application/xhtml+xml"/>'
        )
        spine.append('    <itemref idref="cover" linear="yes"/>')

    # intro
    if (OEBPS_DIR / "intro.xhtml").exists():
        manifest.append(
            '    <item id="intro" href="intro.xhtml"'
            ' media-type="application/xhtml+xml"/>'
        )
        spine.append('    <itemref idref="intro"/>')

    # index — linear="no"，不进入主阅读流
    if (OEBPS_DIR / "index.xhtml").exists():
        manifest.append(
            '    <item id="index" href="index.xhtml"'
            ' media-type="application/xhtml+xml"/>'
        )
        spine.append('    <itemref idref="index" linear="no"/>')

    # 章节
    for i, f in enumerate(html_files):
        iid = "chap" + str(i).zfill(4)
        manifest.append(
            '    <item id="' + iid + '" href="' + f.name + '"'
            ' media-type="' + mt(f) + '"/>'
        )
        spine.append('    <itemref idref="' + iid + '"/>')

    # CSS
    for css in sorted(OEBPS_DIR.glob("*.css")):
        manifest.append(
            '    <item id="css-' + css.stem + '" href="' + css.name + '"'
            ' media-type="text/css"/>'
        )

    # 字体
    fonts_dir = OEBPS_DIR / "fonts"
    if fonts_dir.exists():
        for font in sorted(fonts_dir.iterdir()):
            if font.suffix.lower() in (".ttf", ".otf", ".woff", ".woff2"):
                manifest.append(
                    '    <item id="font-' + font.stem + '"'
                    ' href="fonts/' + font.name + '"'
                    ' media-type="' + mt(font) + '"/>'
                )

    # 其余图片（封面已单独处理）
    images_dir = OEBPS_DIR / "images"
    if images_dir.exists():
        for img in sorted(images_dir.iterdir()):
            if img == COVER_IMAGE:
                continue
            if img.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".svg"):
                manifest.append(
                    '    <item id="img-' + img.stem + '"'
                    ' href="images/' + img.name + '"'
                    ' media-type="' + mt(img) + '"/>'
                )

    # 删除旧的 metadata.opf
    old = OEBPS_DIR / "metadata.opf"
    if old.exists():
        old.unlink()

    opf = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package version="3.0"\n'
        '         xmlns="http://www.idpf.org/2007/opf"\n'
        '         unique-identifier="bookid">\n\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '    <dc:identifier id="bookid">urn:uuid:' + book_id + "</dc:identifier>\n"
        "    <dc:title>" + BOOK_TITLE + "</dc:title>\n"
        "    <dc:creator>" + BOOK_AUTHOR + "</dc:creator>\n"
        "    <dc:language>" + BOOK_LANG + "</dc:language>\n"
        '    <meta property="dcterms:modified">'
        + date
        + "</meta>\n"
        + (
            '    <meta name="cover" content="cover-image"/>\n'
            if has_cover and COVER_IMAGE
            else ""
        )
        + "  </metadata>\n\n"
        "  <manifest>\n" + "\n".join(manifest) + "\n"
        "  </manifest>\n\n"
        "  <spine>\n" + "\n".join(spine) + "\n"
        "  </spine>\n\n"
        "</package>\n"
    )

    (OEBPS_DIR / "content.opf").write_text(opf, encoding="utf-8")


# =============================================================
# 打包 EPUB
# =============================================================


def pack_epub():
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    with zipfile.ZipFile(OUTPUT_FILE, "w") as epub:
        # mimetype 第一个，不压缩
        epub.write(
            PROJECT_DIR / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED
        )
        # META-INF
        for f in sorted(META_DIR.rglob("*")):
            if f.is_file():
                epub.write(
                    f, f.relative_to(PROJECT_DIR), compress_type=zipfile.ZIP_DEFLATED
                )
        # OEBPS
        for f in sorted(OEBPS_DIR.rglob("*")):
            if f.is_file():
                epub.write(
                    f, f.relative_to(PROJECT_DIR), compress_type=zipfile.ZIP_DEFLATED
                )

    size = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print("✅ EPUB 生成完成: " + str(OUTPUT_FILE))
    print("   大小: " + f"{size:.1f} MB")


# =============================================================
# 主流程
# =============================================================


def main():
    print("\n📦 EnglishPod EPUB3 Builder\n")

    ensure_mimetype()
    ensure_container()

    html_files = get_html_files()
    print("  章节数: " + str(len(html_files)))

    has_cover = generate_cover()
    print("  封面: " + ("✅" if has_cover else "⚠️  无封面"))

    generate_nav(html_files, has_cover)
    generate_opf(html_files, has_cover)
    pack_epub()

    print("\n🎉 完成\n")


if __name__ == "__main__":
    main()
