# Task Report: 001-pdf-export-build-contract

## Status

DONE

## Files Changed

- `src/thesis_forge/application/pdf_preview.py`
- `src/thesis_forge/application/contracts.py`
- `src/thesis_forge/application/services.py`
- `src/thesis_forge/application/office_refresh.py`
- `src/thesis_forge/application/__init__.py`
- `tests/test_pdf_preview.py`
- `tests/test_application_services.py`

## What Changed

- Added typed preview artifact/exporter contracts and optional
  `BuildResult.final_preview`.
- Added validated `%PDF-` export through an isolated LibreOffice profile,
  temporary directory and atomic replacement.
- Kept the core/CLI dependency default disabled; Web and Tauri adapter builds
  opt in explicitly so ordinary CLI builds never launch LibreOffice for preview.
- Preserved successful DOCX output for missing Office, timeout, invalid PDF and
  exporter exceptions.

## TDD Evidence

- Focused tests cover derived paths, signature validation, success, missing
  executable, invalid output, timeout cleanup, atomic replacement and build
  success isolation.
- A regression test locks the core default to
  `pdf_preview_exporter is None`.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_pdf_preview.py tests/test_application_services.py`
  passed in the focused integration run.
- `.venv/bin/python -m pytest` -> `441 passed`.
- `.venv/bin/ruff check .` -> passed.
- `git diff --check` -> passed.

## Concerns

- No task-owned correctness concern remains after the focused exporter/build
  tests, full Python suite, Ruff, and diff validation. Cross-platform native
  Office execution remains a later verification surface.

## Scope Deviations

- None recorded.

## Follow-up Needed

- Six-domain verification should rerun the real LibreOffice export from the
  committed state.

## Adjudication

Implementation is ready for independent review.
