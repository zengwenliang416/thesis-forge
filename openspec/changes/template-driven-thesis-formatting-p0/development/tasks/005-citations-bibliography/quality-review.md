# Quality Review: 005-citations-bibliography

## Verdict

approved

## Separation Of Concerns

- `citation_run_element()` receives renderer-neutral citation text and a
  presentation boolean, and owns only DOCX run construction.
- Compiler, `CitationRun`, bibliography records and `Gbt7714Formatter` remain
  free of Word properties.

## Component Cohesion / Coupling

- Body, heading, list and footnote citations reuse one focused OOXML helper.
- `FootnoteManager` receives a boolean instead of the full template or
  bibliography service.
- Bibliography entries continue through the existing semantic resolver and
  shared paragraph translator.

## Test Quality

- Direct package assertions cover `document.xml`, `footnotes.xml` and
  `styles.xml`.
- Coverage includes omitted/inline/superscript policy, grouped locator text,
  ordinary text isolation, body and footnote citations, stable bibliography
  style IDs, fonts, size, bold, two-character left/hanging indentation,
  paragraph spacing, fixed line spacing and bibliography order.
- Existing bibliography golden tests run without constructing DOCX.

## Error Handling

- Missing citation keys remain Compiler errors; unsupported inline runs remain
  `DocxRenderError` failures with capability context.
- No new exception swallowing or fallback changes were introduced.

## Reuse / Duplication

- Citation OOXML construction is centralized.
- Footnote `_text_run()` remains limited to ordinary text and does not duplicate
  citation presentation logic.

## Complexity Delta

- Low: one O(1) run helper and one boolean passed to `FootnoteManager`.
- No formatter registry, CSL dependency, network behavior or compatibility
  layer was added.

## Required Fixes

- None.
- Non-blocking reviewer suggestions for omitted-policy persistence and stronger
  bibliography font/layout assertions were incorporated before closure.
