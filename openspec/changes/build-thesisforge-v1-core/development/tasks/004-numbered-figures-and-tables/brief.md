# Task Brief: 004-numbered-figures-and-tables

## Goal

A thesis author can build an editable DOCX containing validated local figures
and Markdown tables as real Word objects, with deterministic chapter-aware
captions, stable bookmarks, template-driven figure widths, caption placement
and table borders.

## Parent Artifacts

- `openspec/changes/build-thesisforge-v1-core/requirements.md`
- `openspec/changes/build-thesisforge-v1-core/acceptance.md`
- `openspec/changes/build-thesisforge-v1-core/design.md`
- `openspec/changes/build-thesisforge-v1-core/prototype/handoff.md`

## Vertical Slice

Extend the existing `FLOW-BUILD` path from validated `Figure` and `Table`
domain blocks, through renderer-neutral structured instructions, into real
DOCX image relationships, drawings, captions, bookmarks and table objects.
The generated package must expose the required relationships and border
structures for direct XML verification.

## In Scope

- Resolve figure asset paths relative to the thesis source file before
  rendering, without mutating source assets.
- Preserve explicit Markdown figure width and fall back to the selected
  template's `figure.default_width`.
- Compile pipe-table source into typed rows and cells in Compiler, while
  retaining the original Markdown compatibility payload.
- Preserve deterministic chapter-aware figure and table numbers already owned
  by Compiler.
- Render real image parts, image relationships and `w:drawing` objects.
- Render figure and table captions above or below their objects according to
  `CaptionSpec.position`, with template-driven alignment, font and size.
- Wrap figure and table captions in real Word bookmarks using the Compiler
  supplied bookmark names.
- Render real `w:tbl` tables from structured instructions.
- Render `three_line`, `grid` and `plain` table border policies from
  `TableSpec.style`, with focused three-line table XML assertions.
- Add Compiler tests and direct DOCX package/XML tests for rows, cells,
  numbering, relationships, drawings, bookmarks, captions and borders.

## Out Of Scope

- New Markdown table or figure syntax and Parser changes.
- New Template Model fields or changes to template YAML schema.
- `SEQ`, `REF`, TOC, PAGE or NUMPAGES fields; task 005 owns Word fields.
- OMML equations, footnote package parts, sections, headers and footers; task
  005 owns those capabilities.
- Bibliography loading or formatting; task 006 owns those capabilities.
- Atomic output replacement; task 007 owns that capability.
- Production UI, network services, accounts or AI-assisted compilation.

## Files Allowed

- `src/thesis_forge/core/__init__.py`
- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/__init__.py`
- `src/thesis_forge/renderers/docx/bookmarks.py`
- `src/thesis_forge/renderers/docx/captions.py`
- `src/thesis_forge/renderers/docx/figures.py`
- `src/thesis_forge/renderers/docx/tables.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/units.py`
- `src/thesis_forge/cli.py`
- `tests/test_architecture.py`
- `tests/test_cli.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `tests/test_render_plan.py`

## Interfaces / Seams

- `compile_document(document, template=None, template_path=None) -> RenderPlan`
- `FigureInstruction` carries a resolved local asset path, requested width and
  Compiler-resolved numbering/bookmark semantics.
- `TableInstruction` carries typed `TableRowInstruction` and
  `TableCellInstruction` values plus the original Markdown compatibility
  payload.
- DOCX figure/table helpers accept typed instructions and template specs; they
  do not import Parser or calculate numbering.
- Bookmark helpers accept valid Compiler-generated names and create matching
  `w:bookmarkStart` and `w:bookmarkEnd` nodes.

## Components To Create

- Renderer-neutral table row and cell instruction dataclasses.
- DOCX bookmark helper reusable by later object renderers.
- DOCX caption helper for shared text, font, alignment and bookmark behavior.
- DOCX figure helper for image insertion, width selection and caption layout.
- DOCX table helper for object creation, caption layout and border policy.
- Direct package/XML regression tests for figures and tables.

## Components To Reuse

- Existing `Figure`, `Table`, `ThesisDocument` and stable semantic IDs.
- Existing Compiler chapter counters, labels and bookmark naming.
- Existing `FigureSpec`, `TableSpec`, `CaptionSpec` and `LengthSpec`.
- Existing DOCX document, font, unit and package helpers.
- Existing Parser and Validator guarantees for semantic containers and local
  image existence.

## Components To Extract

- Bookmark XML creation is centralized in `renderers/docx/bookmarks.py`.
- Shared caption formatting is centralized in `renderers/docx/captions.py`.
- Figure relationship, drawing, sizing and caption behavior is centralized in
  `renderers/docx/figures.py`.
- Table construction and border policy is centralized in
  `renderers/docx/tables.py`.
- Markdown pipe-table parsing remains a Compiler helper and never moves into
  Renderer.
- Renderer instruction dispatch remains orchestration-only.

## API / Data Flow Contracts

- Build completes Parser and fatal validation before Compiler or Renderer.
- Compiler resolves source-relative figure paths and structured table cells.
- Renderer consumes only RenderPlan instructions and selected template values.
- Explicit figure width takes precedence over template default width; absent
  values preserve the image's intrinsic size.
- Caption text combines the Compiler-resolved label and source caption without
  recalculating the number.
- Bookmark names are supplied by Compiler and are not regenerated by Renderer.
- Three-line tables contain only top, header-bottom and bottom horizontal
  rules; they contain no vertical or ordinary internal horizontal rules.
- Same document, source path and template produce the same instruction rows,
  cells, numbers, captions, bookmark names and border policy.
- Source Markdown, template YAML and image assets remain read-only.

## State / Error / Empty / Loading Behavior

- Loading: all figure and table compilation/rendering is synchronous and local.
- Empty: an empty table payload compiles to no rows and renders no fake table.
- Error: malformed pipe-table structure fails explicitly during Compiler
  semantic compilation; image decoding or rendering errors propagate through
  the existing build failure boundary.
- Disabled: fatal validation blocks build when a used figure/table semantic
  object lacks its required template section; Renderer fallbacks do not
  authorize bypassing that validation contract.
- Permission: unreadable assets remain validation/source failures before
  rendering; this slice does not add filesystem write locations.

## TDD Requirement

- TDD route is strict.
- Add focused failing Compiler and DOCX XML tests and observe the expected RED
  state before production-code changes.
- Run focused tests after each behavior group, then full regression checks.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_compiler.py tests/test_render_plan.py tests/test_docx_renderer.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `.venv/bin/thesisforge build examples/bachelor-thesis/thesis.md -o /tmp/thesisforge-004.docx`
- Direct ZIP/XML inspection of `/tmp/thesisforge-004.docx`.
- `git diff --check`
- SpecNav development entry, task review checks and CodeGraph claim checks.

## Stop Conditions

- Scope lock mismatch or edits outside the allowed files.
- Parser or Domain would need to import Template, Renderer, DOCX, UI or AI.
- Renderer would need to parse Markdown, resolve source-relative paths,
  calculate numbers or generate bookmark names.
- A missing image or invalid semantic structure would be silently replaced by
  placeholder text.
- Completing the slice would require Word fields or advanced capabilities owned
  by tasks 005-007.
- Direct XML tests or either independent review fails.

## Unsafe Assumptions

- Do not assume python-docx creates school-compliant captions or table borders.
- Do not assume Markdown table source is safe to parse inside Renderer.
- Do not assume figure paths are relative to the current process directory.
- Do not assume explicit and template figure widths use the same source type
  without conversion.
- Do not use ordinary caption text as evidence that a bookmark exists.
- Do not claim `SEQ` or `REF` behavior from deterministic static caption text.
