# Quality Review: 003-template-driven-basic-docx

## Verdict

approved

## Separation Of Concerns

- Compiler keeps numbering, bookmark, reference, and citation resolution in
  Core and emits renderer-neutral typed instructions without importing DOCX or
  OOXML implementations.
- DOCX responsibilities remain separated across document, style, font, unit,
  package, list-numbering, and instruction-dispatch helpers.
- `renderers/docx/lists.py` now owns real list numbering construction, while
  `renderer.py` only passes resolved ordered/start/level values and binds runs.
- The original semantic-loss finding is resolved: ordered starts and nested
  levels now reach real `w:abstractNum`, `w:num`, and paragraph `w:numPr`
  structures.

## Component Cohesion / Coupling

- `lists.py` is cohesive: ID allocation, nine-level definitions,
  decimal/bullet formats, indentation, root insertion order, and paragraph
  numbering binding are localized in one DOCX-specific helper.
- Renderer coupling is narrow and typed through `create_list_numbering()` and
  `apply_list_numbering()`.
- The second-review ordering blocker is resolved. New `w:abstractNum` elements
  are inserted before the first existing `w:num`; concrete list-instance
  `w:num` elements are appended after all abstract definitions.
- Multiple list instances remain isolated through distinct `numId` values
  while sharing no mutable Core or Parser state.

## Test Quality

- `test_docx_renderer_preserves_list_start_and_nesting_xml` directly verifies
  ordered start `3`, paragraph levels `0/1/0`, paragraph `numId` presence,
  root element ordering, and that every concrete `num` reference resolves to
  an existing `abstractNumId`.
- The red/green test targets the exact prior failure: before the fix,
  `abstractNum` elements appeared after existing `num` elements; after the
  fix, all abstract definitions precede all concrete instances.
- Focused DOCX tests passed (`3 passed`) and the full suite passed
  (`44 passed`).
- Reviewer-generated ordered and bullet lists additionally verified two
  distinct list instances, nine levels per abstract definition, decimal and
  bullet formats, start `3`, and paragraph levels through level `8`.
- The CLI invalid-output branch still lacks an automated test. Its runtime
  behavior was verified in prior reviews and this is a non-blocking residual
  test gap, not a defect in the 003 list fix.

## Error Handling

- CLI parse/read/build boundaries remain concise and suppress tracebacks at the
  command boundary.
- Numbering creation introduces no new swallowed exception or ambiguous
  fallback path.
- List levels outside the Word-supported range are deterministically clamped
  to `0..8` when bound to paragraphs.

## Reuse / Duplication

- Ordered and bullet lists reuse ID allocation, level construction,
  indentation, insertion, and paragraph binding logic.
- Numbering XML manipulation is not duplicated in the renderer loop.
- No material copy/paste duplication or competing list-numbering abstraction
  was found.

## Complexity Delta

- The added helper complexity is justified by replacing style-only list
  paragraphs with actual editable DOCX numbering objects.
- One abstract definition and one concrete numbering instance per list provide
  deterministic independent starts without leaking OOXML into Core.
- Insertion before the first `w:num` preserves WordprocessingML root ordering
  for both the default numbering part and repeated generated lists.
- The implementation remains small, linear in the fixed nine levels plus list
  items, and does not introduce hidden network, UI, or AI dependencies.

## Required Fixes

- No further fixes are required: the original list semantic-loss blocker and
  the subsequent `numbering.xml` child-order blocker are both resolved by
  `test_docx_renderer_preserves_list_start_and_nesting_xml`, which verifies
  ordered start and nested `ilvl` values, paragraph `numId` bindings, all
  `w:abstractNum` elements preceding all `w:num` elements, and every concrete
  numbering reference resolving to an existing `abstractNumId`.

## Reviewer Commands

- `.venv/bin/python -m pytest tests/test_docx_renderer.py` -> `3 passed`.
- `.venv/bin/python -m pytest` -> `44 passed`.
- `.venv/bin/ruff check .` -> passed.
- `.venv/bin/python -m pip check` -> passed.
- `git diff --check` -> passed.
- Independent ordered/bullet XML probe -> `max(abstractNum index)=10`,
  `min(num index)=11`, and all concrete references resolved to existing
  abstract IDs.
- Independent XML probe -> ordered and bullet definitions each contained nine
  levels; ordered level zero started at `3`; paragraph levels were
  `0,1,0,8`; list instances used distinct `numId` values.
- `/opt/homebrew/bin/soffice --headless --convert-to pdf` on the independently
  generated review DOCX -> passed.
- Reported CodeGraph evidence `ev-ms79z0ze` was not used as sole approval
  proof; approval is based on current source, current tests, generated XML,
  and runtime document loading.
