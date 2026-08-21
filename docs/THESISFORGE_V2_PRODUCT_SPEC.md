# ThesisForge v2 Product and Engineering Specification

**Status:** Normative target contract  
**Change type:** Intentional breaking reset  
**Compatibility:** Old ThesisForge Markdown is not supported and no automatic migration is provided  
**Primary implementation driver:** `LOOP.md`  
**Task catalogue:** `docs/THESISFORGE_V2_IMPLEMENTATION_PLAN.md`

## 1. Final product statement

ThesisForge v2 is an offline-first, project-based academic thesis compiler. A project has one mandatory `thesisforge.yaml`, one readable Markdown source, declared resources, and one school template. The project compiles through a single typed and lossless pipeline into:

1. a clean content Review;
2. a technical Structure view;
3. a structurally valid DOCX and optional final-layout PDF preview;
4. a typed BuildReport for every build attempt.

The system must never silently discard or flatten supported semantics. Unsupported and legacy input must produce stable structured diagnostics.

## 2. Product decisions

### 2.1 Breaking reset

The v2 implementation deliberately does not preserve the old source format.

The following are invalid:

- opening or compiling a bare thesis `.md` file;
- YAML Front Matter in `thesis.md`;
- legacy `::: figure`, `::: table`, `::: equation`, `::: listing`, `::: algorithm`, or `::: bibliography` containers;
- legacy `@fig:id`, `@tbl:id`, `@eq:id`, `@sec:id`, `@chap:id`, `@lst:id`, or `@alg:id` cross-reference syntax;
- Markdown-side layout keys such as figure width;
- hidden fallback to the old parser;
- automatic old-format migration;
- dual old/new protocol responses.

Invalid legacy input returns a stable diagnostic such as `TF-SOURCE-LEGACY-001` with a concrete replacement example.

### 2.2 One source of truth per responsibility

| Responsibility | Source of truth |
|---|---|
| Project entry and schema version | `thesisforge.yaml` |
| Author, institution, degree, dates, title | `thesisforge.yaml` |
| Resource roots and bibliography | `thesisforge.yaml` |
| Template selection | `thesisforge.yaml` |
| Object-level layout overrides | `thesisforge.yaml` |
| Readable prose and content order | `thesis.md` |
| Stable semantic IDs | `thesis.md` adjacent to the target object |
| Citations, cross-references, footnotes | `thesis.md` |
| School page, font, style, section and numbering policy | template contract |
| Reader-facing content review | generated Review projection |
| Technical IDs, source spans and diagnostics | Structure projection |
| Final editable document | generated DOCX |
| Build status, diagnostics and logs | BuildReport |

Do not represent the same semantic value as both `text` and `inlines`, both raw Markdown and structured rows, both raw and resolved layout, or both manually maintained document caches and traversable AST nodes.

## 3. Non-goals

The v2 Goal excludes:

- LaTeX import;
- DOCX to Markdown round-trip;
- automatic old-source migration;
- AI thesis writing or rewriting;
- cloud collaboration;
- account systems;
- template marketplace;
- Word or WPS add-ins;
- arbitrary TeX macro execution;
- pixel-identical output across office suites;
- unrelated visual redesign;
- multi-user review comments unless separately approved after v2.

## 4. Repository project format

A thesis project is a directory containing:

```text
my-thesis/
├── thesisforge.yaml
├── thesis.md
├── references.bib
├── assets/
│   └── model.png
├── build/
└── review/
```

The accepted application input is either:

```text
/path/to/my-thesis
```

or:

```text
/path/to/my-thesis/thesisforge.yaml
```

A bare `/path/to/my-thesis/thesis.md` is rejected.

## 5. `thesisforge.yaml` contract

### 5.1 Example

