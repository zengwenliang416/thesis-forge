# System Architecture & Database Spec

## Overview

ThesisForge 是本地优先、确定性、模板驱动的学术论文编译器。V1 的主链路是：

```text
Markdown -> ThesisDocument -> Validation -> Template -> Compiler -> RenderPlan -> DOCX
```

基础编译必须在无网络、无 API Key、无数据库和无 AI 服务时运行。Python CLI 保持独立
产品入口；可视化产品使用共享 Web 前端，并通过 Web 或 Tauri adapter 复用同一编译核心。

## Application Topology

- Frontend runtime: React + TypeScript + Vite；浏览器直接运行，macOS 与
  Windows 由 Tauri 2 包装同一构建产物。
- Backend runtime: Python 3.11+ application services。Web runtime 通过薄 HTTP
  adapter 调用；Tauri runtime 通过 command bridge 管理本地 Python sidecar。
- API gateway or edge layer: V1 无独立 gateway；HTTP adapter 使用版本化路由。
- Background workers: CLI 同步执行；Web/Tauri adapter 可在受控 worker/sidecar
  中执行长任务并发送阶段进度。
- External services: 核心链路无外部服务。CSL 数据或学校模板作为本地文件加载。
- Local development entrypoints: `thesisforge inspect`、`thesisforge validate`、
  `thesisforge build`、Vite dev server、Python Web adapter、Tauri dev shell。
- Production deployment shape: Python package/CLI、Web frontend + Python HTTP
  service、macOS/Windows Tauri package + bundled Python sidecar。

## Module Boundaries

### Core Domain

- Responsibility: 定义 `ThesisDocument`、语义块、引用对象、source location 与结构化 `ValidationIssue`。
- Public contract: `src/thesis_forge/core/model.py` 中的纯 Python domain types。
- Owned data: 解析后的论文语义、稳定 ID、引用与诊断。
- Dependencies: Python 标准库。
- Forbidden dependencies: `python-docx`、`lxml`、Renderer、UI、AI provider。
- Extension points: 新增语义块、inline 类型和 validation issue code。

### Parser

- Responsibility: 读取 YAML Front Matter、Markdown 基础结构、语义容器、交叉引用与引用。
- Public contract: `parse_markdown(path) -> ThesisDocument`。
- Owned data: 解析过程中的文本、行号和语法状态，不拥有最终编号。
- Dependencies: Core Domain、PyYAML。
- Forbidden dependencies: Template、Compiler、Renderer、`docx`、`lxml`、AI。
- Extension points: 新 Markdown 语法必须同步更新 `docs/MARKDOWN_SPEC.md` 与 parser tests。

### Validator

- Responsibility: 执行结构、引用、资源、模板和文献校验，返回 `ValidationIssue[]`。
- Public contract: `validate_document(...)` 及后续可组合 validator rules。
- Owned data: 无持久状态；仅产生确定性诊断。
- Dependencies: Core Domain、Template/Bibliography 的只读接口。
- Forbidden dependencies: Rich/CLI 输出、DOCX Renderer、网络和 AI。
- Extension points: duplicate ID、missing reference/image/citation、heading rules、required metadata/style rules。

### Template Model

- Responsibility: 把学校 YAML 渲染规则校验为强类型 Template Model。
- Public contract: `load_template(path) -> ThesisTemplate`。
- Owned data: 页面、字体、段落、标题、图表、公式、引用、section 与页眉页脚规则。
- Dependencies: Pydantic、PyYAML。
- Forbidden dependencies: 论文内容、Parser 状态、DOCX 实现对象。
- Extension points: 新模板字段必须同步更新 `docs/TEMPLATE_SPEC.md`、model 与 tests。

### Compiler and RenderPlan

- Responsibility: 统一计算编号、bookmark、引用解析和模板绑定，并产出 renderer-neutral `RenderPlan`。
- Public contract: `compile_document(...) -> RenderPlan`。
- Owned data: resolved numbering、stable bookmark names、render instructions。
- Dependencies: Core Domain、Template Model、Bibliography interface。
- Forbidden dependencies: `python-docx`、`lxml`、CLI/UI。
- Extension points: figure/table/equation/algorithm/listing/citation/section render nodes。

