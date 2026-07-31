# Task Report: 006-local-citations-and-bibliography

## Status

DONE

## Files Changed

- `src/thesis_forge/bibliography/__init__.py`
- `src/thesis_forge/bibliography/engine.py`
- `src/thesis_forge/bibliography/bibtex.py`
- `src/thesis_forge/bibliography/formatter.py`
- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/model.py`
- `src/thesis_forge/core/parser.py`
- `src/thesis_forge/core/validator.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/footnotes.py`
- `src/thesis_forge/cli.py`
- `docs/BIBLIOGRAPHY_SPEC.md`
- `docs/MARKDOWN_SPEC.md`
- `tests/fixtures/bibliography/gbt7714-v1.bib`
- `tests/fixtures/bibliography/gbt7714-v1.json`
- `tests/test_architecture.py`
- `tests/test_bibliography.py`
- `tests/test_cli.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `tests/test_parser.py`
- `tests/test_render_plan.py`
- `tests/test_validator.py`

## What Changed

- Replaced the bibliography placeholder with renderer-neutral typed records,
  database, loader and formatter protocols plus explicit typed errors.
- Added a deterministic local UTF-8 BibTeX parser supporting the reviewed V1
  types `article`, `book`, `inproceedings`, `mastersthesis` and `phdthesis`.
- Added malformed input, duplicate key, unsupported type and required-field
  failures without network or required optional dependencies.
- Added the documented GB/T 7714-2025 V1 formatter and reviewed JSON/BibTeX
  golden fixtures while explicitly limiting the compliance claim to the
  documented record subset.
- Added renderer-neutral `BibliographyBlock`, `CitationRun.text`,
  `BibliographyEntryInstruction` and `BibliographyInstruction`.
- Parser now records `::: bibliography` placement without loading BibTeX.
- Validator loads the local database only after resource-root checks, stores it
  in the active `ValidationContext`, reports `invalid-bibliography`, and reports
  each unknown key as `missing-citation` at its Markdown source line.
- Compiler preserves grouped source order, assigns first-use ordinals,
  formats inline citations, emits each cited record once in first-use order,
  omits uncited records, uses the first marker, and appends the bibliography
  when no marker exists.
- Footnote citation ordinals are resolved at the first body
  `FootnoteReference` position rather than the later definition-block position.
- Every validation run clears the context's derived bibliography database
  before executing its active rule set, preventing stale database reuse.
- Body and footnote renderers now consume `CitationRun.text`; the DOCX renderer
  writes bibliography entries as ordinary editable paragraphs and never reads
  BibTeX or chooses citation style.
- CLI validate/build now reuse the database loaded during validation and expose
  localized invalid/missing bibliography diagnostics.

## TDD Evidence

- Initial RED run for bibliography/parser/validator collected 11 tests and
  failed on missing `BibliographyParseError` exports and `BibliographyBlock`.
- Initial RED run for Compiler/RenderPlan/DOCX/CLI/architecture collected 14
  tests and failed on missing formatter, loader, RenderPlan instructions and
  bibliography modules.
- The first GREEN run passed all 47 Compiler/RenderPlan/DOCX/CLI/architecture
  tests and 25 of 26 bibliography/parser/validator tests.
- The one remaining failure was a test-fixture mistake: an existing source
  without a bibliography marker had incorrectly been given a
  `BibliographyBlock` expectation. Correcting that expectation produced the
  final focused `26 passed` and `47 passed`.
- Independent quality review reproduced footnote first-use misordering and a
  stale `ValidationContext.bibliography_database` when default rules were
  replaced.
- Two dedicated RED tests reproduced both findings. Compiler now expands a
  footnote definition's citations at its first reference position, and
  `validate_document()` resets derived bibliography state before each run.
- Final review-fix focused suite passed 75 tests and the full suite passed 90
  tests.

## Verification Commands

- Bibliography/parser/validator focused tests -> `26 passed in 0.49s`.
- Compiler/RenderPlan/DOCX/CLI/architecture focused tests ->
  `47 passed in 1.48s`.
- Review-fix focused tests -> `75 passed in 2.44s`.
- `.venv/bin/python -m pytest -p no:cacheprovider` ->
  `90 passed in 2.68s`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
- `.venv/bin/python -m pip check` -> `No broken requirements found.`
- `git diff --check` -> no whitespace errors.
- Offline example `validate` with proxy variables removed ->
  `未发现结构性问题`.
- Offline example review-fix `build` ->
  `/tmp/thesisforge-006-review-v2.docx`, 38862 bytes, SHA-256
  `4fc3a899fb9ddef94a77582fdf3e7d9ff1519410ba5db894711e198286af4239`.
- ZIP integrity -> 17 parts and no compressed-data errors.
- Direct XML inspection -> body contains `[1]`, the formatted article entry,
  `参考文献` before the entry and `致谢` after it; no raw
  `[@ref-example-1]` remains.
- python-docx reload -> 29 paragraphs; resolved citation and bibliography text
  present, raw citation absent, and the final paragraph sequence preserves
  reference placement before acknowledgements.
- LibreOffice review-fix headless conversion -> 2-page A4 PDF, 144173 bytes,
  SHA-256
  `92f40bff63c5c684cc5d4cc26c830aeaa56521d8a2344f9dfd36b3e8bc88f9f8`.
- CodeGraph final review-fix evidence -> `ev-ms8mm4y1`, confidence `matched`,
  no blockers.
- CodeGraph claims check -> all 6 development claims verified, no blockers.

## Concerns

- GB/T 7714-2025 behavior is intentionally limited to the five documented V1
  record types and reviewed fixtures; broader standard coverage remains future
  work.
- The V1 name formatter targets deterministic Latin-name initials. Full
  multilingual personal/corporate author rules require a broader style backend.
- Multiple bibliography markers intentionally render records only at the first
  marker to preserve the each-key-once contract.
- The repository still has no baseline commit and all files remain untracked;
  executable tests, static checks and direct package evidence are the meaningful
  current-checkout proof.

## Scope Deviations

- None. All product, documentation, fixture and test edits are within the 006
  allowlist.
- No Template Model schema, network service, `citeproc-py` requirement, atomic
  output, UI, account, marketplace or AI behavior was added.

## Follow-up Needed

- Task 007 still owns temporary output, package smoke validation and atomic
  replacement.
- Task 008 still owns the complete final example and broad Office sensory
  acceptance surface.

## Adjudication

Implementation evidence and both final independent reviews approve tasks
6.1-6.6 and acceptance assertions A1, A2, A3, A4 and A8.
