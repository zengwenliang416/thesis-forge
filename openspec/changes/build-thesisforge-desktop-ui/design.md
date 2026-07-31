## Context

The deterministic compiler, application services, package validation, and
atomic DOCX replacement are complete. The existing UI package is empty, PySide6
is already an optional dependency, and the approved HTML prototype defines the
academic three-pane information architecture and required states.

The UI must remain optional and offline. It cannot introduce a second parser,
validator, compiler, or renderer. The first baseline defect is independent of
Qt: prototype acceptance tests refer to the archived change by its former active
path and currently fail.

## Goals / Non-Goals

**Goals:**

- Restore an archive-safe green baseline.
- Provide a responsive local PySide6 workbench for one Markdown source.
- Reuse application services through a testable controller and typed view
  models.
- Support explicit atomic source saving, template selection, diagnostics,
  renderer-neutral preview, progress, cancellation, and safe DOCX output.
- Keep the core package and CLI usable without PySide6.
- Make controller and most view behavior testable headlessly.

**Non-Goals:**

- Multi-document projects, autosave, recent-file persistence, cloud sync,
  accounts, database, HTTP API, AI, marketplace, dark mode, or runtime i18n.
- Exact Word pagination or a DOCX/OOXML preview engine.
- Replacing the existing application/domain/compiler/renderer pipeline.

## Decisions

### 1. Keep PySide6 behind an optional adapter boundary

`src/thesis_forge/ui/` owns every PySide6 import. A small `thesisforge-ui`
entrypoint imports the Qt application lazily and reports a clear installation
message when the `ui` extra is absent. Core and CLI imports remain unchanged.

Alternative considered: make PySide6 a required dependency. Rejected because it
would enlarge and platform-bind the offline CLI installation.

### 2. Use a controller plus immutable view models

`WorkspaceController` owns source/template/output paths, saved text, dirty
state, current operation token, diagnostics, preview data, progress, and
user-visible state. Widgets emit intent and render immutable view models.

The controller depends on injected application service callables and filesystem
adapters, allowing headless unit tests without a visible Qt session.

Alternative considered: let each widget call services directly. Rejected
because it duplicates state transitions and couples presentation to domain
execution.

### 3. Preserve path-based services with an explicit save gate

The editor loads a saved file and may become dirty, but there is no autosave.
Validate and Build are disabled while dirty. Save and Save As use an atomic text
writer; only after replacement succeeds does the controller refresh the saved
snapshot and call inspection/validation.

Alternative considered: validate/build an unsaved temporary Markdown snapshot.
Rejected for this milestone because relative images, BibTeX, and template
resolution are anchored to the real source path and a synthetic path could
change behavior.

### 4. Run long operations through a replaceable task runner

The Qt adapter uses `QThreadPool`/`QRunnable` (or an equivalent isolated Qt
worker) for inspect, validate, and build. Every operation receives a generation
token. Results and callbacks from an older token are ignored.

Controller tests use a synchronous fake runner. Widgets never own threads or
call application services directly.

### 5. Add cooperative build cancellation at application stage boundaries

`build_service` gains an optional cancellation predicate with a default that
preserves the current API behavior. It checks before each expensive stage and
again before final atomic replacement. Cancellation raises a typed application
stage error and leaves the previous output unchanged.

This cannot interrupt a third-party renderer in the middle of one call, but it
prevents a canceled result from being finalized. UI stale-result tokens provide
an additional presentation guard.

Alternative considered: terminate worker threads. Rejected because forced Qt or
Python thread termination can corrupt process state and temporary files.

### 6. Build preview from renderer-neutral instructions

A preview mapper converts `ThesisDocument` and typed `RenderPlan` instructions
into `PreviewViewModel` sections, text runs, diagnostics markers, and page-like
layout hints. It does not import python-docx/lxml or claim exact pagination.

Alternative considered: render DOCX and convert it to images after every edit.
Rejected because it is slow, requires an external Office renderer, and makes
preview availability depend on tools outside the core package.

### 7. Treat the archived HTML prototype as immutable review evidence

Prototype acceptance tests locate exactly one archived directory ending in
`-build-thesisforge-v1-core` and validate its committed harness/artifact/evidence.
They do not recreate an active change or mutate archive contents.

Production PySide6 tests become the ongoing behavior gate; the archived HTML
tests remain evidence that implementation stays aligned with the approved
variant.

## Risks / Trade-offs

- [Qt event-loop tests can be platform-sensitive] -> keep controller/view-model
  coverage headless, isolate a small widget integration suite, and set the
  offscreen platform in CI.
- [Cancellation is cooperative] -> check at every application boundary and
  before final replacement; document that an in-flight renderer may finish its
  temporary file before cancellation is observed.
- [Dirty-state build guard adds an explicit save step] -> display a direct
  reason and Save action instead of silently building stale content.
- [Renderer-neutral preview differs from Word pagination] -> label it as a
  structural preview and retain DOCX/Office verification for final output.
- [PySide6 package size is large] -> keep it in the optional `ui` extra and
  exclude it from core distribution verification.

## Migration Plan

1. Repair archive-safe prototype test discovery and restore the baseline.
2. Add headless controller/view-model contracts and tests.
3. Add optional entrypoint and workbench shell.
4. Add source lifecycle and atomic save.
5. Add template, diagnostics, outline, and preview mapping.
6. Add background build, cancellation, progress, and output feedback.
7. Run full package, offline, Qt offscreen, accessibility, and sensory
   verification.

Rollback is commit-based. The optional UI entrypoint can be removed without
changing core CLI behavior or user documents.

## Open Questions

None.
