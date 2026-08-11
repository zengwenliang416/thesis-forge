# Task Report: 002-libreoffice-refresh

## Status

DONE

## Files Changed

- `src/thesis_forge/application/office_refresh.py`
- `tests/test_application_services.py`
- `tests/conftest.py`

## What Changed

- Added injectable `DocumentRefresher` and default `LibreOfficeDocumentRefresher`.
- Added macOS, Linux and Windows executable discovery plus an executable Python
  probe that must successfully import UNO.
- Added one-process-per-build headless refresh with an isolated user profile,
  private UNO pipe, hidden load, macro/external-update restrictions, same-file
  save, timeout and cleanup.
- Added empty-cache fallback that creates a real `ContentIndex` at the stable
  `tf_toc_index` bookmark and derives its maximum level from the Word TOC field.
- Added Windows suspended process creation, Job Object ownership with
  `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, assign-before-resume ordering and
  deterministic job/process/thread handle cleanup.

## TDD Evidence

- Discovery tests cover macOS bundles, Windows Program Files, Linux PATH,
  explicit overrides and missing runtimes.
- Failure tests cover disabled refresh, incompatible UNO Python, no TOC field,
  timeout, runner failure, corrupt writes and restoration of the original DOCX.
- Process tests cover headless arguments, unique profile/pipe state, profile
  removal, Windows taskkill fallback, Job Object configuration, assign-before-
  resume ordering, assignment failure, resume failure and cleanup error paths.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_application_services.py -q`
  -> `64 passed`.
- `.venv/bin/python -m pytest tests/test_application_services.py -k 'windows_' -q`
  -> `7 passed`.
- `.venv/bin/ruff check src/thesis_forge/application/office_refresh.py tests/test_application_services.py`
  -> `All checks passed`.
- Real macOS LibreOffice 26.2.3.2 headless refresh completed without residual
  LibreOffice processes or `thesisforge-lo-*` profiles.

## Concerns

- Windows and Linux discovery and process lifecycle are covered by deterministic
  tests but still require target-native runtime verification before release.

## Scope Deviations

- None recorded.

## Follow-up Needed

- Run the existing target-native Windows distribution gate with LibreOffice
  installed before claiming Windows runtime acceptance.

## Adjudication

Approved against tasks 2.1-2.3 and acceptance assertions `A2` and `A3` after
independent process-lifecycle review.
