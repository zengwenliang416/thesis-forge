## Why

ThesisForge 当前只有可开发骨架：基础 Parser、Validator、Template Model 与 DOCX smoke
renderer 尚不能生成学校标准、可交叉引用、可继续编辑的完整论文。现在需要按既定架构补齐
V1 核心，使 Markdown 到 DOCX 的全链路可离线、确定性地运行和验证。

## What Changes

- 完成 ThesisForge Markdown 语义解析与稳定 ID/domain model。
- 扩展结构、资源、引用、文献和模板校验，并保持结构化 diagnostics。
- 完成学校 YAML Template Model 与模板解析/校验。
- 将 Compiler/RenderPlan 扩展为统一编号、bookmark、reference、citation 和 section 解析层。
- 将 DOCX smoke renderer 扩展为模板驱动的正文、标题、图、三线表、公式和高级 Word 对象渲染器。
- 实现真实 TOC、SEQ、REF、Bookmark、OMML、Footnote、Section、Header/Footer 和 PAGE fields。
- 实现本地 BibTeX、citation key validation、inline citation、bibliography 与 GB/T 7714-2025 接口。
- 完成离线 inspect/validate/build CLI 和完整端到端示例。
- 提供 review-only HTML 工作台原型，用于评审未来桌面 UI 的结构、状态和响应式行为。
- 增加行为测试、OOXML 结构测试、失败保护与 Office 客户端人工验证证据。
- 保持 UI、AI、数据库、Web API、账号系统和云服务不进入 V1 核心。

## Capabilities

### New Capabilities

- `thesis-markdown-model`: Markdown、Front Matter、semantic containers、stable IDs、source locations、citations 和 cross-references 到 `ThesisDocument` 的行为合同。
- `validation-template-resolution`: 结构化校验、资源/引用/文献检查、学校 YAML Template Model 与模板解析行为。
- `render-plan-docx`: Compiler 编号/引用解析、typed RenderPlan，以及模板驱动 DOCX/OOXML 渲染行为。
- `bibliography-citations`: 本地 BibTeX、citation key validation、inline citation、bibliography 和 GB/T 7714-2025 输出行为。
- `offline-cli-pipeline`: inspect、validate、build 的离线端到端行为、exit codes、原子输出和失败保护。

### Modified Capabilities

None. The repository has no pre-existing capability `spec.md` contracts; the
four project foundation specs remain authoritative architecture constraints.

## Impact

- Affected code: `src/thesis_forge/core/`, `templates/`, `renderers/docx/`,
  `bibliography/`, `cli.py`, examples and tests；评审原型仅位于 change 的 `prototype/`。
- Public contracts: Parser、Validator、Template loader、Compiler/RenderPlan、
  BibliographyEngine、DocxRenderer 与三个 CLI commands。
- Dependencies: 保持当前 Python/Pydantic/PyYAML/python-docx/lxml/Typer/Rich；
  citeproc-py 作为 bibliography 可选依赖候选。
- Storage and services: 仅本地文件，无数据库、HTTP API、账号、网络或必需 AI。
- Compatibility: 保留既有最小 API，并通过增量 typed contracts 避免 Domain 暴露 Word 对象。
