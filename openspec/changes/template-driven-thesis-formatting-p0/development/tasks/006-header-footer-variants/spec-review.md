# Spec Review: 006-header-footer-variants

## Verdict

approved

## Missing Requirements

- None found within tasks 6.1-6.9 at the implementation boundary.
- Task 6.1 is covered by the typed page geometry additions, including absolute
  validation for all four page margins, header/footer distances and document
  grid line pitch.
- Tasks 6.2-6.4 are covered by the explicit default/first/even variant and
  page-number display models, legacy normalization, real PAGE/NUMPAGES fields,
  prefixes, suffixes, separators, total-page toggle and alignment.
- Tasks 6.5-6.7 are covered by shared initial/added-section geometry,
  relationship unlinking and part clearing, first/even fallback, borders,
  `w:pgNumType`, `w:titlePg`, `w:evenAndOddHeaders` and direct section
  settings/package assertions.
- Tasks 6.8-6.9 are covered by the disabled-variant, inheritance, fallback,
  field, format/restart, border, relationship and XML-order regression tests.

## Extra Behavior

- None that changes the task contract. The narrow OOXML child-order updates in
  `fields.py` and `styles.py` are within the task allowlist and support valid
  settings/paragraph XML for the new fields and borders.

## Misunderstood Requirements

- None found. The page-number Chinese text remains only as a compatibility
  default in the Template Model; new variants use their declarative display
  policy rather than renderer constants. The `page.margin.*` `em` rejection
  is now aligned with the physical-unit rule.

## Cannot Verify From Diff

- Microsoft Word/WPS sensory review and complete P0 build acceptance remain
  deferred to tasks 007-008 and are not blockers for this slice review.

## Acceptance Assertions Verified

- A6: current source and saved-package tests verify real first/default/even
  relationships, page distances, document grid, header borders,
  `w:pgNumType`, PAGE/NUMPAGES fields and stale-inheritance clearing. The
  current validation log records system-executed results of 33 focused tests,
  356 full tests, Ruff, `git diff --check`, strict OpenSpec validation and
  matching CodeGraph evidence `ev-msheib8s`.
- 6.1: `PageSpec`/`MarginSpec` physical-unit validation, header/footer distance
  translation and document-grid XML.
- 6.2: typed default/first/even header/footer variants with text, style, border
  and page-number policy.
- 6.3: legacy header/footer normalization and compatibility defaults.
- 6.4: declarative PAGE/NUMPAGES display content and alignment.
- 6.5: shared initial/added-section geometry plus explicit unlink/clear paths.
- 6.6: even/odd settings and first/default/even relationships.
- 6.7: borders, `w:pgMar`, `w:docGrid` and `w:pgNumType`.
- 6.8: inheritance, disabled variants, fallback and invalid-combination tests.
- 6.9: direct section/settings/relationship/header/footer XML assertions.

## Required Fixes

- The approved task has no remaining blocking spec correction after physical
  page-margin validation was added.
