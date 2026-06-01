#!/usr/bin/env python3
"""逐章生成扉页插画：codex 生图 → 取最新产物 → 色键抠透明。

依赖：本机 codex CLI 具备生图能力（`codex exec` 会把图存到
~/.codex/generated_images/<session>/ig_*.png）；numpy + Pillow。

输入：<project>/illustration-specs.json，形如
    [{"num":0,"hex":"#609A81","colorName":"鼠尾草绿","concept":"……画面意象……"}, ...]
（由 TOC 阶段从 toc.json 抽取：num / dividerColor / colorName / illustrationConcept。）

风格前缀取自 skill 的 styles/<style>/illustration-prompt.md 第一个代码块。

产物：<project>/assets/chNN-head.png（透明，落到 Typst 同色扉页上无缝融入）。

用法：
    python3 gen_illustrations.py --project /path/to/bookproj --style anthropic
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from chroma_key import chroma_key  # noqa: E402


def load_style_prefix(style):
    md = os.path.join(HERE, "..", "styles", style, "illustration-prompt.md")
    text = open(md, encoding="utf-8").read()
    m = re.search(r"```(?:\w+)?\n(.*?)```", text, re.S)
    if not m:
        sys.exit(f"未在 {md} 找到风格前缀代码块")
    return m.group(1).strip()


def newest_png():
    pngs = glob.glob(os.path.expanduser("~/.codex/generated_images/*/*.png"))
    return max(pngs, key=os.path.getmtime) if pngs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="含 illustration-specs.json 与 assets/ 的项目目录")
    ap.add_argument("--style", default="anthropic")
    a = ap.parse_args()

    prefix = load_style_prefix(a.style)
    specs = json.load(open(os.path.join(a.project, "illustration-specs.json"), encoding="utf-8"))
    assets = os.path.join(a.project, "assets")
    os.makedirs(assets, exist_ok=True)

    for s in specs:
        n = s["num"]
        prompt = (
            f"{prefix}\n背景必须是纯色 {s['hex']}（{s.get('colorName', '')}）填满整张画布。\n"
            f"画面内容：{s['concept']}"
        )
        print(f"[ch{n:02d}] generating ...", flush=True)
        try:
            subprocess.run(["codex", "exec", "--skip-git-repo-check", prompt],
                           cwd="/tmp", capture_output=True, text=True, timeout=600)
        except Exception as e:
            print(f"[ch{n:02d}] codex error: {e}", flush=True)
            continue
        src = newest_png()
        if not src:
            print(f"[ch{n:02d}] NO IMAGE FOUND", flush=True)
            continue
        from PIL import Image
        raw = os.path.join(assets, f"ch{n:02d}-head-raw.png")
        Image.open(src).convert("RGB").save(raw)
        bg = chroma_key(raw, os.path.join(assets, f"ch{n:02d}-head.png"))
        print(f"[ch{n:02d}] done -> assets/ch{n:02d}-head.png (keyed bg {bg})", flush=True)

    print("ALL ILLUSTRATIONS DONE", flush=True)


if __name__ == "__main__":
    main()
