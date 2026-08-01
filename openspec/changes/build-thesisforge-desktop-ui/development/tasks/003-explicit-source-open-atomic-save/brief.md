# Task Brief: 003-explicit-source-open-atomic-save

## Goal

Users can open one authorized Markdown source, edit without autosave, and
explicitly persist it through honest desktop or Web capabilities without
allowing unsaved text to reach validation or build.

## Parent Artifacts

- `openspec/changes/build-thesisforge-desktop-ui/requirements.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.json`
- `openspec/changes/build-thesisforge-desktop-ui/spec-map.json`
- `openspec/changes/build-thesisforge-desktop-ui/component-impact-map.json`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/handoff.md`

## Vertical Slice

Extend the pure-Python workspace reference with explicit desktop open,
desktop atomic Save/Save As, authorized Web snapshot loading, Web
workspace-save/download capability seams, and post-save inspection/validation.
All source persistence remains behind injected adapters.

## In Scope

- Add a reusable local UTF-8 filesystem adapter that writes a same-directory
  temporary file and atomically replaces the target.
- Preserve an existing target when writing or replacement fails and clean up
  temporary files on every outcome.
- Open desktop sources through the filesystem seam and distinguish missing,
  decoding, generic, and permission failures through existing workspace states.
- Load Web sources only from an adapter-provided saved snapshot and internal
  service path; never accept an arbitrary browser-native path.
- Model desktop, writable Web workspace, and Web upload/download capabilities
  explicitly in immutable workspace state and actions.
- Keep dirty edits in memory with no autosave and guard Validate/Build until a
  save operation succeeds.
- Implement desktop Save and Save As plus Web workspace-save and download
  methods through injected persistence seams.
- Refresh inspection and validation only after source persistence succeeds.
- Add strict-TDD tests for open/save paths, failures, capability limits,
  unchanged content, state recovery, and service non-mutation.

## Out Of Scope

- React, TypeScript, Vite, HTTP endpoints, DTO serialization, Tauri commands,
  native dialogs, or Python sidecar lifecycle.
- Browser File System Access API implementation or actual browser download
  dispatch; this slice defines and tests the reference capability seam.
- Autosave, recent files, multi-document workspaces, concurrent file watching,
  external-change conflict resolution, or source version history.
- Template-selection UI, diagnostics localization, outline, preview, build
  cancellation, or DOCX changes.
- Parser, Validator, Compiler, Renderer, or application service behavior
  changes.

## Files Allowed

- `src/thesis_forge/ui/__init__.py`
- `src/thesis_forge/ui/models.py`
- `src/thesis_forge/ui/tasks.py`
- `src/thesis_forge/ui/filesystem.py`
- `src/thesis_forge/ui/controller.py`
- `tests/test_ui_controller.py`
- `tests/test_ui_filesystem.py`
- `tests/test_architecture.py`

## Interfaces / Seams

- `WorkspaceFileSystem.read_text(path)` reads one authorized desktop source.
- `WorkspaceFileSystem.write_text_atomic(path, text)` persists UTF-8 text by
  same-directory atomic replacement.
- `WebWorkspacePersistence.save_workspace(...)` persists to an authorized Web
  workspace and returns the internal path used by application services.
- `WebWorkspacePersistence.download(...)` prepares an explicit download-backed
  saved snapshot and returns its internal service path.
- `WorkspaceController` remains the state reference and calls only injected
  inspect/validate/build and persistence seams.

## Components To Create

- `LocalWorkspaceFileSystem`.
- Immutable Web source handle and source-kind models.
- Web workspace persistence protocol.

## Components To Reuse

- `WorkspaceController`, immutable workspace view models, operation tokens, and
  task runner from Slice 002.
- Existing `inspect_service`, `validation_service`, and `build_service`.
- Standard-library `Path`, `tempfile`, `os.replace`, UTF-8 text I/O, and
  immutable dataclasses.

## Components To Extract

- Keep atomic source replacement in one filesystem adapter instead of
  duplicating it in controller methods or future React/Tauri adapters.
- Keep Web capability branching in one persistence protocol and one action
  derivation path.
- Reuse one post-persistence refresh path for desktop Save, Save As, Web
  workspace save, and Web download.

## API / Data Flow Contracts

- `open_source(path)` reads through `WorkspaceFileSystem`, commits the saved
  snapshot only after read success, then calls inspect and validation.
- `open_web_snapshot(service_path, text, handle)` accepts content and an opaque
  Web handle supplied by a future transport adapter; it performs no native path
  discovery.
- `save()` persists the exact editor text captured when the action starts.
- `save_as(path)` updates the active desktop source path only after atomic
  replacement succeeds.
- `download_source()` is available for Web sources and delegates to the Web
  persistence seam instead of pretending to write a browser-local path.
- Persistence failure retains the prior saved snapshot, editor text, source
  identity, diagnostics, and dirty state.
- Persistence success advances the saved snapshot before inspection and
  validation refresh; a later refresh failure must not claim the write failed.
- Validate and Build always receive the persisted internal source path and are
  unavailable while editor text differs from the saved snapshot.

## State / Error / Empty / Loading Behavior

- Loading: open, save, save-as, download, inspect, or validation work is active;
  repeated persistence is disabled.
- Empty: no source is selected; only Open is available.
- Populated: persisted editor text matches the saved snapshot and refresh
  completed.
- Dirty: editor text differs from the saved snapshot; only supported
  persistence actions are enabled.
- Error: missing files, decoding failures, adapter failures, or refresh failures
  preserve recoverable workspace data.
- Disabled: no new source or persistence action starts.
- Permission: read/write permission failures remain distinct and preserve the
  prior source and saved snapshot.

## TDD Requirement

- TDD Route: strict.
- Record an observed RED for missing open/save APIs and missing atomic writer.
- Add the minimal production behavior in filesystem, desktop lifecycle, and Web
  capability cycles, keeping focused tests green between cycles.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_ui_filesystem.py tests/test_ui_controller.py tests/test_architecture.py -q`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `OPENSPEC_TELEMETRY=0 openspec validate build-thesisforge-desktop-ui --strict --json`
- `SPECNAV_CHANGE=build-thesisforge-desktop-ui OPENSPEC_TELEMETRY=0 node /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js --mode entry --json`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch or edits are required outside the eight allowed
  source/test files.
- Correct behavior requires React, HTTP, Tauri, browser API, parser, compiler,
  renderer, or application-service changes.
- A browser flow would expose or accept an arbitrary native path instead of an
  authorized snapshot/opaque handle.
- Atomic replacement cannot preserve the prior target on failure.
- Save completion cannot distinguish persistence success from later refresh
  failure.

## Unsafe Assumptions

- Do not assume a browser can read or write arbitrary native paths.
- Do not assume a writable Web workspace and a download-only upload have the
  same actions.
- Do not mark a source saved before the persistence seam returns successfully.
- Do not treat a post-save inspect/validation failure as a failed atomic write.
- Do not allow editing or cancellation to make an in-flight persistence result
  ambiguous.
- Do not assume filesystem permission tests are portable without injected
  failures.
