# ThesisForge Template Package Spec v2 — Draft

> 状态：Design Draft  
> 目标：替代“单个 YAML 文件描述全部学校版式”的 v0.1 模型。

## 1. 设计目标

Template Package v2 必须同时解决：

- 学校格式规则的结构化表达；
- Word 原生样式、主题、页眉页脚和节属性复用；
- 复杂封面和声明页；
- 模板校验、测试、版本、迁移和发布；
- 来源、许可证和学校文件版本追踪；
- 同一论文源切换模板；
- 模板作者不修改 Compiler 核心代码。

## 2. 非目标

- 用 YAML 表达 Word 的每一个底层 XML 属性；
- 自动理解任意学校上传的 DOCX；
- 允许模板执行任意代码；
- 允许模板静默访问网络或项目目录外文件；
- 通过复制整份 Word 文件内容来“伪装”为模板系统。

## 3. 包结构

```text
example-university-bachelor-2026/
├── template.yaml
├── reference.docx
├── shell.docx                  # optional
├── assets/
│   ├── logo.png
│   └── placeholder-seal.png
├── layouts/
│   ├── cover.yaml
│   ├── declaration.yaml
│   └── abstract.yaml
├── styles/
│   └── aliases.yaml
├── citations/
│   ├── style.csl
│   └── overrides.yaml
├── fixtures/
│   ├── minimal/
│   ├── full/
│   └── edge-cases/
├── expected/
│   ├── manifest.json
│   ├── xml/
│   └── visual/
├── provenance.yaml
├── CHANGELOG.md
├── LICENSES/
└── README.md
```

最小包只要求：

```text
template.yaml
reference.docx
provenance.yaml
fixtures/minimal/
README.md
```

## 4. `template.yaml`

### 4.1 Header

```yaml
schema_version: 2
id: example-university.bachelor.2026
version: 1.0.0
name: XX大学本科毕业论文（2026）
language: zh-CN
status: active

compatibility:
  thesisforge: ">=1.0,<2.0"
  document_types:
    - bachelor_thesis
  target_apps:
    word: primary
    wps: compatible
    libreoffice: preview
```

### 4.2 Inheritance

```yaml
extends:
  id: thesisforge.base.bachelor.zh-cn
  version: "^2.0"
```

继承规则：

- 只允许显式声明的字段合并；
- list 默认 replace，不默认 concat；
- 不允许循环；
- 构建 manifest 记录完整继承链和哈希；
- `template inspect --resolved` 可查看最终值；
- 模板包不能从未授权网络位置动态加载父模板。

### 4.3 Word source

```yaml
word:
  reference_docx: reference.docx
  shell_docx: shell.docx       # optional
  macro_policy: forbid
  external_relationships: forbid
  anchors:
    body: tf_body
    toc: tf_toc
    bibliography: tf_bibliography
```

#### `reference.docx`

用途：

- styles；
- theme；
- font table；
- page setup；
- header/footer；
- numbering base；
- document settings；
- default language。

其正文应为空或仅包含模板允许清理的占位内容。

#### `shell.docx`

可选，用于复杂学校前置页。允许包含：

- 封面；
- 声明页；
- 学校 Logo；
- 预先设计的表格；
- section breaks；
- content controls 或 bookmarks；
- 正文/目录/参考文献插入锚点。

安全约束：

- 禁止宏；
- 禁止外部 OLE；
- 默认禁止外部 relationships；
- 所有 anchors 必须唯一且可验证；
- shell 处理必须保留 relationships、styles 和 sections；
- 缺失 body anchor 为阻断错误。

## 5. Units

所有长度必须显式带单位：

- `mm`
- `cm`
- `pt`
- `in`
- `em`（仅允许在具有字体上下文的字段）
- `%`（仅允许在可计算父宽度的字段）

禁止隐式裸数字。

```yaml
page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    inner: 30mm
    outer: 25mm
  gutter: 0mm
  mirror_margins: false
```

## 6. Fonts

```yaml
fonts:
  body:
    east_asia: SimSun
    latin: Times New Roman
    complex_script: Times New Roman
    fallback:
      east_asia: [Noto Serif CJK SC]
      latin: [Liberation Serif]
  code:
    east_asia: Sarasa Mono SC
    latin: Consolas

font_policy:
  missing_primary: error
  missing_fallback: warning
  embed_fonts: false
```

模板必须区分：

- East Asia；
- ASCII；
- High ANSI；
- Complex Script。

模板中使用的是字体族要求，不应假设所有平台都有相同内部名称。`doctor` 负责探测。

## 7. Style tokens

Compiler 和 RenderPlan 使用稳定 token，不直接硬编码学校 style ID：

