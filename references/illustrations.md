# 扉页插画管线（生图 → 色键抠透明 → 落到同色扉页）

## 为什么这么做

- **生图**：用一个可用的图像生成 CLI/能力（例如 `codex` 或任意能生图的命令行工具）。以 `codex` 为例，`codex exec "<prompt>"` 会把图存到其生成目录（如 `~/.codex/generated_images/<session-uuid>/ig_*.png`）。不需要额外图像 API key。换成别的生图工具时，逻辑相同——只是产物落地目录和取图方式要按该工具调整。
- **抠透明**：生成的 PNG 常带颜色描述文件(P3 等)，直接贴到 Typst 纯色页上会整块偏色、露出**矩形贴图边界**。把插画背景色键抠成透明后，只剩白形状+黑线，落在 Typst 同色扉页上**无缝融入**，且物理上不可能有矩形（没有背景了）。
- **每章一张、各不相同但呼应主题**——风格语言不变（白形状+黑线+圆点+手绘），换的是构图/形状/颜色。

## 🚫 生图失败时——STOP，别静默降级（最重要）

这条是血泪：生图通道一旦坏掉，最糟的不是"没图"，而是**脚本/agent 假装成功、悄悄用了错的东西**。两种已发生的静默降级，都要堵死：

- **别静默复用旧图**：生图没产出时，绝不能"取最新 png"抓个旧图当本次结果（曾把一本书 10 张扉页全覆盖成同一张无关图）。脚本已改成「快照取新增 + 失败保留旧图」。
- **别用本机代码画几何形顶替**：扉页插画必须是**图像模型手绘的、能认出意象的概念线描**（地图、闸门、总机、漏斗…），**不是**程序画的裸方块/圆/三角——后者什么都没表达，比没有还糟。同理内文信息图必须走 `gen_infographics.py` 生成，不能用简单流程图悄悄顶替。

**正确做法**：脚本现在会打印 codex 的退出码/报错。一旦看到生图报错或零产出，**停下、把错误原样告诉用户、先修前置条件再继续**。最常见根因：

- `codex exec` 启动即报 `Error loading config.toml: unknown variant 'priority' … service_tier`——`~/.codex/config.toml` 的 `service_tier`（含 `default-service-tier`）写了当前 codex CLI 不认的值，改成 `flex` 或 `fast`（或临时用一份修好的 `CODEX_HOME` 配置）即可。
- 未登录 / 额度问题 / 模型不支持生图——按报错处理。
- 换了别的图像生成 CLI——产物落地目录与"取新增"的方式按该工具调整。

## 一键脚本

```bash
python3 $SKILL/scripts/gen_illustrations.py --project $PROJECT --style <style>
```
它对 `$PROJECT/illustration-specs.json` 里每章：拼 `风格前缀 + 背景纯色<hex> + 画面<concept>` → 调用生图 CLI（默认 `codex exec`）→ **只取本次新增产物**（生成前后快照取差集）→ `chroma_key` 抠透明 → 存 `$PROJECT/assets/chNN-head.png`。每张最多重试 3 次，仍失败则**保留旧图不动**并在末尾列出失败章节。顺序跑，约 1–2 分钟/张。

> ⚠️ **绝不要并行跑生图**：多个 `codex exec` 会抢同一个生成目录的产物，快照差集会串图。要快就顺序跑完。

> `illustration-specs.json` 由 TOC 阶段抽出：`[{"num","hex","colorName","concept"}, ...]`。
> 风格前缀来自 `$SKILL/styles/<style>/illustration-prompt.md` 的第一个代码块。

## 实操坑（踩过的）

1. **目录信任**：非 git 目录跑 `codex` 要加 `--skip-git-repo-check`（脚本已带）。换其他生图工具时，照该工具对非 git 目录的要求处理。
2. **沙箱只读**：生图工具自身沙箱常无法写到 /tmp 或项目目录；以 `codex` 为例，它只会把图落在自己的生成目录（如 `~/.codex/generated_images/`），由脚本**用生成前后快照取差集**拿到本次新增的那张复制出来（**不要用「ls 取最新」**——某张失败时会抓到上一张/别项目的旧图，静默把扉页覆盖成错图）。
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
