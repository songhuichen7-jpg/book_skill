# 风格系统（可插拔）

`$SKILL/styles/` 下每个子目录是一个**风格**。本 skill 生成的每本书都选定一个风格。换风格只需换一套实现了同一契约的资产，正文/流水线/脚本都不用改。

```
$SKILL/styles/
├── README.md          ← 本文件
├── anthropic/         ← 内置：Anthropic 编辑设计语言（暖纸 + clay + 衬线/无衬线 + 黑白连线插画）
│   ├── template.typ          风格契约的 Typst 实现（导出全部组件 + 调色板）
│   ├── style.md              该风格的视觉令牌、页面结构、排版口味
│   └── illustration-prompt.md 扉页插画的 art-direction 前缀 + 取材原则
└── <你的新风格>/       ← 未来在这里加，照搬上面三件套即可
```

## 风格契约（每个 `template.typ` 必须导出）

正文与脚本只依赖这组名字，所以任何风格都必须提供同名实现：

| 组件 | 签名 | 作用 |
|---|---|---|
| `book` | `book(title: str, body)` | 主模板（页面/字体/表格/标题/代码的全局规则）；用 `#show: book.with(title: ...)` 套上 |
| `cover` | `cover(title:, subtitle:, series:)` | 封面页 |
| `chapter-divider` | `chapter-divider(num:, title:, accent:, img:)` | 整版彩色章节扉页（含隐藏一级标题供目录抓取） |
| `toc-page` | `toc-page()` | 自动目录页（查询一级标题 + 页码） |
| `content-header` | `content-header(num:, title:)` | 内文章首的标签 + 标题 |
| `prose` | `prose(body)` | 正文容器（如双栏） |
| `keypoint` | `keypoint(body)` | 要点框 |
| `jd-box` | `jd-box(role:, body)` | 应用/案例/小结框（带角色标签的强调框，名称为契约固定值，勿改） |
| `note` | `note(body)` | 提示/陷阱框 |
| `flow` | `flow(items, loopback: none)` | 横向流程图 |
| `loop-diagram` | `loop-diagram()` | 示例循环图（可选，主要是 flow 的特例） |
| `divider-palette` | 颜色数组 | 章节扉页配色循环（TOC 阶段据此给每章配色） |

只要导出这组名字，正文文件（`#import "../template.typ": *` + `prose/keypoint/...`）就能在任何风格下原样编译。

## 加一个新风格（约定）

1. `cp -r $SKILL/styles/anthropic $SKILL/styles/<新风格>`。
2. 改 `$SKILL/styles/<新风格>/template.typ`：调色板、字体、页面、各组件的视觉实现——**只改样式，别改导出的名字与签名**。
3. 改 `$SKILL/styles/<新风格>/style.md`、`$SKILL/styles/<新风格>/illustration-prompt.md`（视觉令牌 + 插画语言；若该风格不用插画，把扉页 `img` 留空即可）。
4. 生成时把 `--style <新风格>` 传给本 skill 的排版脚本（`$SKILL/scripts/...`）即可。

> 设计提示：让「页面底色 = 插画背景色」，插画抠透明后就能无缝融入；强调色尽量克制（一个为主）。详见 `anthropic/style.md` 末尾「为什么好看」。
