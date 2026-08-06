# Quality Review: 006-header-footer-variants

## Verdict

approved

## Separation Of Concerns

- `src/thesis_forge/templates/model.py` remains renderer-neutral: it contains typed
  page/section/header/footer policy and validation, with no `docx`, OOXML, or
  renderer implementation objects.
- `src/thesis_forge/renderers/docx/document.py` owns page geometry and document
  grid translation; `sections.py` owns section policy, variant relationships,
  part clearing, borders, and PAGE/NUMPAGES materialization; `fields.py` and
  `styles.py` retain their existing field/style responsibilities.
- Initial and added sections use the shared `configure_section_geometry` path,
  so geometry behavior is not duplicated across section creation paths.

## Component Cohesion / Coupling

- The new section logic is cohesive around one section-policy seam. The
  `VARIANT_ACCESSORS` table centralizes first/default/even Word accessors, while
  `_page_number_display` and `_add_page_number` isolate declarative field
  selection and field emission.
- Coupling stays at the intended renderer boundary: section helpers consume
  typed template models and reuse the existing length/style/field helpers.
  Raw Word objects do not leak into the template model or compiler path.
- The OOXML child-order corrections in `fields.py` and `styles.py` are narrow
  support changes for the new settings and paragraph properties, not unrelated
  cross-layer behavior.

## Test Quality

- The focused suite asserts saved-package behavior directly across
  `document.xml`, `settings.xml`, `document.xml.rels`, and all referenced
  header/footer parts. Coverage includes geometry, `w:docGrid`, `w:pgNumType`,
  `w:titlePg`, `w:evenAndOddHeaders`, real field instructions, relationships,
  borders, and current-section first/even fallback.
- Regression coverage exercises disabled variants, stale inheritance, blank
  fallback, legacy normalization, conflicting policies, exact validation paths
  for all four `page.margin.*` fields, and the other physical dimensions that
  must reject `em`.
- `_clear_part` has a direct regression test covering stale paragraphs, tables,
  drawings, and image relationships. The broader variant tests also verify
  that cleared parts contain no text or field instructions.
- The current `validation-log.jsonl` records the system-executed evidence:
  `33 passed` focused tests, `356 passed` full tests, Ruff clean, `git diff
  --check` clean, strict OpenSpec validation, and matching CodeGraph evidence
  `ev-msheib8s`.
- The in-memory `_clear_part` test does not assert removal of orphaned package
  media after a save/reload; this is a non-blocking coverage note because the
  required part relationships and content are asserted, and Word/WPS sensory
  validation is explicitly deferred to task 008.

## Error Handling

- Template validation rejects contradictory legacy/variant policies, invalid
  PAGE/NUMPAGES combinations, invalid page-number restarts, and relative
  `em` lengths in physical page and border fields. `load_template` preserves
  exact nested field paths through `TemplateLoadError`.
- Renderer boundary failures from the new geometry and section helpers are
  converted to the existing `DocxRenderError` capability context. Invalid
  enum/model states are not silently ignored, and `_clear_part` performs a
  deterministic clear plus relationship drop without swallowing errors.

## Reuse / Duplication

- Geometry is extracted and reused by both initial and added sections.
  Existing `to_docx_length`, `to_points`, `apply_paragraph_style`, and
  `add_complex_field` helpers are reused rather than reimplemented.
- Variant selection, fallback, field display, and part clearing are centralized
  in small helpers. The obsolete paragraph-only cleanup path was removed, so
  there are no competing cleanup implementations.
- The added tests extend the existing DOCX/template suites and reuse their
  package/XML helpers instead of introducing a parallel test harness.

## Complexity Delta

- The implementation adds meaningful behavior but keeps the new source logic
  below the repository's high-complexity signals: no newly introduced function
  has obvious excessive nesting or broad unrelated responsibilities, and the
  variant path is split into focused helpers.
- `sections.py` grows substantially because it is the owning section seam, but
  the growth follows the task boundary rather than creating a new cross-layer
  abstraction. The large existing `tests/test_docx_renderer.py` remains the
  established integration-test surface; the new cases are grouped with the
  relevant section tests.
- The fixed `page.margin.*` validation and complete `_clear_part` path reduce
  hidden behavior rather than adding compatibility branches or speculative
  fallbacks.

## Required Fixes

- None. The current production diff, tests, task report, and system validation
  evidence meet the quality bar for this slice. Word/WPS sensory review remains
  the explicitly scoped task-008 follow-up, not a quality blocker for task 006.
