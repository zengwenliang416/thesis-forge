# Task Report: 004-optional-pyside6-workbench-shell

## Status

DONE

## Files Changed

- `package.json`
- `frontend/**`
- `src-tauri/**`
- `src/thesis_forge/adapters/**`
- `tests/fixtures/workspace-state-v1.json`
- `tests/test_adapters.py`
- `tests/test_frontend_contract.py`

## What Changed

- Added one React 19 + TypeScript + Vite frontend shared by Web and Tauri 2.
- Added the `WorkbenchApp` orchestration layer and extracted
  `WorkbenchShell`, `ProductBar`, `StatusStrip`, `OutlinePanel`,
  `MarkdownEditor`, `PaperPreview`, `DiagnosticsPanel`, `TemplateSelector`,
  `BuildProgress`, and `OutputFeedback`.
- Added immutable TypeScript workspace state, capability-aware actions,
  operation generations, stale-completion suppression, dirty guards, explicit
  save, post-save inspect/validation refresh, and recoverable error states.
- Added a versioned `thesisforge.workbench.v1` DTO contract and strict response
  validation.
- Added `WebWorkbenchTransport` over `/api/v1` and
  `TauriWorkbenchTransport` over one command bridge. Shared components do not
  call `fetch`, Tauri `invoke`, Python, or compiler modules directly.
- Added opaque Web workspaces, atomic Web/desktop source save dispatch,
  JSON-safe inspection/validation/build mapping, WSGI HTTP dispatch, and a
  JSON-lines Python sidecar over existing application services.
- Added a Tauri 2 Rust shell, native Markdown picker, request validation, and
  sidecar process bridge for macOS and Windows targets.
- Added desktop, minimum-window, and mobile behavior coverage. A visual review
  found intrinsic grid overflow that ordinary visibility checks missed; direct
  viewport bounding-box assertions now prevent recurrence.
- Retained the historical task ID for ledger compatibility only. No PySide6,
  PyQt, Electron, or second frontend tree was introduced.

## TDD Evidence

- Baseline: `11` frontend unit tests passed, while Playwright exposed one
  mobile launch failure because the product identity was hidden.
- First RED: frontend returned `6 failed, 11 passed`; Python adapters returned
  `2 failed, 7 passed`; the Rust protocol test returned `1 failed, 3 passed`;
  mobile Playwright returned two failures.
- First GREEN: explicit save/refresh, path-safe Web output, error recovery,
  mobile identity, and Rust payload validation returned `17` frontend unit,
  `9` Python adapter, `4` Rust protocol, and `4` executed Playwright tests
  passing.
- Protocol RED/GREEN: unexpected Python failures and incomplete TypeScript
  envelopes failed first, then passed after transport normalization and strict
  response validation. Counts reached `18` frontend unit and `10` adapter
  tests.
- Recovery RED/GREEN: a successful save followed by failed refresh could
  recover without revalidation. The new test failed, then passed after recovery
  was changed to rerun inspect and validation. Frontend count reached `19`.
- Sensory RED/GREEN: mobile controls were technically visible but had right
  edges beyond the `393px` viewport. Bounding-box RED observed
  `427.8125 > 393`; grid-child `min-width: 0` made the direct viewport test
  pass.

## Verification Commands

- `pnpm --dir frontend install --frozen-lockfile` -> lockfile current.
- `pnpm frontend:test` -> `19 passed`.
- `pnpm frontend:typecheck` -> passed.
- `pnpm frontend:lint` -> passed.
- `pnpm frontend:build` -> production Vite bundle built.
- `pnpm frontend:e2e` -> three viewport projects, `8 passed`, `7` intentional
  runtime-specific skips.
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check` -> passed.
- `cargo test --manifest-path src-tauri/Cargo.toml` -> `4 passed`.
- `cargo check --manifest-path src-tauri/Cargo.toml` -> passed.
- `cargo run --manifest-path src-tauri/Cargo.toml` -> macOS shell compiled and
  entered the application event loop; process was then stopped intentionally.
- `.venv/bin/python -m pytest tests/test_adapters.py
  tests/test_frontend_contract.py tests/test_architecture.py -q` -> `20 passed`.
- `.venv/bin/python -m pytest -q` -> `191 passed in 9.67s`.
- `.venv/bin/ruff check .` -> all checks passed.
- `.venv/bin/python -m pip check` -> no broken requirements.
- strict OpenSpec validation -> one change passed, zero failed.
- SpecNav development entry -> `ok:true`, no blockers or warnings.
- CodeGraph development contract -> all four required claims verified;
  evidence `ev-ms9wkbhd` matched Slice 004 with no blockers.
- all OpenSpec JSON parsed with `jq`; `git diff --check` passed.

## Concerns

- Windows installer execution and signed macOS/Windows package acceptance are
  intentionally not claimed; they remain Slice 008.
- Build cancellation, streamed progress, final output presentation, template
  diagnostics, and renderer-neutral preview data remain Slices 005-007.
- The Web adapter is tested as a WSGI contract and through Playwright HTTP
  interception. Production hosting/operation setup remains a later acceptance
  concern.

## Scope Deviations

- None. Parser, Validator, Compiler, RenderPlan, Renderer, template,
  bibliography, DOCX, database, account, AI, and telemetry semantics were not
  changed.
- The approved prototype remained read-only.

## Follow-up Needed

- Slice 005: bind template selection and structured diagnostics.
- Slice 006: replace shell outline/preview fixtures with renderer-neutral data.
- Slice 007: add cancellable background build, streamed progress, and final
  output/error presentation.
- Slice 008: run complete Web/macOS/Windows packaging and cross-host E2E.

## Adjudication

Tasks `4.1` through `4.9` are complete. Slice 004 contributes verified evidence
to `A1`, `A2`, `A3`, `A7`, `A8`, `A10`, `A11`, and `A12`; final installer and
cross-host acceptance remains assigned to Slice 008. Spec and quality reviews
approved the implementation after all findings were fixed.