```yaml
styles:
  paragraph:
    body: TF Body
    body_first: TF Body First
    abstract: TF Abstract
    bibliography: TF Bibliography
    caption_figure: TF Figure Caption
    caption_table: TF Table Caption
    equation: TF Equation
    listing: TF Listing
    footnote: Footnote Text
  heading:
    1: TF Heading 1
    2: TF Heading 2
    3: TF Heading 3
    4: TF Heading 4
  character:
    emphasis: Emphasis
    strong: Strong
    code: TF Code Char
    hyperlink: Hyperlink
```

模板 lint 检查：

- style 是否存在；
- 类型是否匹配（paragraph/character/table）；
- style ID 是否重复；
- basedOn/next/link 是否有效；
- 内置样式名称本地化问题；
- 不允许引用不存在的 style。

## 8. Body and headings

```yaml
body:
  style: body
  alignment: justify
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
  spacing:
    before: 0pt
    after: 0pt
  widow_control: true

headings:
  1:
    style: 1
    page_break_before: true
    keep_with_next: true
    numbering:
      enabled: true
      pattern: "第{chapter_zh}章"
  2:
    style: 2
    keep_with_next: true
    numbering:
      enabled: true
      pattern: "{chapter}.{section}"
```

样式优先，YAML 属性用于：

- 学校规范中需要动态变化的规则；
- 编译器必须知道的语义；
- 无法只靠 style 表达的设置；
- lint 和诊断。

避免同时在 style 和 YAML 中重复定义同一属性。若不可避免，必须定义 precedence。

## 9. Document regions

```yaml
regions:
  order:
    - cover
    - originality_statement
    - authorization_statement
    - abstract_zh
    - abstract_en
    - toc
    - main
    - bibliography
    - acknowledgements
    - appendices
    - achievements

  cover:
    required: true
    section: cover
    heading_numbering: false

  abstract_zh:
    required: true
    section: front_matter
    title: 摘要
    title_style: 1

  main:
    required: true
    section: main

  bibliography:
    required: true
    section: back_matter
    title: 参考文献
```

Region 与 Heading 不应混为一谈。封面、目录等是文档结构单元，可能没有普通标题。

## 10. Section policies

```yaml
sections:
  cover:
    page_number:
      display: false
    header_footer:
      first_page: none
      default: none
    start: new_page

  front_matter:
    page_number:
      display: true
      format: roman-lower
      restart: 1
    header_footer:
      default: front_default
    start: next_page

  main:
    page_number:
      display: true
      format: decimal
      restart: 1
    header_footer:
      default: main_default
      even: main_even
      first: main_first
    start: next_page

  back_matter:
    page_number:
      continue: true
    header_footer:
      default: main_default
```

需要类型化支持：

- break type；
- page number display/format/restart/continue；
- first/even/default headers and footers；
- title page；
- page size/orientation overrides；
- columns；
- vertical alignment；
- footnote restart。

## 11. Numbering

```yaml
numbering:
  chapter:
    source: heading_1
    format: decimal
    display: "第{n}章"

  figure:
    scope: chapter
    sequence_name: TF_FIGURE
    separator: "-"
    caption_prefix: 图
    caption_pattern: "{prefix} {number}  {caption}"
    reference_forms:
      number: "{number}"
      label_number: "{prefix} {number}"
      full: "{prefix} {number} {caption}"

  table:
    scope: chapter
    sequence_name: TF_TABLE
    separator: "-"
    caption_prefix: 表

  equation:
    scope: chapter
    sequence_name: TF_EQUATION
    display: "（{number}）"
```

必须区分：

- 内部 sequence name；
- 用户显示编号；
- caption pattern；
- reference display；
- appendix scope；
- restart rules。

## 12. Figures

```yaml
figures:
  placement: inline
  alignment: center
  max_width: 100%
  max_height: 220mm
  keep_with_caption: true
  caption:
    position: bottom
    style: caption_figure
  source_note:
    enabled: optional
    style: body
```

策略字段：

- image format allowlist；
- DPI warning；
- max byte size；
- width/height；
- crop policy；
- floating/inline；
- alt text required；
- subfigure support level。

## 13. Tables

```yaml
tables:
  default_style: three_line
  width: 100%
  autofit: false
  repeat_header: true
  allow_row_break: false
  caption:
    position: top
    style: caption_table

  styles:
    three_line:
      borders:
        top: 1.5pt
        header_bottom: 0.75pt
        bottom: 1.5pt
        inside_vertical: none
      cell:
        vertical_alignment: center
        padding:
          top: 1mm
          bottom: 1mm
          left: 1mm
          right: 1mm
```

必须定义超宽处理：

```yaml
overflow:
  strategy: diagnose  # diagnose | scale | landscape_section
  threshold: 100%
```

不应静默压缩到不可读。

## 14. Equations

