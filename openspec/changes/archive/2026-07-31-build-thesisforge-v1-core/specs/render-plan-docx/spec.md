## ADDED Requirements

### Requirement: Resolve document-wide numbering and references
The Compiler SHALL resolve chapter-aware numbering, stable bookmark names, cross-reference targets,
citation order and section policy before the DOCX Renderer runs.

#### Scenario: Chapter-aware objects
- **WHEN** two figures appear in different chapters under chapter numbering
- **THEN** the compiled instructions contain deterministic chapter-aware numbers and unique bookmarks

### Requirement: Produce renderer-neutral typed instructions
The Compiler SHALL produce typed RenderPlan instructions that contain resolved semantics and
template values without containing python-docx or lxml objects.

#### Scenario: RenderPlan architecture
- **WHEN** a document is compiled
- **THEN** RenderPlan can be inspected and tested without importing or constructing a DOCX document

### Requirement: Render template-driven document layout
The DOCX Renderer SHALL apply page size, margins, paragraph fonts, East Asia and Latin fonts,
heading styles, indentation, spacing, alignment and page breaks from the Template Model.

#### Scenario: Body font mapping
- **WHEN** a template specifies separate East Asia and Latin fonts
- **THEN** generated runs and styles contain the corresponding `w:rFonts` mappings

### Requirement: Render figures and three-line tables
The renderer SHALL create images, chapter-aware captions, bookmarks and template-sized widths,
and SHALL create table objects with template-driven caption placement and three-line borders.

#### Scenario: Figure and table output
- **WHEN** a valid figure and Markdown table are compiled
- **THEN** the DOCX contains an image relationship, figure caption, table object, table caption and matching bookmarks

### Requirement: Render editable equations
Block equations SHALL be rendered as editable OMML with template-driven numbering and bookmarks;
unsupported LaTeX MUST fail explicitly rather than silently becoming plain text or PNG.

#### Scenario: Supported equation
- **WHEN** a supported LaTeX equation is compiled
- **THEN** the DOCX contains an `m:oMath` or `m:oMathPara` object and its resolved equation number

### Requirement: Render real Word fields and bookmarks
TOC, SEQ, REF, PAGE and NUMPAGES behavior MUST use Word field instructions, and all
cross-reference targets MUST use valid bookmarks.

#### Scenario: Cross-reference field
- **WHEN** prose references a compiled figure
- **THEN** the DOCX contains a REF field targeting that figure bookmark rather than static display text

#### Scenario: Automatic table of contents
- **WHEN** the template enables a table of contents
- **THEN** the DOCX contains a TOC field configured for the supported heading range

### Requirement: Render sections, headers, footers and page numbering
The renderer SHALL create real section properties, header/footer relationships and page-number
fields according to template policy, including optional Roman front matter and restarted decimal main matter.

#### Scenario: Front matter and main matter
- **WHEN** a template defines Roman front matter and decimal main matter restarting at one
- **THEN** the DOCX contains separate sections with matching page-number formats and restart behavior

### Requirement: Verify OOXML structures
Tests MUST inspect DOCX package XML and relationships for advanced Word capabilities and MUST NOT
treat file existence alone as sufficient verification.

#### Scenario: OOXML field test
- **WHEN** an integration test builds a document with TOC, REF and PAGE
- **THEN** the test opens the DOCX zip and asserts the expected field and relationship structures
