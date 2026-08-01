# Tasks: build-thesisforge-desktop-ui

## 1. Archive-Safe Prototype Baseline

用户结果：完成 V1 归档后，已批准桌面原型的契约测试仍能稳定运行，后续 UI 开发从绿色基线开始。

- [x] 1.1 Add a deterministic helper that locates the single archived `build-thesisforge-v1-core` prototype.
- [x] 1.2 Update prototype harness, artifact, and browser-evidence tests to use the archived location.
- [x] 1.3 Add tests for missing archive evidence and ambiguous matching archive directories.
- [x] 1.4 Assert the locator never selects an active change or mutates archived evidence.
- [x] 1.5 Run `tests/test_prototype_acceptance.py` and the closest archive/OpenSpec checks.
- [x] 1.6 Record red-green evidence, spec review, quality review, and extraction decision for slice 001.

## 2. Framework-Neutral Workspace State Reference

用户结果：用户看到的空白、加载、已打开、脏编辑、错误、禁用和权限状态由一个可测试控制器一致管理。

- [x] 2.1 Define immutable workspace, diagnostics, progress, output, and operation-token view models.
- [x] 2.2 Implement `WorkspaceController` with injected inspect, validate, build, filesystem, and task-runner dependencies.
- [x] 2.3 Implement empty, loading, populated, dirty, error, disabled, permission, and canceled state transitions.
- [x] 2.4 Suppress callbacks and results whose generation token is no longer current.
- [x] 2.5 Add headless unit tests for every state transition, repeated action, stale result, and recovery path.
- [x] 2.6 Add architecture tests proving controller/view models do not import PySide6, python-docx, or lxml.
- [x] 2.7 Record red-green evidence, spec review, quality review, and extraction decision for slice 002.

## 3. Explicit Source Open And Atomic Save

用户结果：用户可以在 Web、macOS、Windows 打开 Markdown 工作区、编辑并显式保存；未保存内容不会被误用于验证或构建，失败保存不会损坏已有内容。

- [x] 3.1 Implement source open with desktop readable-path checks, Web workspace/upload handling, and saved snapshot creation.
- [x] 3.2 Implement dirty tracking without autosave and disable Validate/Build while dirty.
- [x] 3.3 Implement desktop atomic Save/Save As and explicit Web workspace-save/download semantics with prior-content preservation on failure.
- [x] 3.4 Refresh inspection and validation only after a successful save.
- [x] 3.5 Add tests for missing files, encoding errors, read-only paths, browser capability limits, replace failure, Save As/download, and unchanged saves.
- [x] 3.6 Add tests proving inspect, validate, and build never mutate source files.
- [x] 3.7 Record red-green evidence, spec review, quality review, and extraction decision for slice 003.

## 4. Shared React Workbench And Runtime Transports

用户结果：同一套学术论文工作台可在 Web 直接运行，并通过 Tauri 2 在 macOS、Windows 安装运行；核心 CLI 不依赖前端工具链。

- [ ] 4.1 Create the React + TypeScript + Vite frontend workspace with deterministic build, lint, typecheck, and test commands.
- [ ] 4.2 Implement the light-theme workbench shell, product bar, responsive resizable panel layout, and minimum-window behavior.
- [ ] 4.3 Add outline, editor, preview, diagnostics, template, build, progress, and output React component shells.
- [ ] 4.4 Bind component intent and rendering to TypeScript workspace state and `WorkbenchTransport` without direct HTTP, Tauri, or Python calls.
- [ ] 4.5 Add Vitest/Testing Library and Playwright tests for launch, labels, panel presence, keyboard focus order, shortcuts, responsive layout, and resize behavior.
- [ ] 4.6 Add import-boundary tests proving the Python core and CLI work without Node.js, Rust, Tauri, or an HTTP server.
- [ ] 4.7 Record red-green evidence, spec review, quality review, and extraction decision for slice 004.
- [ ] 4.8 Implement the versioned Web HTTP adapter and contract tests against existing Python application services.
- [ ] 4.9 Implement the Tauri 2 macOS/Windows shell, command bridge, managed Python sidecar protocol, and transport parity tests.

