# Requirements: build-thesisforge-desktop-ui

## Summary

Build the production PySide6 desktop workbench for ThesisForge. The desktop
adapter must preserve the deterministic offline compiler boundary, reuse the
existing application services, and promote the approved academic three-pane
prototype into a real local workflow.

## Users & Actors

- Thesis authors who want a local visual workflow for Markdown, diagnostics,
  school templates, preview, and DOCX builds.
- Maintainers who need deterministic, testable UI controllers without copying
  Parser, Validator, Compiler, or Renderer logic into widgets.
- The operating-system file picker and local filesystem are adapters, not
  trusted domain sources.

## In Scope

- Restore the post-archive test baseline by locating the approved V1 prototype
  through its archived change instead of the removed active-change path.
- Add an optional PySide6 application entrypoint without making PySide6 a core
  CLI dependency.
- Implement the approved workbench information architecture: product bar,
  outline, Markdown editor, paper-style preview, diagnostics, template selector,
  build action, progress, and output feedback.
- Open one local Markdown source and derive outline and diagnostics from the
  same saved source snapshot.
- Allow editing with explicit Save/Save As only. There is no autosave. While
  the editor is dirty, validation and build are disabled so path-based
  application services never consume a stale or synthetic source.
- Resolve templates through the existing Template Model and display structured
  template failures without entering compile or render.
- Call `inspect_service`, `validation_service`, and `build_service` through a
  UI controller; expose build stages `parse`, `validate`, `compile`, `render`,
  and `finalize`.
- Render a renderer-neutral preview from typed document/render-plan data. The
  UI must not parse DOCX XML or expose python-docx objects.
- Preserve an existing output when validation, rendering, finalization,
  permission, or cancellation fails.
- Cover populated, loading, empty, error, disabled, and permission states with
  keyboard-accessible recovery actions.
- Keep all UI workflows local and usable without network, API keys, accounts,
  database, telemetry, or AI services.

## Out of Scope

- AI chat, provider integration, accounts, cloud sync, collaboration, template
  marketplace, analytics, and remote telemetry.
- Dark mode, theme switching, runtime localization, and locale switching.
- Background daemon, HTTP API, database, project library, recent-file
  persistence, autosave, and multi-document tabs.
- Exact Word pagination or embedding Word/WPS/LibreOffice as the preview engine.
- Changing compiler numbering, bibliography, template, or OOXML behavior except
  where a UI adapter exposes an existing contract defect.

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- Required UI decisions: promote the approved `academic-three-pane` layout to
  PySide6, use tokenized light surfaces and compact academic-tool density, retain
  visible focus, pair severity colors with icons/text, and provide native
  keyboard navigation for file, template, diagnostics, panel, save, and build
  actions.

## Theme & Locale Capability Impact

- Theme support: `light-only`.
- Theme toggle policy: explicitly omit; do not create a toggle.
- Internationalization: `disabled`.
- Supported locales: `zh-CN`.
- Default locale: `zh-CN`.
- Prototype coverage: the approved light/`zh-CN` desktop and mobile HTML
  prototype remains the visual contract; production verification covers the
  desktop PySide6 workbench and its responsive minimum-window behavior.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Required architecture/database decisions: add only optional UI adapters under
  `src/thesis_forge/ui/`; keep one local Python process, no HTTP service and no
  database. UI controllers depend on `thesis_forge.application` contracts.
  Core, Parser, Validator, Compiler, Template, Bibliography, and Renderer must
  not import PySide6 or UI modules.
- Packaging decision: expose a `thesisforge-ui` entrypoint and retain PySide6 in
  the existing `ui` optional dependency extra.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- Required data-flow decisions: add `FLOW-OPEN-SOURCE` and `FLOW-SAVE-SOURCE`;
  route inspect, validate, and build through the existing `FLOW-INSPECT`,
  `FLOW-VALIDATE`, and `FLOW-BUILD` application services. UI state owns paths,
  saved text, dirty state, selections, panel state, diagnostics, progress, and
  presentation copy only.
- Cancellation and stale-result policy: ignore results whose operation token is
  no longer current; cancellation must not report success or replace output.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Cohesion/coupling impact: widgets render state and emit user intent;
  `WorkspaceController` owns orchestration; immutable UI view models map domain
  results to presentation; file dialogs, filesystem writes, and preview mapping
  remain replaceable adapters.
- Shared extraction requirement: extract diagnostics localization, operation
  tokens, progress mapping, preview view models, and atomic source saving when
  those behaviors would otherwise be duplicated across widgets/controllers.

## Unresolved Gaps

- None.
