# Task Brief: 003-dual-preview-ui

## Goal

用户可在右侧切换快速结构预览和真实最终 PDF，并准确看到引擎、构建中、最新、过期、
不可用和失败状态。

## Parent Artifacts

- `openspec/changes/wps-pdf-final-preview-p1/requirements.md`
- `openspec/changes/wps-pdf-final-preview-p1/acceptance.md`
- `openspec/changes/wps-pdf-final-preview-p1/prototype/handoff.md`

## Vertical Slice

从 build event/transport PDF bytes 到 workspace freshness state、object URL 和右侧 viewer
完成共享 Web/Tauri 用户流程。

## In Scope

- 扩展 workspace preview mode、descriptor、revision/freshness 和 reducer events。
- 实现 `PreviewModeControl`、`FinalLayoutPreview` 和 object URL lifecycle。
- 接入 build success 与 WPS PDF picker。
- 增加可访问性、响应式、stale 和 stale-event 测试。

## Out Of Scope

- Office exporter、HTTP/Tauri native internals、PDF.js 高级控件和文档更新。

## Files Allowed

- `frontend/src/components/*`
- `frontend/src/state/*`
- `frontend/src/styles.css`
- `frontend/e2e/*`
- `src-tauri/tauri.conf.json`
- `openspec/changes/wps-pdf-final-preview-p1/development/tasks/003-dual-preview-ui/*`
- `openspec/changes/wps-pdf-final-preview-p1/development/*.jsonl`

## Interfaces / Seams

- `BuildOutput.finalPreview`.
- `WorkbenchTransport.resolveFinalPreview` and `pickFinalPreview`.
- Existing `WorkspaceState`, `PaperPreview`, `WorkbenchApp` and `WorkbenchShell`.

## Components To Create

- `PreviewModeControl`
- `FinalLayoutPreview`
- `usePdfObjectUrl`

## Components To Reuse

- `PanelHeader`
- `PaperPreview`
- workspace reducer generation guard
- existing mobile panel shell

## Components To Extract

- One PDF object URL hook and one final-preview presentation state.

## API / Data Flow Contracts

- Current build success -> resolve bytes -> blob URL -> ready viewer.
- Edit/template/source mutation -> stale or cleared preview.
- Explicit WPS selection -> `WPS PDF` ready viewer.

## State / Error / Empty / Loading Behavior

- Loading: final tab shows current build progress without fake pages.
- Empty: prompts to build or select WPS PDF.
- Error: preserves DOCX success and offers rebuild/select recovery.
- Disabled: automatic export unavailable still allows WPS PDF selection.
- Permission: displays transport permission failure without leaking path.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `pnpm --dir frontend test`
- `pnpm --dir frontend build`
- `pnpm --dir frontend exec playwright test`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Native PDF viewer controls may differ; test page visibility and state behavior.
- Every object URL must be revoked when replaced or unmounted.
