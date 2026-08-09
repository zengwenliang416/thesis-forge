# Spec Review: 005-citations-bibliography

## Verdict

approved

## Missing Requirements

- All task 005 requirements were satisfied before approval; no requirement is
  missing.

## Extra Behavior

- `footnotes.py` was added to the allowed task boundary after a failing
  end-to-end test exposed a second citation-run path. This closes the same
  presentation requirement in `footnotes.xml`; it does not alter footnote
  data, numbering or citation text.
- CodeGraph and SpecNav metadata changes are evidence refreshes, not product
  behavior.

## Misunderstood Requirements

- None. `inline` correctly omits `w:vertAlign`; `superscript` writes the Word
  run property without changing formatter output or `CitationRun`.
- The two-character hanging layout is template-driven through `left_indent:
  2em` plus `hanging_indent: 2em`, not a hard-coded school value.

## Cannot Verify From Diff

- Formatter, Compiler, `CitationRun`, template model and semantic style
  resolver were already present and unchanged in this slice. Their contracts
  are verified by the current source and existing bibliography/compiler tests,
  not by new production diff lines.
- Word/WPS sensory review remains tasks 007-008.

## Acceptance Assertions Verified

- A5.
- Task 5.1: `CitationSpec.presentation` defaults to `inline`, including omitted
  citation-policy fallback.
- Task 5.2: one `citation_run_element()` serves document and footnote paths and
  writes only `w:vertAlign w:val="superscript"`.
- Tasks 5.3-5.4: bibliography title/entry roles retain heading/body fallback and
  shared paragraph translation for fonts, indentation, spacing and line
  spacing.
- Task 5.5: formatter golden tests remain DOCX-free; Compiler tests preserve
  grouped citations, locators, repeated citations and first-use ordering.
- Task 5.6: saved `document.xml`, `footnotes.xml` and `styles.xml` directly
  assert superscript, stable style IDs, fonts and `w:left`/`w:hanging`.

## Required Fixes

- The approved task has no remaining blocking spec correction.
