#!/usr/bin/env python3
"""色键抠图：把插画的纯色背景抠成透明。

为什么需要：codex / 多数生图模型产出的 PNG 常带颜色描述文件(P3 等)，直接贴到
Typst 纯色页上会整块偏色、露出矩形贴图边界。把背景抠透明后，插画落在 Typst
同色页上就无缝融入，且绕开色差问题。

用法：
    python3 chroma_key.py <输入.png> <输出.png> [--t1 60] [--t2 112]
或作为模块：
    from chroma_key import chroma_key
    bg_hex = chroma_key("raw.png", "cut.png")
"""
import argparse
import statistics
import numpy as np
from PIL import Image


def chroma_key(src, dst, t1=60, t2=112):
    """按与四角背景色的欧氏距离设 alpha：<t1 全透明、t1~t2 羽化、>t2 不透明。
    返回采样到的背景色 hex（便于把 Typst 页面底色对齐）。"""
    im = Image.open(src).convert("RGB")
    arr = np.asarray(im).astype(np.float32)
    h, w, _ = arr.shape
    corners = [arr[2, 2], arr[2, w - 3], arr[h - 3, 2], arr[h - 3, w - 3]]
    bg = np.array([statistics.median(c[i] for c in corners) for i in range(3)])
    dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))
    alpha = np.clip((dist - t1) / (t2 - t1), 0, 1) * 255
    rgba = np.dstack([arr, alpha]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(dst)
    return "#%02X%02X%02X" % tuple(int(x) for x in bg)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--t1", type=int, default=60)
    ap.add_argument("--t2", type=int, default=112)
    a = ap.parse_args()
    print("keyed bg", chroma_key(a.src, a.dst, a.t1, a.t2))
