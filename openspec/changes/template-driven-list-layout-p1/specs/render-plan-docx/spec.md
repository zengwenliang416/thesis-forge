## ADDED Requirements

### Requirement: Preserve renderer-neutral list semantics
The Compiler and RenderPlan MUST represent list kind, starting value, nesting level, ordinal and
inline content without Template Model objects, python-docx, lxml, raw OOXML or Word style IDs.

#### Scenario: Inspect list instruction
- **WHEN** ordered and unordered Markdown lists are compiled
- **THEN** their instructions contain only semantic list data and can be tested without constructing a DOCX document

### Requirement: Render template-driven Word numbering
The DOCX Renderer SHALL create true Word numbering definitions from the selected template policy,
map semantic ordered formats to Word formats, preserve the semantic starting value and apply the
configured level to every list item.

#### Scenario: Custom ordered definition
- **WHEN** an ordered list uses a lower-roman level with prefix `(`, suffix `)` and custom indentation
- **THEN** `numbering.xml` contains the mapped format, level text, alignment, start value and indentation

#### Scenario: Custom unordered definition
- **WHEN** an unordered list uses a custom Unicode marker and indentation
- **THEN** `numbering.xml` contains a bullet level with the configured marker and geometry

#### Scenario: Policy shorter than Markdown depth
- **WHEN** a Markdown item is nested deeper than the configured level policy
- **THEN** the renderer deterministically reuses the final policy level and emits a valid Word level

### Requirement: Style every list paragraph
The DOCX Renderer SHALL apply the selected level's common paragraph style after creating each list
paragraph and inline runs.

#### Scenario: Styled list paragraph
- **WHEN** a list level configures font, size, color, spacing and line spacing
- **THEN** `document.xml` contains the configured paragraph and run properties alongside `numPr`
