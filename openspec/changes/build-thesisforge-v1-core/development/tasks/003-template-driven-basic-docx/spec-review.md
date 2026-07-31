# Spec Review: 003-template-driven-basic-docx

## Verdict

approved

## Missing Requirements

- None. The reviewer checked `tasks.md` 3.1-3.11 against current source and
  independently executed evidence.
- `3.1-3.2`: `core/render_plan.py` defines typed instructions for every current
  V1 block type while retaining `kind`, `payload`, `to_render_node()` and mixed
  `RenderPlan.nodes` compatibility. `ListInstruction` retains ordered/start and
  item-level semantics without exposing OOXML. `tests/test_render_plan.py` and
  the compiler aggregate test cover the compatibility surface.
- `3.3-3.6`: `core/compiler.py` performs chapter-aware figure/table/equation
  numbering, Word-safe bookmark naming and collision detection, reference
  resolution, citation ordering, exact template/path binding and section-policy
  binding before returning `RenderPlan`. Compiler tests verify `图1-1`,
  `图2-1`, `表1-1`, `(1-1)`, bookmark collision diagnostics, reference targets,
  citation ordinals and the bound template objects.
- `3.7`: the focused RenderPlan, Compiler, DOCX, CLI and architecture suite
  passed with `19 passed`; the full suite passed with `44 passed`.
- `3.8`: DOCX construction, style application, font mapping, unit conversion
  list numbering and package inspection are separated into `document.py`,
  `styles.py`, `fonts.py`, `units.py`, `lists.py` and `package.py`; dispatch
  remains in `renderer.py`. `lists.py` is present in the task brief and context
  `allowed_files`.
- `3.9-3.10`: `create_document()` and `configure_styles()` consume the resolved
  template for page dimensions/orientation/margins, body font/size/alignment,
  indentation/line spacing, and heading font/size/emphasis/alignment/spacing/
  page-break behavior. DOCX list rendering additionally preserves ordered
  starts and item nesting through real `w:abstractNum`, `w:num`, `w:numId` and
  `w:ilvl` structures. A reviewer-created template using 18pt italic Heading 1,
  10pt/6pt spacing and page-break-before produced the corresponding style XML.
- `3.11`: `tests/test_docx_renderer.py` opens the DOCX package and directly
  asserts `w:pgSz`, `w:pgMar`, `Normal` paragraph/font properties, `Heading1`
  properties, landscape orientation and list numbering XML rather than treating
  file existence as proof. The list test also asserts that every concrete
  numbering reference resolves and all `abstractNum` definitions precede
  concrete `num` instances.

## Extra Behavior

- No out-of-scope implementation was detected.
- Real editable list numbering is part of the existing basic list rendering
  contract. The focused `lists.py` helper does not move numbering semantics into
  Parser/Core and does not implement task 004 figure/table or task 005 field,
  bookmark, equation, footnote or section capabilities.
- The reviewer-built package had no media, footnote, header/footer, field or
  bookmark parts/elements. Figures, tables, equations, references, citations
  and footnotes remain editable basic fallback content for tasks 004-006.
- CLI still renders directly to the requested path, leaving atomic replacement
  and failed-build preservation to task 007 as required by this slice boundary.

## Misunderstood Requirements

- None. Compiler owns semantic resolution, RenderPlan remains free of
  python-docx/lxml objects, and Renderer does not import or rerun Parser logic.

## Cannot Verify From Diff

- CodeGraph evidence `ev-ms79z0ze` is recorded as matched, but it was not used as
  sole approval evidence. Prior DOCX hashes and prior SpecNav entry results were
  also not used as substitutes for the incremental review.
- No blocking claim remains unverifiable. Approval uses current source plus
  reviewer-rerun pytest, Ruff, pip and direct package/XML evidence.

## Acceptance Assertions Verified

- `A4`: compiler tests and source inspection verify deterministic numbering,
  bookmarks, references, citation order and section policy before rendering.
  The list change consumes already-compiled ordered/start/level values and does
  not alter Compiler ownership of A4 semantics.
- `A8`: focused tests (`19 passed`), full tests (`44 passed`), architecture
  checks, direct page/style/list package XML tests, `ruff check .`, `pip check`
  and `git diff --check` all passed.

## Required Fixes

- No implementation or test fix is required for this task before spec approval.

## Reviewer Commands

- `.venv/bin/python -m pytest tests/test_render_plan.py tests/test_compiler.py tests/test_docx_renderer.py tests/test_cli.py tests/test_architecture.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- Reviewer Python probe for two independent ordered/bullet list instances,
  ordered start 3, nested/clamped levels, distinct `numId` values, numbering
  schema order, complete abstract-number references and python-docx reload.
- `git diff --check`
