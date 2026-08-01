# Spec Review: 003-explicit-source-open-atomic-save

## Verdict

approved

## Missing Requirements

- None after review fixes.
- Task `3.1`: desktop open uses readable UTF-8 path I/O; Web open accepts only
  an adapter-provided saved snapshot, opaque handle, and internal service path.
- Task `3.2`: dirty edits remain memory-only and disable Validate/Build.
- Task `3.3`: desktop Save/Save As use one atomic writer; Web workspace save and
  download remain explicit, separate capabilities.
- Task `3.4`: inspect and validation refresh only after persistence returns
  successfully.
- Task `3.5`: tests cover missing files, decoding, permission, replacement,
  Save As, unchanged Save, invalid Web handles, upload/download limits, and
  successful-write/failed-refresh recovery.
- Task `3.6`: validate/build source-byte tests prove controller orchestration
  does not mutate the persisted source.
- Task `3.7`: TDD, validation, CodeGraph, drift, report, and review evidence are
  recorded.

## Extra Behavior

- Existing file mode is preserved during atomic replacement. This is a narrow
  cross-platform safety property of the single source writer and does not
  expand product scope.
- Direct open/reset/disable calls are ignored while persistence is active. This
  closes a state/disk divergence path and matches the immutable action contract.

## Misunderstood Requirements

- The first GREEN implementation allowed a persistence callback to be
  invalidated by direct workspace actions. That could leave disk updated while
  state retained an older saved snapshot; persistence operations are now
  non-cancelable and cannot be superseded before their callback.
- The first review did not validate contradictory or path-like Web handles.
  Handles now require a plain file name and a workspace ID before claiming
  writability.
- Persistence and refresh were clarified as separate outcomes: a refresh error
  after atomic success preserves the newly saved snapshot and retries analysis.

## Cannot Verify From Diff

- Actual browser File System Access behavior, download dispatch, HTTP workspace
  persistence, Tauri native dialogs, sidecar lifecycle, and macOS/Windows
  packaging remain assigned to Slice 004 and Slice 008.
- Frontend DTOs and TypeScript parity fixtures do not exist yet and are not
  claimed by this slice.

## Acceptance Assertions Verified

- `A2`: the reference lifecycle opens one saved snapshot and derives inspection
  plus validation from its persisted internal source path; final outline,
  preview, and browser/Tauri E2E remain later work.
- `A3`: dirty state blocks Validate/Build until persistence succeeds; failed
  persistence retains dirty state and the prior saved snapshot.
- `A6`: source permission and persistence failures preserve prior content and
  expose recovery; render/finalize/cancellation coverage remains Slice 007.
- `A12`: desktop I/O is local and deterministic; Web behavior requires an
  authorized opaque handle and injected persistence seam with no network or
  credential dependency in the reference layer.

## Required Fixes

- None. All review findings were fixed and the final focused suite returned
  `52 passed`.
