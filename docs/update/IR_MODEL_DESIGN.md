# ThesisForge IR 模型设计（Inline / Block / Region / Project）

> 状态：Design Draft（Phase 0 产出，待 ADR 评审）
> 日期：2026-08-15
> 关联决策：执行摘要第 3 项「模型分成 Normalized IR 和 Resolved IR：编号、引用、模板和字段解析集中到 Compiler」（`ThesisForge_优化计划_执行摘要.md`）
> 事实输入：`CURRENT_STATE_AUDIT.md`、`spikes/phase0/parser/REPORT.md`、`QUALITY_STRATEGY.md` §3.2、`RISK_REGISTER.md` R-003/R-018/R-029、`TEMPLATE_PACKAGE_SPEC_V2.md` §9、`MARKDOWN_SPEC.md`
> 关联代码：`src/thesis_forge/core/model.py`、`core/parser.py`、`core/compiler.py`、`core/render_plan.py`

## 1. 设计目标与原则

本文件定义 ThesisForge 的中间表示（IR）：四层对象模型（Inline / Block / Region / Project）、
Normalized IR 与 Resolved IR 的分工、SourceMap 机制，以及与现有实现的映射和迁移路径。

### 1.1 目标

- **G1 结构与样式分离**：IR 只承载论文结构与语义；字体、字号、页边距、行距等一律来自
  Template Model，IR 中不出现任何版式值（AGENTS.md §1.4）。
- **G2 IR 与 DOCX 解耦**：IR 中不得出现 `w:p`、`SEQ ... \* ARABIC`、`CT_P` 等 OOXML
  实现对象（AGENTS.md §1.2）；Word 字段语法是 renderer 层的私有细节。
- **G3 稳定 ID**：所有可被引用的对象携带 `<prefix>:<name>` 稳定 ID
  （`chap/sec/fig/tbl/eq/alg/lst`，见 `core/ids.py` 与 MARKDOWN_SPEC「Reserved IDs」）；
  编号由 Compiler 统一计算，Parser 阶段不产出最终编号。
- **G4 source span 全程贯通**：每个 IR 对象携带 `SourceSpan`（file/line/column/end）与
  origin chain；诊断必须能回到正确源文件与行列（R-003）。
- **G5 确定性**：同一输入产出逐字节一致的 IR JSON 序列化结果，支撑 contract snapshot
  与可复现构建（QUALITY_STRATEGY §3.2、D6）。

### 1.2 原则

- **P1 Parser 不算编号**：Normalized IR 中无「图 3-2 / 式（3-1）」、无引用序号、
  无书签、无模板绑定；这些全部属于 Resolved IR（MARKDOWN_SPEC 已声明此边界）。
- **P2 未知语法不静默降级**：现有 parser 把粗体/链接/顶层代码围栏静默吞入口袋段落
  （D-01，parser.py:379-384）。新模型中，后端能识别但 V1 不支持的语法必须产生结构化
  节点 + 诊断，不允许无声丢失。
- **P3 IR 是稳定 contract**：parser 后端（ADR-0001 选定 markdown-it-py + 自研插件）、
  validator、compiler、renderer 之间只通过 IR 交互；后端可替换，IR 契约不变。
  Contract snapshot 版本化，breaking change 必须显式声明（QUALITY_STRATEGY §3.2、R-029）。
- **P4 位置缺失可声明，不可伪造**：允许 `approx` 降级（块级仅行号），禁止返回错误
  文件或误导性行号（R-003 退路）。
- **P5 generated 节点必须显式标记**：TOC、封面、文献条目等编译期生成的内容与用户
  源码节点严格区分，便于诊断归属与审计。

## 2. 四层模型总览

```text
Project        多文件工程：manifest（显式顺序）、SourceFile、全局符号表
  └─ Region    文档结构单元：cover / abstract_zh / toc / main / bibliography / ...
       └─ Block    块级内容：Heading / Paragraph / List / Figure / Table / Equation / ...
            └─ Inline   行内内容：Text / Emphasis / Citation / CrossRef / Math / ...
```

包含关系是**逻辑视图**：物理上 `ProjectDocument.blocks` 是按 manifest 顺序拼接的扁平
元组（与现有 `ThesisDocument.blocks` 同构，迁移成本最低），Region 是叠加其上的区间
索引，Block 持有自己的 Inline 列表。所有节点共享两个公共字段：

```python
@dataclass(frozen=True, slots=True)
class IRNode:
    source: SourceSpan | None   # 源码位置；仅 generated 节点允许 None
    origin: Origin              # 来源链，见 §4.2
```

`SourceSpan` / `Origin` 的完整定义见 §4，此处各层伪代码省略继承声明。

### 2.1 Inline 层

行内对象不再区分「正文串 + 引用对象」两类存储（现有模型同时保留 `text` 与 `inlines`
两份事实源），**inlines 列表是唯一事实源**；需要纯文本处（标题投影、TOC 条目）通过
`plain_text(inlines)` 投影函数派生，不冗余存储。

