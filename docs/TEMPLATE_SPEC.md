# School Template Spec v0.2

学校模板只描述渲染规则，不保存论文内容。模板使用 YAML 编写，由 Pydantic
严格校验；未知字段、无单位长度、非法枚举值和缺失必填样式都会被拒绝。

## 选择规则

模板选择按以下优先级执行：

1. CLI 显式传入的 `--template <path>`；
2. Markdown Front Matter 中的 `render.template_id`。

显式路径必须指向本地 `.yaml` 或 `.yml` 模板文件。模板 ID 先在论文源文件最近祖先目录中的
`templates/` 树确定性查找；项目没有模板树时，再回退到安装包内置模板。
找不到或同一优先级内一个 ID 匹配多个文件都会产生结构化校验错误。解析结果
不依赖进程当前工作目录，模板解析也不访问网络。

## 完整结构

```yaml
id: example-university-2026
name: XX大学本科毕业论文
year: 2026

page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm

body:
  font:
    east_asia: 宋体
    latin: Times New Roman
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt

heading:
  level1:
    font:
      east_asia: 黑体
      latin: Times New Roman
    size: 16pt
    bold: true
    italic: false
    alignment: center
    space_before: 12pt
    space_after: 12pt
    page_break_before: false
  level2:
    size: 14pt
    bold: true
    alignment: left
  level3:
    size: 12pt
    bold: true
    alignment: left

figure:
  numbering:
    mode: chapter
    separator: "-"
  caption:
    position: bottom
    prefix: 图
    size: 10.5pt
    alignment: center
  default_width: 150mm

table:
  style: three_line
  numbering: chapter
  caption:
    position: top
    prefix: 表
    alignment: center

equation:
  numbering: chapter
  alignment: center

sections:
  cover:
    start: new_page
    header:
      enabled: false
    footer:
      enabled: false
    page_number:
      format: none
  front_matter:
    start: new_page
    header:
      enabled: false
    footer:
      enabled: true
    page_number:
      format: roman-lower
  main:
    start: new_page
    header:
      enabled: true
      text: 论文标题
      different_first_page: false
    footer:
      enabled: true
    page_number:
      format: decimal
      restart: 1

citation:
  style: GB-T-7714-2025
```

`numbering` 支持字符串短写，例如 `numbering: chapter`，等价于：

```yaml
numbering:
  mode: chapter
  separator: "-"
```

## 必填字段

- 顶层：`id`、`name`、`year`、`page`、`body`、`heading`。
- 页面：`page.margin.top/bottom/left/right`。
- 正文：`body.size`、`body.first_line_indent`、`body.line_spacing`。
- 标题：至少提供 `heading.level1`，每个标题级别必须提供 `size`。

`figure`、`table`、`equation` 和 `citation` 可以省略，但当论文实际使用对应
语义对象时，Validator 会产生 `missing-template-style`。文档出现 H2/H3 时，
模板也必须定义对应的 `heading.level2/level3`。

## 单位

所有显式长度必须写为字符串并带单位：

- `mm`
- `cm`
- `pt`
- `em`

合法示例：`25mm`、`2.5cm`、`12pt`、`2em`。

非法示例：`25`、`"12"`、`"12px"`、`"large"`。错误会包含完整字段路径，
例如 `page.margin.top` 或 `heading.level1.size`。

## 枚举值

- `page.size`：`A3`、`A4`、`A5`、`Letter`、`Legal`。
- `page.orientation`：`portrait`、`landscape`。
- 对齐：正文/标题/题注支持 `left`、`center`、`right`、`justify`；公式支持
  `left`、`center`、`right`。
- `line_spacing.type`：`single`、`multiple`、`fixed`。
- `numbering.mode`：`chapter`、`continuous`、`none`。
- `caption.position`：`top`、`bottom`。
- `table.style`：`three_line`、`grid`、`plain`。
- `section.start`：`continuous`、`new_page`、`odd_page`、`even_page`。
- `page_number.format`：`none`、`decimal`、`roman-lower`、`roman-upper`。

`fixed` 行距必须使用带单位长度；`multiple` 行距必须使用正数倍数。
`page_number.restart` 必须是大于等于 1 的整数。

## 字体

字体通过 `font.east_asia` 和 `font.latin` 分开配置。DOCX Renderer 会把两者
写入正确的 Word 字体槽位，不能只设置 Latin 字体或在 Renderer 中硬编码学校
字体。正文和标题的字号、加粗、斜体、对齐、段前段后、首行缩进、行距和标题
前分页也由模板写入 Word 样式。

## 编译与基础 DOCX 应用

模板解析成功后，CLI 把同一个强类型模板实例传给 Compiler。Compiler 在渲染前
把页面、正文、标题和 section policy 绑定进 renderer-neutral `RenderPlan`，
Renderer 不再搜索 YAML，也不重新计算编号、bookmark、引用目标或 citation
顺序。

基础 DOCX 阶段应用：

- 页面尺寸、方向和四边页边距；
- `Normal` 正文字体、字号、对齐、首行缩进和行距；
- `Heading 1-3` 的字体、字号、强调、对齐、段前段后和分页行为。

图表真实对象、Word fields、OMML、多个 section、页眉页脚和页码由对应后续能力
在同一 `RenderPlan` 合同上继续实现。

## 校验结果

模板相关问题通过 `ValidationIssue` 返回：

- `missing-template`：未选择模板或本地找不到模板；
- `ambiguous-template`：一个模板 ID 匹配多个本地文件；
- `invalid-template`：YAML、字段、单位或枚举值无效；
- `missing-template-style`：论文使用了模板未定义的标题或语义对象样式。

`thesisforge validate` 会收集这些问题并与文档诊断一起稳定排序。warning
不会导致失败；存在任意 error 时退出码为 1。源 Markdown 无法读取或解析时
退出码为 2。
