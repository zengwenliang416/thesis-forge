# Architecture

## 1. 分层

```text
Input → Parser → ThesisDocument → Validator → Compiler → RenderPlan → Renderer
```

## 2. Parser

职责：

- 读取 YAML Front Matter
- 解析 Markdown 基础结构
- 识别 ThesisForge 扩展块
- 识别 `@fig:* / @tbl:* / @eq:* / [@bibkey]`
- 保留 source line
- 产出 `ThesisDocument`

不负责学校字体、Word 样式、最终编号与 OOXML。

## 3. ThesisDocument

```text
ThesisDocument
├── Metadata
├── Block[]
│   ├── Heading
│   ├── Paragraph
│   ├── Figure
│   ├── Table
│   ├── Equation
│   ├── Algorithm
│   └── Listing
└── BibliographyConfig
```

## 4. Validator

- Structural：标题层级、必需章节、重复 ID
- Reference：交叉引用目标、图片路径、BibTeX key
- Template：必需样式、配置字段合法性

## 5. Compiler

Compiler 把语义对象转成可渲染 `RenderPlan`。

```text
Figure(id=fig:model)
   ↓
ResolvedFigure(number="3-2", bookmark="tf_fig_model")
```

Parser 不计算编号。

## 6. DOCX Renderer

推荐两层：

```text
High-level: python-docx
Low-level:  lxml / OxmlElement
```

重点 Word Field：

- TOC → 自动目录
- SEQ → 图/表/公式编号
- REF → 交叉引用
- PAGE → 页码
- NUMPAGES → 总页数（模板需要时）

## 7. Formula

```text
LaTeX → Math representation → OMML → Editable Word Equation
```

禁止默认以 PNG 作为公式主实现。

## 8. Bibliography

```text
references.bib → Bibliography Loader → Citation Engine → Inline Citation + Bibliography
```

GB/T 7714-2025 必须做 golden tests。

## 9. UI

UI 不属于 Core。推荐后置 PySide6：Outline / Editor / Preview / Diagnostics / Template Selector / Export。

核心编译器必须可以纯 CLI 使用。
