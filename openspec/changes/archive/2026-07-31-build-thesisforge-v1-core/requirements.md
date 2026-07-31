# Requirements: build-thesisforge-v1-core

## Summary

实现 ThesisForge V1 的确定性、离线优先、模板驱动论文编译核心，使用户能够用
Markdown、学校 YAML 模板、本地图片和 BibTeX 数据生成结构正确、可继续编辑的 DOCX。
核心流水线必须保持：

```text
Markdown -> ThesisDocument -> Validation -> Template -> Compiler -> RenderPlan -> DOCX
```

当前骨架已经证明 Parser、Validator、Template Model、Compiler/RenderPlan 和 DOCX smoke
output 的最小边界；本变更负责把这些边界补全到 V1 可用状态。

## Users & Actors

- 论文作者：维护 Markdown、图片和 BibTeX，运行 inspect、validate、build。
- 学校模板维护者：把学校版式规则维护在版本化 YAML Template Model 中。
- ThesisForge 开发者：扩展语义对象、validation rules、compiler 与 renderer。
- 文档审核者：在 Word、WPS 或 LibreOffice 中检查最终 DOCX。
- 可选 UI/AI adapter 开发者：未来通过稳定 application contracts 调用核心，不改变编译语义。

## In Scope

- YAML Front Matter、Heading、Paragraph、List、Figure、Table、Equation、Algorithm、Listing、Footnote、Citation 与 CrossReference 解析。
- 所有可引用语义对象使用稳定 ID；Parser 不计算最终图、表、公式编号。
- duplicate ID、missing reference/image/citation、heading jump、required metadata、template existence/schema/style coverage 等结构化校验。
- 学校 YAML 模板的页面、字体、字号、段落、标题、图表、公式、引用、section、页眉页脚和页码规则。
- Compiler 统一解析 chapter counters、编号、bookmark names、cross-reference targets、citation order 与 section policy。
- Renderer-neutral、可测试的 RenderPlan；Domain Model 不含 Word/OOXML implementation objects。
- DOCX 基础页面、正文、标题、分页、图片、三线表、题注、公式、目录、section、页眉页脚与页码。
- 真实 Bookmark、SEQ、REF、TOC、PAGE/NUMPAGES 与 OMML；不得用普通文本或图片伪造主要能力。
- 本地 BibTeX 加载、citation key validation、inline citation 与 bibliography 输出接口。
- GB/T 7714-2025 风格的确定性输出接口和 golden tests。
- `thesisforge inspect`、`thesisforge validate`、`thesisforge build` 的稳定 CLI 行为和 exit codes。
- 一个 review-only HTML 工作台原型，展示 Outline、Markdown Editor、Word Preview、Diagnostics、Template Selector 和 Build 状态。
- 端到端示例覆盖 cover、摘要、TOC、三级标题、图、三线表、公式、交叉引用、引用、参考文献、致谢和附录。
- OOXML package/XML 结构测试，以及 Word/WPS/LibreOffice 至少一种目标环境的人工检查记录。

## Out of Scope

- AI 自动写整篇论文或把 AI 服务放入编译依赖。
- 生产 PySide6 桌面 UI、真实编辑保存、实时 DOCX 渲染和 UI backend 集成。
- 暗色主题、主题切换、多语言运行时和 locale switcher。
- 云端账号、认证、数据库、Web API、多人协作、在线模板市场。
- Word/WPS 插件、在线文档同步、云存储和远程编译服务。
- 未经许可证审查复制参考仓库的大段实现。

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- 本变更无生产 UI，但必须交付可交互 HTML prototype 供界面与信息架构评审。
- CLI 输出保持简洁中文；domain error code 与 UI 文案解耦。
- 后续 UI 必须复用相同 Parser、Validator、Compiler 和 build services。
- 原型必须展示论文结构、编辑区、版式预览、诊断、模板选择和构建动作，并提供 populated、loading、empty、error、disabled、permission 状态。

## Theme & Locale Capability Impact

- Theme support: `light-only`，仅为未来 UI foundation 保留。
- Theme toggle policy: `none`，本变更不展示、不创建主题切换。
- Internationalization: `disabled`。
- Supported locales: `zh-CN`。
- Default locale: `zh-CN`。
- Prototype coverage: HTML 原型覆盖 desktop/mobile、light、`zh-CN`，且不展示主题或语言切换。

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- 保持单进程 Python 3.11+ 本地 CLI，不增加数据库、HTTP API 或后台 worker。
- 保持 Parser、Domain、Validator、Template、Compiler/RenderPlan、Bibliography、Renderer 分层。
- AI 仅允许位于 `src/thesis_forge/ai/` 或调用该层的 adapter。
- 输入和模板只读；build 仅写入显式 output，采用临时文件后原子替换，失败不破坏已有 DOCX。

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- 实现并验证 `FLOW-INSPECT`、`FLOW-VALIDATE`、`FLOW-BUILD`。
- inspect 无副作用；validate 返回结构化问题并以 error 决定非零 exit code。
- build 必须先完成 fatal validation，再进入 Compiler 和 Renderer。
- 所有核心 flow 在无网络、无 API Key 环境运行。
- 同一输入、模板和依赖版本的编号、引用顺序与 OOXML 语义必须稳定。

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Parser 不得 import Template、Renderer、`docx`、`lxml` 或 AI。
- Core Domain 不得包含 `w:p`、`CT_P`、`WD_*`、`docx.Document` 等 Word 对象。
- Renderer 不得重新解析 Markdown、计算学校规则或硬编码学校样式。
- 编号、bookmark naming、单位解析、字体应用、field code、OMML、section 和 bibliography formatting 需要共享 service/helper。
- `RenderNode.payload` 在能力扩展时迁移为可验证的 typed render instructions，避免跨模块依赖魔法 key。

## Unresolved Gaps

None. Product scope, UI/theme/locale policy, architecture boundaries, data flows,
component extraction rules, and verification expectations are confirmed for this change.