### DOCX Renderer

- Responsibility: 将 `RenderPlan` 渲染为真实 DOCX/OOXML 对象。
- Public contract: `DocxRenderer.render(plan, output) -> Path`。
- Owned data: 临时 `docx.Document` 与 OOXML package parts。
- Dependencies: RenderPlan、python-docx、lxml。
- Forbidden dependencies: Markdown Parser、AI provider、学校规则硬编码。
- Extension points: TOC、SEQ、REF、Bookmark、OMML、Footnote、Section、Header/Footer、PAGE。

### Bibliography

- Responsibility: 加载 BibTeX、校验 citation key、格式化 inline citation 与 bibliography。
- Public contract: `BibliographyEngine`。
- Owned data: 本地 bibliography records 与 deterministic citation ordering。
- Dependencies: Core Domain；可选 citeproc-py/CSL。
- Forbidden dependencies: UI、网络服务、DOCX internals。
- Extension points: GB/T 7714-2025 golden cases 与其他本地 CSL styles。

### CLI, Frontend Adapters, and AI

- Responsibility: CLI 编排核心用例；Web/Tauri adapters 调用同一 application
  services；React frontend 负责交互与展示；AI 仅提供可选辅助。
- Public contract: `thesisforge inspect|validate|build`、版本化 transport DTO、
  Web HTTP endpoints、Tauri commands。
- Owned data: 命令参数、序列化请求响应、client workspace state 和用户可见输出，
  不拥有 domain truth。
- Dependencies: Core application APIs。
- Forbidden dependencies: UI 或 AI 反向进入 Parser/Domain/Compiler；AI 成为 build 必需依赖。
- Extension points: Web/Tauri transport adapters 与
  `src/thesis_forge/ai/` providers。

## Frontend Architecture

- Routing: 单工作台路由；后续页面必须保持可部署的 browser history/base path。
- Rendering mode: Vite SPA；Tauri WebView 复用同一构建。
- State management: TypeScript workspace store 拥有 dirty、selection、operation
  token、diagnostics、preview 与 progress；domain truth 仍由 Python 返回。
- Form handling: React 表单只生成 typed command DTO。
- Data fetching: `WorkbenchTransport`；Web 使用 HTTP，Tauri 使用 command bridge。
- Error handling: Domain 返回稳定 code/target/line；adapter 序列化，frontend
  负责中文展示与恢复动作。
- Design system source: `openspec/specs/ui-design/design.md`。

## Backend Architecture

- API style: 进程内 Python function contracts 为核心；外层提供版本化 HTTP 和
  sidecar RPC/command adapter。
- Request validation: CLI/transport DTO 校验、workspace boundary、Parser、
  Template Model 与 Validator 分层负责。
- Auth/session model: 无账号、认证或会话。
- Domain service boundaries: Parser、Validator、Template、Compiler、Bibliography、Renderer。
- Background jobs: adapter 内受控任务；无持久队列。
- File/object storage: 本地 Markdown、YAML、BibTeX、图片和 DOCX。
- Observability: CLI exit code、结构化 `ValidationIssue`、测试与可选 debug logs；不得依赖云端遥测。

## API Surface

| Route or RPC | Owner | Input | Output | Auth | Side Effects |
| --- | --- | --- | --- | --- | --- |
| `parse_markdown` | Parser | Markdown file path | `ThesisDocument` | none | local file read |
| `validate_document` | Validator | `ThesisDocument` plus local context | `ValidationIssue[]` | none | none |
| `load_template` | Template Model | YAML file path | `ThesisTemplate` | none | local file read |
| `compile_document` | Compiler | document, template, bibliography context | `RenderPlan` | none | none |
| `DocxRenderer.render` | DOCX Renderer | render plan and output path | output path | none | creates/replaces requested DOCX |
| CLI `inspect` | CLI | source path | JSON-like structure on stdout | none | local file read |
| CLI `validate` | CLI | source path and template context | diagnostics and exit code | none | local file read |
| CLI `build` | CLI | source, template, output options | DOCX path and exit code | none | local file reads and DOCX write |
| HTTP `/api/v1/inspect` | Web adapter | workspace/source DTO | serialized inspection | deployment policy | adapter-scoped reads |
| HTTP `/api/v1/validate` | Web adapter | workspace/template DTO | serialized diagnostics | deployment policy | adapter-scoped reads |
| HTTP `/api/v1/build` | Web adapter | workspace/template/output DTO | progress plus downloadable DOCX | deployment policy | temporary build/output |
| Tauri commands | Desktop adapter | versioned workbench DTO | same serialized contracts | local user | local dialogs, sidecar, files |

