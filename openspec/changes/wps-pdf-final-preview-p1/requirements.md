# Requirements: wps-pdf-final-preview-p1

## Summary

把当前右侧“结构预览”扩展为双预览：保留快速、可导航的 RenderPlan 结构预览，并在
成功构建 DOCX 后显示由真实 Office 布局引擎导出的 PDF 最终版式。自动导出与用户从
WPS 手工导入的 PDF 必须标明真实引擎，源文稿或模板变化后必须明确显示预览已过期。

## Users & Actors

- 论文作者：编辑时使用快速结构预览，构建后检查真实分页、字体、目录和图表版式。
- WPS 用户：可把 WPS 导出的 PDF 关联为最终预览，并看到 `WPS PDF` 引擎标识。
- Web、macOS 和 Windows 用户：使用同一 React 交互和同一 application 导出契约。
- 部署维护者：可选安装 LibreOffice 以启用自动 PDF，不把 Office 变成核心构建依赖。

## In Scope

- 右侧预览提供“结构预览 / 最终版式”可访问切换控件。
- DOCX 构建成功后，通过可注入 `PdfPreviewExporter` 尝试生成同一文档的 PDF。
- 默认 `LibreOfficePdfPreviewExporter` 跨平台发现 LibreOffice，使用隔离 profile、
  hidden conversion、有界超时和临时输出，再原子发布 PDF。
- 构建输出返回可选、引擎标记的最终预览描述，不暴露 Web workspace 或桌面私有路径。
- Web 仅通过 workspace-bound、PDF-only、no-store 的读取路由提供自动生成 PDF。
- macOS/Windows Tauri 通过受限原生命令读取自动生成 PDF 或用户明确选择的 PDF。
- Web 通过浏览器 file picker、Tauri 通过原生 file picker 关联 WPS 导出的 PDF。
- 自动生成与手工关联 PDF 均使用浏览器/WebView 的真实 PDF 显示能力。
- 源 Markdown、模板选择或工作区切换后，当前最终预览标记为过期；成功重建或重新关联
  后恢复为最新。
- 自动导出缺失或失败不影响已成功生成的 DOCX，并提供准确恢复提示。

## Out of Scope

- 在 HTML/CSS 中复制 Word/WPS 排版引擎或承诺结构预览所见即所得。
- 把 LibreOffice 生成的 PDF 标记为 WPS PDF，或声称不同 Office 引擎逐像素一致。
- 通过 macOS Accessibility 点击 WPS 菜单，或依赖未公开、不可测试的 WPS 私有接口。
- 将 WPS、LibreOffice、网络、AI 或 PDF 生成变成 `inspect`、`validate`、`build` 的
  必需依赖。
- PDF 编辑、批注、文字选择同步、页面缩略图、搜索和打印控制。
- 上传论文到第三方转换服务。

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- 在现有 `PaperPreview` 面板内增加紧凑 segmented control，不新增路由或第二套 shell。
- 结构预览保留大纲联动；最终版式使用完整面板宽度显示 PDF 页面或浏览器 PDF viewer。
- 最终预览必须覆盖 empty、building、ready、stale、unavailable、failed 六种状态。
- 引擎标签与 stale/error 文本同时呈现，不能只用颜色表达。

## Theme & Locale Capability Impact

- Theme support: `light-only`.
- Theme toggle policy: explicitly omit; do not create a theme switcher.
- Internationalization: `disabled`.
- Supported locales: `zh-CN`.
- Default locale: `zh-CN`.
- Prototype coverage: desktop and mobile-width review in light theme with fixed `zh-CN` copy.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Preserve `Markdown -> ThesisDocument -> Validation -> Template -> RenderPlan -> DOCX`.
- Add application-layer PDF export after successful DOCX publication; Parser, Domain, Compiler,
  RenderPlan and DOCX Renderer remain unaware of PDF viewers and Office processes.
- `BuildResult` gains optional typed final-preview metadata; DOCX success remains authoritative.
- No database, network service, account, migration or persistent server-side domain state.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- Extend `FLOW-BUILD`: publish DOCX -> optional Office PDF export -> return output plus preview
  descriptor. PDF failure is a non-fatal preview result, not a false build failure.
- Add `FLOW-FINAL-PREVIEW`: resolve a trusted automatic PDF or explicitly selected WPS PDF ->
  create/revoke browser object URL -> render -> mark stale on source/template mutation.
- Web artifact reads stay inside the opaque workspace and accept plain PDF names only.
- Tauri file reads are limited to the generated sibling PDF or a file selected by the user.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Cohesion/coupling impact: Office conversion belongs in `application/pdf_preview.py`; runtime
  presentation belongs in adapters; object URL lifecycle belongs in a shared frontend hook/component.
- Shared extraction requirement: one typed `FinalPreviewDescriptor`, one transport-level preview
  resolver/import contract, and one `FinalLayoutPreview` component are reused by Web and Tauri.

## Unresolved Gaps

None for P1. Native unattended WPS export remains explicitly out of scope until WPS exposes a
documented, testable cross-platform automation surface.
