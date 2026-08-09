## ADDED Requirements

### Requirement: Render template-driven cover paragraphs
The DOCX Renderer SHALL render cover paragraphs in template item order, resolve metadata-backed
values from the renderer-neutral `CoverInstruction`, apply configured prefixes and suffixes, and
apply the common paragraph style policy.

#### Scenario: Styled reordered cover
- **WHEN** a template places the thesis title before the university and assigns different alignment and spacing
- **THEN** `document.xml` contains the title paragraph first with the configured paragraph and run properties

#### Scenario: Empty optional field
- **WHEN** a metadata-backed item resolves to an empty value and `skip_if_empty` is true
- **THEN** the renderer emits no paragraph for that item

### Requirement: Preserve renderer-neutral cover content
The Compiler and RenderPlan MUST represent cover content without python-docx, lxml, raw OOXML or
Word style identifiers.

#### Scenario: Inspect cover instruction
- **WHEN** Front Matter is compiled into a cover instruction
- **THEN** its payload contains only semantic string values and can be tested without constructing a DOCX document
