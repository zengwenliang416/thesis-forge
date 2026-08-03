## MODIFIED Requirements

### Requirement: Provide a complete end-to-end example
The repository SHALL include an example that exercises cover, Chinese and English abstracts,
keywords, TOC, headings, figure, three-line table, equation, cross-references, superscript
citations, styled bibliography, acknowledgements, appendix, odd/even headers and restarted page numbering.

#### Scenario: P0 full example build
- **WHEN** the documented example build command is executed with the P0 school template
- **THEN** it produces a DOCX whose package passes paragraph-style, TOC, citation, bibliography,
  section, header/footer and page-number structure checks

#### Scenario: Legacy example compatibility
- **WHEN** the existing example is built with a template that omits P0 fields
- **THEN** build remains successful and preserves existing semantic output

## ADDED Requirements

### Requirement: Keep P0 formatting offline and deterministic
Template validation, semantic role resolution and DOCX formatting SHALL run without network access,
AI credentials or external Office automation, and repeated builds SHALL produce semantically
equivalent normalized OOXML.

#### Scenario: Repeated offline P0 build
- **WHEN** the P0 example is built twice with network access disabled
- **THEN** both builds succeed and normalized style, field, section and header/footer semantics are equivalent