```yaml
schema: thesisforge.project.v2

project:
  id: example-thesis
  language: zh-CN

document:
  source: thesis.md

metadata:
  title:
    zh: 基于示例系统的研究
    en: Research on an Example System
  author:
    name: 张三
    student_id: "20260001"
  institution:
    university: 示例大学
    college: 计算机学院
  degree:
    name: 工学硕士
    major: 计算机科学与技术
  advisor:
    name: 李教授
    title: 教授
  dates:
    completed: "2026-05"

resources:
  root: .
  assets: assets
  bibliography: references.bib

render:
  template_id: example-university-2026
  citation_style: gbt7714-numeric

layout:
  objects:
    fig:model:
      width: 85%

output:
  directory: build
  docx: thesis.docx
  retain_last_successful_preview: true

review:
  directory: review
  markdown: thesis.review.md
  source_map: thesis.review-map.json
```

### 5.2 Required properties

- `schema` equals `thesisforge.project.v2`;
- `document.source` is a project-relative Markdown path;
- required metadata is validated against the selected template;
- `resources` paths are project-relative and may not escape the project root;
- `render.template_id` selects a known template;
- unknown fields are rejected unless a future version explicitly defines an extension namespace;
- object override keys must resolve to existing semantic object IDs of the expected type;
- orphan overrides are errors, not warnings;
- duplicate YAML keys are rejected;
- aliases or constructs that create unsafe or surprising object graphs are rejected or bounded.

### 5.3 Path security

Project loading must reject:

- `..` traversal outside project root;
- absolute resource paths unless an explicit future security policy allows them;
- symlink escape;
- remote URLs in local resource fields;
- excessive recursive resolution;
- files larger than configured resource limits;
- unexpected executable or macro-enabled output relationships.

Errors include the source field, attempted target and safe project root without leaking unrelated machine paths to Review.

## 6. Thesis Markdown v2

### 6.1 Design principle

The raw source should remain readable in ordinary Markdown tools. Custom syntax is limited to stable academic semantics that standard Markdown cannot express reliably.

### 6.2 Example

````markdown
# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

