# Quality Review: 004-numbered-figures-and-tables

## Verdict

approved

## Separation Of Concerns

- Parser and Domain remain unchanged and contain no Template, Renderer, DOCX
  or OOXML dependencies.
- Compiler owns source-relative path resolution, width policy parsing, table
  structure parsing, numbering and bookmark names.
- Renderer consumes typed instructions and delegates image, caption, bookmark
  and table XML construction to focused DOCX helpers.
- Validator remains the single owner of resource-root and required-template
  style enforcement.

## Component Cohesion / Coupling

- `bookmarks.py` only allocates and writes matching bookmark elements.
- `captions.py` only formats caption text, style and bookmark wrapping.
- `figures.py` only translates width policy and renders image/caption objects.
- `tables.py` only creates table rows/cells and applies border policies.
- `renderer.py` remains orchestration-only and does not parse Markdown.

## Test Quality

- Compiler tests cover source-relative paths, source/template width precedence,
  typed rows/cells, alignment and malformed column counts.
- Direct package/XML tests cover image relationships, media parts, drawings,
  explicit/template/intrinsic widths, caption styles and positions, bookmarks,
  real tables, empty tables and all three border policies.
- CLI tests reproduce invalid image decoding and assert exit code `2`, concise
  output, no traceback and no requested output file.
- Architecture tests keep Core renderer-neutral and Renderer independent of
  Parser.

## Error Handling

- Invalid width and malformed table structures use typed Compiler errors.
- Invalid image streams are converted to `FigureRenderError`, a `ValueError`
  consumed by the existing CLI build boundary.
- Missing, escaped or unreadable resources remain Validator responsibilities
  before Compiler and Renderer.
- No exception is swallowed and no placeholder image/table is produced.

## Reuse / Duplication

- Caption formatting and bookmark XML are shared by figure and table rendering.
- Length conversion reuses the existing `LengthSpec` and DOCX unit helpers.
- Alignment mapping reuses the existing DOCX style mapping.
- Border creation uses one replacement helper for all supported policies.

## Complexity Delta

- No maintained source file exceeds 800 lines.
- `compiler.py` grew to 482 lines but remains the correct semantic owner; new
  parsing helpers are bounded and independently testable.
- New DOCX helpers are 31-107 lines each and have one focused responsibility.
- `renderer.py` remains 128 lines after replacing fallback figure/table logic
  with helper dispatch.
- One new invalid-image error branch replaces an uncaught third-party exception
  with the existing CLI error contract.
- Net entropy is increased with justification; monitor Compiler growth during
  task 005 rather than refactoring this completed slice.

## Required Fixes

- None. Initial review requests for intrinsic-size and `grid/plain` border tests
  were implemented and the task was re-reviewed as approved.

## Reviewer Commands

- `.venv/bin/python -m pytest tests/test_compiler.py tests/test_render_plan.py tests/test_docx_renderer.py tests/test_architecture.py` -> `17 passed` at independent re-review.
- `.venv/bin/python -m pytest` -> `54 passed` in final controller validation.
- `.venv/bin/ruff check .` -> passed.
- `.venv/bin/python -m pip check` -> passed.
