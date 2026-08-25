# Prototype Handoff: docforge-workbench-ui-redesign

## Approved Branch Variant

- Branch: `ui-html`
- Variant: `dual-canvas-docforge`
- Approval evidence: 用户选择方案三，并要求更换产品名；最终基准使用
  `DocForge` 和“Markdown → Word 文档工坊”。

## Screens Or Flows

- 单工作台：文档大纲、Markdown 编辑、Microsoft Word 版式预览、诊断和输出状态。
- 打开、保存、检查、模板选择、生成 DOCX、取消构建、预览模式切换和
  Office PDF 选择。
- 桌面三栏与移动四面板切换。

## Components To Create

- 无新的数据组件或 service。
- 允许在现有组件内部增加只承担视觉分组的语义容器。

## Components To Reuse

- `WorkbenchApp`
- `WorkbenchShell`
- `ProductBar`
- `StatusStrip`
- `OutlinePanel`
- `MarkdownEditor`
- `DualPreviewPanel`
- `DiagnosticsPanel`
- `OutputFeedback`
- `PanelHeader`

## Extraction Targets

- 本次不提前提取新抽象。
- 仅当相同 command bar 或状态呈现在第二个 screen 复用时再提取。

## API Contracts

- `workbench.v1`
- `preview`
- `save`
- `build`
- build event stream
- final preview descriptor resolution
- Office PDF selection callback

## Data Flows

- `FLOW-OPEN-SOURCE`
- `FLOW-SAVE-SOURCE`
- validate/preview
- build/cancel
- live preview
- final preview resolution

## State Behavior

- Loading: 工作区保留结构并显示正在读取文档与 Word 版式。
- Empty: 引导打开 Markdown 文档或 DocForge 项目。
- Error: 保留内容并把失败与恢复动作放在上下文状态区域。
- Disabled: 存在阻断诊断时禁用生成 DOCX，并保持编辑和诊断可用。
- Permission: 明确目标位置不可写，不使用兜底输出文案。
- Populated: 大纲、编辑器、Word 预览和诊断同步展示。

## Theme And Locale Policy

- Theme support: `light-only`
- Theme modes shown in prototype: `light`
- Theme toggle: intentionally omitted
- Internationalization: disabled
- Locales shown in prototype: `zh-CN`
- Locale switcher: intentionally omitted

## Out Of Scope Items

- 仓库名、Python 包名、CLI、Tauri bundle identifier 和 protocol 重命名。
- Parser、domain、compiler、RenderPlan、renderer 或 OOXML 行为。
- AI、账号、云同步、协作、分析、数据库和模板市场。
- WPS 预览与深色模式。

## Required Tests

- ProductBar 品牌、模板和按钮 gating。
- StatusStrip 通用状态与恢复文案。
- WorkbenchShell 桌面布局、移动面板和 resizer。
- Outline、Editor、Preview、Diagnostics 的通用文案与交互。
- 现有 preview/build/save/project transport 回归。
- 1440x1024 与移动断点视觉 QA。

## Open Risks

- 现有 CSS 选择器较多，重排时需要避免破坏测试依赖的 aria label 和
  `data-mobile-active` 行为。
- 最终 PDF 预览内容由 Microsoft Word 生成，生产视觉验收需要使用已有可用的
  final preview fixture 或真实构建结果。
- `DocForge` 当前仅为可见产品名，内部 ThesisForge 标识继续保留，后续若要
  全量重命名需独立变更。
