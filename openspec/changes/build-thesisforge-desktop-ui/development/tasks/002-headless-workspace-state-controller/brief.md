# Task Brief: 002-headless-workspace-state-controller

## Goal

Users see one deterministic workspace state for empty, loading, opened, dirty,
error, disabled, permission-denied, and canceled conditions before Qt widgets
are introduced.

## Parent Artifacts

- `openspec/changes/build-thesisforge-desktop-ui/requirements.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.json`
- `openspec/changes/build-thesisforge-desktop-ui/spec-map.json`
- `openspec/changes/build-thesisforge-desktop-ui/component-impact-map.json`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/handoff.md`

## Vertical Slice

Provide a pure-Python `WorkspaceController` that accepts saved source snapshots,
routes inspect, validate, and build intent through injected application
services, publishes immutable view models, and rejects repeated or stale
operation callbacks.

## In Scope

- Define immutable workspace, diagnostics, progress, output, action, and
  operation-token view models.
- Define one replaceable task-runner protocol plus a synchronous implementation
  for headless use and tests.
- Inject inspect, validate, build, filesystem, and task-runner dependencies into
  `WorkspaceController`.
- Accept an already-read saved source snapshot without implementing filesystem
  open or save behavior.
- Implement empty, loading, populated, dirty, error, disabled, permission, and
  canceled state transitions.
- Guard validate/build while empty, dirty, disabled, or another action is
  active.
- Use one monotonic generation-token contract to ignore stale success, failure,
  and progress callbacks.
- Provide recovery transitions that clear transient error, permission, canceled,
  and disabled presentation without discarding the last valid workspace data.
- Add headless tests for state transitions, action guards, repeated actions,
  stale callbacks, newer-generation wins, and recovery.
- Add static architecture tests for forbidden imports.

## Out Of Scope

- Importing PySide6 or creating widgets, windows, event-loop adapters, dialogs,
  or a UI entrypoint.
- Reading, writing, saving, Save As, atomic source replacement, encoding checks,
  and real filesystem permission probes; those belong to Slice 003.
- Cooperative cancellation inside `build_service`; this slice invalidates UI
  callbacks only, while application-stage cancellation belongs to Slice 007.
- Diagnostics localization/filtering, renderer-neutral preview mapping, outline
  selection, and template-selection UI.
- Changing Parser, Validator, Compiler, Renderer, application service behavior,
  or DOCX output contracts.

## Files Allowed

- `src/thesis_forge/ui/__init__.py`
- `src/thesis_forge/ui/models.py`
- `src/thesis_forge/ui/tasks.py`
- `src/thesis_forge/ui/controller.py`
- `tests/test_ui_controller.py`
- `tests/test_architecture.py`

## Interfaces / Seams

- `WorkspaceController` receives callables compatible with
  `inspect_service`, `validation_service`, and `build_service`.
- `TaskRunner.submit(...)` owns execution timing and invokes controller-provided
  success/failure callbacks; tests may delay and reorder callbacks.
- `WorkspaceFileSystem` is an injected seam reserved for Slice 003 source
  lifecycle work; Slice 002 stores it without performing source I/O.
- State subscribers receive immutable `WorkspaceViewModel` snapshots and never
  raw mutable controller internals.

## Components To Create

- `WorkspaceController`.
- Immutable view models and state/operation enums under `ui/models.py`.
- `TaskRunner`, `SynchronousTaskRunner`, and the minimal filesystem protocol
  under `ui/tasks.py`.

## Components To Reuse

- `InspectionResult`, `ValidationResult`, `BuildResult`, `BuildStage`, and
  `ValidationIssue`.
- Existing `inspect_service`, `validation_service`, and `build_service`.
- Standard-library `dataclass`, `Path`, enum, callable, and protocol contracts.

## Components To Extract

- Centralize all generation-token allocation and current-token checks in the
  controller; inspect, validate, build, progress, success, and failure paths
  must not implement separate stale-result rules.
- Centralize action availability in the immutable workspace view model instead
  of duplicating guards in future widgets.

## API / Data Flow Contracts

- `load_snapshot(path, saved_text)` invalidates older operations, records the
  saved source snapshot, and schedules inspection.
- `edit_text(text)` changes only controller presentation state and never calls
  filesystem or application services.
- `discard_edits()` restores the saved snapshot without source I/O, and
  `reset()` invalidates pending callbacks before returning to the empty state.
- `validate()` and `build(output_path)` return the accepted operation token, or
  `None` when guarded or repeated.
- Service results are mapped to immutable diagnostics/output state; controller
  code does not parse Markdown, validate domain rules, compile, or render.
- `cancel_current()` invalidates the active generation and reports canceled
  state without claiming application-level interruption.
- Success, error, and progress callbacks apply only when their token equals the
  current active token.

## State / Error / Empty / Loading Behavior

- Loading: an accepted inspect, validate, or build operation exposes its token
  and operation kind while disabling repeated actions.
- Empty: no saved source snapshot exists; inspect, validate, build, and save are
  unavailable.
- Populated: the latest accepted inspection succeeded for the saved snapshot.
- Dirty: edited text differs from the saved snapshot; validate and build remain
  unavailable and no autosave occurs.
- Error: non-permission operation failures retain prior workspace data and
  expose a retry/recovery reason.
- Disabled: explicit controller disablement preserves the resumable prior state
  and prevents new actions.
- Permission: a `PermissionError` is presented distinctly and preserves prior
  workspace data.
- Canceled: controller cancellation invalidates the generation so delayed
  progress, success, and failure callbacks cannot change the state.

## TDD Requirement

- TDD Route: strict.
- Record an observed missing-API RED before production implementation.
- Add the minimal production behavior for each state/guard/token cycle and keep
  focused tests green before broad verification.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_ui_controller.py tests/test_architecture.py -q`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `OPENSPEC_TELEMETRY=0 openspec validate build-thesisforge-desktop-ui --strict --json`
- `SPECNAV_CHANGE=build-thesisforge-desktop-ui OPENSPEC_TELEMETRY=0 node /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js --mode entry --json`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.
- The controller would need to import PySide6, python-docx, lxml, Parser,
  Compiler, Renderer, or other private implementation modules.
- Correct behavior would require reading/writing source files or changing
  application build cancellation semantics in this slice.
- A service signature cannot be reused through the documented injected callable
  boundary without a breaking application API change.

## Unsafe Assumptions

- Do not assume task-runner callbacks arrive in order or on the same generation.
- Do not treat UI callback invalidation as cooperative build cancellation.
- Do not infer that dirty editor text has been saved or is safe for path-based
  validation/build.
- Do not collapse permission failures into generic errors.
- Do not expose mutable lists or service-owned objects as controller state.
- Do not use a successful build result from an obsolete token to replace the
  current output presentation.
