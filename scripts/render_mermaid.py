#!/usr/bin/env python3
"""把 Mermaid 定义渲染成 SVG，供嵌进 Typst 书。

每个图是 <project>/diagrams/<name>.mmd（agent 由 styles/<style>/mermaid-template.mmd
复制改写而来，文件内含 %%{init}%% 主题）。本脚本渲染到 <project>/assets/diagrams/<name>.svg，
章节里用 #diagram("<name>") 嵌入。

需要 mermaid-cli（mmdc）：优先用 skill 的 tools/node_modules/.bin/mmdc；缺了用 npx 现装。

用法：
    python3 render_mermaid.py --project <proj> [--style anthropic]   # 渲染 diagrams/ 下全部
    python3 render_mermaid.py --file a.mmd --out a.svg [--style anthropic]  # 渲染单个（agent 自验用）
"""
import argparse, glob, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)


def mmdc_base():
    local = os.path.join(SKILL, "tools", "node_modules", ".bin", "mmdc")
    return [local] if os.path.exists(local) else ["npx", "-y", "@mermaid-js/mermaid-cli"]


def render_one(infile, outfile, style):
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    pc = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump({"args": ["--no-sandbox"]}, pc); pc.close()
    # 输出 PNG（非 SVG）：Mermaid 的 SVG 用 foreignObject 放文字，Typst 渲染不出文字；
    # PNG 由 chromium 栅格化、文字完整，-s 3 高 DPI 保证印刷清晰。
    cmd = mmdc_base() + ["-i", infile, "-o", outfile, "-b", "transparent", "-s", "3", "-p", pc.name]
    css = os.path.join(SKILL, "styles", style, "mermaid.css")
    if os.path.exists(css):
        cmd += ["-C", css]
    subprocess.run(cmd, check=True)
    os.unlink(pc.name)
    print(f"  ✓ {os.path.basename(outfile)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--file")
    ap.add_argument("--out")
    ap.add_argument("--style", default="anthropic")
    a = ap.parse_args()
    if a.file:
        render_one(a.file, a.out or os.path.splitext(a.file)[0] + ".png", a.style)
        return
    if not a.project:
        sys.exit("需要 --project 或 --file")
    src = sorted(glob.glob(os.path.join(a.project, "diagrams", "*.mmd")))
    if not src:
        print("diagrams/ 下没有 .mmd，跳过"); return
    outdir = os.path.join(a.project, "assets", "diagrams")
    print(f"渲染 {len(src)} 张 Mermaid 图 → assets/diagrams/")
    for f in src:
        name = os.path.splitext(os.path.basename(f))[0]
        render_one(f, os.path.join(outdir, name + ".png"), a.style)
    print("ALL MERMAID DONE")


if __name__ == "__main__":
    main()
