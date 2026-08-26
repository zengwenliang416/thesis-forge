# Task Brief: 004-runtime-protocol

## Goal

Browser and desktop runtimes exchange one DocForge workbench and BuildReport
contract with matching cancellation, progress, diagnostics, output, and preview
authorization behavior.

## Vertical Slice

Add parity fixtures, migrate Python adapters and schemas, migrate TypeScript
DTOs and transports, migrate Rust Tauri validation and authorization, reject old
identifiers, and pass cross-runtime tests.

## In Scope

- Checklist items `4.1` through `4.6`.
- `docforge.workbench.v1`, `docforge.build-report.v2`, typed requests,
  responses, progress, diagnostics, cancellation, output, and final preview.

## Files Allowed

- `src`
- `protocol`
- `frontend/src/transport`
- `frontend/src/state`
- `frontend/e2e`
- `src-tauri`
- `tests/adapters`
- `tests/application`
- `tests/test_adapters.py`
- `openspec/changes/docforge-project-format-v1/development/tasks/004-runtime-protocol`
- `openspec/changes/docforge-project-format-v1/development`

## Components To Create

- Per-language protocol identity constants and shared parity fixtures.

## Components To Reuse

- Existing HTTP and sidecar adapters, `WorkbenchTransport`, build event guards,
  Tauri command bridge, cancellation, stale-result, and preview authorization.

## Components To Extract

- Repeated protocol, report, stage, output, and filename values must have one
  authoritative module in each language boundary.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/adapters tests/application tests/test_adapters.py`
- `pnpm --dir frontend test`
- `cargo test --manifest-path src-tauri/Cargo.toml`

## Stop Conditions

- Python, TypeScript, and Rust contract values cannot be made identical.
- A runtime adapter would implement parser, validator, compiler, or renderer
  behavior.
- Old protocol acceptance is needed to make a test pass.

## Unsafe Assumptions

- Matching field names do not prove runtime guards enforce the same contract.
- A successful build event must not authorize a preview under an obsolete
  BuildReport identity.
