# Architecture

## 1. 分层

```text
CLI / Future UI
      ↓
Application Services
      ↓
Parser → ThesisDocument → Validator → Compiler → RenderPlan → DOCX Renderer
```

`application` 层统一 inspect、validate、build、进度阶段、临时输出、DOCX package
校验和原子替换。CLI 只负责参数、结构化展示和退出码；未来 UI 复用相同服务。

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

V1 已将 Field、Bookmark、OMML、Footnote、Section、Header/Footer、Figure、
Table 和 package validation 分离到 focused helpers。Parser、Domain Model 和
RenderPlan 不包含 python-docx、lxml 或 OOXML 对象。

## 7. Formula

```text
LaTeX → Math representation → OMML → Editable Word Equation
```

禁止默认以 PNG 作为公式主实现。

## 8. Bibliography

```text
references.bib → Bibliography Loader → Citation Engine → Inline Citation + Bibliography
```

V1 使用受 golden tests 约束的本地 GB/T 7714-2025 子集，不依赖网络或
`citeproc-py`。citation ordinal 和 referenced-only bibliography 顺序由 Compiler
统一解析，Renderer 只输出已编译文本。

## 9. UI

UI 不属于 Core。产品前端使用 React + TypeScript + Vite，同一构建支持 Web，并由
Tauri 2 包装为 macOS / Windows 应用。前端只依赖版本化 `WorkbenchTransport` 与
JSON DTO：Web 使用 HTTP adapter，桌面使用 Tauri command bridge 和托管 Python
sidecar，二者最终调用相同的 application services。

Parser、Validator、Compiler、编号和 DOCX Renderer 不得在前端复制。核心编译器必须
可以在没有 Node.js、Rust、Tauri 和 HTTP server 时纯 CLI 使用。

## 10. 安全构建与发行

```text
parse → validate → compile → render temporary DOCX
      → package validation → atomic replace
```

任一阶段失败时不得覆盖已有有效输出。wheel 将内置模板放在
`thesis_forge/template_data/`，Template Resolver 优先使用论文最近祖先目录的
`templates/`，不存在项目模板树时才使用包内模板。发行验证必须从仓库外安装 wheel
并运行离线 inspect、validate、build，具体命令见 `docs/MAINTENANCE.md`。
