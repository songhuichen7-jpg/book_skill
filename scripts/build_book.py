#!/usr/bin/env python3
"""从 toc.json 拼装整本 book.typ：封面 → 目录 → 每章(扉页 + 章头 + 正文)。

把选定风格的 template.typ 复制进项目（让各章 `#import "../template.typ"` 生效），
再生成 book.typ。各章正文文件须已存在于 <project>/chapters/NN.typ。

toc.json 需含 chapters[]，每章字段：num, part, title, dividerColor(hex)，
以及 bookTitle / subtitle（顶层）。

用法：
    python3 build_book.py --project /path/to/bookproj --style anthropic
    typst compile <project>/book.typ <project>/book.pdf
"""
import argparse
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def q(s):  # Typst 字符串（双引号，转义兼容 JSON）
    return json.dumps(s, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--style", default="anthropic")
    ap.add_argument("--series", default="")
    a = ap.parse_args()

    # 1) 把风格模板装进项目根
    style_tpl = os.path.join(HERE, "..", "styles", a.style, "template.typ")
    shutil.copyfile(style_tpl, os.path.join(a.project, "template.typ"))

    toc = json.load(open(os.path.join(a.project, "toc.json"), encoding="utf-8"))
    L = ['#import "template.typ": *', ""]
    L.append(f'#show: book.with(title: {q(toc["bookTitle"])})')
    L += ["", "// ===== 封面 ====="]
    L.append(f'#cover(title: {q(toc["bookTitle"])}, subtitle: {q(toc.get("subtitle", ""))}, '
             f'series: {q(a.series)})')
    L += ["", "// ===== 目录 =====", "#toc-page()", ""]

    missing = []
    for c in toc["chapters"]:
        nn = f"{c['num']:02d}"
        chap = f"chapters/{nn}.typ"
        img = f"assets/ch{nn}-head.png"
        if not os.path.exists(os.path.join(a.project, chap)):
            missing.append(chap)
        img_arg = q(img) if os.path.exists(os.path.join(a.project, img)) else "none"
        L.append(f"// ===== 第 {c['num']} 章 · {c.get('part', '')} =====")
        L.append(f'#chapter-divider(num: {q(str(c["num"]))}, title: {q(c["title"])}, '
                 f'accent: rgb({q(c["dividerColor"])}), img: {img_arg})')
        L.append(f'#content-header(num: {q(str(c["num"]))}, title: {q(c["title"])})')
        L.append(f"#include {q(chap)}")
        L.append("")

    open(os.path.join(a.project, "book.typ"), "w", encoding="utf-8").write("\n".join(L))
    print(f"book.typ 生成完毕：{len(toc['chapters'])} 章，风格 {a.style}")
    print("缺正文文件：", missing if missing else "无（全部就位）")


if __name__ == "__main__":
    main()
