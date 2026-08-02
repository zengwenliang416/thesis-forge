# Task Report: 003-explicit-source-open-atomic-save

## Status

DONE

## Files Changed

- `src/thesis_forge/ui/__init__.py`
- `src/thesis_forge/ui/models.py`
- `src/thesis_forge/ui/tasks.py`
- `src/thesis_forge/ui/filesystem.py`
- `src/thesis_forge/ui/controller.py`
- `tests/test_ui_controller.py`
- `tests/test_ui_filesystem.py`
- `tests/test_architecture.py`

## What Changed

- Added `LocalWorkspaceFileSystem` with exact UTF-8 reads, same-directory
  temporary writes, flush/fsync, existing-mode preservation, `os.replace`, and
  unconditional temporary-file cleanup.
- Added explicit desktop, Web workspace, and Web upload source kinds plus an
  immutable `WebSourceHandle` that rejects path-like names, blank workspace
  identifiers, and writable handles without a workspace identity.
- Added desktop `open_source`, `save`, and `save_as` controller flows.
- Added adapter-provided `open_web_snapshot`, writable workspace `save`, and
  upload/read-only `download_source` flows without accepting browser-native
  paths.
- Added distinct `can_save_as` and `can_download` actions while preserving
  dirty-state Validate/Build guards and no-autosave behavior.
- Split persistence and refresh into separate operation tokens. A successful
  write advances the saved snapshot before inspect/validation; later refresh
  failure remains recoverable without falsely reporting that persistence
  failed.
- Prevented editing, cancellation, opening, reset, or disablement from
  invalidating an in-flight persistence callback.
- Kept inspect, validation, and build routed through injected application
  services and added source-byte preservation tests.

## TDD Evidence

- Initial RED: focused collection failed with two import errors because
  `LocalWorkspaceFileSystem` and `thesis_forge.ui.filesystem` did not exist.
- Initial GREEN: atomic I/O, source lifecycle, Web capability, and architecture
  implementation returned `44 passed`.
- Persistence-race review added a direct-action invalidation test; the guarded
  implementation returned `45 passed`.
- Final review added invalid Web handle cases and successful-write/failed-refresh
  recovery coverage; the focused suite returned `52 passed`.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_ui_filesystem.py
  tests/test_ui_controller.py tests/test_architecture.py -q` -> `52 passed`.
- `.venv/bin/python -m pytest -q` -> `178 passed in 7.37s`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
- `.venv/bin/python -m pip check` -> `No broken requirements found.`
- `git diff --check` -> no whitespace errors.
- `find openspec -name '*.json' ... jq empty` -> all JSON files valid.
- `OPENSPEC_TELEMETRY=0 openspec validate
  build-thesisforge-desktop-ui --strict --json` -> one change passed, zero
  failed.
- CodeGraph evidence `ev-ms9ubt02` matched final desktop/Web lifecycle,
  persistence guards, handle validation, refresh semantics, and tests with no
  blockers.

## Concerns

- The Python controller is intentionally a backend state reference, not the
  browser implementation. Slice 004 must prove TypeScript parity through shared
  fixtures rather than importing this controller into the frontend.
- Browser download dispatch and workspace persistence remain adapter behavior;
  this slice defines and tests the capability contract only.

## Scope Deviations

- None. Production/test edits remained inside the eight allowed files.
- No Parser, Validator, Compiler, Renderer, HTTP, React, Tauri, sidecar, DOCX,
  database, network, or credential behavior was added.

## Follow-up Needed

- Slice 004 must add versioned DTO fixtures and run the same source lifecycle
  transitions against TypeScript workspace state.
- Web HTTP and Tauri sidecar adapters must implement the persistence protocols
  without exposing internal service paths in serialized responses.
- Browser/Tauri native open, save, download, and dialog E2E remain required in
  Slice 004 and final Slice 008 acceptance.

## Adjudication

Tasks `3.1` through `3.7` are complete. Slice 003 contributes verified
reference behavior to `A2`, `A3`, `A6`, and `A12`; full browser/macOS/Windows
acceptance remains assigned to later slices. Dedicated spec and quality reviews
approved the final implementation after all findings were fixed.
