# Acceptance Criteria: docforge-workbench-ui-redesign

## User-Visible Criteria

- 应用顶部显示 `DocForge` 与“Markdown → Word 文档工坊”，不再将产品描述为
  论文编译工作台。
- 用户可在顶部命令栏完成打开、保存、检查、取消构建和生成 DOCX；按钮启用
  条件与当前 workspace actions 保持一致。
- 用户可在顶部选择“Word 模板”，模板变化仍触发现有预览刷新流程。
- 1440x1024 桌面视口同时显示文档大纲、Markdown 编辑器和 Microsoft Word
  版式预览，底部显示诊断与输出状态。
- 空工作区、已打开文档、dirty、loading、validation error、build progress、
  build success、permission 和 canceled 状态均具有明确且通用的中文文案。
- 实时版式区域明确标注 Microsoft Word，不出现 WPS 兜底或产品文案。
- 移动端可以通过“大纲 / 编辑 / 预览 / 诊断”切换全部核心面板，操作栏不溢出
  或遮挡主内容。

## System Criteria

- `WorkbenchTransport` 请求、DTO、protocol version、template ID、build intent、
  output descriptor 和 final preview resolution 行为不变。
- Parser、domain model、compiler、RenderPlan 和 DOCX renderer 无 UI 反向依赖。
- 浏览器和 Tauri runtime 继续复用同一 React 组件树。
- 无网络、账号、AI、数据库或新持久化依赖。

## Data Criteria

- 现有 workspace state 字段及 reducer action 语义不变。
- 用户 Markdown 内容、项目身份、保存状态、诊断、预览和输出名称不因布局
  重构而丢失或重置。
- 模板下拉只改变现有 `templateId`，不创造未被 transport 支持的新模板 ID。

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- `WorkbenchShell` 保持布局职责，异步命令仍由 `WorkbenchApp` 编排。
- `ProductBar`、`StatusStrip`、`OutlinePanel`、`MarkdownEditor`、
  `DualPreviewPanel` 和 `DiagnosticsPanel` 具有覆盖关键文案和交互的测试。

## Verification Surfaces

- Facticity: 对照现有 transport/store 源码确认请求、状态和能力未变化。
- Static: `pnpm frontend:typecheck`、`pnpm frontend:lint`、
  `pnpm frontend:build`。
- Unit: `pnpm frontend:test`。
- Redteam: 覆盖空状态、disabled、dirty、fatal diagnostic、permission、
  canceled 和 preview failure 文案。
- E2E: `pnpm frontend:e2e`，验证打开/编辑/保存/检查/构建/预览主路径。
- Sensory: 在 1440x1024 和移动断点截图，与
  `assets/docforge-workbench-reference.png` 对照，`design-qa.md` 结果为 passed。

## Unresolved Gaps

- None.
