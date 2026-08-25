# Tasks: docforge-workbench-ui-redesign

## 1. Development Baseline

用户结果：生产 UI 修改从已批准、可追溯且不会混入其他变更的基线开始。

- [x] 1.1 Create and validate SpecNav requirements, approved UI prototype, proposal, design, delta spec, and task baseline.
- [x] 1.2 Record the development entry basis, prototype promotion map, scope, ownership, task graph, and acceptance freeze.

## 2. DocForge Product Command Surface

用户结果：用户看到通用 DocForge 文档工坊，并可从一个紧凑命令栏完成 Word 文档生产操作。

- [x] 2.1 Update visible brand, generic document status copy, accessibility labels, template labels, preview labels, and output feedback.
- [x] 2.2 Move Word template selection into the product command bar while preserving existing template IDs and callbacks.
- [x] 2.3 Add or update focused ProductBar, StatusStrip, Preview, Outline, and output component tests.

## 3. Dual-Canvas Workbench Layout

用户结果：桌面用户可同时编辑 Markdown 和检查 Microsoft Word 版式，移动用户可切换全部核心面板。

- [x] 3.1 Recompose WorkbenchShell into command/status, outline/editor/preview canvas, bottom diagnostics drawer, and narrow output status.
- [x] 3.2 Rebuild frontend CSS to match the approved DocForge light editorial workshop while preserving resizers, focus states, and runtime states.
- [x] 3.3 Preserve and validate mobile outline/editor/preview/diagnostics panel navigation and minimum-window behavior.

## 4. Regression And Visual Verification

用户结果：现有打开、保存、检查、构建和预览行为不回退，生产界面与批准稿一致。

- [x] 4.1 Update unit and Playwright expectations affected by copy, DOM hierarchy, and responsive layout.
- [x] 4.2 Run frontend lint, typecheck, unit tests, production build, browser E2E, and real HTTP E2E.
- [x] 4.3 Capture 1440x1024 and mobile production screenshots, compare them with the approved reference, and complete `design-qa.md` with a passed result.

## 5. Desktop Packaging

用户结果：macOS 安装包显示新的 DocForge 界面，并继续使用 Microsoft Word 最终版式预览。

- [x] 5.1 Build the macOS desktop application with the existing release workflow.
- [x] 5.2 Install the rebuilt application to `/Applications/ThesisForge.app` and verify the visible DocForge UI plus Microsoft Word preview path.
- [x] 5.3 Complete SpecNav verification evidence and record remaining risks without modifying unrelated OpenSpec work.
