# Spec Review: 004-runtime-protocol

## Verdict

approved

## Missing Requirements

- None within the Task 004 scope. Python, TypeScript, and Rust use the
  versioned DocForge workbench and BuildReport identities, preserve the typed
  build lifecycle, and reject obsolete protocol/report values at the runtime
  boundaries.
- The real HTTP browser receipt remains blocked before HTTP dispatch because
  `frontend/src/components/WorkbenchApp.tsx` still filters for
  `thesisforge.yaml`. This is the explicitly assigned Task 006 picker
  migration, not a missing Task 004 transport requirement.

## Extra Behavior

- No compatibility dispatch, fallback protocol, or second adapter domain model
  was found.
- Obsolete identifiers are retained only as explicit negative-test vectors or
  obsolete constants used by those tests. Product-owned desktop/package names
  and environment variables are outside this task and remain follow-up work.

## Misunderstood Requirements

- None found. The implementation keeps parsing, validation, compilation,
  rendering, finalization, postflight, and preview in the existing application
  services rather than moving those responsibilities into adapters.

## Cannot Verify From Diff

- Installed desktop product identity, packaged sidecar naming, user-visible
  picker terminology, release assets, and repository-wide facticity/sensory
  criteria are owned by later tasks and are not claimed here.
- The failing real HTTP browser flow cannot evaluate HTTP protocol dispatch
  because the UI picker rejects the DocForge manifest before the request is
  sent. Task 006 must close that boundary and Task 008 must rerun the flow.

## Acceptance Assertions Verified

- `A4` (runtime subset): old workbench and BuildReport identifiers are rejected
  before Python application dispatch, Rust sidecar spawn, TypeScript event
  acceptance, or Rust preview authorization. Broader CLI/package/export
  identity remains outside this task.
- `A5` (runtime default-path subset): the shared fixture and Python,
  TypeScript, and Rust contract tests agree on `document.md`,
  `build/document.docx`, `review/document.review.md`, and
  `review/document.review-map.json`.
- `A8`: all three executable language-boundary tests load
  `protocol/runtime-contract.v1.json`; protocol, project/source/output
  identities, ordered stages, diagnostics, BuildReport schema, and preview
  authorization data match the DocForge contract.

## Required Fixes

- None for Task 004.
- Follow-up only: Task 006 must migrate the component picker and remaining
  product-owned desktop terminology; Task 008 must rerun the real HTTP and
  installed desktop receipts afterward.

## Verification Evidence

- `PYTHONPATH=src .venv/bin/python -m pytest tests/adapters tests/application tests/test_adapters.py -q`
  -> `135 passed`.
- `.venv/bin/ruff check src/docforge/adapters src/docforge/application/contracts.py tests/adapters tests/application tests/test_adapters.py`
  -> passed.
- `pnpm --dir frontend typecheck`, `pnpm --dir frontend lint`,
  `pnpm --dir frontend test`, and `pnpm --dir frontend build`
  -> passed; `20` files and `241` tests passed.
- `cargo fmt --check --manifest-path src-tauri/Cargo.toml`,
  `cargo check --manifest-path src-tauri/Cargo.toml`, and
  `cargo test --manifest-path src-tauri/Cargo.toml`
  -> passed; `11` project tests and `32` protocol-contract tests passed.
- `git diff --check -- openspec/changes/docforge-project-format-v1/development/tasks/004-runtime-protocol/spec-review.md`
  -> passed.
