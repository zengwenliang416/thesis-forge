# Task Report: 002-docx-paragraph-translation

## Status

DONE

## Files Changed

- `src/thesis_forge/renderers/docx/styles.py`
- `src/thesis_forge/renderers/docx/fonts.py`
- `src/thesis_forge/templates/model.py`
- `tests/test_docx_renderer.py`
- `tests/test_template.py`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence.jsonl`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence-index.json`

## What Changed

- Extracted `apply_paragraph_style()` as the single typed translator for a
  validated `ParagraphStyleSpec` applied to a Word paragraph style or concrete
  paragraph.
- Migrated Normal and Heading 1-3 configuration to the translator.
- Added font, size, emphasis, alignment, left/right/first-line/hanging
  indentation, paragraph spacing and fixed/multiple/single line-spacing
  translation.
- Added explicit widow, keep-lines, keep-next, page-break, outline-level and
  snap-to-grid handling, including false-value OOXML.
- Resolved `em` indentation and spacing from the target style font size.
  Relative heading font sizes use the body font size as their explicit base
  instead of a global 12 pt assumption.
- Added a closed stable semantic named-style registry and rejected arbitrary
  Word style IDs.
- Rejected `body.size: em` during template validation because the root body
  style has no deterministic absolute font-size base; heading `em` sizes
  remain supported relative to the validated body size.
- Preserved existing Heading keep-next/keep-lines XML when optional template
  pagination fields are omitted.

## TDD Evidence

- Initial focused collection failed because `apply_paragraph_style` and
  `ensure_paragraph_style` did not exist.
- The first implementation run exposed the installed python-docx
  `ParagraphStyle` import path and wrapper-identity behavior; tests and typing
  were corrected against the actual dependency.
- Code review found and fixed optional `None` assignments that would have
  removed built-in Heading keep-next/keep-lines behavior.
- Independent quality review found and closed body-size validation, single
  line-spacing quantization and stable-style package round-trip gaps.
- Added direct `styles.xml` and paragraph XML assertions for every common
  property, Heading 1-3, target-size `em` conversion, all stable role IDs,
  arbitrary style rejection, single spacing, package reopen and two-template
  semantic equivalence.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_docx_renderer.py tests/test_template.py -q`
  -> `78 passed`.
- `.venv/bin/python -m pytest -q` -> `308 passed`.
- `.venv/bin/ruff check .` -> `All checks passed`.
- `git diff --check` -> passed.
- CodeGraph evidence `ev-mscq4qfn` and final review-fix evidence
  `ev-mscqnesn` matched
  `development:task-002-docx-paragraph-translation`.

## Concerns

- Stable semantic styles are created by the shared helper but are not yet
  selected by RenderPlan instructions; role recognition and binding remain
  task 003.
- TOC tabs, bibliography presentation and header/footer paragraph use remain
  deferred to tasks 004-006.

## Scope Deviations

- Independent review required a narrow Template Model correction so
  `body.size: em` fails before rendering. `src/thesis_forge/templates/model.py`
  was added to the task brief/context allowlist; no unrelated model behavior
  changed.

## Follow-up Needed

- Task 003 must bind renderer-neutral semantic roles to the stable styles.
- Tasks 004-006 must reuse the translator rather than reimplement paragraph
  formatting.

## Adjudication

The slice is complete at the shared DOCX paragraph translation boundary.
Broader A3-A6 behavior remains owned by downstream slices.
