# Acceptance Criteria: template-driven-thesis-formatting-p0

## User-Visible Criteria

- A template can configure正文的中西文字体、字号、首行缩进、段前、段后、固定 20 pt
  行距、两端对齐和孤行控制，生成 DOCX 使用这些值而不是 Word 默认值。
- Existing templates that omit the new fields continue to load and preserve their prior output semantics.
- A school template can independently style Chinese abstract body, English abstract body,
  Chinese keywords and English keywords without changing source Markdown text.
- A school template can configure TOC 1-3 indentation, line spacing, right-aligned page-number
  tab stops and dot leaders.
- A school template can render inline citations as superscript and bibliography entries with a
  two-character hanging indent and configured spacing.
- A school template can render different odd/even headers, an optional first-page header/footer,
  header bottom borders, configured header/footer distances and centered page numbers.
- The generated DOCX opens successfully in at least one primary target client, Microsoft Word or
  WPS, and remains editable.

## System Criteria

- Template loading rejects unknown fields, invalid enums and incompatible line-spacing/indent values
  with field-specific errors.
- Compiler/RenderPlan exposes semantic style roles for abstract, keywords, TOC, bibliography and
  special headings without importing DOCX modules.
- Renderer creates real `w:pStyle`, `w:spacing`, `w:ind`, `w:widowControl`, `w:keepNext`,
  `w:tabs`, `w:headerReference`, `w:footerReference`, `w:pgNumType`, `w:pgMar`,
  `w:pBdr`, PAGE and optional NUMPAGES structures.
- Odd/even header behavior enables `w:evenAndOddHeaders`; disabled variants do not inherit stale
  content from previous sections.
- Page-number content is driven by template configuration and is not forced to
  “第 X 页 / 共 Y 页”.
- School-specific names, fonts, dimensions and border values do not appear as renderer constants.

## Data Criteria

- Existing Markdown, YAML, BibTeX and image inputs are never modified.
- The same source and two different valid templates produce style-different but semantically
  equivalent documents without parser changes.
- Existing template YAML files remain valid through documented defaults.
- RenderPlan and normalized OOXML output remain deterministic for repeated builds with the same inputs.

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- Body, heading, semantic paragraph, TOC, bibliography and header/footer formatting reuse the
  common paragraph-style contract and DOCX formatting helper.
- Parser and Domain remain free of `docx`, `lxml`, Renderer and Word implementation objects.
- Bibliography formatting tests continue to run without constructing a DOCX document.

## Verification Surfaces

- Facticity: compare YAML schema, current model, RenderPlan types, renderer code, generated package
  and this acceptance contract.
- Static: run Ruff, architecture import tests, package validation and `git diff --check`.
- Unit: template defaults/validation, semantic-role compilation, paragraph style translation,
  citations, bibliography, TOC styles and section variant helpers.
- Redteam: invalid lengths/enums, contradictory indentation, disabled header inheritance,
  missing semantic style fallbacks and unsupported page-number combinations.
- E2E: build a complete thesis with a P0 school template and inspect `styles.xml`,
  `document.xml`, `settings.xml`, section properties and header/footer parts.
- Sensory: open the generated DOCX in Microsoft Word or WPS and review body rhythm, abstracts,
  TOC, bibliography, odd/even headers and page numbering.

## Unresolved Gaps

None.