已有研究表明，**结构化编译**能够提升文档一致性 [@smith2025]。
项目入口使用 `thesisforge.yaml`，详细流程见[图](#fig:model)。

![模型总体结构](assets/model.png){#fig:model}

损失函数定义如下：

$$
L=-\sum_{i=1}^{N} y_i \log \hat y_i
$$
{#eq:loss}

其计算方式见[式](#eq:loss)。

| 指标 | 实验组 | 对照组 |
|---|---:|---:|
| 准确率 | 96.2% | 91.8% |
| 召回率 | 94.1% | 89.6% |

: 模型实验结果 {#tbl:experiment}

结果汇总见[表](#tbl:experiment)。

```python {#lst:training title="训练代码"}
for epoch in range(epochs):
    train_one_epoch()
```

```algorithm {#alg:training title="训练流程"}
输入：训练集 D
输出：模型 M
1. 初始化参数
2. 迭代优化
```

这里包含一个说明性脚注[^scope]。

[^scope]: Review 中显示脚注号和正文，DOCX 中生成原生脚注。

# 参考文献 {#region:bibliography}
````

### 6.3 Supported source constructs

#### Inline

- plain text;
- soft break;
- hard break;
- strong;
- emphasis;
- inline code;
- standard links;
- inline math;
- citation clusters such as `[@smith2025; @doe2024, p. 12]`;
- internal semantic links such as `[图](#fig:model)`;
- footnote references;
- superscript and subscript if included in the capability registry.

#### Blocks

- ATX headings with optional stable ID;
- paragraphs;
- ordered and unordered nested lists;
- blockquotes;
- fenced code blocks;
- standard images with stable figure ID;
- GFM-style tables followed by a caption line and stable table ID;
- display math followed by a stable equation ID;
- listing fences with ID and title attributes;
- algorithm fences with ID and title attributes;
- footnote definitions;
- semantic region headings/IDs for bibliography, acknowledgements, appendices and achievements;
- an explicit TOC placeholder only if the final grammar requires user placement; otherwise TOC position is manifest/template-owned. The implementation must choose one mechanism and reject duplicates.

### 6.4 Cross-reference contract

A Markdown link whose destination matches a semantic ID becomes a CrossReference rather than a normal hyperlink:

```markdown
[图](#fig:model)
[表](#tbl:experiment)
[式](#eq:loss)
[本节](#sec:background)
```

The link label is readable fallback text. Resolved Review and DOCX use the target type and template numbering policy, for example `图 2-1` or `式（3-2）`.

Broken targets, type mismatches and duplicate IDs are errors with source spans.

### 6.5 Soft and hard breaks

- ordinary source newline inside a paragraph becomes a SoftBreak and must not create a Word manual break;
- two trailing spaces plus newline or backslash plus newline becomes a HardBreak and may create `w:br`;
- a blank line ends the paragraph.

### 6.6 Legacy rejection

The parser preflight explicitly detects old Front Matter and old `:::` thesis containers before general Markdown parsing. It returns one or more structured diagnostics and does not flatten legacy syntax into normal prose.

## 7. Target typed document model

The exact implementation may evolve, but these invariants are mandatory.

### 7.1 Identity and source mapping

Every semantic node has:

```python
NodeId
SourceSpan(
    source_file,
    start_line,
    start_column,
    end_line,
    end_column,
)
```

Generated nodes use a typed `GeneratedOrigin` and may refer back to one or more source nodes.

### 7.2 Inline model

At minimum:

```text
Text
SoftBreak
HardBreak
Strong(children)
Emphasis(children)
InlineCode
Link(label, destination)
InlineMath
Citation
CrossReference(target, fallback, display_mode)
FootnoteReference
```

Rich containers own `tuple[Inline, ...]` or nested blocks. They do not own a duplicate plain-text field as source of truth.

### 7.3 Block model

At minimum:

```text
Heading
Paragraph
OrderedList
BulletList
ListItem
BlockQuote
CodeBlock
Figure
StructuredTable
Equation
Listing
Algorithm
FootnoteDefinition
SemanticRegion
TocPlaceholder, only if explicitly selected by the grammar
```

Table cells contain typed inline or block content, not a pipe-delimited string.

### 7.4 Document index

Citation, cross-reference, footnote and ID indexes are derived from the immutable AST by a `DocumentIndex` builder. The parser does not maintain synchronized duplicate caches.

Duplicate public IDs are errors and may never be overwritten by dictionary construction.

## 8. Compilation architecture

```text
Project Loader
    ↓
Source Parser
    ↓
Normalized Typed ThesisDocument
    ↓
DocumentIndex and Resource Resolution
    ↓
Semantic Validation and Compile Preflight
    ↓
Resolved ThesisDocument / Symbol Table
    ↓
Typed RenderPlan
    ↓
DOCX Renderer
    ↓
DOCX Package Postflight
    ↓
Optional Office Finalization / PDF Preview
    ↓
BuildReport
```

### 8.1 Dependency boundaries

- Domain/parser code does not import `python-docx`, lxml OOXML helpers, office automation or UI code.
- Application use cases depend on ports/protocols rather than concrete template, bibliography, renderer or office implementations.
- Concrete dependencies are assembled in one bootstrap/composition root.
- Renderer consumes typed instructions and does not parse Markdown, split raw tables, resolve references, decide numbering, or infer semantic regions.
- Word field codes are generated in the DOCX infrastructure layer, not stored as domain strings.

### 8.2 Typed RenderPlan

Production `RenderPlan.nodes` accepts typed instructions only.

Remove:

- `RenderNode(kind, payload)`;
- `Instruction.payload` compatibility dictionaries;
- `to_render_node()`;
- `_render_legacy()`;
- unknown-node debug output such as `[kind] {payload}`.

Unknown instructions are internal errors and fail explicitly.

## 9. Review, Structure and Final Layout

### 9.1 Review

Review is for authors, supervisors and content auditors.

It must:

- omit Front Matter and configuration;
- hide stable IDs;
- hide citation keys;
- hide cross-reference targets;
- hide original local/absolute resource paths;
- render or meaningfully display math;
- show formatted citations;
- show resolved figure, table and equation numbering;
- show figures and tables as readable content;
- show listing and algorithm content;
- show footnote numbers and definitions;
- preserve headings, lists, emphasis, links and code;
- attach source navigation metadata without exposing it in the visible prose;
- remain available as a partial Review when localized validation errors exist;
- show unresolved content as explicit reader-facing problems, not raw compiler syntax;
- exempt literal code content from marker-leak scanning.

### 9.2 Structure

Structure is for technical inspection.

It may display:

- node type;
- stable semantic ID;
- source file and SourceSpan;
- resource resolution state;
- diagnostic codes;
- numbering/symbol information;
- template region and style token;
- original formula source.

### 9.3 Final Layout

Final Layout uses the latest successful DOCX/PDF finalization result. It checks school layout, pagination, headers, footers, table flow and actual office-suite rendering.

### 9.4 Failed-build preview retention

When the latest build fails:

- retain the last successful preview;
- overlay or display a clear stale banner;
- identify the failed build and failed stage;
- provide a direct action to open the primary error;
- never present the stale preview as the current source result.

### 9.5 Review export

CLI and desktop may export:

```text
review/thesis.review.md
review/thesis.review-map.json
```

The Markdown is generated and read-only. It must state its source and generated nature. It may use sanitized project-relative asset links, but must not contain absolute machine paths, raw IDs, raw citation keys or legacy containers.

The source map relates generated blocks to source NodeId and SourceSpan. Review output is not a second editable truth.

## 10. BuildReport v2

Every build attempt—manual publish or live preview—must end with one typed report.

The normative machine schema is:

```text
protocol/build-report.v2.schema.json
```

### 10.1 Required report information

- schema version;
- build ID;
- intent: `publish` or `live-preview`;
- outcome: `succeeded`, `failed`, or `canceled`;
- timestamps where available;
- lifecycle status for every build stage;
- failed stage or null;
- all structured diagnostics;
- primary diagnostic ID or null;
- bounded, sanitized logs;
- output artifact information or null;
- whether displayed preview is stale;
- last successful build ID when relevant.

### 10.2 Stage states

Stages are at least:

```text
parse
validate
compile
render
finalize
postflight
preview
```

Each stage is one of:

```text
pending
running
succeeded
failed
skipped
```

Receiving a “stage started” event never marks it succeeded.

### 10.3 Diagnostics

A diagnostic includes:

- stable ID;
- severity;
- category;
- stable code;
- stage;
- localized or presentation-ready message;
- source location or null;
- target or null;
- suggestion or null;
- related locations;
- optional structured details.

Validation failures preserve every original issue, its order and details. Non-validation exceptions become stable stage-specific diagnostics instead of untyped strings.

### 10.4 Logs

Logs are:

- ordered;
- stage-associated;
- bounded in entry count and message size;
- sanitized for secrets and irrelevant absolute paths;
- copyable from the UI;
- never the only representation of a known structured error.

### 10.5 Build event stream

Recommended terminal protocol:

```text
stage(started/succeeded/failed/skipped)
diagnostic
audit-safe log
completed(BuildReport)
```

The terminal event is always `completed` with a BuildReport, including failures and cancellation.

## 11. Build error experience

The desktop interface follows the proven editor/compiler pattern used by tools such as Overleaf without copying its visual design.

### 11.1 Entry point

The Build button shows an error badge after failure, for example:

```text
构建 DOCX  ● 3
```

The badge opens Build Output and focuses the first primary error.

### 11.2 Build Output panel

Provide tabs or filters:

```text
All
Errors
Warnings
Raw logs
```

The panel displays stage status, diagnostic count, primary error and output/stale-preview state.

### 11.3 Error card

Each error card includes:

- severity and stable code;
- concise message;
- source file, line and column where available;
- stage;
- target/context;
- suggestion;
- related locations;
- actions: locate source, copy error, view logs.

The first/highest-priority error is expanded by default. Later cascading errors remain accessible but do not overwhelm the user.

### 11.4 Manual versus live-preview failure

Manual build failure:

- opens Build Output;
- selects Errors;
- expands primary diagnostic;
- may navigate on explicit user action;
- preserves stale preview.

Live-preview failure:

- updates report, badge and stale state;
- does not repeatedly steal focus or switch panels while typing;
- keeps the editor usable;
- opens detail only on user action.

### 11.5 Source navigation

Clicking a diagnostic focuses the editor and selects or positions at its SourceSpan. The active diagnostic remains visibly selected.

## 12. CLI contracts

The final CLI supports project input only.

```bash
thesisforge inspect ./my-thesis
thesisforge validate ./my-thesis
thesisforge review ./my-thesis --output-dir ./my-thesis/review
thesisforge build ./my-thesis -o ./my-thesis/build/thesis.docx
```

A machine-readable option is required for automated verification, for example:

```bash
thesisforge validate ./my-thesis --json
thesisforge build ./my-thesis -o /tmp/thesis.docx --report-json /tmp/build-report.json
```

Exact option names may differ only if this specification, goal verifier and examples are updated in the same explicitly authorized verification-surface task.

CLI requirements:

- exit `0` on successful operation;
- distinguish user/project errors from internal/environment errors;
- emit stable diagnostic codes;
- reject bare Markdown and legacy input explicitly;
- work offline;
- generate BuildReport JSON for build attempts;
- do not require desktop transport.

## 13. Desktop contracts

The desktop application:

- opens a project directory or `thesisforge.yaml`, not a standalone Markdown file;
- displays project identity and active source;
- edits the readable Markdown source;
- offers Review, Structure and Final Layout modes;
- displays Build Output with errors/warnings/logs;
- retains stale preview after failure;
- navigates diagnostics to source;
- uses the same application contracts as CLI;
- does not duplicate parsing, validation or numbering rules;
- distinguishes manual build from live preview;
- respects project path authorization and symlink boundaries.

## 14. Format capability closure

`spec/format-capabilities.yaml` is the complete list of promised v2 capabilities.

Every capability marked required must name:

- source representation;
- typed IR representation;
- validation/resolution responsibility;
- typed RenderPlan representation;
- Review behavior;
- DOCX behavior;
- automated evidence path.

CI/final goal verification must fail when:

- a typed Inline, Block or RenderInstruction has no registered capability/handler;
- a required capability lacks Review or DOCX evidence;
- an unsupported node is silently ignored;
- an object override targets a missing object;
- raw semantic markers reach normal Review or DOCX body text.

## 15. Validation and preflight contract

Formal invariant:

> If `validate` returns no error diagnostics for a project and environment-independent preflight, `build` may not later fail because of user source syntax, missing local resource, unsupported formula, invalid table, duplicate bookmark, unresolved reference, footnote graph, or template capability.

Validation phases:

```text
project/schema
source syntax
semantic structure
resource resolution
template compatibility
compile preflight
```

Compiler and Validator call shared pure parsers/probers for widths, tables, images, formulas, bookmark names and footnote/reference graphs.

Build may still fail for disk, permission, external office, operating-system or internal defects; those failures must produce typed diagnostics.

## 16. DOCX structural acceptance

DOCX success requires postflight validation of:

- valid ZIP/OPC package;
- content types;
- required parts;
- all XML well-formed;
- relationship IDs and targets;
- no missing media targets;
- no unexpected external relationships;
- existing style IDs;
- valid numbering IDs;
- bookmark start/end pairs and unique names;
- field begin/separate/end structure;
- expected `TOC`, `SEQ`, `REF`, `PAGEREF`, `PAGE`, and `NUMPAGES` behavior;
- footnote references and `footnotes.xml` consistency;
- OMML for supported equations;
- valid sections, headers and footers;
- no unresolved citation/cross-reference markers in normal body content;
- no debug placeholder text.

Microsoft Word desktop is the authority for manual release acceptance. WPS is a high-priority compatibility target. LibreOffice may be used for automated preview but is not proof of complete Word compatibility.

## 17. Error and diagnostic taxonomy

Use stable families such as:

```text
TF-PROJECT-*     manifest/project loading
TF-SOURCE-*      Markdown syntax and legacy rejection
TF-SEMANTIC-*    IDs, regions and structure
TF-REFERENCE-*   citation, cross-reference and footnote
TF-RESOURCE-*    images, bibliography and paths
TF-TEMPLATE-*    template and style compatibility
TF-COMPILE-*     preflight/compiler
TF-DOCX-*        rendering and package postflight
TF-OFFICE-*      Word/LibreOffice/WPS finalization
TF-TRANSPORT-*   sidecar and desktop transport
TF-INTERNAL-*    invariant violations
```

Messages are presentation concerns. Core data uses code plus typed parameters and SourceSpan.

## 18. Security requirements

At minimum test:

- path traversal;
- symlink escape;
- absolute paths;
- remote resource attempts;
- malformed/duplicate-key YAML;
- oversized images and source files;
- deeply nested Markdown;
- excessive include/recursion if introduced;
- dangerous external DOCX relationships;
- temporary file cleanup;
- log redaction;
- output authorization;
- cancellation cleanup;
- ZIP/package abuse in template packages;
- no AI/network dependency in core workflow.

## 19. Test strategy

### 19.1 Unit

- project schema and path policy;
- parser nodes and SourceSpan;
- DocumentIndex;
- diagnostic conversion;
- stage lifecycle;
- Review serialization;
- capability registry;
- DOCX field/bookmark/relationship helpers.

### 19.2 Contract

- BuildReport JSON Schema examples;
- backend event to frontend type parity;
- CLI exit codes and JSON output;
- every capability handler present;
- validate-build invariant;
- marker-leak prevention.

### 19.3 Integration

- full v2 fixture inspect/validate/review/build;
- legacy fixture rejection;
- missing asset failure;
- unresolved reference failure;
- Office/finalizer failure report;
- stale-preview retention.

### 19.4 E2E

- desktop opens project;
- edits and saves source;
- manual build succeeds;
- manual build fails and opens Build Output;
- live preview fails without stealing focus;
- clicking an error navigates source;
- last successful preview remains with stale banner;
- Review hides markers;
- Final Layout returns after recovery.

## 20. Definition of Done for the overall Goal

The Goal is complete only when:

1. `LOOP.md` has no Open or Blocked items;
2. `./stop-check.sh` exits `0`;
3. only one production parser remains;
4. project manifest is mandatory across CLI and desktop;
5. old Front Matter and `:::` source are explicitly rejected;
6. no old/new dual source-of-truth fields remain;
7. every build attempt produces a typed BuildReport;
8. manual errors are visibly discoverable and source-navigable;
9. live-preview errors do not steal focus;
10. stale successful preview is retained and clearly marked;
11. Review hides technical markers while preserving content;
12. all registered capabilities have end-to-end evidence;
13. unknown semantics fail explicitly;
14. RenderPlan is typed-only and legacy fallback is removed;
15. validate-build preflight contract is demonstrated;
16. v2 fixture builds a structurally valid DOCX;
17. legacy fixture is rejected with stable diagnostics;
18. security/path tests pass;
19. full repository verification passes;
20. remote PR, merge and release remain human decisions.
