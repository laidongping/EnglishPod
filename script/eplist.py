import os, re

# 假设你的单篇 HTML 文件在 episodes/ 目录下
ep_dir = "episodes"
entries = []

for fname in sorted(os.listdir(ep_dir)):
    if not fname.endswith(".html"):
        continue
    path = os.path.join(ep_dir, fname)
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # 从 <title> 或 <h1> 提取标题
    m = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
    title = m.group(1).strip() if m else fname.replace(".html", "")
    # 从文件名提取 ID，如 englishpod_0001.html → B0001 / C0001
    num = re.search(r"(\d{4})", fname)
    ep_id = title.split()[0] if title else fname  # 用标题第一个词作 ID
    entries.append(f'  {{ id: "{ep_id}", title: "{title}" }}')

print("const episodes = [\n" + ",\n".join(entries) + "\n];")
