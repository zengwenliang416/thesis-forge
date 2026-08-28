# Prototype Question: docforge-workbench-ui-redesign

## Question

选定的 DocForge “文档工坊”方向能否在不改变现有 workspace state 和 transport
行为的前提下，把大纲、Markdown 编辑、Microsoft Word 版式预览和诊断重组为
更清晰的通用文档生产工作流？

## Branch

`ui-html`

## Review Target

- Entry: `artifact/index.html`
- Required reviewer decision: 桌面三栏和底部诊断层级可直接作为生产 React
  工作台的视觉与布局基准。
- Selected visual: `../assets/docforge-workbench-reference.png`

## Out of Scope

- Production implementation.
- Database writes.
- Deployment behavior.
- Parser、compiler、renderer 或 transport contract 变更。
