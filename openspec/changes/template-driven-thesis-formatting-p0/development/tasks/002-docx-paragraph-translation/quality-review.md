# Quality Review: 002-docx-paragraph-translation

## Verdict

approved

The latest worktree closes all three previous blocking findings with direct
model, XML and package round-trip evidence. No remaining quality issue requires
task 002 changes before handoff.

## Separation Of Concerns

- `ParagraphStyleSpec` remains renderer input policy. DOCX types, python-docx
  APIs and raw OOXML remain confined to `renderers/docx`; Compiler, RenderPlan
  and Domain are unchanged.
- `configure_styles()` routes Normal and Heading 1-3 through the shared typed
  `apply_paragraph_style()` translator.
- Semantic role recognition and RenderPlan binding are not implemented early.
  Task 003 remains the sole owner of those concerns.
- `BodySpec` owns the newly explicit root font-size constraint. Rejecting
  `body.size: em` in the Template Model prevents a model-valid policy from
  reaching a renderer that has no deterministic absolute base.
- `src/thesis_forge/templates/model.py` is now present in both task brief and
  context allowlists, and the report records the review-driven scope correction.

## Component Cohesion / Coupling

- `styles.py` coherently owns paragraph/style translation and the closed
  renderer-owned named-style registry.
- `fonts.py` remains a focused font-slot helper. Optional font policy and an
  explicit `em_size_pt` input support inherited paragraph policy without
  duplicating Word font XML.
- Supported paragraph properties use python-docx public APIs. Focused raw
  OOXML remains limited to unsupported properties such as `w:outlineLvl` and
  `w:snapToGrid`.
- Optional fields are assigned only when non-`None`, preserving inherited
  Heading behavior. Explicit `False` values remain distinct and produce
  disabled OOXML rather than being treated as omission.
- The two local font-size resolution helpers repeat a small fallback guard, but
  this does not create material coupling or maintenance complexity.

## Test Quality

- Independently reproduced on August 3, 2026:
  `.venv/bin/python -m pytest tests/test_docx_renderer.py tests/test_template.py -q`
  passed `78` tests.
- `.venv/bin/python -m pytest -q` passed `308` tests.
- `.venv/bin/ruff check .` and `git diff --check` passed.
- Body `em` rejection is exercised through `load_template()` and asserts the
  exact `body.size` error path, so the test verifies the public validation
  boundary rather than directly invoking the validator.
- The `single` line-spacing test builds a DOCX and directly asserts package
  `styles.xml` contains `w:lineRule="auto"` and quantized `w:line="240"`.
- Stable style tests combine in-memory idempotency for every registered role
  with package-level `styles.xml`, paragraph `w:pStyle` and python-docx
  save/reopen assertions. They do not rely solely on the registry helper's
  returned wrapper.
- Existing tests quantify target-size `em` conversion in twips, cover fixed and
  multiple line spacing, Heading 1-3, optional inheritance, and explicit
  true/false forms for pagination and grid properties.
- The two-template test preserves ordered semantic text while requiring
  different style XML, avoiding a self-referential implementation assertion.

## Error Handling

- `BodySpec.validate_absolute_body_size()` now rejects root-relative font size
  during YAML validation, before document creation, while preserving heading
  `em` sizes relative to an absolute body size.
- The resulting `TemplateLoadError` retains the precise `body.size` location
  and a specific absolute-unit diagnostic.
- Unsupported registry roles fail deterministically with a chained
  `ValueError`; renderer entry points continue to wrap translation failures as
  `DocxRenderError`.
- Heading-relative size and paragraph-relative lengths have direct positive
  evidence: a `1.5em` heading over a `10pt` body becomes `15pt`, and its `1em`
  indentation becomes `300` twips without a global 12 pt base.

## Reuse / Duplication

- Normal, Heading 1-3 and downstream semantic/TOC/bibliography/header-footer
  consumers can reuse one translator instead of reimplementing paragraph
  formatting.
- Existing `apply_font`, `to_docx_length` and `to_points` helpers are reused;
  no school-specific formatting constants were introduced.
- `PARAGRAPH_STYLE_NAMES` is a closed renderer registry. Templates cannot
  provide arbitrary Word style IDs, and unknown role strings are rejected.

## Complexity Delta

- The implementation increase is proportional to the approved slice: one
  reusable translator, focused OOXML support, target-relative unit resolution
  and stable named styles replace duplicated body/heading formatting.
- Direct paragraph formatting affects existing runs only. There is no current
  production caller, and downstream callers can apply it after run creation;
  this remains a non-blocking API usage constraint.
- CodeGraph evidence `ev-mscqnesn` is matched to
  `development:task-002-docx-paragraph-translation` alongside the original
  task evidence. The evidence index and current CodeGraph status report no task
  002 blocker.
- Unverified task 003-008 claims remain downstream work and do not represent
  premature implementation or a task 002 quality defect.

## Blocking Items

- None.

## Required Fixes

- None.

## Deferred Boundaries

- Task 003 owns semantic role recognition and binding to stable styles.
- Tasks 004-006 own TOC, bibliography and header/footer-specific rendering.
- Tasks 007-008 own complete P0 package, determinism and Word/WPS handoff
  evidence.
