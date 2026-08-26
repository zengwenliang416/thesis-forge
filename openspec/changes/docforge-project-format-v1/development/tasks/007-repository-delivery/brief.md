# Task Brief: 007-repository-delivery

## Goal

Examples, documentation, CI, installers, and release downloads demonstrate one
DocForge project format without mixed active ThesisForge contracts.

## Vertical Slice

Convert repository-owned projects and docs, update build and release automation,
add obsolete-identity facticity checks, and build a release-grade macOS artifact
with verified contents and names.

## In Scope

- Checklist items `7.1` through `7.5`.
- Active examples, fixtures, docs, schemas, CI, scripts, distribution
  allowlists, installers, release workflows, and macOS artifact validation.

## Files Allowed

- `examples`
- `tests/fixtures`
- `docs`
- `protocol`
- `qa`
- `scripts`
- `.github`
- `.woodpecker`
- `templates`
- `pyproject.toml`
- `package.json`
- `README.md`
- `Makefile`
- `tests/test_desktop_distribution.py`
- `openspec/changes/docforge-project-format-v1/development/tasks/007-repository-delivery`
- `openspec/changes/docforge-project-format-v1/development`

## Components To Create

- Active-runtime obsolete-identity facticity checks.
- Release artifact assertions for DocForge names and contents.

## Components To Reuse

- Existing examples, distribution tests, build scripts, Woodpecker workflows,
  GitHub release flow, installer packaging, checksums, and maintenance docs.

## Components To Extract

- Repeated package, executable, installer, release asset, manifest, source, and
  output identity belongs in shared packaging configuration or checked constants.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_desktop_distribution.py tests/cli tests/project`
- `.venv/bin/ruff check scripts tests/test_desktop_distribution.py`
- `pnpm --dir frontend build`
- `cargo check --manifest-path src-tauri/Cargo.toml`

## Stop Conditions

- A command would push, publish, tag, upload, or deploy without separate
  authorization.
- Historical OpenSpec evidence or valid academic prose would be rewritten by a
  blanket term replacement.
- CI changes conflict with unrelated existing dirty workflow edits.

## Unsafe Assumptions

- A passing local build does not prove release asset names or installer contents.
- Every ThesisForge occurrence is not invalid; historical evidence must be
  classified.
