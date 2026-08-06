# Task Report: 006-header-footer-variants

## Status

DONE

## Files Changed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/renderers/docx/document.py`
- `src/thesis_forge/renderers/docx/fields.py`
- `src/thesis_forge/renderers/docx/sections.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `tests/test_template.py`
- `tests/test_docx_renderer.py`

## What Changed

- Added absolute-unit validation for all four page margins, page
  header/footer distances, document-grid line pitch and paragraph-border
  width/space.
- Added a reusable section-geometry path so initial and newly inserted sections
  receive the same page size, orientation, margins, header/footer distances and
  optional `w:docGrid`.
- Normalized legacy header/footer policy into explicit default variants while
  rejecting ambiguous mixes of legacy and variant fields.
- Added first/default/even header and footer materialization with explicit
  unlinking, complete part clearing and deterministic fallback to the current
  section's default policy.
- Added template-driven header/footer paragraph styles, bottom borders and
  declarative PAGE/NUMPAGES prefix, suffix, separator, total-page and alignment
  behavior.
- Added `w:pgNumType` format/restart handling, `w:titlePg`,
  `w:evenAndOddHeaders`, ordered section/settings properties and real
  header/footer relationships.
- Preserved legacy footer page-number text only through template defaults; no
  school-specific page text or dimensions were added to renderer constants.

## TDD Evidence

- Saved-package tests inspect `document.xml`, `settings.xml`,
  `document.xml.rels` and all referenced header/footer parts.
- Regressions cover explicit disabled variants, first/even fallback to the
  current section rather than the previous section, blank disabled fallback,
  pure PAGE, PAGE plus NUMPAGES, custom text and alignment.
- A direct part-clearing test proves stale paragraphs, tables, drawings and
  image relationships are removed rather than merely hidden.
- Model tests cover legacy normalization, conflicting legacy/variant fields,
  page-number format/restart conflicts and exact error paths for every physical
  page or border dimension that incorrectly uses `em`.
- Independent review exposed that page margins still accepted `em`; the fix
  added four exact-path regressions and removed the obsolete paragraph-only
  cleanup helper.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py -k 'section or header or footer or page_number or grid or physical_page' -q`
  -> `33 passed, 84 deselected in 1.35s`.
- `.venv/bin/python -m pytest -q`
  -> `356 passed in 27.50s`.
- `.venv/bin/ruff check .`
  -> `All checks passed`.
- `git diff --check`
  -> passed.
- `openspec validate template-driven-thesis-formatting-p0 --strict`
  -> valid.
- `codegraph sync .`
  -> synchronized 3 modified files; index has no pending changes.
- CodeGraph evidence `ev-msheib8s` matches
  `development:task-006-header-footer-variants`.

## Concerns

- Microsoft Word/WPS sensory review is intentionally deferred to task 008.
- School-specific distances, border values and plain centered PAGE policy
  remain deferred to task 007's YAML rather than being embedded here.

## Scope Deviations

- `fields.py` and `styles.py` required narrow OOXML child-order corrections so
  generated settings and paragraph properties remain schema valid after adding
  this slice's fields and borders. Both files were already allowed.

## Follow-up Needed

- Task 007 must document and select the new page/variant policy in the HUT P0
  template and complete example.
- Task 008 must open the complete artifact in Word or WPS and record sensory
  evidence.

## Adjudication

Tasks 6.1-6.9 are implemented and A6 has direct package-level evidence. The
physical-margin review finding is fixed and recorded. Independent spec and
quality reviews both approved the final diff with no required fixes.
