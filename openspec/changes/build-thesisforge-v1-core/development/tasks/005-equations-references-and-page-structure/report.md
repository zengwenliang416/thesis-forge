# Task Report: 005-equations-references-and-page-structure

## Status

DONE

## Files Changed

- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/core/math.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/bookmarks.py`
- `src/thesis_forge/renderers/docx/captions.py`
- `src/thesis_forge/renderers/docx/equations.py`
- `src/thesis_forge/renderers/docx/errors.py`
- `src/thesis_forge/renderers/docx/fields.py`
- `src/thesis_forge/renderers/docx/figures.py`
- `src/thesis_forge/renderers/docx/footnotes.py`
- `src/thesis_forge/renderers/docx/inlines.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/sections.py`
- `src/thesis_forge/renderers/docx/tables.py`
- `docs/MATH_SPEC.md`
- `tests/test_architecture.py`
- `tests/test_cli.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `tests/test_math.py`
- `tests/test_render_plan.py`

## What Changed

- Added a renderer-neutral `MathConverter` protocol, semantic math AST and
  deterministic V1 LaTeX converter.
- Documented the supported operators, scripts, fractions, radicals, sums,
  Greek symbols, functions and accents plus explicit unsupported-input
  behavior.
- Added typed `SequenceInstruction`, `TocInstruction`,
  `SectionBreakInstruction`, numeric footnote IDs and initial section role to
  RenderPlan.
- Extended Compiler to resolve chapter-aware SEQ names/values, footnote IDs,
  front-matter-aware chapter numbering, TOC placement and explicit section
  transitions before rendering.
- Added one reusable complex-field implementation for SEQ, REF, TOC, PAGE and
  NUMPAGES, including begin/instruction/separate/result/end runs and dirty
  update state.
- Added one typed inline dispatcher shared by body and footnote rendering, and
  moved generic REF construction into the field component.
- Replaced static figure/table labels with SEQ fields and static cross-reference
  text with REF fields.
- Narrowed figure/table/equation bookmark ranges to the resolved number so Word
  REF updates do not include caption text or equation content.
- Replaced equation LaTeX fallback text with editable OMML structures for the
  supported math AST and explicit errors for unsupported commands.
- Added real `word/footnotes.xml`, reserved separator definitions, positive
  footnote IDs, document relationships/content types and body references.
- Added template-driven section starts, header/footer parts and relationships,
  first-page policy, Roman/decimal page formats, restart values and PAGE /
  NUMPAGES footer fields.
- Prevented enabled-to-disabled section transitions from inheriting prior
  header/footer text or page fields by materializing empty non-linked parts.
- Disabled header/footer policies now ignore configured text while still
  materializing the empty non-inheriting part required to prevent leakage.
- Body and footnote cross-references now reuse one target-neutral
  `reference_field_runs()` implementation.
- Added `DocxRenderError` to convert private python-docx/OOXML API failures into
  capability-specific build errors, including low-level `ValueError`, while
  preserving intentional `MathConversionError` behavior.
- Split `compile_document()` into a 32-line orchestrator backed by a section
  planner, compilation context, bounded per-block builder and result helpers.
- Added TOC update-on-open through `w:updateFields`.
- Added heading bookmarks so resolved heading references also target real Word
  bookmarks.

## TDD Evidence

- Initial focused collection failed because `core.math`,
  `SequenceInstruction`, `SectionBreakInstruction` and `TocInstruction` did
  not exist.
- Renderer-neutral math, Compiler and RenderPlan tests then passed 12 focused
  tests before DOCX integration.
- First DOCX integration left three failures caused by old static-run
  assertions and the accepted inline `m:oMath` representation; assertions were
  updated to inspect field-aware visible text and real OMML.
- A later test exposed front-matter headings incorrectly incrementing main
  chapter numbering; Compiler now excludes abstract/TOC headings when a front
  matter policy is active.
- A bookmark-range test exposed figure caption text remaining inside the
  bookmark; caption and equation bookmarks now contain only the resolved
  number field.
- A page-policy test proves `format: none` omits PAGE/NUMPAGES even when a
  footer text is enabled.
- A final RED test exposed `cover + main` templates without front matter
  leaving main content in the cover section; Compiler now emits a direct main
  section transition.
