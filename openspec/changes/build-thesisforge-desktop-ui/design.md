## Context

The deterministic compiler, application services, package validation, and
atomic DOCX replacement are complete. The approved HTML prototype defines the
academic three-pane information architecture and required states, but the
production frontend has not yet been implemented.

The product must share one dedicated frontend across Web, macOS, and Windows.
The UI cannot introduce a second parser, validator, compiler, or renderer. The
first baseline defect is frontend-independent: prototype acceptance tests refer
to the archived change by its former active path and currently fail.

## Goals / Non-Goals

**Goals:**

- Restore an archive-safe green baseline.
- Provide one responsive React + TypeScript + Vite workbench for Web, macOS,
  and Windows.
- Package macOS and Windows with Tauri 2 while preserving one frontend codebase.
- Reuse Python application services through versioned transport DTOs and thin,
  testable Web/Tauri adapters.
- Support explicit atomic source saving, template selection, diagnostics,
  renderer-neutral preview, progress, cancellation, and safe DOCX output.
- Keep the core package and CLI usable without Node.js, Rust, Tauri, or an HTTP
  server.
- Make frontend state, transport, and components testable without launching a
  native desktop shell.

**Non-Goals:**

- Multi-document projects, autosave, recent-file persistence, cloud sync,
  accounts, database, AI, marketplace, dark mode, or runtime i18n.
- Public multi-tenant hosting, authentication, billing, and collaboration.
- Exact Word pagination or a DOCX/OOXML preview engine.
- Replacing the existing application/domain/compiler/renderer pipeline.

## Decisions

### 1. Use one React frontend and Tauri 2 desktop wrappers

`frontend/` owns the React + TypeScript + Vite application. `src-tauri/` owns
the macOS and Windows shell, native dialogs, package metadata, and sidecar
lifecycle. The browser build and both desktop packages consume the same React
components, routes, state machine, design tokens, and transport interface.

Alternative considered: PySide6. Rejected because it creates a separate desktop
UI, does not provide the Web product, and duplicates a frontend implementation.

### 2. Put a typed transport boundary between frontend and Python

The frontend depends on a `WorkbenchTransport` TypeScript interface and
versioned JSON DTOs. `WebWorkbenchTransport` calls a thin Python HTTP adapter.
`TauriWorkbenchTransport` calls Tauri commands; the Rust shell manages a Python
sidecar and forwards versioned requests and streamed progress events.

Both Python adapters call `inspect_service`, `validation_service`, and
`build_service`. They serialize results and errors but do not parse Markdown,
validate, compile, number, or render documents themselves.

Alternative considered: let React components call ad hoc endpoints or Tauri
commands. Rejected because runtime differences would leak into components and
create divergent Web/desktop behavior.

### 3. Use frontend-owned workspace state with DTO parity tests

TypeScript workspace state owns source/template/output handles, saved text,
dirty state, current operation token, diagnostics, preview data, progress, and
user-visible state. React components emit intent and render immutable selectors
or view models.

The existing pure-Python `WorkspaceController` remains a tested reference for
the state semantics already delivered in Slice 002. The browser bundle never
imports it. Before the frontend claims parity, contract tests must run the same
state-transition fixtures against Python reference behavior and TypeScript
state behavior.

Alternative considered: make Python own browser presentation state. Rejected
because it would require chatty transport calls and couple product interaction
to a local Python object graph.

### 4. Preserve path-based services with an explicit save gate

The editor loads a saved file and may become dirty, but there is no autosave.
Validate and Build are disabled while dirty. Save and Save As use an atomic text
writer; only after replacement succeeds does the controller refresh the saved
snapshot and call inspection/validation.

Desktop uses native dialogs and local paths through Tauri. Web uses explicit
browser file/workspace handles, uploads, and downloads. The Web UI must not
pretend it can access arbitrary native paths.

Alternative considered: validate/build an unsaved temporary Markdown snapshot.
Rejected for this milestone because relative images, BibTeX, and template
resolution are anchored to the real source path and a synthetic path could
change behavior.

### 5. Keep runtime adapters replaceable

The Web adapter uses cancellable HTTP requests and an event stream for build
progress. The Tauri adapter uses asynchronous commands and sidecar progress
events. Every operation receives a generation token. Results and callbacks from
an older token are ignored.

Frontend tests use a deterministic fake transport. Components never own process
lifecycle, open raw sockets, or call Python application services directly.

### 6. Add cooperative build cancellation at application stage boundaries

`build_service` gains an optional cancellation predicate with a default that
preserves the current API behavior. It checks before each expensive stage and
again before final atomic replacement. Cancellation raises a typed application
stage error and leaves the previous output unchanged.

This cannot interrupt a third-party renderer in the middle of one call, but it
prevents a canceled result from being finalized. Transport cancellation and
frontend stale-result tokens provide additional guards.

Alternative considered: terminate the Python sidecar or HTTP worker. Rejected
because forced process termination can corrupt temporary work and unrelated
requests.

### 7. Build preview from renderer-neutral instructions

A preview mapper converts `ThesisDocument` and typed `RenderPlan` instructions
into `PreviewViewModel` sections, text runs, diagnostics markers, and page-like
layout hints. It does not import python-docx/lxml or claim exact pagination.

Alternative considered: render DOCX and convert it to images after every edit.
Rejected because it is slow, requires an external Office renderer, and makes
preview availability depend on tools outside the core package.

### 8. Treat the archived HTML prototype as immutable review evidence

Prototype acceptance tests locate exactly one archived directory ending in
`-build-thesisforge-v1-core` and validate its committed harness/artifact/evidence.
They do not recreate an active change or mutate archive contents.

Production browser and Tauri tests become the ongoing behavior gate; the
archived HTML tests remain evidence that implementation stays aligned with the
approved variant.

## Risks / Trade-offs

- [Three runtimes can drift] -> share React code and DTO fixtures, keep only
  transport adapters runtime-specific, and run parity tests in Web and Tauri.
- [Bundling Python with Tauri increases release complexity] -> keep sidecar
  packaging isolated, pin the protocol version, and verify macOS and Windows
  artifacts independently.
- [The Web runtime cannot use arbitrary native paths] -> expose explicit
  upload/workspace/download semantics and capability-aware UI copy.
- [Cancellation is cooperative] -> check at every application boundary and
  before final replacement; document that an in-flight renderer may finish its
  temporary file before cancellation is observed.
- [Dirty-state build guard adds an explicit save step] -> display a direct
  reason and Save action instead of silently building stale content.
- [Renderer-neutral preview differs from Word pagination] -> label it as a
  structural preview and retain DOCX/Office verification for final output.
- [HTTP exposure expands the attack surface] -> keep the adapter thin, validate
  request sizes and workspace boundaries, avoid raw filesystem paths in hosted
  mode, and keep public multi-tenant hosting out of scope.

## Migration Plan

1. Repair archive-safe prototype test discovery and restore the baseline.
2. Retain the headless Python state reference and define serialized transport
   DTOs plus parity fixtures.
3. Add the React + TypeScript + Vite workspace and shared workbench shell.
4. Add the Web HTTP adapter and Tauri 2 sidecar/command adapter.
5. Add source lifecycle and platform-capability-aware save behavior.
6. Add template, diagnostics, outline, and preview mapping.
7. Add background build, cancellation, progress, and output feedback.
8. Run browser, macOS, Windows, Python package, offline desktop,
   accessibility, and sensory verification.

Rollback is commit-based. Frontend, HTTP, and Tauri adapters can be removed
without changing core CLI behavior or user documents.

## Open Questions

None.