```python
# ---- V1 支持（与 MARKDOWN_SPEC 对齐）----
@dataclass(frozen=True, slots=True)
class Text(InlineNode):
    value: str

@dataclass(frozen=True, slots=True)
class Citation(InlineNode):
    keys: tuple[str, ...]        # 多 key 拆分在 parser 完成
    locator: str | None
    raw: str                     # 原始源码文本，诊断与兜底渲染用

@dataclass(frozen=True, slots=True)
class CrossRef(InlineNode):
    target: str                  # 完整稳定 ID，如 "fig:model"
    kind: str                    # 由前缀派生：fig/tbl/eq/alg/lst/sec/chap，冗余存储便于校验

@dataclass(frozen=True, slots=True)
class FootnoteRef(InlineNode):
    label: str                   # 独立 footnote namespace（MARKDOWN_SPEC），不进交叉引用符号表

# ---- markdown-it 后端天然可得；V1 策略：解析进 IR + validator 报 unsupported-inline（P2）----
@dataclass(frozen=True, slots=True)
class Emphasis(InlineNode):
    children: tuple[InlineNode, ...]

@dataclass(frozen=True, slots=True)
class Strong(InlineNode):
    children: tuple[InlineNode, ...]

@dataclass(frozen=True, slots=True)
class CodeInline(InlineNode):
    value: str

@dataclass(frozen=True, slots=True)
class Link(InlineNode):
    href: str
    children: tuple[InlineNode, ...]

@dataclass(frozen=True, slots=True)
class MathInline(InlineNode):
    latex: str

# ---- 演进位（IR 预留、V1 任何后端均不产出；加入时需 contract minor 版本）----
# Strikethrough / Superscript / Subscript / Underline
# RawInline(format, value)   —— 受控原生片段，若启用必须隔离（R-009 退路同原则）
# ImageInline(src, alt)      —— 行内图片；V1 仅支持块级 Figure
```

设计要点：

- `CrossRef.kind` 由 parser 从前缀派生并冗余存储，使「fig: 引用指向 table」这类
  类型错配诊断（QUALITY_STRATEGY TF-D2-REF-004）不必重复解析 ID 字符串。
- Citation 在 Normalized IR 中只保存 keys/locator/raw；序号与格式化文本属于
  Resolved IR（§3）。
- Inline 行列位置是硬需求（现有 parser 已精确到列；spike 证实 markdown-it 自写
  inline rule 可经段内偏移 + 宿主 token `map` 换算列号），`SourceSpan` 行列齐全；
  仅当后端确无能力时按 P4 降级。

### 2.2 Block 层

```python
@dataclass(frozen=True, slots=True)
class BlockNode(IRNode):
    id: str | None               # 稳定 ID，可空（匿名段落、无 ID 标题等）

@dataclass(frozen=True, slots=True)
class Heading(BlockNode):
    level: int                   # 1..6
    inlines: tuple[InlineNode, ...]
    # 编号不入 IR：章号/节号由 Compiler 按模板策略计算

@dataclass(frozen=True, slots=True)
class Paragraph(BlockNode):
    inlines: tuple[InlineNode, ...]

@dataclass(frozen=True, slots=True)
class ListItem(IRNode):          # List 的子结构，不是独立 Block
    level: int                   # 缩进层级（两空格一级，与现行为一致）
    marker: str                  # 原始 marker，如 "-"、"3."
    ordinal: int | None          # 有序项的原始序号
    inlines: tuple[InlineNode, ...]

@dataclass(frozen=True, slots=True)
class ListBlock(BlockNode):
    ordered: bool
    start: int | None            # 起始序号（如 3）
    items: tuple[ListItem, ...]

@dataclass(frozen=True, slots=True)
class Figure(BlockNode):
    src: str                     # 源码原样相对路径；解析为绝对路径是 resolve 阶段职责
    caption: tuple[InlineNode, ...]   # caption 结构化（现实现仅 caption 内联提取，此处统一）
    width: str | None            # 源码原样，如 "85%"；合法性校验在 validator/resolve

@dataclass(frozen=True, slots=True)
class TableCell(IRNode):
    inlines: tuple[InlineNode, ...]
    alignment: Literal["left", "center", "right"] | None
    # 演进位（V2 StructuredTable，R-009）：colspan: int = 1; rowspan: int = 1; header_scope

@dataclass(frozen=True, slots=True)
class TableRow(IRNode):
    header: bool
    cells: tuple[TableCell, ...]

@dataclass(frozen=True, slots=True)
class Table(BlockNode):
    caption: tuple[InlineNode, ...]
    rows: tuple[TableRow, ...]
    # 不再持有 markdown 原文：表格结构化从 compiler 前移到 normalize（§5.2）

@dataclass(frozen=True, slots=True)
class Equation(BlockNode):
    latex: str                   # 已剥离外层 $$（现行为保留）
    display: bool = True         # 为行内数学区分预留

@dataclass(frozen=True, slots=True)
class Listing(BlockNode):
    caption: tuple[InlineNode, ...]
    language: str | None
    code: str

@dataclass(frozen=True, slots=True)
class Algorithm(BlockNode):
    caption: tuple[InlineNode, ...]
    body: str                    # V1 保留原文；结构化程度见开放问题 O-7

@dataclass(frozen=True, slots=True)
class FootnoteDef(BlockNode):
    label: str
    inlines: tuple[InlineNode, ...]   # 含续行合并结果

@dataclass(frozen=True, slots=True)
class BibliographyMarker(BlockNode):
    """::: bibliography 放置标记；只决定文献条目插入位置。"""

# ---- 演进位 ----
# BlockQuote(children)      —— 通用 Markdown 基础结构
# CodeBlock(code, language) —— 顶层 ``` 围栏（MARKDOWN_SPEC 暗示、现不支持）
# ThematicBreak
# RawBlock(format, value)   —— 受控原生块，默认禁用
```

设计要点：

- 现有 `Heading.text` / `Paragraph.text` 冗余串取消，统一走 `plain_text()` 投影
  （开放问题 O-5 记录取舍）。
- `Table` 的结构化（分隔行对齐、列数一致性）在 normalize 完成；现
  `TableCompilationError`（compiler.py:139）对应的失败转为 parse/normalize 期
  `Diagnostic`，单元格粒度位置受后端能力约束（见开放问题 O-4）。
- 块级位置：markdown-it 块 token `map=[start,end)` 仅行无列（spike §2.3），故
  Block 的 `SourceSpan` 允许列缺省 + `approx=True`；行内仍要求行列齐全。

### 2.3 Region 层

Region 是**文档结构单元**，与 Heading 有本质区别（TEMPLATE_PACKAGE_SPEC_V2 §9 已声明
「Region 与 Heading 不应混为一谈」）：

- 封面、声明页、目录等 Region 可能没有普通标题；
- `main` Region 横跨多个章标题；
- Region 的顺序、必备性与节策略由模板 `regions.order` 声明，属于校验与绑定对象，
  而非源码内容本身。

```python
RegionKind = Literal[
    "cover",
    "originality_statement",       # 原创性声明
    "authorization_statement",     # 授权声明
    "abstract_zh",
    "abstract_en",
    "toc",
    "main",
    "bibliography",
    "acknowledgements",
    "appendices",
    "achievements",                # 攻读学位期间成果
]

