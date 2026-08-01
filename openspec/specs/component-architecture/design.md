# Component Architecture & Reuse Spec

## Overview

ThesisForge 同时包含 Python domain/application/rendering components 和共享
React frontend components。核心以纯领域模型和 `RenderPlan` 隔离 Markdown、学校模板
与 OOXML；Web/Tauri adapters 必须复用核心服务。

## Component Taxonomy

- Page/screen components: React Workbench、Outline、Editor、Preview、
  Diagnostics、Template Selector、Build。
- Layout components: shared application shell、resizable panel layout、
  responsive mobile views。
- Domain components: `ThesisDocument`、Block/Inline types、`ValidationIssue`。
- Form components: V1 核心无；未来 template/build options forms。
- Data display components: CLI inspect output、diagnostics table；未来 outline/diagnostics/preview views。
- Feedback components: CLI exit code 与 Rich diagnostics；未来 progress、toast、error panel。
- Headless hooks: TypeScript workspace store、transport hooks、Python application
  services；不在页面内复制 parser/build state。
- Domain utilities/services: Parser、Validator rules、Template loader、Compiler、numbering/bookmark resolver、Bibliography、DOCX field/OMML helpers。

## Cohesion Rules

- 每个模块只有一个主要变化原因。
- Parser 只负责 syntax-to-domain，不计算最终编号、不应用学校样式、不写 DOCX。
- Validator rules 只产生 `ValidationIssue`，不打印 UI 文本、不修复用户输入。
- Compiler 只解析语义与模板为 `RenderPlan`，不创建 `docx.Document`。
- Renderer 只消费 `RenderPlan`，不重新解析 Markdown 或决定学校业务规则。
- OOXML helper 按 field、bookmark、OMML、section、header/footer 等能力拆分，避免单个 renderer 文件无限增长。

## Coupling Rules

- `core/model.py` 仅依赖标准库。
- Parser 可依赖 Core Domain 和 YAML parser，不得依赖 Template/Compiler/Renderer/UI/AI。
- Validator 可依赖 Domain 和只读 contract，不得依赖 CLI/Rich 或 DOCX internals。
- Compiler 可依赖 Domain、Template、Bibliography interface 和 RenderPlan。
- DOCX Renderer 可依赖 RenderPlan、python-docx、lxml，不得依赖 Parser。
- CLI/Web/Tauri/AI 仅向内调用 application contracts；Core 不反向 import adapters。
- React components only depend on frontend state, shared DTOs, and
  `WorkbenchTransport`; they do not call HTTP/Tauri/Python directly.
- Shared modules must not import feature-specific UI or command modules.

## Shared Component Extraction Rules

- 同一 validation rule 或 formatting conversion 出现第二次时提取为共享 utility/rule。
- Web/Tauri 出现第二份相同 DTO、diagnostic mapping、preview mapping、operation
  token 或 capability logic 时提取为 shared frontend module。
- 同一 OOXML field/bookmark creation logic 被两种 node 使用时提取 helper。
- 编号、bookmark naming、unit parsing、font application 和 XML namespace 操作必须有单一实现。
- Parser container handling 保持按语义类型可扩展，避免在 CLI/Renderer 复制 syntax logic。
- 只有稳定的重复行为才提取公共 abstraction；一次性里程碑代码不提前建立框架。

## Component Public API Rules

- Public APIs 接收 domain/model values 或明确 command DTO，不暴露 renderer 私有 XML node。
- Functions 返回值必须可测试；错误使用 typed exception 或 `ValidationIssue`，不依赖 stdout。
- `RenderPlan` payload 最终应由 typed render node/fields 取代无约束 dict，迁移期间保持兼容。
- Service names 表达用户或 domain intent，例如 `compile_document`、`resolve_references`，不暴露 DOM/OOXML 偶然细节。
- 新 API 默认保持向后兼容；breaking contract 需要更新 OpenSpec、docs 和 tests。

## State Ownership Rules

