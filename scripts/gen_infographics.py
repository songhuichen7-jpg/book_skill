#!/usr/bin/env python3
"""逐张生成 codex 插画信息图（手账涂鸦风等），替换 diagrams 的 PNG。

读 <project>/diagrams/<name>.prompt.txt（每个 = 一张图的完整 codex 生图 prompt，
含风格前缀 + 内容 + 精确中文标注），顺序调 codex 生成，取最新产物存到
<project>/assets/diagrams/<name>.png（同名覆盖 → 章节里的 #diagram("name") 不用改）。

顺序执行（不并行）——并行会抢 ~/.codex/generated_images 里的最新产物，串错图。

用法：
    python3 gen_infographics.py --project <proj>            # 生成全部 *.prompt.txt
    python3 gen_infographics.py --project <proj> --only 03-x,07-y   # 只重做这几张
"""
import argparse, glob, os, subprocess
import numpy as np
from PIL import Image


def list_pngs():
    return set(glob.glob(os.path.expanduser("~/.codex/generated_images/*/*.png")))


def whiten(path):
    """把近白/低饱和的背景与纸纹强制成纯白 #FFFFFF——生图模型常给 ~#FAFAFA 的
    近白底，挨着 Typst 纯白页会显出一块灰。墨线(暗)与彩色(高饱和)不受影响。"""
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    mn, mx = a.min(2), a.max(2)
    bg = (mn >= 236) & ((mx - mn) <= 16)
    a[bg] = [255, 255, 255]
    Image.fromarray(a.astype("uint8")).save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--only", default="", help="逗号分隔的 name，只重做这些")
    a = ap.parse_args()
    only = {x for x in a.only.split(",") if x}
    files = sorted(glob.glob(os.path.join(a.project, "diagrams", "*.prompt.txt")))
    out = os.path.join(a.project, "assets", "diagrams")
    os.makedirs(out, exist_ok=True)
    for f in files:
        name = os.path.basename(f)[:-len(".prompt.txt")]
        if only and name not in only:
            continue
        prompt = open(f, encoding="utf-8").read().strip()
        ok = False
        for attempt in range(1, 4):   # 复杂 prompt 偶发卡死/不出图 → 自动重试至多 3 次
            print(f"[{name}] generating (try {attempt}/3) ...", flush=True)
            before = list_pngs()      # 生成前快照
            try:
                proc = subprocess.run(["codex", "exec", "--skip-git-repo-check", prompt],
                                      cwd="/tmp", capture_output=True, text=True, timeout=720)
            except Exception as e:
                print(f"[{name}] codex error/timeout (try {attempt}): {e}", flush=True)
                continue
            if proc.returncode != 0:
                # 暴露 codex 自己的报错（如 config.toml 的 service_tier 不被当前 CLI 接受、未登录）
                err = (proc.stderr or proc.stdout or "").strip().splitlines()
                print(f"[{name}] codex 退出码 {proc.returncode}：{err[0] if err else '(no stderr)'}", flush=True)
                continue
            new = list_pngs() - before  # 只认这次新增的图；没新增=本次未产出，重试
            if not new:
                print(f"[{name}] NO NEW IMAGE (try {attempt})", flush=True)
                continue
            src = max(new, key=os.path.getmtime)
            dst = os.path.join(out, name + ".png")
            Image.open(src).convert("RGB").save(dst)
            whiten(dst)               # 背景强制纯白，消除近白/纸纹的灰块
            print(f"[{name}] -> assets/diagrams/{name}.png", flush=True)
            ok = True
            break
        if not ok:
            print(f"[{name}] FAILED after 3 tries — 保留旧图待手动重跑", flush=True)
    print("ALL INFOGRAPHICS DONE", flush=True)


if __name__ == "__main__":
    main()