@dataclass(frozen=True, slots=True)
class Region(IRNode):
    kind: RegionKind
    heading_id: str | None       # 绑定的一级标题稳定 ID（如 chap:abstract-zh）；cover/toc 常为 None
    blocks: tuple[int, ...]      # 指向 ProjectDocument.blocks 的下标区间（overlay，非拥有）
    title: str | None            # Normalized 阶段取标题文本；Resolved 阶段模板可覆盖
```

Region 的产出分两步：

1. **Normalized 阶段（模板无关）**：按约定规则初步划分——一级标题的稳定 ID 命中
   约定集合（现行 `SEMANTIC_HEADING_ROLES` 的 `chap:abstract-zh`、`chap:toc`、
   `chap:bibliography`、`chap:acknowledgements` 等，compiler.py:77-98）即划定对应
   Region 起点；首个非前置一级标题起的内容为 `main`。此步骤把现有
   `_is_front_matter_heading()` / `_SemanticContext` 的隐式规则显式化为数据。
2. **Resolved 阶段（模板绑定）**：按模板 `regions.order` 校验必备 Region
   （`required: true` 缺失 → 诊断）、补全 title/style/section 绑定，并注入 generated
   Region 内容（封面字段、TOC 块，origin 标记见 §4.4）。

这样，Region 模型同时吸收了现有三处隐式逻辑：语义标题角色映射
（`SEMANTIC_HEADING_ROLES` / `SEMANTIC_BODY_ROLES`）、节切换规划（`_SectionPlanner`）、
前置内容判定（`_is_front_matter_heading`），并给模板留出显式声明入口。

### 2.4 Project 层

多文件 include 是 R-018 的核心对象。spike 结论：markdown-it `parse()` 只接受字符串，
include 必须由调用层递归/拼接并自行维护位置（spike §2.5）——因此 Project 层把
「文件清单与顺序」做成一等数据，而不是拼接字符串技巧。

```python
@dataclass(frozen=True, slots=True)
class ProjectManifest:
    root: str                    # 项目根（绝对路径，构建期解析）
    entry: str                   # 入口文件（root 相对，POSIX 风格）
    files: tuple[str, ...]       # 显式有序清单；禁止隐式无序 glob（R-018）
                                 # 若提供 glob 语法必须稳定排序并在 manifest 中固化结果

@dataclass(frozen=True, slots=True)
class SourceFile(IRNode):
    path: str                    # root 相对路径，SourceSpan.file 与之同源
    blocks: tuple[BlockNode, ...]
    metadata: dict[str, Any]     # 仅 entry 允许 front matter；非 entry 出现 → 诊断（见 O-2）

@dataclass(frozen=True, slots=True)
class SymbolEntry:
    id: str                      # 稳定 ID 或 footnote label
    kind: str                    # chap/sec/fig/tbl/eq/alg/lst/footnote
    file: str                    # 定义所在文件
    span: SourceSpan             # 定义点
    block_index: int             # 在 ProjectDocument.blocks 中的下标

