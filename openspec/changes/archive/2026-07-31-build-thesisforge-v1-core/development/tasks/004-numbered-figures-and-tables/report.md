# Task Report: 004-numbered-figures-and-tables

## Status

DONE

## Files Changed

- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/bookmarks.py`
- `src/thesis_forge/renderers/docx/captions.py`
- `src/thesis_forge/renderers/docx/figures.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/tables.py`
- `tests/test_architecture.py`
- `tests/test_cli.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `tests/test_render_plan.py`

## What Changed

- Added renderer-neutral figure width, table row and table cell instructions.
- Resolved figure asset paths relative to the thesis source file in Compiler.
- Implemented explicit figure width precedence, template default width fallback
  and intrinsic-size fallback.
- Compiled pipe-table Markdown into typed header/body rows and aligned cells,
  with explicit malformed-table errors.
- Replaced figure fallback text with real image relationships, media parts and
  `w:drawing` objects.
- Added template-driven figure/table captions with configurable position,
  alignment, font and size.
- Added real matching `w:bookmarkStart` and `w:bookmarkEnd` elements around
  figure and table captions.
- Replaced table Markdown fallback paragraphs with real `w:tbl` objects.
- Added deterministic `three_line`, `grid` and `plain` border policies.
- Prevented empty tables from creating fake table objects.
- Converted invalid image streams into concise build failures without
  traceback leakage.

## TDD Evidence

- Initial focused collection failed because `TableCompilationError` and
  `FigureWidthInstruction` did not exist.
- Compiler and RenderPlan behavior then passed 7 focused tests.
- The first DOCX run failed on the template length construction boundary and
  was fixed by reusing `LengthSpec.model_validate()`.
- The next DOCX run exposed Word twip-to-EMU rounding; the test was corrected
  to assert the actual deterministic package value.
- Independent quality review identified missing intrinsic-size and
  `grid/plain` border coverage; both were added before approval.
- Independent spec review identified an incorrect task-brief state, an empty
  table coverage gap and an uncaught invalid-image build path.
- A dedicated RED test reproduced invalid image exit code `1`; the focused
  figure error wrapper changed it to exit code `2` with no traceback.
- Final full suite passed 54 tests.

## Verification Commands

- `.venv/bin/python -m pytest` -> `54 passed in 1.18s`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
- `.venv/bin/python -m pip check` -> `No broken requirements found.`
- `git diff --check` -> no whitespace errors.
- Offline example build -> `/tmp/thesisforge-004-v2.docx`, 38389 bytes,
  SHA-256 `8834b6a6e21ca29e816202c06e37989f3e9a781813ab2a3003716686371c5e2f`.
- Example package inspection -> one real table, bookmark
  `tf_tbl_objects`, and three-line top/bottom borders.
- Figure/table review build -> `/tmp/thesisforge-004-review/review.docx`,
  37659 bytes, SHA-256
  `25c484757c9dbae530fa8238dee251018c08158a861522fc778c97d990fada5a`.
- Review package inspection -> one drawing, one image relationship, one media
  part, one table and bookmarks `tf_fig_model` / `tf_tbl_results`.
- python-docx reload -> one inline shape and one table.
- LibreOffice headless conversion -> `/tmp/thesisforge-004-review/review.pdf`,
  SHA-256 `253a2286d3fce17282933bd418a7fc9d866bae00b5ace3e6ca83df042e2d3650`.
- CodeGraph development evidence -> `ev-ms7eai06`, `ev-ms7euh9i` and
  `ev-ms7exunz`, matched with no blockers.
- Independent spec review -> approved after fixes.
- Independent quality review -> approved after fixes.

## Concerns

- `compile_document()` intentionally assumes the caller completed fatal
  validation. Direct callers that bypass Validator also bypass resource-root
  enforcement.
- Pipe-table compilation implements the documented container form with leading
  and trailing pipes; escaped pipes and looser Markdown dialects are not part
  of this slice.
- Real `SEQ`, `REF`, TOC, PAGE, OMML, footnote, section, header and footer
  structures remain owned by task 005.

## Scope Deviations

- Added focused `captions.py` after task-packet planning to avoid coupling
  figure and table helpers to each other.
- Added invalid-image CLI coverage and a figure-specific render error wrapper
  after independent spec review exposed an uncaught python-docx exception.

## Follow-up Needed

- Task 005 should reuse `bookmarks.py` while adding fields, references,
  equations, footnotes and page structures.
- Task 007 still owns temporary output and atomic replacement; this task only
  verifies that invalid image decoding does not produce the requested DOCX.

## Adjudication

The slice satisfies tasks 4.1-4.5. Both independent reviews returned
`approved` after their findings were resolved. Approval covers the real
figure/table bookmark subset of A5 only; the remaining advanced Word structures
are explicitly deferred to task 005.
