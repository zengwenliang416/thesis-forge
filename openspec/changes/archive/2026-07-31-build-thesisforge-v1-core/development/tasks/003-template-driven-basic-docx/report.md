# Task Report: 003-template-driven-basic-docx

## Status

DONE

## Files Changed

- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/document.py`
- `src/thesis_forge/renderers/docx/fonts.py`
- `src/thesis_forge/renderers/docx/lists.py`
- `src/thesis_forge/renderers/docx/package.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `src/thesis_forge/renderers/docx/units.py`
- `src/thesis_forge/cli.py`
- `tests/test_architecture.py`
- `tests/test_cli.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `tests/test_render_plan.py`
- `docs/TEMPLATE_SPEC.md`

## What Changed

- Added typed renderer-neutral instructions for every current V1 block type,
  inline text, cross-references, citations and footnote references.
- Preserved generic `RenderNode(kind, payload)` and `RenderPlan.nodes`
  compatibility while moving new Compiler behavior to typed dataclasses.
- Added deterministic chapter-aware figure, table and equation counters.
- Added stable Word-safe bookmark names with explicit collision errors.
- Resolved reference display targets and first-use citation order before
  rendering.
- Bound the exact resolved template, template path and section policy into the
  `RenderPlan`.
- Split DOCX page construction, unit conversion, font application, style
  application, list numbering, package reading and instruction dispatch into
  focused modules.
- Applied template-driven page size/orientation/margins, body font/size,
  alignment, indentation/line spacing and heading formatting.
- Replaced smoke `[TODO:*]` paragraphs with editable basic representations for
  semantic types owned by later advanced slices.
- Updated CLI build to reuse the validated template and report concise compiler
  or output errors.
- Documented the Compiler-to-Renderer template application contract.

## TDD Evidence

- Initial focused collection failed because `HeadingInstruction` and
  `BookmarkCollisionError` did not exist.
- The first implementation passed 16 focused tests.
- A later red run caught an indentation error introduced while adding boundary
  coverage; the exact same suite was rerun after repair.
- Final focused suite passed 18 tests.
- Independent quality review found that list `start`, nesting `level` and
  ordinal semantics were not written to numbering XML.
- A review-driven red test reproduced the missing `w:numPr/w:ilvl` and start
  value before the focused list helper was added.
- The same reviewer then found invalid numbering-part ordering; a second red
  test proved a new `abstractNum` followed existing `num` instances.
- The list helper now inserts every definition before the first numbering
  instance and tests every `num -> abstractNumId` relationship.
- Final full suite passed 44 tests.

## Verification Commands

- `.venv/bin/python -m pytest` -> `44 passed in 1.37s`.
- `.venv/bin/ruff check .` -> `All checks passed!`.
- `.venv/bin/python -m pip check` -> `No broken requirements found.`
- `git diff --check` -> no whitespace errors.
- Offline example build -> generated
  `/tmp/thesisforge-003-final.41kLf1/thesis.docx`.
- Generated DOCX -> 17 package parts, 37917 bytes, no `[TODO:]`, East Asian
  font and Heading styles present.
- Review-fix DOCX -> real `abstractNum`, `numId` and paragraph `numPr/ilvl`
  structures, no `[TODO:]`.
- Review-fix DOCX SHA-256 ->
  `420c199d7b1ab774905b28325b9d518df3a85a154b7342ae801fac12c501aafe`.
- CodeGraph development evidence -> `ev-ms78q7o6`, `ev-ms79plyr` and
  `ev-ms79z0ze`, matched with no blockers.
- SpecNav development entry -> `ok:true`.

## Concerns

- Figure relationships, real tables, fields, equations, footnote package parts,
  multiple sections, headers/footers and page fields remain deliberately
  unimplemented here. Their typed instructions and template policy are ready
  for tasks 004 and 005.
- Citation ordering is resolved, but formatted citation and bibliography output
  remains owned by task 006.
- Output is written directly in this slice; task 007 owns atomic replacement
  and preservation of a previous valid output.

## Scope Deviations

- Review-driven `renderers/docx/lists.py` was added to the task packet before
  implementation to keep list OOXML construction out of Renderer dispatch.

## Follow-up Needed

- Task 004 consumes `FigureInstruction` and `TableInstruction` to create real
  image/table objects and caption numbering.
- Task 005 consumes resolved bookmarks/references/section policy to create real
  Word fields, equations, footnotes and page structures.
- Task 006 replaces citation fallback text with local formatted output.
- Task 007 wraps rendering with safe temporary output and atomic replacement.

## Adjudication

The slice meets the basic editable DOCX boundary without claiming advanced Word
objects owned by later tasks. Independent spec and quality reviews both returned
`approved` after the list-numbering findings were fixed and re-reviewed.
