# Task Report: 001-preview-font-adaptation

## Status

DONE

## Files Changed

- `src/thesis_forge/application/pdf_preview.py`
- `src/thesis_forge/application/office_refresh.py`
- `tests/test_pdf_preview.py`
- `tests/test_application_services.py`
- `output/verification/libreoffice-preview-fidelity-p1/*`

## What Changed

- Added a macOS-only installed-font probe and enabled the verified
  `宋体 -> Source Han Serif SC` and `黑体 -> PingFang SC` aliases only when a
  compatible Songti/Heiti family is installed.
- Added a disposable DOCX adapter that preserves ZIP metadata and rewrites only
  WordprocessingML `w:rFonts` and `w:font` attribute values. Non-Word
  namespaces, document text and binary resources remain unchanged.
- Preserved the source DOCX, existing timeout/process cleanup, PDF signature
  validation, previous-PDF retention and atomic publication behavior.
- Restored renderer-owned `styles.xml` and `fontTable.xml` after LibreOffice
  field refresh, including when LibreOffice deletes those parts. Invalid
  refreshed packages now roll back to the original DOCX.

## TDD Evidence

- Added failure-path tests for missing/failed font probing, unavailable
  candidates, non-WordprocessingML namespace lookalikes, deleted renderer-owned
  parts and invalid refreshed ZIP packages.
- The new regression set passed before the broad suite:
  `29 passed` in `tests/test_pdf_preview.py` and `19 passed` in refresh-focused
  application tests.

## Verification Commands

- `.venv/bin/python -m pytest -p no:cacheprovider tests/test_pdf_preview.py -q`
  -> `29 passed`.
- `.venv/bin/python -m pytest -p no:cacheprovider
  tests/test_application_services.py -k refresh -q` -> `19 passed`.
- `.venv/bin/python -m pytest -p no:cacheprovider
  tests/test_template.py tests/test_docx_renderer.py tests/test_pdf_preview.py
  tests/test_application_services.py tests/test_acceptance.py -q`
  -> `254 passed`.
- `.venv/bin/python -m pytest -p no:cacheprovider -q` -> `475 passed`.
- `.venv/bin/ruff check .`, `git diff --check`, and `.venv/bin/python -m pip
  check` -> passed.
- A current complete DOCX exported through `LibreOfficePdfPreviewExporter`
  retained SHA-256
  `b358ea9ea98be1d14cb0f56cf772af747325936ddfe266efdfd8abb5d2210a3d`
  before and after conversion.

## Concerns

- The macOS aliases are integration-specific names verified against
  LibreOffice 26.2.3.2. The installed-family probe prevents use when the
  compatible system families are absent, but future LibreOffice/font changes
  may require refreshing the candidate policy.

## Scope Deviations

- None recorded.

## Follow-up Needed

- Six-domain verification should rebind the current task assertions to a clean
  reviewed Git snapshot and signed validation receipts.

## Adjudication

The prior independent `needs-fix` findings were addressed in production code
and focused regression tests. A fresh independent review is required before
controller completion.
