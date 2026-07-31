# Prototype Question: build-thesisforge-desktop-ui

## Question

已于 2026 年 7 月 30 日批准的“论文大纲 + Markdown 编辑器 + Word 纸张预览 +
结构化诊断”三栏学术布局，是否仍适合作为生产 PySide6 工作台的视觉与信息架构基线，
并承载显式保存、模板选择、问题定位、构建进度、取消和 DOCX 输出反馈？

## Branch

`ui-html`

## Review Target

- Entry: `artifact/index.html`
- Variant: `academic-three-pane`
- Generation source: Open Design project `thesisforge-html-workbench-20260729`
- Approval source: archived
  `2026-07-31-build-thesisforge-v1-core/prototype/decision.json` and
  `prototype/handoff.md`, recording explicit user approval on 2026-07-30.
- Promotion target: production PySide6 workbench through the development gate.

## Out of Scope

- 原型本身执行真实文稿保存、DOCX 渲染或本地文件选择。
- 数据库、账号、云端同步或网络服务。
- 暗色主题、主题切换、运行时多语言和语言切换。
- 将原型 DOM/CSS 直接作为生产 Qt 组件代码。