@dataclass(frozen=True, slots=True)
class SymbolTable:
    entries: dict[str, SymbolEntry]      # 交叉引用命名空间，全局唯一
    footnotes: dict[str, SymbolEntry]    # footnote 独立 namespace（MARKDOWN_SPEC）

@dataclass(frozen=True, slots=True)
class ProjectDocument(IRNode):           # Normalized IR 的根
    ir_version: str                      # contract 版本，见 §3.4
    manifest: ProjectManifest
    files: tuple[SourceFile, ...]
    blocks: tuple[BlockNode, ...]        # 按 manifest.files 顺序拼接的全文视图
    regions: tuple[Region, ...]
    symbols: SymbolTable
    metadata: dict[str, Any]             # entry front matter
    bibliography: BibliographyConfig | None   # path + citation_style，原样保留
```

设计要点：

- **全局符号表**在 normalize 阶段构建：跨文件重复 ID 在此产出 `duplicate-id` 诊断
  （QUALITY_STRATEGY TF-D2-ID-001），引用查找、书签生成、编号遍历全部以符号表为
  入口，替代现有 `ThesisDocument.index_by_id()` + `register_inlines()` 的聚合机制。
- `blocks` 拼接顺序 = manifest 显式顺序，编号与引用序因此确定（R-018 关闭条件）。
- 单文件工程是 `files=(entry,)` 的退化情形，Alpha 只承诺该情形（R-018 退路）。

## 3. Normalized IR 与 Resolved IR

### 3.1 分工

| | Normalized IR | Resolved IR |
|---|---|---|
| 产出者 | Parser 后端 + normalize 阶段 | Compiler（resolve 阶段） |
| 编号 | **无**（无「图 3-2」、无引用序号、无脚注号） | 全部计算完毕 |
| 引用 | 未解析：`CrossRef.target` 只是字符串 | 已解析：书签、显示文本、类型核对 |
| 模板 | 无关（IR 中无模板值） | 已绑定：numbering 模式、caption 前缀、样式角色、节策略 |
| 资源路径 | 源码原样（相对路径） | 已解析绝对路径 + 边界校验结果 |
| 生成内容 | 无 | cover/toc/文献条目等 generated 节点 |
| 字段 | 无 | 中性 `FieldRequest`（§3.3），**不含 Word 字段码** |
| 消费者 | Validator（模板无关规则）、contract snapshot | Renderer、模板相关校验、build report |

Normalized IR 等价于「parser 输出 + 多文件拼装 + 符号表 + 表格结构化」；
Resolved IR 等价于现有 `compile_document()` 的全部语义输出重新组织后的形式。

### 3.2 转换管线与校验点

```text
Markdown 文件组 + manifest
   │
   ▼ parse            （ParserBackend 协议；ADR-0001：markdown-it-py + 自研插件）
后端 token/AST
   │  校验点 P0：后端无关预检——未闭合 ::: 容器、front matter 非法、非法 ID 字面量
   │            （A/B 两路线诊断均需自建，spike §2.6；ParseError 语义保留）
   ▼ normalize        （token→IR 映射；逐文件解析；表格结构化；include 拼装；
Normalized IR           全局符号表；Region 初步划分）
   │  校验点 V1（模板无关，现 validator 规则归位）：
   │    duplicate-id（跨文件，符号表）、invalid-id-prefix、missing-image、
   │    resource-path-escape、heading-level-jump、required-metadata、
   │    empty-document、unsupported-inline（P2，替代静默降级）、
   │    表格结构（分隔行/列数，原 TableCompilationError 诊断化）
   │  Contract snapshot：Normalized IR JSON（QUALITY_STRATEGY §3.2）
   ▼ resolve           （Compiler：编号/书签/引用/文献/脚注/Region 绑定/节计划/字段计划）
Resolved IR
   │  校验点 V2（模板相关）：
   │    missing-reference / UnresolvedCitation / UnresolvedFootnote、
   │    BookmarkCollision、模板必备 Region 缺失、模板样式缺失、
   │    figure width 合法性（模板默认值合并后）
   │  Contract snapshot：Resolved IR JSON
   ▼ render            （DOCX renderer；FieldRequest → 真实 OOXML 字段在此翻译）
DOCX
```

### 3.3 Resolved IR 的字段级草案

```python
@dataclass(frozen=True, slots=True)
class Numbering:
    chapter: int
    number: str | None           # "3-2"；numbering.mode=none 时 None
    label: str                   # "图 3-2" / "(3-1)" / caption 原文

@dataclass(frozen=True, slots=True)
class FieldRequest(IRNode):
    """renderer-neutral 字段请求；Word 字段码由 renderer 翻译（§5.3）。"""
    kind: Literal["seq", "ref", "pageref", "toc", "page", "numpages"]
    identifier: str | None       # SEQ 序列名（如 TF_Figure_1）或书签名
    pinned_result: str | None    # cached result；SEQ 钉值取舍（D-08）在此显式建模
    number_format: str | None    # arabic / lowerRoman / ...（中性枚举）
    switches: tuple[str, ...] = ()   # 中性开关，renderer 负责映射为 \h \z \u 等

