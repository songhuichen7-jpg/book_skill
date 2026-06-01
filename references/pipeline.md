# 多 agent 生书流水线（6 阶段）

这是从零生成一整本书的实战流程，按**阶段（phase）**组织：每阶段是一个（或多个）子任务，阶段之间你读结果再决定下一步。**若你所在环境支持并行子代理（如某些 CLI 的子代理/工作流机制），就把同阶段内彼此独立的工作 fan out 并行；否则顺序逐个完成**。**token 不是约束，质量是**。

本 skill 不绑定任何一本书——下面以"目标书 / 某本书 / 一章 / 示例图"等中性说法描述。

工作目录约定（下称 `$PROJECT`，即用户的成书工作目录）：
```
$PROJECT/
├── toc.json                # 阶段1产出：全书目录（驱动后续一切）
├── illustration-specs.json # 从 toc.json 抽出的插画规格（num/hex/colorName/concept）
├── template.typ            # build_book.py 从选定风格复制进来
├── book.typ                # build_book.py 生成
├── chapters/NN.typ         # 阶段2每章产出
└── assets/chNN-head.png    # 阶段3每章插画（透明）
```

本 skill 根目录下称 `$SKILL`（即本 skill 目录）。外部依赖统一申明为命令行工具：`codex`（或任意可用的图像生成 CLI/能力，用于生图）、`typst`（排版）、`mmdc`（Mermaid 渲染）。

---

## 阶段 0 · 立项（和用户对齐，别跳过）
确认：主题与读者、深度、**风格**（默认 anthropic）、语言、是否要插画。
读 `$SKILL/styles/<style>/style.md` 把视觉与口味载入脑子。

## 阶段 1 · 广泛调研 → 最终 TOC（一个调研+合成阶段）
**先调研再定目录**，别拍脑袋。fan-out 多路并行调研（一手来源：官方文档/博客/GitHub/论文/真实资料），再由一个 synthesis 子任务汇总成结构化 TOC。

TOC schema 每章应含：`num, part, title, coreQuestion(唯一核心问题), sections[{id,title,summary}], keyConcepts[], codeExamples[], jdCompetencies[](若为教材类), dividerColor(从风格调色板循环、相邻不撞), colorName, illustrationConcept(呼应该章主题)`；顶层 `bookTitle, subtitle`。

落盘 `$PROJECT/toc.json`，并抽 `$PROJECT/illustration-specs.json`：
```python
specs=[{"num":c["num"],"hex":c["dividerColor"],"colorName":c["colorName"],
        "concept":c["illustrationConcept"]} for c in toc["chapters"]]
```
→ **把 TOC 给用户过目**（这是全书地基，值得一个确认点）。
- **坑（合成 TOC 的子任务易翻车）**：综合那一步要一次性产出很大的结构化对象，要求强 schema 时偶有子任务「把 TOC 当普通文字写了、没按结构化方式返回」导致整阶段失败。两条对策：① synthesis 的 prompt 里加硬性指令「你必须一次性返回符合 schema 的结构化对象，篇幅大就精炼每条 summary/数组条数，但务必走结构化输出通道」；② 真失败了别重跑全部——尽量只重跑失败项 + synthesis，调研结果尽量复用（缓存/续跑机制视你所在环境而定，具体编排用你所在环境的子代理机制）。

## 阶段 2 · 逐章并行写作（一个写作阶段）
每章一个子任务：读 `$PROJECT/toc.json` 拿本章规格 → 按需联网核实 → 写 `$PROJECT/chapters/NN.typ` → **自己编译自修复到零错误** → 返回结构化报告。
- 严格交给每个子任务一份「写作契约」：见 `$SKILL/references/template-api.md`。
- 自验夹具（在 `$PROJECT` 下，让相对 import 生效）：
  ```
  #import "template.typ": *
  #show: book.with(title: "t")
  #content-header(num: "N", title: "标题")
  #include "chapters/NN.typ"
  ```
  `cd $PROJECT && typst compile _tNN.typ /tmp/tNN.pdf` 须零错误。
- **坑**：要求结构化输出时，偶有子任务「干完活没按结构化方式返回」而被判失败——但文件其实写好了。完成后务必 `ls $PROJECT/chapters/` 核实，缺的（常是最后一两章）单独补一个轻量子任务（不强制 schema，让它写文件 + 回一句话即可）。

## 阶段 3 · 配图（先决策走哪条路，再生成）
**开工前先按 SKILL.md「配图决策」判一遍**：章节扉页这类技术内容 → 默认极简线条；封面/截图美化/杂志级大图/社交传播图，或用户要"精美" → 该处升级到更精美的图像生成路径。**如果**你的环境里有专门做封面/社交卡这类美化出图的 skill（例如某社交卡 skill），就用它；**否则**用本 skill 的图像生成管线自己出图。同一本书可混用：扉页走线条、封面走美化路径。

默认线条路线——用 `codex`（或任意可用的图像生成 CLI/能力）生图 + 色键抠透明的管线较专（路径/沙箱/色差），用脚本比让十几个子任务各自摸索更稳：
```bash
python3 $SKILL/scripts/gen_illustrations.py --project $PROJECT --style <style>
```
顺序跑、约 1–2 分钟/张。详见 `$SKILL/references/illustrations.md`（含何时升级到美化出图路径的判据与嵌图方式）。**可与阶段 2 并行启动**（互不依赖）。

## 阶段 4 · 拼装 + 编译
```bash
python3 $SKILL/scripts/build_book.py --project $PROJECT --style <style> --series "系列名"
typst compile $PROJECT/book.typ $PROJECT/book.pdf
```
逐页抽查：封面 / 目录 / 几张扉页（确认插画各异、配色循环、无贴图矩形）/ 带代码与表格的正文页。
（导出某页 PNG 抽查：`typst compile --pages "1,2,N" --format png --ppi 110 book.typ "p-{p}.png"`）

## 阶段 5 · 事实核查 + 统稿（两个阶段）
**核查**（按章并行）：每章一个子任务联网核实事实/数字/版本/API/模型名，校验交叉引用（对照 `$PROJECT/toc.json`），**外科手术式就地修正**（明确错的改对并记 before/after+来源；查不到的软化措辞或 flag；闭源系统内部细节须注明「据社区逆向/分析」），重编验证。
**统稿**（一个子任务）：跨章查术语一致性（grep 各概念译法）、矛盾、深度参差，汇总人工待决清单。
然后：把明确的正确性/严谨度修正再起一个「定点修复」阶段应用；术语统一 + 给零子节的长章补 `===` 锚点起一个「轻量统稿」阶段。每轮都重编。

---

## 通用编排写法要点
- 同阶段内彼此独立的工作（多路调研、逐章写作、逐章核查）应 fan out 并行；具体编排用你所在环境的子代理机制（若环境不支持并行子代理，则顺序逐个完成）。
- 每章子任务需要 Web 检索 + 运行命令（typst 编译）+ 写文件三种能力。
- 每个子任务只写自己的 `$PROJECT/chapters/NN.typ` 和自己的 `/tmp/_xNN.typ` 夹具 → 并行无冲突；共享 `template.typ` 只读。
- 给子任务的 prompt 里把「写作/修改契约」写死、强调**外科手术式、不破坏版式、改完必须编译零错误**。
- 调研/核查需要一手来源时明确要求联网检索并引用真实 URL。
