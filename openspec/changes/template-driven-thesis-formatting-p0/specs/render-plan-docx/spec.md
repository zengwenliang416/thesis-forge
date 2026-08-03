## MODIFIED Requirements

### Requirement: Render template-driven document layout
The DOCX Renderer SHALL apply page size, margins, header/footer distances, optional document grid,
East Asia and Latin fonts, reusable paragraph properties, heading styles, indentation, spacing,
alignment, outline levels and pagination controls from the Template Model.

#### Scenario: Complete body paragraph style
- **WHEN** a template specifies Songti and Times New Roman at 12 pt, two-character first-line
  indentation, zero paragraph spacing, exact 20 pt line spacing, justification and widow control
- **THEN** the generated Normal style contains the corresponding `w:rFonts`, `w:sz`, `w:ind`,
  `w:spacing`, `w:jc` and `w:widowControl` properties

#### Scenario: Heading pagination
- **WHEN** a heading style enables keep-with-next and declares an outline level
- **THEN** the generated heading style contains `w:keepNext` and the configured `w:outlineLvl`

### Requirement: Render sections, headers, footers and page numbering
The renderer SHALL create real section properties, first/odd/even header/footer relationships,
page distances, optional header bottom borders and configurable page-number fields according to
template policy, including Roman front matter and restarted decimal main matter.

#### Scenario: Odd and even main headers
- **WHEN** a main section defines the thesis title for odd pages and the university thesis label
  for even pages
- **THEN** the package enables even/odd headers and contains separate default and even header relationships with configured text and styles

#### Scenario: Configurable page number display
- **WHEN** a footer requests a centered PAGE field without NUMPAGES, prefix or suffix
- **THEN** the footer contains only the configured PAGE field and does not contain hard-coded Chinese page text

#### Scenario: Header footer distances
- **WHEN** a template declares header and footer distances
- **THEN** each applicable section writes those values to `w:pgMar/@w:header` and `w:pgMar/@w:footer`

## ADDED Requirements

### Requirement: Render semantic thesis paragraph roles
The RenderPlan SHALL carry semantic paragraph and heading roles, and the DOCX Renderer SHALL map
those roles to template-selected Word styles without inferring document meaning from display text.

#### Scenario: Independent abstract styles
- **WHEN** Chinese and English abstract body roles use different template styles
- **THEN** their DOCX paragraphs reference different configured `w:pStyle` values

#### Scenario: Special unnumbered heading
- **WHEN** a bibliography or acknowledgements heading is compiled as a special heading role
- **THEN** it receives its configured style and does not acquire numbered chapter behavior

### Requirement: Render configurable TOC styles
The renderer SHALL configure the TOC title and supported TOC level styles with template-driven
font, paragraph spacing, indentation, right-aligned page-number tab stops and leader values while
retaining a real TOC field.

#### Scenario: Three-level dotted TOC
- **WHEN** a template defines TOC levels one through three with increasing indentation and dot leaders
- **THEN** `styles.xml` contains configured TOC 1-3 styles and the document contains a real TOC field

### Requirement: Reuse one paragraph property translator
Body, heading, semantic, TOC, bibliography and header/footer paragraph rendering SHALL reuse one
tested translation path for common paragraph and font properties.

#### Scenario: Shared exact spacing
- **WHEN** body and bibliography styles both request exact 20 pt line spacing
- **THEN** both emit semantically equivalent `w:spacing` values through the shared translator