@dataclass(frozen=True, slots=True)
class ResolvedBlock:
    block: BlockNode             # 不可变复用 Normalized 节点，span 天然保留（§4.2 R2）
    numbering: Numbering | None
    bookmark: str | None         # tf_ 前缀 + 40 字符截断规则不变
    style_role: str | None       # 现 ParagraphRole 的泛化（body/abstract.zh.title/...）
    sequence: FieldRequest | None

@dataclass(frozen=True, slots=True)
class ResolvedReference:
    target_id: str
    bookmark: str
    display: str                 # 显示文本（label 或 target id 兜底，现行为保留）
    ref_field: FieldRequest      # kind="ref"
    source: SourceSpan | None    # 引用点位置（现模型缺失，诊断需要）

@dataclass(frozen=True, slots=True)
class ResolvedCitation:
    keys: tuple[str, ...]
    ordinals: tuple[int, ...]
    locator: str | None
    text: str                    # 经 CitationProvider 格式化的文内引用文本
    source: SourceSpan | None

@dataclass(frozen=True, slots=True)
class ResolvedRegion:
    region: Region
    title: str                   # 模板覆盖后的最终标题
    section_role: str | None     # cover / front_matter / main（v2 演进：back_matter）
    generated_blocks: tuple[BlockNode, ...]   # 封面字段块、TOC 块等，origin=generated

@dataclass(frozen=True, slots=True)
class SectionPlanEntry:
    role: str
    before_block_index: int      # 在全文 blocks 视图中的插入点

@dataclass(frozen=True, slots=True)
class ResolvedDocument(IRNode):
    ir_version: str
    normalized: ProjectDocument
    template_id: str | None
    template_snapshot_hash: str | None   # 可复现性审计（D6）
    blocks: tuple[ResolvedBlock, ...]
    references: dict[str, ResolvedReference]
    citations: tuple[ResolvedCitation, ...]
    citation_order: tuple[str, ...]
    footnote_ids: dict[str, int]
    regions: tuple[ResolvedRegion, ...]
    sections: tuple[SectionPlanEntry, ...]
    fields: tuple[FieldRequest, ...]
    bibliography_entries: tuple[BibliographyEntry, ...]   # generated，origin 指向 citation keys
```

「Parser 阶段不计算最终编号」的落实方式从约定升级为**类型系统保证**：
Normalized IR 的类定义中不存在 number/bookmark/ordinal 字段，任何在后端或
normalize 阶段计算编号的代码无处可写。

### 3.4 序列化与 contract 版本

- 两档 IR 均可序列化为确定性 JSON（键排序、元组转数组、路径一律 root 相对 POSIX）。
- 文档级 `ir_version`（如 `"1.0"`）遵循 R-029：Alpha 前标记 experimental，Beta 冻结，
  breaking change 提升 major 并写 deprecation 说明。
- Contract snapshot 进入 `qa/baselines/`，修改必须声明是否 breaking
  （QUALITY_STRATEGY §3.2）。

## 4. SourceMap 设计

### 4.1 SourceSpan

```python
@dataclass(frozen=True, slots=True)
class SourceSpan:
    file: str                    # 项目 root 相对路径（POSIX 分隔符）；多文件歧义由此消除
    start_line: int              # 1-based
    start_column: int | None     # 1-based；None = 后端无列能力
    end_line: int | None
    end_column: int | None
    approx: bool = False         # True = 位置降级（如块级仅行号），展示须标注「位置近似」
```

对照现状：`SourceLocation(line, column)` 无 file、无 end、无 approx；块级 column 恒
None（D-02，parser.py:195/257/326）。新结构把「不知道列」与「列是 1」在类型上区分开，
把「降级」从隐式现状变成显式标记（P4）。

### 4.2 Origin chain 保留规则

```python
@dataclass(frozen=True, slots=True)
class Origin:
    kind: Literal["source", "generated"]
    generator: str | None = None       # generated 时必填，如 "compiler.toc"
    parents: tuple[str, ...] = ()      # 直接母体节点 ID（符号表可查回定义点 span）
