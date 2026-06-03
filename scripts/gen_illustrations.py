#!/usr/bin/env python3
"""逐章生成扉页插画：图像模型生图 → 只取本次新增产物 → 色键抠透明。

依赖：本机 codex CLI 具备生图能力（`codex exec` 会把图存到
~/.codex/generated_images/<session>/ig_*.png）；numpy + Pillow。

输入：<project>/illustration-specs.json，形如
    [{"num":0,"hex":"#609A81","colorName":"鼠尾草绿","concept":"……画面意象……"}, ...]
（由 TOC 阶段从 toc.json 抽取：num / dividerColor / colorName / illustrationConcept。）

风格前缀取自 skill 的 styles/<style>/illustration-prompt.md 第一个代码块。

产物：<project>/assets/chNN-head.png（透明，落到 Typst 同色扉页上无缝融入）。

铁律（踩过坑）：
  * **只取本次新增图**（生成前后快照取差集），绝不用 glob「取最新」——某张失败时
    「取最新」会抓到上一张/别项目的旧图，静默把扉页覆盖成同一张错图（曾把整本书的
    10 张扉页覆盖成一张无关图）。没新增 = 本次没出图 → 重试，仍失败就**保留旧图不动**。
  * **暴露 codex 报错**：codex 启动失败（如 config.toml 的 service_tier 不被当前 CLI 版本
    接受、未登录）会让每次生图静默零产出；把 returncode/stderr 打出来，便于一眼看根因。

用法：
    python3 gen_illustrations.py --project /path/to/bookproj --style anthropic
    python3 gen_illustrations.py --project <proj> --only 3,7   # 只重做这几章
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


def list_pngs():
    return set(glob.glob(os.path.expanduser("~/.codex/generated_images/*/*.png")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True, help="含 illustration-specs.json 与 assets/ 的项目目录")
    ap.add_argument("--style", default="anthropic")
    ap.add_argument("--only", default="", help="逗号分隔的 num，只重做这几章")
    a = ap.parse_args()
    only = {x.strip() for x in a.only.split(",") if x.strip()}

    prefix = load_style_prefix(a.style)
    specs = json.load(open(os.path.join(a.project, "illustration-specs.json"), encoding="utf-8"))
    assets = os.path.join(a.project, "assets")
    os.makedirs(assets, exist_ok=True)

    from PIL import Image
    failed = []
    for s in specs:
        n = s["num"]
        if only and str(n) not in only:
            continue
        prompt = (
            f"{prefix}\n背景必须是纯色 {s['hex']}（{s.get('colorName', '')}）填满整张画布。\n"
            f"画面内容：{s['concept']}"
        )
        ok = False
        for attempt in range(1, 4):   # 偶发卡死/不出图 → 自动重试至多 3 次
            print(f"[ch{n:02d}] generating (try {attempt}/3) ...", flush=True)
            before = list_pngs()      # 生成前快照
            try:
                proc = subprocess.run(
                    ["codex", "exec", "--skip-git-repo-check", prompt],
                    cwd="/tmp", capture_output=True, text=True, timeout=600)
            except Exception as e:
                print(f"[ch{n:02d}] codex error/timeout (try {attempt}): {e}", flush=True)
                continue
            if proc.returncode != 0:
                # 暴露 codex 自己的报错（如 config.toml service_tier 不被接受、未登录）
                err = (proc.stderr or proc.stdout or "").strip().splitlines()
                hint = err[0] if err else "(no stderr)"
                print(f"[ch{n:02d}] codex 退出码 {proc.returncode}：{hint}", flush=True)
                continue
            new = list_pngs() - before   # 只认本次新增；没新增=本次没出图
            if not new:
                print(f"[ch{n:02d}] NO NEW IMAGE (try {attempt})", flush=True)
                continue
            src = max(new, key=os.path.getmtime)
            raw = os.path.join(assets, f"ch{n:02d}-head-raw.png")
            Image.open(src).convert("RGB").save(raw)
            bg = chroma_key(raw, os.path.join(assets, f"ch{n:02d}-head.png"))
            print(f"[ch{n:02d}] done -> assets/ch{n:02d}-head.png (keyed bg {bg})", flush=True)
            ok = True
            break
        if not ok:
            failed.append(n)
            print(f"[ch{n:02d}] FAILED after 3 tries — 保留旧图不动，勿当成功", flush=True)

    if failed:
        nums = ",".join(str(x) for x in failed)
        print(f"!! 有章节没生成成功：{nums}。先排查 codex（`codex exec` 能否出图、"
              f"config.toml/登录是否正常），修好后用 --only {nums} 重跑。", flush=True)
    else:
        print("ALL ILLUSTRATIONS DONE", flush=True)


if __name__ == "__main__":
    main()
