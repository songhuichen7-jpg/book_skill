# 图：Mermaid（富表达）vs flow()（极简）

书里三类内文图，由"要功能还是要美"分流：

- **`#flow((...), loopback:)`**（template 自带）：只够画**一条线性步骤序列**。简单、克制。
- **Mermaid → PNG → `#diagram("name")`**：画**有结构的功能图**——状态机、分组、带标签/虚线的边、反馈回路、多块架构。**精确、可改、技术感**，但美术一般。见下方「Mermaid」。
- **插画信息图 → `#diagram("name")`**（**最精致 / 最有趣，推荐用于面向人的书**）：用图像生成能力（`codex` 或任意可用的图像生成 CLI/能力）把概念画成**手账涂鸦 / sketchnote 等插画风信息图**（冰山、登山岔路、过河踩石+闸机、海关通关地图…），中文标签准确、有视觉隐喻、有手工趣味。详见 **`$SKILL/styles/<style>/infographic-prompt.md`** + **`$SKILL/scripts/gen_infographics.py`**。

判断：要**精确可改的技术流程/状态机**用 Mermaid；要**有趣、精致、有比喻感、面向大众读者**用插画信息图；线性三五步用 `flow()`。三者都嵌成 `#diagram("name")`（同名 PNG 放 `$PROJECT/assets/diagrams/`），可在一本书里混用。

> 插画信息图的实测踩坑（已固化）：① **prompt 别太长**——过度细写每根箭头会让生图 >900s 超时，写"风格前缀 + 场景隐喻 + 精确中文标注"即可，箭头关系点到为止；② `gen_infographics.py` 用**生成前后快照取新增图**（不是"取最新"），否则某张失败时会把上一张的旧图串成错名字；③ 仍要**逐张 Read 验中文标签**，糊字/错字用 `--only <name>` 重生成。

## 为什么走 Mermaid（而不是手摆坐标）

Mermaid 是声明式「图的语言」，自动布局——agent 写 `A --> B` 比用 fletcher/cetz 手算坐标可靠得多，能规模化到"各种图"。代价是要外部渲染（mmdc）+ 以 **PNG** 嵌入。

## 怎么做（按阶段；本阶段处理单张图，可由一个子任务完成）

1. **复制模板**：把 `$SKILL/styles/<style>/mermaid-template.mmd` 复制成 `$PROJECT/diagrams/<NN-slug>.mmd`（NN=章号，slug 描述性，如 `03-last20`）。模板顶部已含 `%%{init}%%` 书主题 + 7 个配色 class。
2. **写图**：改 `flowchart LR/TB` 的节点与边。形状：`([圆角])` `[方角]` `{{六边形}}` `{菱形判断}`；边：`-->` `==>` `-. 标签 .->`；分组：`subgraph G["组名"] ... end`。**多彩**：给节点 `class X c1`（c1 长春花紫 / c2 赤陶橙 / c3 鼠尾草绿 / c4 灰蓝 / c5 赭黄 / c6 砖玫红 / neutral 灰）。
3. **自验渲染**：`python3 $SKILL/scripts/render_mermaid.py --file $PROJECT/diagrams/<NN-slug>.mmd --out $PROJECT/assets/diagrams/<NN-slug>.png --style <style>`。报错就是 Mermaid 语法问题，改到能出 PNG。
4. **嵌入**：在章节 .typ 里把原来的 `#flow(...)` 替换成 `#diagram("<NN-slug>")`（放在 prose 块之间，跨整页宽、自带细线框）。
5. 章节编译（PNG 已生成）→ 零错误。

全书一把渲染（拼装前）：`python3 $SKILL/scripts/render_mermaid.py --project $PROJECT --style <style>` → 渲染 `$PROJECT/diagrams/*.mmd` 到 `$PROJECT/assets/diagrams/*.png`。若图较多且你的环境支持并行子代理（如某些 CLI 的子代理/工作流机制），可把每张图 fan out 给一个子任务并行渲染；否则顺序逐张完成即可——具体编排用你所在环境的子代理机制。

## 必须横版适配（最容易翻车的地方）

书是**横版**页（可用区约 235mm 宽 × 175mm 高，高是稀缺维度）。**图必须比一页矮、且优先做宽**，否则 `#diagram` 自动缩放会把高瘦图压成一条细窄竖带、文字小到看不清。

硬规则：
- **优先 `flowchart LR`（横排），目标长宽比 ≥ 1.5（宽 > 高）**，理想 ~2:1。出现"竖到比页还高"就是设计错了。
- **紧凑**：≤ 约 8 个节点；用 `subgraph` 横向铺开分组，别一路 `TB` 往下堆很多 rank。
- **标签短 + `<br/>` 断行**；**菱形 `{}` 里别放长句**（mmdc 会把超出的字切掉，如"statu"），长条件挪到边标签 `-. 长条件 .->` 上，菱形内 ≤ 6 字。
- 渲染后**用 PIL 量长宽比**（`Image.open(p).size`）——`h > w` 就重画得更扁（减少纵向 rank、并排放节点）；再 Read 看 PNG 确认没有节点内文字被切。
- `#diagram` 已 `breakable:false` + 自动缩放：图永远塞进单页不溢出，但**塞得下 ≠ 好看**——宽图才能在横版页上放大、清晰。

## 坑（都验证过）

- **必须输出 PNG，不能 SVG**：Mermaid 的 SVG 用 `<foreignObject>` 放文字，Typst 渲染不出文字（只剩空形状）。`render_mermaid.py` 已固定出 PNG（-s 3 高 DPI，印刷够清晰）。
- **节点文字别太长**：mmdc 按内容裁边，过长的单行会贴右边缘。用 `<br/>` 断行、标签精炼；`$` 在 .mmd 里直接写（不要像 Typst 那样转义 `\$`）。
- **字体回退**：headless chromium 可能把中文回退成衬线——已用 `$SKILL/styles/<style>/mermaid.css` 强制无衬线，渲染脚本自动带上。
- 依赖 `mmdc`（Mermaid 渲染 CLI）：脚本优先用 `$SKILL/tools/node_modules/.bin/mmdc`，缺了走 `npx`；首次需要在 `$SKILL/tools` 目录下执行 `npm install @mermaid-js/mermaid-cli`（带一个 chromium）。
