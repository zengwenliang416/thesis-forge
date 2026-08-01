# Development Basis: build-thesisforge-desktop-ui

## Approved Outcome

Deliver one React + TypeScript + Vite workbench across Web, macOS, and Windows.
The Tauri 2 desktop packages support offline local operation through a managed
Python sidecar; Web uses a versioned HTTP adapter. Every runtime reuses the
existing inspect/validate/build application services, presents
renderer-neutral data, and keeps the deterministic compiler and CLI usable
without frontend toolchains.

## Requirements Reference

- `openspec/changes/build-thesisforge-desktop-ui/requirements.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.json`
- `openspec/changes/build-thesisforge-desktop-ui/spec-map.json`
- `openspec/changes/build-thesisforge-desktop-ui/component-impact-map.json`
- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`

## Prototype Reference

- `openspec/changes/build-thesisforge-desktop-ui/prototype/handoff.md`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/decision.json`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/verifier-report.json`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/artifact/index.html`

## Handoff Reference

The approved `academic-three-pane` HTML artifact is immutable review evidence.
Production React code may reuse approved labels, state names, information
architecture, and flow semantics, but must reimplement components, state,
transport calls, file access, validation, and side effects. The archived V1
prototype remains immutable evidence used only by its contract tests.

## Implementation Basis

- `frontend/` owns React components, TypeScript workspace state, DTOs, and the
  `WorkbenchTransport` contract.
- `src-tauri/` owns macOS/Windows shell behavior, native dialogs, and Python
  sidecar lifecycle.
- Thin Python HTTP and sidecar adapters call `thesis_forge.application`.
- The existing `WorkspaceController` and immutable view models remain a
  headless Python reference for delivered state semantics, not a browser
  dependency.
- Dirty editor content cannot be validated or built until Save or Save As
  atomically replaces the selected source.
- React components emit user intent and render typed view models; they do not
  call HTTP, Tauri, Parser, Compiler, Renderer, python-docx, or lxml directly.
- Preview mapping consumes `ThesisDocument` and typed `RenderPlan`
  instructions without reading generated DOCX or claiming exact pagination.
- Background work uses generation tokens and cooperative cancellation across
  HTTP and Tauri transports; stale or canceled results cannot replace a
  previously valid output.
- Desktop flows remain local and offline. All runtimes remain single-document,
  fixed `zh-CN`, light-only, and free of accounts, databases, AI, telemetry,
  and cloud sync.

## Component Architecture Constraint

Application services remain the sole inspect, validation, compilation, and
render orchestration. React components consume typed presentation models only.
Diagnostics localization, transport DTOs, capability detection, atomic source
writing, operation-token handling, and preview mapping are extracted before a
second runtime would duplicate them.

## Delivery Strategy

Development follows the eight user-visible slices in `tasks.md`. Each slice
must begin from a green entry contract, use focused behavior tests, preserve
the approved task baseline, and record a report, spec review, quality review,
ledger entry, drift check, and validation evidence before its checkbox group is
completed.