```

变换规则（对应 R-003 预防措施）：

- **R1 parse → normalize**：节点 `origin.kind="source"`，span 取自后端 token；
  后端只有行号时 `start_column=None, approx=True`。
- **R2 normalize → resolve**：resolve **不以新节点替换源节点**，而是以
  `ResolvedBlock.block` 引用 Normalized 节点（§3.3），源 span 结构性保留，零拷贝。
- **R3 必须新建节点**（TOC 条目、封面字段、文献条目、编号文本）：`kind="generated"`，
  `generator` 记录产出阶段，`parents` 指向来源对象（文献条目的 parents 为对应
  citation keys），`source` 取主要母体 span 或 None。**禁止**给 generated 节点编造
  源码 span。
- **R4 任何阶段不得改写已有节点的 span**；派生位置只允许追加 `approx=True` 的新节点。
- **R5 诊断引用位置时优先取节点自身 span，generated 节点回溯 parents 链**；
  链穷尽仍无位置则 `span=None` 并标注诊断为项目级，禁止猜测（R-003 退路）。

### 4.3 多文件 include 的映射

- 每个文件**独立解析**，`SourceSpan.file` 记录该文件的 root 相对路径，行列为文件内
  坐标——不做跨文件行号偏移换算。spike 证实 markdown-it 路线要求调用层自行维护
  include（§2.5）；「逐文件解析 + file 字段消歧」从模型上消除偏移维护出错的可能。
- `ProjectDocument.blocks` 拼接视图只提供**下标**（`block_index`），不提供拼接后的
  全局行号；任何需要源码位置的地方必须经 `SymbolEntry.file/span` 或节点自身 span
  回到具体文件，杜绝「错误文件/误导性行号」（R-003 红线）。
- pandoc 路线的 `data-pos="file@行:列-行:列"`（spike §2.3）与本结构一一对应，
  后端替换时 SourceMap 语义不变（P3）。

### 4.4 generated 节点策略

| generated 内容 | generator | parents | source span |
|---|---|---|---|
| TOC 块/条目 | `compiler.toc` | 各章/节 Heading ID | None（或首个标题 span + approx） |
| 封面字段块 | `compiler.cover` | entry 文件 front matter | front matter span + approx |
| 文献条目 | `compiler.bibliography` | 对应 citation keys 的定义/引用点 | .bib 记录位置（有 BibTeX 行号时） |
| 编号文本 run | `compiler.numbering` | 被编号块 ID | 被编号块 span |
| Region 补全块 | `compiler.regions` | 模板 region 声明 | None（模板侧位置，见 O-6） |

generated 节点参与 Resolved IR 的全部下游流程（渲染、快照），但在诊断归属上永远
经 parents 回溯，不向用户报告不存在的位置。

### 4.5 诊断携带 span（ValidationIssue → JSON/SARIF）

```python
@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str                         # 稳定规则码（duplicate-id 等），契约一部分
    severity: Literal["info", "warning", "error"]
    message: str
    span: SourceSpan | None           # 仅项目级诊断允许 None
    target: str | None                # 相关稳定 ID（沿用现字段语义）
    related: tuple[SourceSpan, ...] = ()   # 多位置诊断：如 duplicate-id 的两处定义
    suggestion: str | None = None     # 修复建议（QUALITY_STRATEGY D2 覆盖项）
    details: dict[str, str | int] = field(default_factory=dict)