- Unsupported matrix LaTeX is reproduced through the real CLI and exits `2`
  with a concise error, no traceback and no output file.
- Independent quality review reproduced inherited disabled headers/footers and
  static footnote references; both paths received dedicated RED tests and
  shared-component fixes.
- Additional tests verify malformed supported math, exact equation bookmark
  pairing/range, per-field dirty/order structure, disabled section inheritance
  and typed private-API failure context.
- The final quality-review RED run reproduced disabled configured text, a
  duplicated REF instruction seam and an unwrapped low-level `ValueError` in
  three focused failures.
- The final GREEN run added one target-neutral REF helper, ignored disabled
  header/footer text and extended the typed error boundary.
- Final full suite passed 72 tests after all review fixes.

## Verification Commands

- `.venv/bin/python -m pytest` -> `72 passed in 1.37s`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
- `.venv/bin/python -m pip check` -> `No broken requirements found.`
- `git diff --check` -> no whitespace errors.
- Offline example build after final review fixes -> `/tmp/thesisforge-005-v3.docx`,
  38829 bytes, SHA-256
  `43d7e4ecc92028b61a11a1a2ca29ff05042b891cabc1fffb17a966e9ab67a3e6`.
- Advanced review build after final review fixes ->
  `/tmp/thesisforge-005-review-v3/review.docx`, 41224 bytes, SHA-256
  `8a215964850bd005e9f01f9f8e568a5f87a77cbb8153fa765974c899c1de5ddf`.
- ZIP integrity -> 23 parts with no compressed-data errors.
- Direct package inspection -> 3 sections, 1 OMML object, TOC plus
  figure/table/equation SEQ and figure/equation REF fields, update-on-open,
  footnotes part/relationship, 2 header and 2 footer parts. The additional
  blank, non-inheriting parts enforce disabled later-section policy without
  leaking prior text or page fields.
- python-docx reload -> 11 paragraphs, 1 table, 1 inline shape and 3 sections.
- LibreOffice 26.2.3.2 headless conversion -> 3-page A4 PDF, SHA-256
  `f0bcda6f0d545c094e03fbfa92caa18cefff61ee03bf8a573f0c17e11666c073`.
- CodeGraph final review-fix evidence -> `ev-ms8d5azt`, matched with no
  blockers and tracing the shared REF helper through footnotes plus the
  section and typed-error regression tests.
- CodeGraph claims check -> all 5 development claims verified with no blockers.
- SpecNav development entry -> `ok:true` with no blockers or warnings.
- Independent spec review -> approved for tasks `5.1-5.8` and acceptance
  assertions `A4`, `A5` and `A8`.
- Independent quality review -> approved after all six review fixes.

## Concerns

- The V1 converter intentionally rejects LaTeX environments, matrices, macros,
  alignment commands and packages; this is documented and fails explicitly.
- Front-matter detection uses stable heading IDs/text for abstract and TOC
  headings because the current Domain Model has no dedicated section marker.
- Word, WPS and LibreOffice can display cached field results differently before
  updating; the package requests update-on-open and stores deterministic result
  text.
- `compiler.py` is 662 lines in total, but `compile_document()` is now 32 lines;
  `_SectionPlanner` and `_compile_block` isolate the added decision surfaces.
- LibreOffice was validated headlessly. Word and WPS were not opened
  interactively in this task.

## Scope Deviations

- `figures.py` and `tables.py` were added to the allowed-file list after the
  initial task packet omitted the existing caption call sites required to pass
  `SequenceInstruction`; the corrected packet passed SpecNav entry before
  review.
- `errors.py` and `inlines.py` were added after independent quality review
  required a typed low-level error boundary and removal of duplicated inline
  dispatch.
- No Parser, Domain Model, Template Model schema, bibliography or atomic-output
  changes were made.

## Follow-up Needed

- Task 006 still owns bibliography loading, citation formatting and
  bibliography output.
- Task 007 still owns temporary output, package smoke validation and atomic
  replacement.
- Task 008 still owns the complete cover/appendix example and broad sensory
  review across the final document.

## Adjudication

Implementation evidence and both independent reviews approve task assertions
5.1-5.8 and acceptance assertions A4, A5 and A8.
