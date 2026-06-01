// ============================================================
//  book skill · 风格：anthropic
//  对标 Anthropic《The Founder's Playbook》
//  横向 · 纯白内文 · 衬线标题+无衬线正文 · 彩色扉页 · Chapter 药丸标签
//
//  这份文件就是「风格契约」：任何风格的 template.typ 都必须导出同一组
//  组件（book / cover / chapter-divider / toc-page / content-header /
//  prose / keypoint / jd-box / note / flow / loop-diagram），并暴露一个
//  扉页配色调色板。换风格 = 换一份实现了同样契约的 template.typ。
// ============================================================

// ---------- 调色板（采样自 Anthropic 官方出版物）----------
#let clay    = rgb("#D97757")   // 封面 / 主强调 · Anthropic 官方赤陶橙
#let sage    = rgb("#609A81")   // 章节扉页色 · 鼠尾草绿（采样自扉页插画背景，使其无缝融入）
#let peri    = rgb("#827DBD")   // 章节扉页色 · 长春花紫
#let ink     = rgb("#191919")   // 文字 · 近黑
#let paper   = rgb("#FFFFFF")   // 内文底 · 纯白
#let mut     = rgb("#6B6B6B")   // 次要文字 · 灰
#let codebg  = rgb("#F4F2EE")   // 代码底 · 极浅暖灰
#let hair    = rgb("#E2E0DB")   // 细分隔线
// 章节扉页 6 色循环（clay 留给封面，相邻章不撞色）：
#let divider-palette = (
  rgb("#609A81"), rgb("#827DBD"), rgb("#C2913B"),
  rgb("#5E7E96"), rgb("#C2766A"), rgb("#87894F"),
)

// ---------- 字体 ----------
#let serif = ("Hoefler Text", "Songti SC")     // 标题：衬线
#let sans  = ("Helvetica Neue", "PingFang SC")  // 正文：无衬线
#let mono  = ("Menlo", "PingFang SC")

// ---------- Chapter 药丸标签 ----------
#let pill(label) = box(
  stroke: 1pt + ink, radius: 20pt, inset: (x: 11pt, y: 5pt),
  text(font: sans, size: 9pt, weight: "medium", fill: ink, label),
)

// ============================================================
//  封面（整版赤陶橙，衬线大标题左上，标记左下）
// ============================================================
#let cover(title: "", subtitle: "", series: "") = page(
  fill: clay, margin: (left: 46pt, right: 46pt, top: 52pt, bottom: 46pt),
  header: none, footer: none,
)[
  #set text(fill: ink)
  #text(font: serif, weight: "semibold", size: 46pt, title)
  #if subtitle != "" { v(8pt); text(font: serif, weight: "regular", size: 26pt, fill: ink.lighten(8%), subtitle) }
  #place(bottom + left)[
    // 简洁星芒标记（手绘风，非任何品牌 logo）
    #box(baseline: 30%, {
      set line(stroke: 2pt + ink)
      box(width: 22pt, height: 22pt, {
        place(center + horizon, line(length: 22pt, angle: 0deg))
        place(center + horizon, line(length: 22pt, angle: 90deg))
        place(center + horizon, line(length: 22pt, angle: 45deg))
        place(center + horizon, line(length: 22pt, angle: 135deg))
      })
    })
    #h(10pt)
    #text(font: serif, weight: "semibold", size: 20pt, fill: ink, series)
  ]
]

// ============================================================
//  章节扉页（整版彩色 + 黑白连线插画右上 + 药丸标签&衬线大标题左下）
// ============================================================
#let chapter-divider(num: "", title: "", accent: sage, img: none) = page(
  fill: accent, margin: (left: 46pt, right: 46pt, top: 46pt, bottom: 50pt),
  header: none, footer: none,
)[
  // 隐藏的一级标题：不显示，但供目录页(outline)抓标题与页码
  #hide(place(heading(level: 1, outlined: true)[#title]))
  #if img != none { place(top + right, dx: 30pt, dy: -16pt, image(img, width: 52%)) }
  #place(bottom + left)[
    #pill("Chapter " + num)
    #v(14pt)
    #text(font: serif, weight: "semibold", size: 40pt, fill: ink, title)
  ]
]

// ============================================================
//  目录页（参考 Founder's Playbook 第 2 页：标题 … 页码）
// ============================================================
#let toc-page() = page(fill: paper, footer: none)[
  #text(font: serif, weight: "semibold", size: 34pt, fill: ink, "目录")
  #v(22pt)
  #context {
    let chs = query(heading.where(level: 1))
    for h in chs {
      let pg = counter(page).at(h.location()).first()
      block(width: 62%, grid(columns: (1fr, auto), column-gutter: 12pt,
        text(font: sans, size: 11.5pt, fill: ink, h.body),
        text(font: sans, size: 11.5pt, fill: mut, str(pg))))
      v(11pt)
    }
  }
]

// ---------- 内文页顶部：药丸 + 衬线标题（跨栏，章节首页用）----------
#let content-header(num: "", title: "") = {
  pill("Chapter " + num)
  v(10pt)
  text(font: serif, weight: "semibold", size: 30pt, fill: ink, title)
  v(14pt)
}

// ---------- 双栏正文容器 ----------
#let prose(body) = columns(2, gutter: 20pt, body)

