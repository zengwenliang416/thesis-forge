# Task Report: 004-toc-styles

## Status

DONE

## Files Changed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `tests/test_template.py`
- `tests/test_docx_renderer.py`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence.jsonl`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence-index.json`

## What Changed

- Added a structural TOC-level default that clears inherited body first-line
  indentation and retains dot leaders.
- Rejected non-positive page-number tab positions with the exact template field
  path while preserving the existing closed leader enum and strict level1-3
  shape.
- Added `configure_toc_styles()` to create or update stable `TOC1`, `TOC2` and
  `TOC3` paragraph styles whenever a template provides a TOC policy.
- Reused `apply_paragraph_style()` for fonts, sizes, indentation, spacing and
  line spacing; no TOC-specific duplicate translator was introduced.
- Added a focused right-tab helper that replaces an existing right tab and maps
  every template leader value to the corresponding Word OOXML token.
- Resolved explicit `em` tab positions from the effective TOC-level size rather
  than a global 12 pt assumption.
- Defined deterministic omitted-level behavior: zero first-line indentation,
  a dot leader and a right tab at the current section's printable content
  width. Templates without any `toc` policy remain unchanged.
- Preserved the existing real `TOC` complex field, dirty flag and
  `w:updateFields=true` behavior; `renderer.py` and `fields.py` required no
  production changes.

## TDD Evidence

- The first focused run failed four tests because TOC defaults, positive tab
  validation, stable TOC styles and tab/leader XML did not exist.
- The first implementation exposed a Pydantic default-factory construction
  error, which was fixed by routing `0pt` through `LengthSpec.model_validate()`.
- A remaining package assertion exposed the actual section-geometry
  quantization of the default tab as 8788 twips; the test was corrected to the
  generated section width rather than changing production math.
- Focused coverage now includes all six leader mappings, effective-size `em`
  tabs, legacy `toc=None`, deterministic level defaults, different level1-3
  indentation and spacing, stable style IDs, complete complex-field structure
  and update-on-open settings.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py -k 'toc or style' -q`
  -> `34 passed, 61 deselected in 1.66s`.
- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py -q`
  -> `95 passed in 27.41s`.
- `.venv/bin/python -m pytest -q`
  -> `334 passed in 29.74s`.
- `.venv/bin/ruff check .`
  -> `All checks passed`.
- `git diff --check`
  -> passed.
- CodeGraph evidence `ev-msh7we5o` matches
  `development:task-004-toc-styles`.

## Concerns

- Office/WPS field recalculation remains client-owned and is intentionally not
  simulated in this slice.
- Full school-template and sensory review remain tasks 007-008.

## Scope Deviations

- None. The renderer and field call paths were verified by package tests but
  did not require source edits.

## Follow-up Needed

- Task 007 should provide explicit HUT level1-3 TOC policies so the school
  template does not rely on generic omitted-level defaults.

## Adjudication

Tasks 4.1-4.6 are implemented at the real TOC field and Word style boundary.
A4 is directly covered by saved-package `styles.xml`, `document.xml` and
`settings.xml` assertions, pending independent task reviews.