```yaml
equations:
  converter: default
  inline_style: equation_inline
  block_style: equation
  alignment: center
  numbered_layout: tab_stop
  number_alignment: right
  unsupported_latex: error
  image_fallback: disabled
```

当前 Word 渲染固定采用 `tab_stop`：居中制表位位于正文可用宽度的 50%，
右对齐制表位位于 100%。公式与编号分别定位，编号宽度不会改变公式的页面几何
中心。`borderless_table` 与 `custom_paragraph` 仍为保留枚举，不属于当前
Renderer 的已实现布局。

## 15. Fields and references

```yaml
fields:
  update_on_open: true
  cached_results: true
  mark_dirty: true
  finalizer:
    draft: none
    final_auto: auto
    final_word: word

cross_references:
  default_form: label_number
  page_reference: false

toc:
  enabled: true
  depth: 3
  title: 目录
  include_page_numbers: true
  right_align_page_numbers: true
  hyperlink: true
```

## 16. Bibliography

```yaml
bibliography:
  provider: default
  style_file: citations/style.csl
  locale: zh-CN
  heading_region: bibliography
  paragraph_style: bibliography
  hanging_indent: 2em
  line_spacing:
    type: single
  sort: style
  uncited: exclude
  missing_field_policy: warning
  overrides_file: citations/overrides.yaml
```

`style.csl` 必须有来源、版本、哈希和许可证记录。

## 17. Layout files

对于封面、声明等规则化内容，可以使用声明式 layout：

```yaml
id: cover
blocks:
  - type: image
    source: assets/logo.png
    width: 35mm
    alignment: center
  - type: spacer
    height: 18mm
  - type: paragraph
    style: cover_title
    value: "${thesis.title}"
  - type: table
    style: cover_metadata
    rows:
      - ["学生姓名", "${author.name}"]
      - ["学号", "${author.student_id}"]
      - ["指导教师", "${advisor.name}"]
```

允许的 block 类型必须有限且类型化，禁止执行任意表达式。变量只能读取白名单 metadata path，并支持 required/default/format。

复杂度超过声明式布局能力时，使用 `shell.docx` anchors，而不是不断扩张 YAML 为 Word 克隆语言。

## 18. Provenance

`provenance.yaml`：

```yaml
school:
  name: XX大学
  official_document:
    title: 2026届本科毕业论文撰写规范
    version: "2026.1"
    issued_date: 2025-09-01
    source_type: official-docx
    source_hash: sha256:...

maintainers:
  - name: ThesisForge Community
    contact: ...

licenses:
  template_code: Apache-2.0
  school_assets: restricted
  citation_style: CC-BY-SA-3.0

review:
  last_verified: 2026-07-20
  verified_with:
    - Microsoft Word ...
```

模板 pack 必须检测缺失 provenance。

## 19. Template validation

`template lint` 分层：

### L1 Package

- required files；
- path safety；
- hashes；
- no macros/external links；
- IDs and versions。

### L2 Schema

- YAML types；
- units；
- enums；
- references；
- inheritance。

### L3 Word assets

- DOCX valid；
- styles exist；
- anchors exist；
- relationships valid；
- headers/footers/sections expected。

### L4 Semantic

- required region has section policy；
- object style exists；
- numbering source exists；
- citation style exists；
- contradictory properties。

### L5 Fixture

- minimal fixture builds；
- full fixture builds；
- expected XML checks；
- optional visual baseline。

## 20. Versioning and migration

模板有三个版本维度：

1. `schema_version`：Template Package 结构版本；
2. `version`：该模板包自身语义版本；
3. `school official version`：学校规范版本。

版本升级规则：

- patch：修复不改变预期版式；
- minor：新增可选能力或学校规则；
- major：改变版式、字段或兼容行为；
- schema migration 必须显式；
- build manifest 记录 resolved template；
- 旧模板不能被静默按新 schema 解释。

## 21. Packaging

建议扩展名：`.tftpl`，本质为受约束的 ZIP 包。

```bash
thesisforge template pack ./template -o dist/example-university-1.0.0.tftpl
thesisforge template verify dist/example-university-1.0.0.tftpl
```

包内包含：

- deterministic entry order；
- manifest；
- file hashes；
- optional signature；
- SBOM/licenses；
- schema and compatibility metadata。

解包必须防止 Zip Slip 和解压炸弹。

## 22. Template Definition of Done

一个模板达到 Beta/GA 要求前，至少必须：

- 通过 package/schema/Word/semantic lint；
- 有 minimal/full/edge fixture；
- 生成 DOCX 无修复提示；
- 通过 OpenXML validation；
- 在目标 Word/WPS/LibreOffice 环境留存证据；
- 有来源、许可证、学校版本和维护者；
- 有 CHANGELOG；
- 有已知限制；
- 有迁移策略；
- 在六域测试目录中可追踪。