// ---------- 通用 callout：细左线 + 小方块 marker + 克制标签 + 浅底 ----------
#let _callout(label, accent, bg, body) = block(
  width: 100%, fill: bg, inset: (x: 16pt, y: 13pt), radius: 7pt,
  stroke: (left: 2pt + accent),
  {
    grid(columns: (auto, 1fr), column-gutter: 8pt, align: horizon,
      box(width: 7pt, height: 7pt, radius: 1.5pt, fill: accent),
      text(font: sans, size: 8.5pt, weight: "bold", fill: accent, tracking: 0.5pt, label))
    v(9pt)
    set text(size: 10pt, fill: ink)
    body
  },
)

// ---------- 重点框（clay）/ 岗位/要点框（近黑）/ 提示框（灰）----------
#let keypoint(body) = _callout("一句话记住", clay, clay.lighten(92%), body)
#let jd-box(role: "", body) = _callout("对应岗位要求 · " + role, ink, codebg, body)
#let note(body) = _callout("注意", mut, rgb("#F6F4F0"), body)

// ---------- 流程图：编辑式·细线·克制（数字圆点 + 细连线 + 小箭头）----------
#let _step(i, label) = block(width: 98pt, align(center, {
  box(width: 22pt, height: 22pt, radius: 50%, stroke: 0.9pt + clay,
    align(center + horizon, text(font: sans, size: 9pt, weight: "bold", fill: clay, str(i))))
  v(8pt)
  text(font: sans, size: 9pt, fill: ink, label)
}))
#let _conn() = pad(top: 6pt, box(width: 32pt, height: 11pt, {
  place(left + horizon, line(length: 24pt, stroke: 0.9pt + mut))
  place(left + horizon, dx: 23pt, polygon(fill: mut, (0pt, 0pt), (6pt, 3pt), (0pt, 6pt)))
}))

#let flow(items, loopback: none) = block(width: 100%, inset: (y: 3pt), {
  line(length: 100%, stroke: 0.6pt + hair)
  v(16pt)
  let cells = ()
  for (i, it) in items.enumerate() {
    if i > 0 { cells.push(_conn()) }
    cells.push(_step(i + 1, it))
  }
  align(center, grid(columns: (auto,) * cells.len(), column-gutter: 5pt, align: top, ..cells))
  if loopback != none {
    v(14pt)
    align(center, box(stroke: 0.8pt + clay, radius: 20pt, inset: (x: 13pt, y: 5pt),
      text(font: sans, size: 8.5pt, fill: clay.darken(6%), loopback)))
  }
  v(15pt)
  line(length: 100%, stroke: 0.6pt + hair)
})

// 示例专用循环图（可按主题改 items/loopback；也可直接用 flow）
#let loop-diagram() = flow(
  ("模型思考", "调用工具", "执行 + 观察", "结果回填"),
  loopback: "未完成 → 带着新信息回到第 1 步，直到模型认为任务结束",
)

// ---------- Mermaid 图嵌入：assets/diagrams/<name>.png，编辑式细线框居中 ----------
// 路径相对本文件(项目根)解析，章节里只需 #diagram("NN-name")。
// 自动等比缩放：同时受可用宽度与 maxh 约束，取小者 → 永远塞进单页、不溢出不截断。
// 整块 breakable:false，宁可整张挪到下一页也不跨页切。
#let diagram(name, maxh: 142mm) = block(width: 100%, breakable: false, inset: (y: 3pt), {
  line(length: 100%, stroke: 0.6pt + hair)
  v(12pt)
  layout(size => {
    let p = "assets/diagrams/" + name + ".png"
    let nat = measure(image(p))
    let s = calc.min(size.width / nat.width, maxh / nat.height)
    align(center, image(p, width: nat.width * s))
  })
  v(12pt)
  line(length: 100%, stroke: 0.6pt + hair)
})

// ============================================================
//  主模板（默认 = 白色横向内文页）
// ============================================================
#let book(title: "", body) = {
  set page(
    width: 11in, height: 8.5in,
    margin: (x: 26mm, top: 22mm, bottom: 15mm),
    fill: paper,
    footer: context {
      set text(8.5pt, fill: mut, font: sans)
      grid(columns: (1fr, 1fr), text(title), align(right, counter(page).display()))
    },
  )
  set text(font: sans, size: 9.5pt, fill: ink, lang: "zh", region: "cn")
  set par(justify: true, leading: 0.82em, spacing: 1.1em)

  // 编辑式表格：无竖线、强调色加粗表头 + 表头下细线、行间淡发丝线
  set table(
    stroke: (x, y) => (bottom: if y == 0 { 0.9pt + ink } else { 0.4pt + hair }),
    inset: (x: 11pt, y: 8pt),
    fill: none,
  )
  show table.cell: set text(font: sans, size: 9pt, fill: ink)
  show table.cell.where(y: 0): set text(weight: "bold", fill: clay, size: 8.5pt)

  show heading.where(level: 2): it => { v(0.6em); text(font: serif, weight: "semibold", size: 15pt, fill: ink, it.body); v(0.25em) }
  show heading.where(level: 3): it => { v(0.5em); text(font: sans, weight: "bold", size: 11pt, fill: clay, it.body); v(0.1em) }

  show raw.where(block: false): it => box(
    fill: codebg, inset: (x: 3pt), outset: (y: 3pt), radius: 2pt,
    text(font: mono, size: 8.5pt, fill: clay.darken(20%), it),
  )
  show raw.where(block: true): it => block(
    fill: codebg, inset: 13pt, radius: 5pt, width: 100%,
    stroke: (left: 2.5pt + clay),
    text(font: mono, size: 8pt, it),
  )
  show link: it => text(fill: clay, it)
  show strong: it => text(fill: ink, weight: "bold", it.body)

  body
}
