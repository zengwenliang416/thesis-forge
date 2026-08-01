# Task Report: 007-safe-background-build-cancellation

## Status

DONE

## Files Changed

- Python application contracts/services and headless controller
- Python Web HTTP, runtime dispatcher, and sidecar adapters
- Shared React workspace state, transport contract, controls, progress, and
  output presentation
- Web NDJSON and Tauri Channel transports
- Tauri Rust managed-sidecar runner and per-request cancellation registry
- Focused Python, TypeScript, React, browser, and Rust tests

## What Changed

- Added backward-compatible `build_service(..., should_cancel=None)` checks
  before parse, validate, compile, render, finalize, and final atomic
  replacement.
- Added typed `BuildCanceledError`; cancellation remains an
  `ApplicationStageError` while adapters serialize it as `canceled`.
- Added one JSON-safe build event contract with ordered progress and exactly one
  terminal success or typed error event.
- Added incremental Web NDJSON streaming plus explicit per-request cancel. A
  request-owned `threading.Event` remains set after disconnect until the worker
  reaches a terminal boundary, preventing the final-replacement race.
- Added Tauri `run_build`/`cancel_build` commands. Rust forwards sidecar NDJSON
  over `Channel<Value>` and writes one request-specific cancellation marker;
  Python observes the marker through the same application predicate. No
  process is force-killed.
- Added workspace progress, output, error-kind, cancel, retry, repeated-click,
  and generation-token stale suppression. Progress, success, error,
  cancellation, and output from old generations are ignored.
- Added visible ordered stage bars, Cancel Build, retry-capable states,
  actionable failures, and retained last-valid output feedback.

## TDD Evidence

- Initial Python RED stopped during collection because `BuildCanceledError` and
  `stream_json_lines` did not exist.
- The first executable Python GREEN reached `93 passed / 3 failed`; fixes added
  the missing stage import and updated the injected fake seam. Final focused
  backend result is `97 passed`.
- Initial frontend RED returned 4 failed files, 6 failed tests, and one missing
  build-event module. It proved the absence of `runBuild`, build reducer events,
  cancel controls, ordered progress, and output state.
- Frontend GREEN returned `53 passed`. The full suite exposed and fixed one
  compatibility regression where non-build refresh errors incorrectly enabled
  Build retry.
- Direct diff review exposed a Web disconnect race: generator cleanup removed
  the cancellation marker before the worker could observe it. Request-owned
  `Event` cleanup was moved to the worker terminal callback and regression
  tests remained green.

## Verification Commands

- `pnpm frontend:test` -> `53 passed`.
- `pnpm frontend:typecheck` -> passed.
- `pnpm frontend:lint` -> passed.
- `pnpm frontend:build` -> Vite production bundle built.
- `pnpm frontend:e2e` -> `10 passed`, `11` intentional matrix skips.
- Focused Python Slice 007 set -> `97 passed`.
- `.venv/bin/python -m pytest -q` -> `230 passed in 29.81s`.
- `.venv/bin/ruff check .` -> all checks passed.
- `.venv/bin/python -m pip check` -> no broken requirements.
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check` -> passed.
- `cargo test --manifest-path src-tauri/Cargo.toml` -> `4 passed`.
- `cargo check --manifest-path src-tauri/Cargo.toml` -> passed.
- Strict OpenSpec validation -> one change passed.
- CodeGraph -> zero pending changes; evidence `ev-msa2361n` and
  `ev-msa23q6c` matched the Slice 007 claim.
- `git diff --check` -> passed.

## Concerns

- Installed Windows packaging and a visible packaged Tauri UI run remain Slice
  008 acceptance work.
- Independent reviewer agents repeatedly failed to return because of the local
  agent channel/model configuration. The controller therefore performed and
  recorded direct spec and quality reviews instead of claiming independent
  approval.
- Cargo emits only the known external-volume hard-link cache warning and falls
  back to copying.

## Scope Deviations

- None. Parser, validator, template, compiler, bibliography, renderer,
  DOCX/OOXML, AI, account, database, telemetry, signing, and installer behavior
  were not changed.

## Follow-up Needed

- Slice 008 must execute complete browser, macOS, and Windows package/offline
  acceptance, distribution builds, documentation, and six-domain verification.

## Adjudication

Tasks `7.1` through `7.8` are complete with direct spec/quality review,
CodeGraph evidence, and full local gates. The whole change remains incomplete:
Slice 008 and final owning verification/operations contracts are still open.