## 5. Template Selection And Structured Diagnostics

用户结果：用户可以选择学校模板、理解所有结构化问题，并从诊断定位到对应 Markdown 行。

- [ ] 5.1 Implement template selection through the existing resolver and validation service.
- [ ] 5.2 Map `ValidationIssue` severity, code, message, line, and target into stable `zh-CN` presentation models.
- [ ] 5.3 Implement diagnostics filtering, summary counts, activation, and editor-line focus.
- [ ] 5.4 Disable Build on fatal diagnostics while preserving warning-only builds.
- [ ] 5.5 Add tests for valid, missing, malformed, and incompatible templates.
- [ ] 5.6 Add tests for diagnostic ordering, localization fallback, no-line issues, activation, and fatal/warning guards.
- [ ] 5.7 Record red-green evidence, spec review, quality review, and extraction decision for slice 005.

## 6. Outline And Renderer-Neutral Paper Preview

用户结果：用户在编辑前即可查看论文结构和接近纸张阅读顺序的预览，同时明确预览不冒充 Word 最终分页。

- [ ] 6.1 Map headings and stable semantic IDs into an outline view model.
- [ ] 6.2 Map typed document/render-plan instructions into page-like preview sections without DOCX objects.
- [ ] 6.3 Synchronize outline selection, preview selection, and editor source locations.
- [ ] 6.4 Render figures, tables, equations, references, bibliography, sections, and unsupported nodes with explicit preview states.
- [ ] 6.5 Add unit/golden tests for preview ordering, numbering labels, diagnostics markers, and unsupported content.
- [ ] 6.6 Add static tests forbidding python-docx/lxml imports from UI preview modules.
- [ ] 6.7 Record red-green evidence, spec review, quality review, and extraction decision for slice 006.

## 7. Safe Cross-Runtime Build, Progress, And Cancellation

用户结果：构建期间界面保持响应，阶段可见，可安全取消；任何失败或过期结果都不会覆盖已有有效 DOCX。

- [ ] 7.1 Add a backward-compatible application cancellation predicate checked at stage boundaries and before final replacement.
- [ ] 7.2 Implement cancellable Web HTTP/event-stream and Tauri command/sidecar runners behind one frontend transport contract.
- [ ] 7.3 Display ordered parse, validate, compile, render, and finalize progress.
- [ ] 7.4 Implement cooperative cancellation, repeated-click suppression, stale completion suppression, and retry.
- [ ] 7.5 Display successful output path and actionable validation, permission, render, finalize, and cancellation failures.
- [ ] 7.6 Add tests for every cancellation boundary, callback failure, renderer failure, replace failure, stale result, and prior-output preservation.
- [ ] 7.7 Add browser and Tauri E2E tests for successful build, cancel, retry, stale completion, and recovery.
- [ ] 7.8 Record red-green evidence, spec review, quality review, and extraction decision for slice 007.

## 8. Complete Web, macOS, And Windows Acceptance

用户结果：用户可在 Web、macOS、Windows 完成打开、编辑、保存、校验、预览和构建；桌面端可离线运行，维护者可重复构建和发布三端产物。

- [ ] 8.1 Run the complete example through the browser adapter and both Tauri desktop targets; block external sockets for desktop verification.
- [ ] 8.2 Verify populated, loading, empty, error, disabled, permission, dirty, canceled, and success states.
- [ ] 8.3 Verify keyboard-only operation, labels, focus visibility, contrast, resizing, and reduced-motion behavior.
- [ ] 8.4 Verify independent Python wheel installation, Web production build, macOS package, and Windows package without cross-toolchain leakage.
- [ ] 8.5 Update README and maintenance documentation for Web, macOS, and Windows installation, launch, capability differences, limitations, troubleshooting, and distribution.
- [ ] 8.6 Run full pytest, Ruff, frontend lint/typecheck/unit/E2E, Tauri checks, package/distribution checks, strict OpenSpec validation, CodeGraph claims, and Git whitespace checks.
- [ ] 8.7 Complete six-domain verification evidence and user-aligned Web/macOS/Windows test cases.
- [ ] 8.8 Record final development handoff, residual risks, and operations readiness inputs.
