# Spec Review: 001-offline-thesis-inspection

## Verdict

approved

## Missing Requirements

- None for the task-owned slice. Current allowed files cover local environment
  hygiene, stable ID utilities, renderer-neutral domain extensions, V1 parser
  coverage, `inspect` serialization, import-boundary protection, and Markdown
  syntax documentation.

## Extra Behavior

- None blocking.
- `src/thesis_forge/cli.py` still keeps `build` as a smoke DOCX path and
  explicitly warns that TOC/SEQ/REF/OMML/citation rendering is not implemented
  yet. That remains consistent with this task brief's out-of-scope boundary on
  DOCX-rendering feature work rather than silently expanding scope.

## Misunderstood Requirements

- None after the latest parser fix.
- `src/thesis_forge/core/parser.py` now derives inline citation/reference
  locations from the original container caption/body lines and footnote
  continuation lines, which matches the brief's requirement to preserve source
  locations and inline ordering.

## Cannot Verify From Diff

- The repository has no baseline commit, so provenance can only be checked
  against the task packet's `allowed_files` list and current file contents, not
  against a conventional pre/post diff.
- Python 3.11 is declared as the minimum in `pyproject.toml`, but this machine's
  direct evidence covers Python 3.14 plus a separate Python 3.12 editable-install
  run recorded in `validation-log.jsonl`.
- This review is scoped to task `001-offline-thesis-inspection`. Whole-change
  assertions A3-A7 and A9 remain outside this slice and were not treated as
  blocking for task approval.
- For A8, I treated the task-owned static/package/architecture surface as the
  relevant check surface. No OOXML helper or OOXML structure test lives in this
  task's allowed files.

## Acceptance Assertions Verified

- `A1` verified.
  - Current local commands all succeeded without any API-key setup:
    `.venv/bin/thesisforge inspect examples/bachelor-thesis/thesis.md`,
    `.venv/bin/thesisforge validate examples/bachelor-thesis/thesis.md`, and
    `thesisforge build ... -o <temp>/thesis.docx`.
  - The current `inspect` run emitted semantic JSON to stdout only; the current
    `validate` run exited cleanly; the current `build` run wrote only the
    requested temporary DOCX output.
  - `tests/test_cli.py` additionally proves `inspect` returns semantic output
    without mutating the source directory, and that malformed Front Matter plus
    unreadable-path cases exit `2` with concise error text and no traceback.
  - I re-ran both negative CLI cases directly: malformed YAML and missing-file
    `inspect` both returned `exit 2`, printed only the expected error line on
    stdout, and produced no stderr traceback.
- `A2` verified.
  - `tests/test_parser.py` covers the required semantic objects:
    `Heading`, `Paragraph`, `ListBlock`, `Figure`, `Table`, `Equation`,
    `Algorithm`, `Listing`, `FootnoteDefinition`, `CrossReference`, `Citation`,
    `FootnoteReference`, and `Text`.
  - The new location regression test proves exact `(line, column)` preservation
    for container caption citations, container-body citations, and footnote
    continuation citations.
  - `tests/test_architecture.py` enforces that Parser and Domain do not import
    `docx`, `lxml`, renderer, template, UI, or AI layers, and the current
    `src/thesis_forge/core/parser.py` imports only `yaml` plus core model types.
- `A8` verified for this task slice.
  - Current local checks passed: `.venv/bin/python -m pytest -q` returned
    `15 passed`, `.venv/bin/ruff check .` returned `All checks passed!`, and
    `.venv/bin/python -m pip check` returned `No broken requirements found.`
  - `tests/test_architecture.py` passed as part of the current `pytest` run, so
    the architecture import boundary is green.
  - `openspec/changes/build-thesisforge-v1-core/development/validation-log.jsonl`
    matches the current results, records `pip check`, records `git diff --check`
    clean, and records a separate Python 3.12 editable-install run with the
    same `15 passed` result.

## Required Fixes

- None. I found no remaining task-scope blocker in the current allowed files,
  parser tests, CLI behavior, or recorded validation evidence.