```

- 现有 `ValidationIssue.line` 由 `span` 取代；迁移期 adapter 保留 `line` 供 CLI 兼容。
- JSON 输出（`thesisforge validate --format json` / `inspect`）随 `api_version` 版本化。
- SARIF 2.1.0 映射：`code→ruleId`，`severity→level`，`span.file→artifactLocation.uri`，
  `start_line/column→region.startLine/startColumn`，`related→relatedLocations`，
  `approx=True` 在 message 追加「（位置近似）」并在 `region.properties` 落
  `"approx": true`（QUALITY_STRATEGY TF-D2-DIAG-022 的验收形态）。

## 5. 与现有实现的映射

### 5.1 model.py → 新模型

| 现有（`core/model.py`） | 新模型 | 变化 |
|---|---|---|
| `SourceLocation(line, column)` | `SourceSpan` + `Origin` | 更名 + 扩展：补 file/end/approx；从节点字段拆出 origin |
| `Inline.location` | `InlineNode.source/.origin` | 字段更名，语义增强 |
| `Text` | `inline.Text` | 平移 |
| `CrossReference(target)` | `inline.CrossRef(target, kind)` | 更名；kind 冗余派生 |
| `Citation(keys, locator, raw)` | `inline.Citation` | 平移 |
| `FootnoteReference(label)` | `inline.FootnoteRef` | 更名对齐 `FootnoteDef` |
| （无） | `inline.Emphasis/Strong/CodeInline/Link/MathInline` | 新增：markdown-it 后端可得，V1 策略 = 解析 + 诊断（P2） |
| `Block.id/.location` | `BlockNode.id/.source/.origin` | 平移 + 扩展 |
| `Heading(level, text, inlines)` | `block.Heading(level, inlines)` | 去 text 冗余，走 plain_text 投影（O-5） |
| `Paragraph(text, inlines)` | `block.Paragraph(inlines)` | 同上 |
| `ListItem`（独立 dataclass） | `block.ListItem`（List 子结构，加 source/origin） | 结构化归位 |
| `ListBlock` | `block.ListBlock` | 平移 |
| `Figure(src, caption: str, width)` | `block.Figure(src, caption: inlines, width)` | caption 结构化 |
| `Table(caption, markdown)` | `block.Table(caption: inlines, rows)` | **拆分**：markdown 结构化前移到 normalize；原文不再入 IR |
| `Equation(latex)` | `block.Equation(latex, display)` | 平移 + display 预留 |
| `Listing` / `Algorithm` | 同名 | 平移（Algorithm.body 结构化程度见 O-7） |
| `FootnoteDefinition` | `block.FootnoteDef` | 更名 |
| `BibliographyBlock` | `block.BibliographyMarker` | 更名（语义即放置标记） |
| （无） | `block.BlockQuote/CodeBlock/...` | 演进位，V1 不产出 |
| `BibliographyConfig` | Project 层同名字段 | 归位 ProjectDocument |
| `ThesisDocument` | **拆分**为 `SourceFile` + `ProjectDocument` | 单文件退化为 files=(entry,) |
| `ThesisDocument.index_by_id()/register_inlines()` | `SymbolTable` + normalize 索引器 | 机制保留，位置迁移，跨文件化 |
| （无） | `Region` / `ProjectManifest` | 新增层 |
| `ValidationIssue` | `Diagnostic` | line→span，新增 related/suggestion |

### 5.2 compiler.py 职责归位

| 现有（`core/compiler.py`） | 归位 | 说明 |
|---|---|---|
| `_resolve_blocks()`（编号/章绑定/书签） | resolve：NumberingPass + BookmarkPass | `_ResolvedBlock` 概念升级为 `ResolvedBlock`；`tf_` 前缀/40 字符截断/BookmarkCollisionError 语义不变 |
| `_sequence_instruction()` | resolve：FieldPlanPass | 产出中性 `FieldRequest`；字段码拼装移出（§5.3） |
| `_compile_inlines()` | resolve：ReferencePass + CitationPass + FootnotePass | Unresolved*Error 转为带 span 的 Diagnostic 或 compile error（策略见 O-8） |
| `_initial_citation_numbers()`（含脚注展开顺序） | resolve：CitationPass | 首次出现编号语义不变，输入从 `document.citations` 聚合改为符号表 + blocks 遍历 |
| `_footnote_ids()` | resolve：FootnotePass | 平移 |
| `_SectionPlanner` / `_SemanticContext` / `_is_front_matter_heading()` / `SEMANTIC_*_ROLES` | normalize 末段（Region 初步划分）+ resolve：RegionPass | 隐式 ID 约定显式化为 Region 数据（§2.3）；节计划输出 `SectionPlanEntry` |
| `_compile_cover()` | resolve：RegionPass | 产出 generated 封面块（§4.4）；11 个固定字段的扩展性归 Template Package v2 跟踪 |
| `_compile_table_rows()` / `_split_table_row()` / `_separator_alignment()` | **normalize**（表格结构化） | `TableCompilationError` 诊断化，进 V1 校验点 |
| `_resolved_figure_width()` | resolve（模板默认值合并） | 现有 `origin="source"/"template"` 雏形泛化为值级 provenance |
| `_resolve_figure_asset()` | resolve（资源解析） | 与 validator 的 resource-path-escape 共用路径策略 |
| `compile_document()` | `resolve(project, template) -> ResolvedDocument` | 签名演进；RenderPlan 作为迁移期 lowering 产物保留（§6.2） |

### 5.3 RenderPlan 的 SEQ 字段码泄漏收敛

现状：`SequenceInstruction.field_code`（render_plan.py:166-167）在 renderer-neutral
层直接拼出 `SEQ TF_Figure_1 \r 2 \* ARABIC`（D-03）。收敛方案：

1. Resolved IR 只携带 `FieldRequest(kind="seq", identifier="TF_Figure_1",
   pinned_result="2", number_format="arabic")`（§3.3），**不出现字段码字符串**。
2. Word 字段语法翻译集中在 `renderers/docx/fields.py`：`FieldRequest` →
   `SEQ {identifier} \r {pinned_result} \* ARABIC`；TOC/REF/PAGE/NUMPAGES 同理。
   renderer 成为唯一知道 `\r`、`\h`、`\* ARABIC` 等开关的层。
3. SEQ `\r` 钉值（D-08，确定性取舍）从隐藏实现细节升级为 `FieldRequest.pinned_result`
   的显式语义：pinned 即「Word 端不重排，以缓存值为准」，该取舍写入
   `docs/MARKDOWN_SPEC.md` 或字段规范，build report 记录字段状态（R-006 预防措施）。
4. 迁移期 `SequenceInstruction` 保留但 `field_code` 标记 deprecated，renderer 改为
   消费 FieldRequest 后删除该属性。

## 6. 演进路径（与 ADR-0001 配合）

### 6.1 IR 作为稳定 contract，后端可替换

ADR-0001 选定 markdown-it-py + 自研插件（容器、crossref、citation 三条自写规则），
并以 ParserBackend 协议隔离后端。IR 设计使该决策落地为：

```python
class ParserBackend(Protocol):
    name: str
    def capabilities(self) -> BackendCapabilities: ...
        # 声明可产出的节点种类与位置粒度（如 inline 列号、表格单元格位置）
    def parse_file(self, text: str, *, path: str) -> SourceFile: ...
        # 单文件、模板无关、无编号；产出 Normalized IR 的 SourceFile