## Database Model

V1 不使用数据库。领域对象只存在于单次编译内存中，持久化来源是用户管理的本地文件。

| Entity | Purpose | Owner | Fields | Relationships | Indexes | Constraints | Lifecycle | Migration | Retention/Deletion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| None | No database persistence in V1 | local file owner | not applicable | not applicable | not applicable | deterministic file contracts | process lifetime | file format versioning only | user controls source/output deletion |

## Permissions & Security

- User roles: CLI/Tauri 为单机当前用户；Web V1 不定义多租户角色。
- Permission checks: 依赖操作系统或 browser workspace 权限；CLI/Tauri 不提升权限。
- Data isolation: desktop 不上传论文内容；Web 仅发送到用户明确配置的
  ThesisForge HTTP endpoint。
- Secret handling: 核心不读取 API Key；可选 AI provider 的 secret 不进入论文、模板、日志或仓库。
- Audit logging: V1 仅记录本地命令结果和可重复验证证据，不建立远程审计。
- Abuse cases: path traversal、模板引用越界、恶意图片/OOXML、超大输入和 zip/XML bomb 需在对应读取边界防护。

## Integration Boundaries

- Third-party APIs: 核心无；Web/Tauri adapter 是产品自有边界；未来 AI 仅在
  `src/thesis_forge/ai/`。
- Webhooks: 无。
- Queues: 无。
- Email/SMS/push: 无。
- Payments: 无。
- Analytics: 核心无远程 analytics。
- Local libraries: PyYAML、Pydantic、python-docx、lxml、Typer、Rich；frontend
  使用 React、TypeScript、Vite，desktop 使用 Tauri 2。HTTP framework 仅允许
  位于 adapter 层。
- Office compatibility: 输出需通过 OOXML 结构测试，并至少在 Word/WPS/LibreOffice 一种目标环境人工验证。

## Operational Constraints

- Performance constraints: 普通本科论文应在单机内存中完成；实现不得为每个 block 启动外部进程。
- Availability expectations: 本地命令可在离线状态运行，不依赖远程可用性。
- Migration rules: Markdown/template schema 变更必须文档化并保留兼容或提供明确迁移。
- Backup/restore: 用户负责源文件版本管理；构建产物可从源文件确定性重建。
- Feature flag rules: 核心行为不使用远程 feature flag。
- Rollback constraints: 每个里程碑保持可测试；不得通过删除用户源文件回滚。
- Build reproducibility: 同一输入、模板和依赖版本应生成语义等价的 OOXML。

## Architecture Do's and Don'ts

- Do preserve `Parser -> ThesisDocument -> Validator -> Compiler -> RenderPlan -> Renderer`.
- Do keep school rules in Template Model and user problems in `ValidationIssue`.
- Do implement advanced Word behavior as true OOXML objects.
- Do keep all core commands offline and deterministic.
- Do keep one React frontend and runtime-specific transport adapters.
- Do keep transport DTOs versioned and free of Python/OOXML implementation objects.
- Don't let Parser import `docx`, `lxml`, Template, Renderer, UI, or AI.
- Don't put Word implementation objects in `core/model.py`.
- Don't hard-code school fonts, margins, numbering, or section policy in Renderer business logic.
- Don't introduce a database, account system, or AI dependency for V1 core.
- Don't let HTTP/Tauri adapters become a second compiler or leak into Core.
