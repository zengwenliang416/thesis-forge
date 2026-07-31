# Development Basis: build-thesisforge-desktop-ui

## Approved Outcome

Deliver an optional local PySide6 workbench that opens one Markdown thesis,
supports explicit atomic saving, reuses the existing inspect/validate/build
application services, presents renderer-neutral structure and preview data, and
builds DOCX without network access. The deterministic compiler and CLI remain
fully usable without the `ui` extra.

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
Production Qt code may reuse approved labels, state names, information
architecture, and flow semantics, but must reimplement widgets, state, service
calls, file access, validation, and side effects. The archived V1 prototype
remains immutable evidence used only by its contract tests.

## Implementation Basis

- `src/thesis_forge/ui/` owns all PySide6 imports and exposes a lazy
  `thesisforge-ui` entrypoint.
- `WorkspaceController` and immutable view models remain headless and depend on
  injected application services, filesystem operations, and task runners.
- Dirty editor content cannot be validated or built until Save or Save As
  atomically replaces the selected source.
- Widgets emit user intent and render typed view models; they do not call
  Parser, Compiler, Renderer, python-docx, or lxml directly.
- Preview mapping consumes `ThesisDocument` and typed `RenderPlan`
  instructions without reading generated DOCX or claiming exact pagination.
- Background work uses generation tokens and cooperative cancellation; stale or
  canceled results cannot replace a previously valid output.
- All flows remain local, single-document, fixed `zh-CN`, light-only, and free
  of accounts, databases, network services, AI, telemetry, and cloud sync.

## Component Architecture Constraint

Application services remain the sole inspect, validation, compilation, and
render orchestration. UI widgets consume typed presentation models only.
Diagnostics localization, atomic source writing, operation-token handling, and
preview mapping are extracted before a second caller would duplicate them.

## Delivery Strategy

Development follows the eight user-visible slices in `tasks.md`. Each slice
must begin from a green entry contract, use focused behavior tests, preserve
the approved task baseline, and record a report, spec review, quality review,
ledger entry, drift check, and validation evidence before its checkbox group is
completed.
