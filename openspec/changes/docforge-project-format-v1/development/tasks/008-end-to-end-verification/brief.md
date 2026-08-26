# Task Brief: 008-end-to-end-verification

## Goal

The breaking migration is proven across static, unit, redteam, E2E, OOXML,
installed Office, facticity, and SpecNav contracts before the importer skill
begins.

## Vertical Slice

Run the complete verification matrix, validate general and academic builds,
inspect generated OOXML and installed macOS behavior, classify remaining old
identities, attach acceptance evidence, and hand off to six-domain verification.

## In Scope

- Checklist items `8.1` through `8.6`.
- Full Python, frontend, Rust, E2E, OOXML, deterministic, installed macOS,
  Microsoft Word, facticity, acceptance, and SpecNav evidence.

## Files Allowed

- `tests`
- `frontend`
- `src-tauri`
- `qa`
- `scripts`
- `examples`
- `openspec/changes/docforge-project-format-v1`

## Components To Create

- Verification evidence, acceptance receipts, task reports and reviews, drift
  and validation logs, and the handoff to six-domain verification.

## Components To Reuse

- Existing pytest, Ruff, frontend, Playwright, Cargo, OOXML, distribution,
  install, preview, CodeGraph, SpecNav, and OpenSpec verification tooling.

## Components To Extract

- Do not create a second test harness when an existing repository validator can
  express the evidence; add focused helpers only for missing contract coverage.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `pnpm --dir frontend typecheck`
- `pnpm --dir frontend test`
- `pnpm --dir frontend test:e2e`
- `cargo fmt --manifest-path src-tauri/Cargo.toml --check`
- `cargo test --manifest-path src-tauri/Cargo.toml`
- `openspec validate docforge-project-format-v1 --strict --json`

## Stop Conditions

- Any executed failure remains unadjudicated.
- Installed Microsoft Word or required macOS package evidence cannot be
  produced.
- An acceptance assertion lacks direct evidence or a remaining active obsolete
  identifier is unexplained.
- The work would begin the separate Markdown importer or npm Agent Skill.

## Unsafe Assumptions

- Passing unit tests does not prove installed desktop, Office, release, or
  cross-language behavior.
- A text scan must distinguish historical evidence from active runtime contract.
