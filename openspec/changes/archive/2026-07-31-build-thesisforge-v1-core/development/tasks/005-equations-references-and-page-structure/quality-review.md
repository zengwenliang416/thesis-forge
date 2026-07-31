# Quality Review: 005-equations-references-and-page-structure

## Verdict

approved

The latest final checkout closes all six Required Fixes from the prior quality
reviews. No blocking correctness, architecture, cohesion, test-quality,
error-boundary, duplication or complexity finding remains for task 005.

| Previous Required Fix | Status | Current evidence |
| --- | --- | --- |
| 1. Disabled section must not inherit | pass | Later disabled header/footer parts are unlinked, cleared and ignore configured text. |
| 2. Footnote reference must be a real REF | pass | `word/footnotes.xml` contains a complete editable REF field. |
| 3. Shared inline dispatcher and REF helper | pass | Body and footnotes share `render_inline_runs()` and `reference_field_runs()`. |
| 4. Split `compile_document()` | pass | It remains a 32-line orchestrator over bounded planning and compilation helpers. |
| 5. Strengthen OOXML/math/section tests | pass | Focused XML, package, malformed-math, field, bookmark, footnote, section and error-path assertions are present. |
| 6. Typed `DocxRenderError` boundary | pass | Low-level `ValueError` is normalized with capability context while `MathConversionError` remains intentional and unwrapped. |

Independent verification on 2026-07-31:

- `PYTHONPYCACHEPREFIX=/tmp/thesisforge-review-pycache .venv/bin/python -m pytest -p no:cacheprovider`
  -> `72 passed in 2.08s`.
- `.venv/bin/ruff check --no-cache .` -> `All checks passed!`.
- `PIP_NO_CACHE_DIR=1 .venv/bin/python -m pip check` ->
  `No broken requirements found`.
- `git diff --check` exited successfully.
- `git ls-files | wc -l` -> `0`; the repository remains all-untracked, so
  executable lint/tests and direct artifact inspection are the meaningful
  source checks rather than Git diff coverage.
- `/tmp/thesisforge-005-v3.docx` SHA-256 matches the report:
  `43d7e4ecc92028b61a11a1a2ca29ff05042b891cabc1fffb17a966e9ab67a3e6`.
- `/tmp/thesisforge-005-review-v3/review.docx` SHA-256 matches the report:
  `8a215964850bd005e9f01f9f8e568a5f87a77cbb8153fa765974c899c1de5ddf`.
- Independent ZIP validation found 23 valid parts and no compressed-data
  errors.
- Independent package inspection found 3 sections, 1 editable OMML object,
  TOC, figure/table/equation SEQ fields, body REF fields, a footnote REF field,
  update-on-open, 2 header parts and 2 footer parts.
- python-docx reload returned 11 paragraphs, 1 table, 1 inline shape and
  3 sections.
- LibreOffice 26.2.3.2 independently converted the v3 review DOCX to a
  3-page A4 PDF. The new PDF SHA-256 is
  `c6e8274c4d0111e259444d2b9864d3b14fae4169976807c65f1f230cf9456db0`;
  PDF binary hashes vary because LibreOffice writes conversion-time metadata.

The three most recent focused reproductions now produce:

```text
section_header_linked=False
section_footer_linked=False
section_header_text=''
section_footer_text=''
value_error_type=DocxRenderError
value_error_is_docx=True
value_error_capability='equation'
math_error_type=UnsupportedMathError
math_error_preserved=True
math_error_is_docx=False
```

## Separation Of Concerns

- The required architecture remains
  `Parser -> ThesisDocument -> Compiler -> RenderPlan -> DOCX Renderer`.
  Parser and Domain contain no python-docx, OOXML or Renderer dependencies.
- `core/math.py:21-86` defines renderer-neutral semantic math nodes,
  `MathExpression` and the `MathConverter` protocol. OMML construction remains
  isolated in `renderers/docx/equations.py`.
- Compiler owns numbering, labels, bookmark names, reference targets,
  footnote IDs and section transitions. Renderer consumes typed instructions
  and does not parse Markdown or recalculate semantic identifiers.
- `renderer.py` remains orchestration-only for advanced capabilities and
  delegates field, bookmark, equation, footnote and section mutations to their
  focused helpers.
- No Parser, Domain Model, Template schema, bibliography or atomic-output
  scope was pulled into task 005.

## Component Cohesion / Coupling

- `fields.py`, `bookmarks.py`, `equations.py`, `footnotes.py` and `sections.py`
  each own one coherent DOCX capability. Private python-docx/OOXML access is
  localized at those renderer boundaries.
