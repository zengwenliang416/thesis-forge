# Task Report: 007-safe-and-repeatable-builds

## Status

DONE

## Files Changed

- `src/thesis_forge/application/__init__.py`
- `src/thesis_forge/application/contracts.py`
- `src/thesis_forge/application/output.py`
- `src/thesis_forge/application/services.py`
- `src/thesis_forge/cli.py`
- `src/thesis_forge/renderers/docx/package.py`
- `tests/test_application_services.py`
- `tests/test_architecture.py`
- `tests/test_cli.py`

## What Changed

- Added renderer-neutral application contracts for inspection, validation and
  build results, the approved five progress stages, structured stage failures
  and fatal-validation failures.
- Added shared `inspect_service`, `validation_service` and `build_service`
  entrypoints with injectable Parser, context, Validator, Compiler, Renderer,
  package-validator and replacement dependencies.
- CLI commands now delegate to application services and retain presentation-only
  responsibilities: JSON/table formatting, Chinese diagnostics and exit codes.
- Build now parses once, validates once, reuses the resolved template and
  bibliography database, compiles a `RenderPlan`, and renders only to a unique
  same-directory temporary DOCX.
- Added generic temporary-output cleanup and injected atomic replacement through
  `os.replace`; the requested target is not passed to Renderer and is touched
  only after package validation succeeds.
- Added DOCX smoke validation for ZIP checksums, duplicate parts, required core
  parts, parseable XML, main Word content type, root officeDocument relationship
  and the `w:document` root.
- Build failures now report the exact `parse`, `validate`, `compile`, `render`
  or `finalize` stage without exposing tracebacks.
- Added repeated-build semantic checks for body text, field instructions,
  bookmark names, footnote text and list-numbering levels.

## TDD Evidence

- Initial RED collection failed because `thesis_forge.application` did not
  exist.
- The first implementation GREEN passed 33 focused application, architecture
  and CLI tests.
- A second RED run produced three direct failures because the initial package
  validator accepted a missing main-document content type, missing
  officeDocument relationship and an invalid Word document root.
- Strengthened package validation closed all three failures.
- Direct temporary-context, injected replacement, CRC-corruption and duplicate
  ZIP-part tests were then added, and the final focused suite passed 40 tests.
- Parameterized failure tests cover parser exceptions, validator exceptions,
  fatal validation, Compiler exceptions, partial Renderer output, package
  validation failure and atomic replacement failure.
- Every failure test asserts the previous target bytes remain unchanged and no
  `.tmp.docx` file remains in the target directory.

## Verification Commands

- Focused application/architecture/CLI suite -> `40 passed in 0.95s`.
- Final `.venv/bin/python -m pytest -p no:cacheprovider` ->
  `113 passed in 1.38s`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
- `.venv/bin/python -m pip check` -> `No broken requirements found.`
- Core commands executed with proxy and AI-key variables removed:
  inspect exited zero with the complete structure, validate reported
  `未发现结构性问题`, and both builds exited zero.
- Repeated review builds:
  `/tmp/thesisforge-007-review-a.docx` and
  `/tmp/thesisforge-007-review-b.docx`, each 38,862 bytes and SHA-256
  `33c55eaab205b7111b35f58741248b361230b6e063259a14efb42ec7823808dd`.
- ZIP integrity reported no compressed-data errors; package validation passed
  with 17 parts and no residual same-directory temporary files.
- Normalized semantic comparison returned equal body text, field instructions,
  bookmarks, footnote text and numbering; the review package contains 4 fields
  and 13 bookmarks.
- python-docx reloaded both files with 29 paragraphs and 1 table.
- LibreOffice 26.2.3.2 converted the review DOCX to a 2-page A4 PDF;
  `qpdf --check` reported no syntax or stream encoding errors.
- Review PDF:
  `/tmp/thesisforge-007-pdf-v1/thesisforge-007-review-a.pdf`,
  144,173 bytes, SHA-256
  `0242208c45988d6f60be2b6c4662b4812564442931540a5818cc7d2bad897583`.
- CodeGraph evidence `ev-ms8ot2wa` and review-fix evidence `ev-ms8pgt9s`
  matched with no blockers; all 7 current development claims are verified and
  the development contract passes.
- Independent spec review approved tasks 7.1-7.5 and acceptance assertions
  A1, A7 and A8.
- Initial independent quality review requested direct CRC-corruption and
  duplicate-part package tests; both tests now pass and final quality re-review
  approved the final checkout.

## Concerns

- `os.replace` provides the required atomic replacement only because the
  temporary file is deliberately created in the target directory.
- DOCX determinism is specified and tested semantically; ZIP byte equality was
  also observed for the review build but is not promoted to a public contract.
- The repository remains all-untracked with no baseline commit, so executable
  tests, static checks, package inspection and CodeGraph are the meaningful
  current-checkout evidence.

## Scope Deviations

- None. Product, test and documentation changes remain inside the 007 allowlist.
- No Parser, Domain, Validator, Compiler, content Renderer, Template Model,
  Markdown syntax, UI, AI or task-008 acceptance behavior was changed.

## Follow-up Needed

- Task 008 still owns complete-example expansion and broad Office sensory
  acceptance.

## Adjudication

Implementation evidence and both final independent reviews approve tasks
7.1-7.5 and acceptance assertions A1, A7 and A8.