```

- 后端产出的节点集合允许是 IR 超集的不同子集；`capabilities()` 使 contract 测试可按
  能力参数化（spike 问题清单第 1/4/7 条的验收口径）。
- spike 问题清单第 10 条（`parse_markdown_text()` 公共契约冻结）由本协议 + IR
  schema 共同回答：冻结面从「函数签名」升级为「Normalized IR contract」。
- 项目专属语法（`::: kind {#id}` 容器、`@fig:x`、`[@k, p. 12]`）由自写插件产出，
  位置换算（段内偏移 + 宿主 token map）在后端内部完成，IR 层无感知。

### 6.2 分阶段迁移步骤

每阶段保持 `thesisforge build/validate/inspect` 全绿、`pytest` 通过；旧结构经
adapter 过渡，不做大爆炸重写。

- **Phase 1 — IR 包与 adapter**：新建 `core/ir/`（四层模型、SourceSpan/Origin、
  JSON 序列化、`ir_version`）；现有 `model.py` 不动，新增 model↔IR 双向 adapter；
  建立 Normalized IR contract snapshot（`qa/baselines/`）。Validator 输出经 adapter
  补 span 雏形（file=source_path）。
- **Phase 2 — ParserBackend 协议落地**：现有手写 parser 包装为 `legacy` 后端；
  markdown-it 后端接入并产出同一 Normalized IR；full-syntax fixture 双后端 diff
  门禁（位置粒度差异只允许表现为 `approx` 标记差异）；Project 层实现 manifest +
  逐文件解析 + 符号表（多文件 include 在此落地，R-018）。
- **Phase 3 — Compiler/Validator 切换**：compiler 改为消费 Normalized IR、产出
  Resolved IR；Region 模型吸收 `_SectionPlanner`/`_SemanticContext`；表格结构化前移；
  `field_code` 下移至 `renderers/docx/fields.py`；validator 迁移到 `Diagnostic`
  （span/related/suggestion），JSON/SARIF 输出定型；Resolved IR contract snapshot 建立。
  RenderPlan 在此期间作为 Resolved IR → 现有 13 种 instruction 的 lowering 保留，
  renderer 零改动。
- **Phase 4 — 收敛与冻结**：删除 `legacy` 后端与旧 `model.py`（或冻结为只读兼容
  adapter）；评估 RenderPlan lowering 是否并入 renderer 前端；IR contract 随 Beta
  冻结（R-029），后续变更走版本化与 deprecation 流程。

## 7. 开放问题清单（留给 ADR 或后续 Phase）

- **O-1 Region 的显式语法**：Region 边界继续靠约定 ID（`chap:abstract-zh` 等）+
  模板 `regions.order` 推导，还是引入显式标记（如 front matter 声明或 `::: region`）？
  附录（appendices）内编号重启（TF-D2-NUM-010）与 Region 的绑定规则需一并回答。
  → 建议 ADR-0002。
- **O-2 include 的表面语法**：独立 manifest 文件 vs entry front matter 内
  `files:` 清单；非 entry 文件出现 front matter 的处理（拒绝/忽略+诊断）；
  与 `resource-path-escape` 资源边界的交互。
- **O-3 块级列号**：接受 markdown-it 块级仅行号 + `approx=True`（R-003 退路），
  还是为块起点补列（需插件补丁，spike §2.3 估算 0.5–1 人日）？验收标准由哪个
  测试域钉死（D1 source map assertions）？
- **O-4 表格单元格位置粒度**：列数不一致等表格诊断定位到行是否可接受？
  （pandoc 路线 Table 子树全盲；markdown-it 路线行级。）
- **O-5 Heading/Paragraph 的纯文本投影**：`plain_text(inlines)` 派生是否覆盖全部
  现有消费点（validator、TOC 生成、书签显示文本）？性能与缓存策略。
- **O-6 模板侧 SourceSpan**：模板缺样式/必备 Region 缺失等诊断指向模板文件位置时，
  YAML 的 span 是否需要（模板 schema 已有 lint 规划，TEMPLATE_PACKAGE_SPEC_V2）？
- **O-7 Algorithm.body 结构化**：保留原文字符串 vs 解析为 ListBlock；对
  caption/body 内 inline（citation 参与编号顺序，现 `_initial_citation_numbers`
  会展开容器内 inline）的行为一致性要求。
- **O-8 编译期错误的诊断化边界**：Unresolved*Error / BookmarkCollisionError 等
  现在是异常（compiler.py）；Resolved IR 阶段是统一转 `Diagnostic`（severity=error，
  build 退出码 1）还是保留快速失败异常？与 CLI 退出码契约（0/1/2）的对齐。
- **O-9 文献条目的 span**：`.bib` 记录行号（现 bibtex.py 已有行号定位）是否纳入
  SourceSpan.file 体系（即 span 可指向非 Markdown 文件）？倾向「是」，需确认
  SARIF 输出与前端展示。
- **O-10 Inline 演进位的启用顺序**：Emphasis/Strong 等节点 V1 以诊断拒绝；哪一档
  release 放行、放行时 contract 版本如何步进（minor vs major）？