- `sections.py:57-92` now separates disabled-state materialization from visible
  text rendering. A later disabled section still creates an empty,
  non-inheriting part, while text is emitted only when the corresponding
  header/footer is enabled.
- `footnotes.py` owns reserved definitions, positive definitions, body
  references, package-part creation and relationship attachment without
  duplicating general inline type dispatch or REF field semantics.
- `renderer.py:39-55` and `footnotes.py:85-98` use the same
  `InlineHandlers` / `render_inline_runs()` dispatch seam. Unsupported inline
  variants fail explicitly through `DocxRenderError`.
- Page-number fields remain controlled by `PageNumberSpec`, while
  header/footer text remains controlled by `HeaderFooterSpec`; this preserves
  the intended separation between text visibility and numbering policy.

## Test Quality

- The full suite increased from 70 to 72 tests and passes independently.
- `tests/test_docx_renderer.py:660-723` covers enabled-to-disabled section
  transitions with non-empty disabled text, python-docx reload state, explicit
  header/footer relationships, absence of inherited and disabled text, and
  absence of footer fields under `format: none`.
- `tests/test_docx_renderer.py:726-740` directly locks the shared
  `reference_field_runs()` instruction.
- `tests/test_docx_renderer.py:743-764` verifies capability-specific wrapping
  for both `AttributeError` and `ValueError`.
- The CLI unsupported-LaTeX test continues to prove that intentional
  `MathConversionError` behavior reaches the user as exit code 2 without a
  traceback or output file.
- Existing direct XML coverage verifies exact equation bookmark range and
  matching IDs, field begin/instruction/separate/end ordering, dirty state,
  cached results, footnote package wiring, page-number policy and
  update-on-open.
- `tests/test_math.py` covers the documented semantic node families plus empty
  input, incomplete fractions, duplicate scripts, missing braces, missing
  function arguments and unsupported commands.

## Error Handling

- Unsupported and malformed LaTeX retain the typed `MathConversionError`
  hierarchy and do not degrade to text, images or partial OMML.
- `DocxRenderError` carries `capability` and `detail` for private
  python-docx/OOXML failures.
- `renderer.py:158-170` first re-raises `DocxRenderError`, then preserves
  `MathConversionError`, then normalizes `AttributeError`, `KeyError`,
  `TypeError` and `ValueError`. This ordering prevents both raw private-API
  failures and accidental loss of intentional math semantics.
- Document creation/configuration and package attach/save boundaries also
  normalize the relevant low-level exception classes.
- Independent injection confirmed that a low-level equation `ValueError`
  becomes `DocxRenderError(capability="equation")`, while unsupported matrix
  LaTeX remains `UnsupportedMathError`.
- Partial-output cleanup and atomic replacement remain correctly deferred to
  task 007.

## Reuse / Duplication

- `complex_field_runs()` remains the single complex-field XML constructor for
  SEQ, REF, TOC, PAGE and NUMPAGES structures.
- `fields.py:80-88` now provides target-neutral
  `reference_field_runs(reference)` and a paragraph adapter
  `add_reference_field()`.
- Body rendering reaches the shared helper through `add_reference_field()`;
  footnote rendering directly extends its OOXML paragraph with
  `reference_field_runs()`. There is no remaining duplicate
  `REF {bookmark} \h` construction.
- Bookmark allocation and start/end construction remain centralized and reused
  by captions, equations and headings.
- The shared inline dispatcher removes the previous body/footnote branch
  duplication and gives both targets the same supported-type/error behavior.

## Complexity Delta

- `src/thesis_forge/core/compiler.py` remains 662 lines.
- `compile_document()` remains 32 lines (`631-662`) with 4 AST decision nodes,
  compared with 208 lines and 39 decision nodes before the extraction.
- `_compile_block()` is 91 lines with 17 decision nodes and remains a bounded
  typed block factory rather than a document-wide state machine.
- `_resolve_blocks()` is 88 lines with 28 decision nodes and remains the
  largest numbering/bookmark decision surface. Current tests cover it, but
  task 006 should keep bibliography resolution separate rather than expanding
  this function.
- The remaining compiler size is a maintainability watch item, not a task-005
  approval blocker, because the top-level orchestration and newly added
  capability seams are now bounded and independently testable.

## Required Fixes

None for task 005.

Non-blocking follow-up: preserve the current helper boundaries when task 006
adds bibliography behavior, and continue direct package/XML verification for
future private OOXML changes. Interactive Word/WPS review remains outside this
task's completed LibreOffice validation.
