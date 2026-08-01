# Spec Review: 005-template-selection-structured-diagnostics

## Verdict

approved

## Missing Requirements

- None. Tasks 5.1 through 5.6 satisfy the Slice 005 brief.
- Fatal diagnostics visibly state the error count and why Build is disabled.
- Diagnostic filters remain rendered and disabled until a source is open.
- Keyboard and pointer activation, source-line focus, and no-line activation
  all have direct test evidence.

## Extra Behavior

- `CommandEnvelope.payload.templatePath` remains as an adapter-only
  compatibility seam. Shared React state and requests use `templateId`, and
  the dispatcher rejects simultaneous selectors.

## Misunderstood Requirements

- None. Fatal-only build blocking, warning-only builds, no-line behavior, and
  frontend/template resolver separation match the brief.

## Cannot Verify From Diff

- Whole-change installed macOS/Windows package acceptance, blocked-socket
  behavior, and assertions owned by Slices 006 through 008 remain outside this
  review.

## Acceptance Assertions Verified

- `A4` is verified: stable `templateId` selection crosses the shared transport,
  the Python adapter resolves it through the existing resolver/search roots,
  and the unchanged validation/build service seam receives a controlled path.
- `A7` is verified for this slice: React depends only on typed transport/state
  boundaries, while the adapter delegates to existing application services.

## Required Fixes

- None.

## Independent Validation

- `pnpm frontend:test` -> `31 passed`.
- `pnpm frontend:e2e` focused review -> `9 passed`, `9 skipped`.
- `.venv/bin/python -m pytest tests/test_adapters.py tests/test_ui_models.py -q`
  -> `25 passed`.
- `.venv/bin/python -m pytest tests/test_architecture.py -q` -> `7 passed`.
