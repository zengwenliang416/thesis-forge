# Requirements: build-thesisforge-desktop-ui

## Summary

Build the production cross-platform workbench for ThesisForge with React,
TypeScript, and Vite. The same frontend must run in a Web browser and inside
Tauri 2 shells on macOS and Windows. Every runtime must preserve the
deterministic compiler boundary, reuse the existing Python application services,
and promote the approved academic three-pane prototype into a real workflow.

## Users & Actors

- Thesis authors who want a visual workflow for Markdown, diagnostics, school
  templates, preview, and DOCX builds.
- Web users who access the workbench through a browser with an available
  ThesisForge HTTP service.
- macOS and Windows users who install a Tauri desktop package with a managed
  local Python sidecar.
- Maintainers who need deterministic, testable frontend state and transport
  contracts without copying Parser, Validator, Compiler, or Renderer logic into
  React components.
- Browser file APIs, native file dialogs, HTTP, Tauri commands, sidecar process
  management, and local filesystems are adapters, not trusted domain sources.

## In Scope

- Restore the post-archive test baseline by locating the approved V1 prototype
  through its archived change instead of the removed active-change path.
- Create a dedicated `frontend/` workspace using React, TypeScript, and Vite.
- Create Tauri 2 desktop packaging for macOS and Windows that embeds the same
  built frontend.
- Define one typed `WorkbenchTransport` contract with a Web HTTP adapter and a
  Tauri command/sidecar adapter.
- Add thin Python HTTP and sidecar protocol adapters that call existing
  application services; neither adapter may implement compiler behavior.
- Implement the approved workbench information architecture: product bar,
  outline, Markdown editor, paper-style preview, diagnostics, template selector,
  build action, progress, and output feedback.
- Open one Markdown workspace and derive outline and diagnostics from the same
  versioned source snapshot. Desktop uses native local paths; Web uses explicit
  upload/workspace handles and downloadable outputs.
- Allow editing with explicit Save/Save As only. There is no autosave. While
  the editor is dirty, validation and build are disabled so path-based
  application services never consume a stale or synthetic source. Web save and
  download semantics must be explicit and must not claim native path access.
- Resolve templates through the existing Template Model and display structured
  template failures without entering compile or render.
- Call `inspect_service`, `validation_service`, and `build_service` through a
  serialized adapter boundary; expose build stages `parse`, `validate`,
  `compile`, `render`, and `finalize`.
- Render a renderer-neutral preview from typed document/render-plan data. The
  frontend must not parse DOCX XML or receive python-docx objects.
- Preserve an existing output when validation, rendering, finalization,
  permission, or cancellation fails.
- Cover populated, loading, empty, error, disabled, and permission states with
  keyboard-accessible recovery actions.
- Keep desktop workflows usable offline without API keys, accounts, database,
  telemetry, or AI services. Web workflows may use the configured ThesisForge
  HTTP adapter but the compiler core itself must remain network-independent.

## Out of Scope

- AI chat, provider integration, accounts, cloud sync, collaboration, template
  marketplace, analytics, and remote telemetry.
- Dark mode, theme switching, runtime localization, and locale switching.
- Database, project library, recent-file persistence, autosave, and
  multi-document tabs.
- Public multi-tenant hosting, authentication, billing, collaboration, and
  untrusted arbitrary code execution.
- Exact Word pagination or embedding Word/WPS/LibreOffice as the preview engine.
- Changing compiler numbering, bibliography, template, or OOXML behavior except
  where a UI adapter exposes an existing contract defect.

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- Required UI decisions: promote the approved `academic-three-pane` layout into
  reusable React components, use tokenized light surfaces and compact
  academic-tool density, retain visible focus, pair severity colors with
  icons/text, and provide consistent keyboard navigation for file, template,
  diagnostics, panel, save, and build actions.

## Theme & Locale Capability Impact

- Theme support: `light-only`.
- Theme toggle policy: explicitly omit; do not create a toggle.
- Internationalization: `disabled`.
- Supported locales: `zh-CN`.
- Default locale: `zh-CN`.
- Prototype coverage: the approved light/`zh-CN` desktop and mobile HTML
  prototype remains the visual contract; production verification covers the
  browser runtime plus macOS and Windows desktop shells, responsive breakpoints,
  and minimum-window behavior.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Required architecture/database decisions: keep the Python compiler core and
  application services framework-independent; add `frontend/`, `src-tauri/`,
  and thin transport adapters only. The Web adapter may expose a versioned HTTP
  API. The desktop shell uses Tauri commands and a managed Python sidecar. No
  database is introduced.
- Core, Parser, Validator, Compiler, Template, Bibliography, and Renderer must
  not import React, Tauri, HTTP framework, or UI modules.
- Packaging decision: Web artifacts are built by Vite; macOS and Windows
  packages are built by Tauri 2; the Python wheel remains independently
  installable and runnable.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- Required data-flow decisions: add `FLOW-OPEN-SOURCE`, `FLOW-SAVE-SOURCE`,
  `FLOW-WEB-TRANSPORT`, and `FLOW-TAURI-TRANSPORT`; route inspect, validate, and
  build through the existing `FLOW-INSPECT`, `FLOW-VALIDATE`, and `FLOW-BUILD`
  application services. Frontend state owns workspace handles, saved text,
  dirty state, selections, panel state, diagnostics, progress, and presentation
  copy only.
- Serialized requests and responses use stable versioned DTOs. They must not
  expose Python class names, pathlib objects, raw exceptions, python-docx, lxml,
  or renderer-private payloads.
- Cancellation and stale-result policy: ignore results whose operation token is
  no longer current; cancellation must not report success or replace output.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Cohesion/coupling impact: React components render state and emit user intent;
  TypeScript workspace state owns client orchestration; transport adapters own
  runtime communication; Python adapters map serialized commands to
  `thesis_forge.application`.
- The existing pure-Python `WorkspaceController` remains a tested reference for
  state semantics until transport DTO parity is proven. It is not imported by
  the browser bundle.
- Shared extraction requirement: extract diagnostics localization, operation
  tokens, progress mapping, preview view models, atomic source saving, transport
  DTOs, and capability detection when those behaviors would otherwise be
  duplicated across Web and Tauri runtimes.

## Unresolved Gaps

- None. The cross-platform product constraint and production frontend stack are
  resolved as React + TypeScript + Vite + Tauri 2.
