# Requirements: docforge-workbench-ui-redesign

## Summary

将现有以学术论文为主叙事的 ThesisForge 工作台，重构为面向通用
Markdown 到 Microsoft Word 输出的 `DocForge` 文档工坊。界面以文档大纲、
Markdown 编辑、Word 最终版式预览和上下文诊断为主工作流，继续复用现有
workspace state、transport DTO、模板选择、验证、构建和 Office PDF 预览能力。

视觉基准：`assets/docforge-workbench-reference.png`。

## Users & Actors

- 主要用户：需要把 Markdown 转为可交付 `.docx` 的技术写作者、咨询顾问、
  产品/项目人员、报告编写者和学术作者。
- 运行时：浏览器工作区与 macOS/Windows Tauri 桌面端，共用同一 React
  组件树。
- Microsoft Word 是本次最终版式预览和兼容性文案的唯一 Office 目标。

## In Scope

- 将可见品牌名改为 `DocForge`，副标题为“Markdown → Word 文档工坊”。
- 将论文专属空状态、按钮、ARIA label、模板标签、预览标题、诊断提示和状态
  文案改为通用文档表达。
- 桌面布局改为顶部命令栏、左侧文档大纲、中间 Markdown 编辑器、右侧 Word
  版式预览、底部上下文诊断/输出状态。
- 模板选择在主命令栏可见，标签改为“Word 模板”；现有模板 ID 和 transport
  payload 不变。
- 继续支持打开 Markdown 或 V2 项目、保存、检查、取消构建、生成 DOCX、
  结构预览、实时版式、审阅、选择 Microsoft Word 导出的 PDF 和错误恢复。
- 保留可拖拽面板宽度、键盘操作、焦点状态、移动端四面板切换和现有
  capability gating。
- 更新受可见文案、DOM 层级和响应式布局影响的单元测试及 Playwright 测试。

## Out of Scope

- 不重命名仓库、Python 包、CLI 命令、Tauri bundle identifier、transport
  protocol 或内部 `ThesisDocument`/`RenderPlan` 类型。
- 不修改 Parser、Validator、Compiler、DOCX Renderer 或 OOXML 行为。
- 不新增 AI、账号、云同步、协作、分析、模板市场、数据库或网络依赖。
- 不新增深色模式、主题切换、语言切换或 WPS 专属预览。
- 不在本次重写代码编辑器为新的第三方编辑器；继续使用现有 textarea
  编辑能力并通过样式建立编辑器视觉。

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- Required UI decisions:
  - 选定稿 `assets/docforge-workbench-reference.png` 是 1440x1024 桌面视觉基准。
  - 使用浅纸灰背景、深墨色文字、青绿色主色、琥珀色警告色和 1px 分隔线。
  - 依靠间距、排版和分隔线建立层级，避免卡片堆叠、渐变和重阴影。
  - 编辑器使用中文友好的等宽字体回退；界面使用中文友好的人文无衬线字体回退。
  - 图标继续复用当前 `lucide-react`，不引入自绘 SVG 或图形占位。
  - 桌面端大纲、编辑、预览同时可见；诊断位于底部抽屉式区域。
  - 窄屏继续使用四个语义面板 tab，禁止仅缩放桌面三栏导致不可用。

## Theme & Locale Capability Impact

- Theme support: `light-only`
- Theme toggle policy: explicitly omit
- Internationalization: `disabled`
- Supported locales: `zh-CN`
- Default locale: `zh-CN`
- Prototype coverage: 1440x1024 desktop and existing mobile breakpoint in
  `light-only` with `zh-CN`

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Required architecture/database decisions:
  - 保持单 React frontend 与 Web/Tauri transport adapters。
  - 不改变 application service、DTO、协议版本和本地文件持久化边界。
  - 数据库影响：无；继续由用户本地文件和 workspace handle 持久化。

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- Required data-flow decisions:
  - `FLOW-OPEN-SOURCE`、`FLOW-SAVE-SOURCE`、validate/preview/build/cancel
    请求和响应保持不变。
  - UI 只重排现有 state 的展示位置，不复制 parser、validation、preview 或
    build 状态机。
  - Microsoft Word PDF 选择和实时预览继续调用现有 transport callbacks。

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Cohesion/coupling impact:
  - `WorkbenchApp` 继续拥有状态编排，`WorkbenchShell` 只负责布局组合。
  - `ProductBar` 负责品牌、文档身份、模板和主操作。
  - `StatusStrip` 缩减为上下文状态/恢复信息，不再承载桌面模板选择。
  - `OutlinePanel`、`MarkdownEditor`、`DualPreviewPanel`、`DiagnosticsPanel`
    继续消费现有 workspace state 和 callbacks。
- Shared extraction requirement:
  - 复用现有 `PanelHeader`、workspace selectors、diagnostic presentation 和
    preview components。
  - 不为一次性视觉容器建立新的数据层或 transport hook。

## Unresolved Gaps

- None.
