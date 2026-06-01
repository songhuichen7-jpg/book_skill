# 扉页插画管线（生图 → 色键抠透明 → 落到同色扉页）

## 为什么这么做

- **生图**：用一个可用的图像生成 CLI/能力（例如 `codex` 或任意能生图的命令行工具）。以 `codex` 为例，`codex exec "<prompt>"` 会把图存到其生成目录（如 `~/.codex/generated_images/<session-uuid>/ig_*.png`）。不需要额外图像 API key。换成别的生图工具时，逻辑相同——只是产物落地目录和取图方式要按该工具调整。
- **抠透明**：生成的 PNG 常带颜色描述文件(P3 等)，直接贴到 Typst 纯色页上会整块偏色、露出**矩形贴图边界**。把插画背景色键抠成透明后，只剩白形状+黑线，落在 Typst 同色扉页上**无缝融入**，且物理上不可能有矩形（没有背景了）。
- **每章一张、各不相同但呼应主题**——风格语言不变（白形状+黑线+圆点+手绘），换的是构图/形状/颜色。

## 一键脚本

```bash
python3 $SKILL/scripts/gen_illustrations.py --project $PROJECT --style <style>
```
它对 `$PROJECT/illustration-specs.json` 里每章：拼 `风格前缀 + 背景纯色<hex> + 画面<concept>` → 调用生图 CLI（默认 `codex exec`）→ 取最新产物 → `chroma_key` 抠透明 → 存 `$PROJECT/assets/chNN-head.png`。顺序跑，约 1–2 分钟/张；若你的环境支持后台/并行执行，可把各章插画 fan out 并行，否则顺序逐个完成，完成会通知。

> `illustration-specs.json` 由 TOC 阶段抽出：`[{"num","hex","colorName","concept"}, ...]`。
> 风格前缀来自 `$SKILL/styles/<style>/illustration-prompt.md` 的第一个代码块。

## 实操坑（踩过的）

1. **目录信任**：非 git 目录跑 `codex` 要加 `--skip-git-repo-check`（脚本已带）。换其他生图工具时，照该工具对非 git 目录的要求处理。
2. **沙箱只读**：生图工具自身沙箱常无法写到 /tmp 或项目目录；以 `codex` 为例，它只会把图落在自己的生成目录（如 `~/.codex/generated_images/`），由脚本从那里取最新的复制出来（顺序跑保证「最新 png」就是本次产物）。
3. **色差**：别试图用「采样 hex 再设页面底色」去对齐——P3 色差会让整块图偏色。**抠透明**才是根治（脚本默认做）。
4. **扉页底色**：`build_book.py` 用 toc.json 里每章 `dividerColor` 设扉页 `accent`，插画透明后正好落在这块纯色上。若想绝对严丝合缝，可让插画背景 hex == dividerColor。

## 手动单张（调试用）

```bash
cd /tmp && codex exec --skip-git-repo-check "<完整 prompt>"
# 找最新（codex 为例）： ls -t ~/.codex/generated_images/*/*.png | head -1
python3 $SKILL/scripts/chroma_key.py <那张raw.png> $PROJECT/assets/chNN-head.png
```

## 需要更"精美"的配图时（封面大图 / 内文杂志级配图 / 截图美化 / 信息图）

本管线产出的是 anthropic 风格的极简线条插画。若目标书想要更丰富、编辑杂志级的视觉：**如果**你的环境里装有一套成熟的「HTML 模板 + 浏览器渲染成图」体系的 skill（例如某社交卡 skill），可借鉴/复用其原则与模板；**否则**就用本 skill 的图像生成管线（上面的生图 → 抠透明流程）自己出图。下面以这类社交卡 skill 为例说明可借鉴的资产——

- `references/style-system.md`、`background-systems.md`、`layout-recipes.md`、`screenshot-treatment.md`、`components.md`：版式/背景/截图美化/组件原则。
- `assets/template-*.html`、`assets/screenshot-backgrounds/`：可直接改用的卡片模板与背景图库。
- 用它生成 PNG/JPG 后，按 `chroma_key.py`（如需抠底）或直接 `image()` 嵌进 Typst 书里。
- 这类 HTML 渲图体系通常依赖浏览器渲染引擎（如 playwright + chromium）：首次用前按其目录的说明安装依赖。
- 它另成一体——**借用其原则与模板即可，不要改它本身**。

## 验收

抽查扉页页：插画应**直接浮在纯色上、无矩形边框**；各章构图/颜色不同；形状是白、线是黑。若仍见矩形，多半是没抠透明（用了 raw 图）或 `chroma_key` 阈值太紧（调大 `--t2`）。
