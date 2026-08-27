# Task Report: 007-repository-delivery

## Status

DONE

## Files Changed

- Active projects and fixtures under `examples/`, `tests/fixtures/`, `qa/`, and
  the phase-zero template-package sample.
- Active user and maintainer documentation under `README.md` and `docs/`.
- Distribution and release automation under `scripts/`, `.github/`,
  `.woodpecker/`, `pyproject.toml`, `package.json`, and Tauri packaging
  metadata.
- `scripts/check_facticity.py` and its focused regression coverage.
- Task-local development evidence under this task directory and the shared
  development ledger.

## What Changed

- Converted repository-owned active project entrypoints to `docforge.yaml`,
  `document.md`, neutral Review filenames, and general or academic templates
  appropriate to each fixture.
- Updated active commands, package names, application identity, sidecar names,
  installer names, checksums, CI checks, and release asset paths to DocForge.
- Preserved historical ThesisForge records and explicit obsolete-input vectors
  instead of applying a blanket text replacement.
- Added a classified facticity scanner that fails on obsolete active manifest,
  schema, command, package, protocol, sidecar, default-output, Review-output,
  release, product, or domain-model identities.
- Built and verified `DocForge.app` and
  `DocForge_0.1.0_aarch64.dmg`, including the managed sidecar, offline
  operations, application metadata, artifact names, and checksums.

## TDD Evidence

- Desktop-distribution tests assert DocForge application, executable, sidecar,
  installer, workflow, and release names and reject obsolete active names.
- Facticity tests cover active findings, explicit negative vectors, historical
  evidence, binary and AppleDouble exclusions, and active Template Package V2
  surfaces.
- General and academic repository fixtures are exercised by CLI, project,
  distribution, acceptance, QA, parser, compiler, and renderer tests.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_facticity.py tests/test_desktop_distribution.py tests/cli
  tests/project -q`
  -> `169 passed in 1.13s`.
- `.venv/bin/ruff check scripts tests/test_facticity.py
  tests/test_desktop_distribution.py`
  -> passed.
- `PYTHONPATH=src .venv/bin/python scripts/check_facticity.py
  --json /tmp/docforge-facticity.json --markdown
  /tmp/docforge-facticity.md`
  -> `ok: true`, `activeFindingCount: 0`,
  `allowedFindingCount: 325`, `scannedFiles: 332`; the allowlisted findings
  include 12 historical or explicit-negative `ThesisDocument` references.
- `pnpm --dir frontend build` -> passed.
- `cargo check --manifest-path src-tauri/Cargo.toml` -> passed.
- `PYTHONPATH=src .venv/bin/python
  scripts/verify_desktop_distribution.py --platform macos --bundle-root
  src-tauri/target/release/bundle`
  -> `ok: true`; DocForge application, DMG, sidecar, offline operations,
  cancellation, build, and reopen checks passed.

## Concerns

- Local packaging does not claim that a GitHub Release was published. External
  tagging, upload, and publication remain separate authorized operations.
- Historical filenames and product names remain in archived specifications,
  migration tools, negative tests, and binary artifacts; the facticity report
  classifies rather than erases them.

## Scope Deviations

- The active Template Package V2 sample and compatibility schema were migrated
  because they are repository-owned delivery surfaces consumed by current
  tests and packaging checks.

## Follow-up Needed

- Task 008 must bind A4 and A10 to the committed HEAD through trusted
  verification receipts.
- Publication of a release remains outside this local implementation task.

## Adjudication

Items 7.1 through 7.5 have direct implementation and local artifact evidence.
Independent spec and quality reviews approved the final Task 007 slice. No
external publication is claimed.