- Local state: 单次 parser/compiler/renderer invocation 的临时状态。
- Shared UI state: TypeScript workspace store 持有，不进入 Core Domain。
- Server/cache state: adapter 仅允许 request/operation scope，无 domain persistence。
- Form state: React feature/form component 持有或提升到 workspace store。
- URL state: 无。
- Derived state: ID index、chapter counters、resolved numbers、bookmark map、citation order、RenderPlan。
- Persistent state: 用户本地 source/template/bibliography/assets 与显式 output。

## Composition Patterns

- Preferred composition patterns: pure function pipeline、small services、typed dataclasses/Pydantic models、dependency injection for template/bibliography/render backends。
- Forbidden composition patterns: parser-to-docx direct call、global mutable counters、renderer hard-coded school profiles、AI callback inside core build。
- Approved provider/context boundaries: CLI 或 transport adapter 构造 build
  context，并显式传入 template/bibliography resolver。
- Approved headless hook patterns: frontend store 可订阅 progress events，但不可
  拥有另一套 compiler。

## File & Naming Conventions

- Component file naming: Python `snake_case.py`；React components 使用
  `PascalCase.tsx`，hooks 使用 `use*.ts`，transport/DTO 使用明确 capability 名。
- Hook naming: Python application hooks 使用 `on_<event>` 或明确 protocol；
  React hooks 遵循 `use*`，不得隐藏 transport side effects。
- Test naming: `tests/test_<capability>.py`；OOXML tests 命名中包含 field/bookmark/omml/section 等被验证结构。
- Story/prototype naming: UI 阶段使用与稳定 flow/feature ID 对应的名称。
- Barrel/export rules: `__init__.py` 只导出稳定 public APIs，不导出 XML/private helpers。

## Testing Expectations

- Shared component tests: 每个 domain/service/helper 的行为测试，当前 tests 目录作为基础。
- Hook tests: progress/cancellation hooks 验证顺序、取消、stale result 和 cleanup。
- Integration tests: Markdown -> ThesisDocument -> Validation -> RenderPlan -> DOCX。
- Accessibility checks: browser、macOS 和 Windows 的键盘、焦点、对比度与
  screen-reader labels 必测。
- Visual/prototype review: 仅在 UI milestone；核心 DOCX 采用 OOXML structure tests 加 Word/WPS/LibreOffice 人工检查。
- Parser coverage: Front Matter、Heading、Figure、Table、Equation、Citation、CrossReference、Algorithm、Listing。
- Validator coverage: duplicate ID、missing reference/image/citation、heading jump、template/metadata rules。
- Renderer coverage: 文件 smoke test 之外必须检查真实 TOC/SEQ/REF/Bookmark/OMML/Section/Header/Footer/PAGE XML。

## Refactor Triggers

- Duplicate logic detected: 第二处相同规则出现即评估提取。
- Cross-boundary import detected: Parser/Domain import renderer、UI 或 AI 时立即阻断。
- Props become data-source-specific: public API 暴露 raw OOXML 或 CLI/Rich objects 时重构。
- Component grows multiple responsibilities: renderer 同时编号、校验、模板解析与 XML 写入时拆分。
- Test setup requires unrelated modules: unit test 需启动 UI/网络/AI 才能测试 core 时修复边界。
- Untyped payload growth: `RenderNode.payload` key 依赖扩散到多个模块时迁移 typed nodes。

## Component Do's and Don'ts

- Do keep Core Domain free of Word implementation details.
- Do centralize numbering, bookmarks, units, fonts, citations, and OOXML field helpers.
- Do reuse the same application services from CLI and future UI.
- Do reuse one React component tree and one DTO contract across Web and Tauri.
- Do add focused tests when a semantic object or OOXML capability is introduced.
- Don't duplicate parser, validator, compiler, or render logic in adapters.
- Don't expose raw `docx`/`lxml` objects through domain public APIs.
- Don't expose Python objects or native-path assumptions through frontend DTOs.
- Don't create UI components before the V1 compiler core and end-to-end build are working.
