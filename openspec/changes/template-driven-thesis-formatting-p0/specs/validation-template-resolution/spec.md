## MODIFIED Requirements

### Requirement: Load strongly typed school templates
Template loading SHALL validate page, reusable paragraph style, body, heading, semantic role,
TOC, figure, table, equation, citation, bibliography, section, header/footer variant and page-number
display rules into a strongly typed Template Model.

#### Scenario: Valid P0 school template
- **WHEN** a supported school YAML template declares body spacing, semantic styles, TOC levels,
  bibliography styles and odd/even headers
- **THEN** the loader returns a validated model whose defaults and explicit values are available to the Compiler

#### Scenario: Legacy template compatibility
- **WHEN** an existing valid template omits all newly introduced P0 fields
- **THEN** the loader applies documented defaults and preserves the template's previous behavior

### Requirement: Keep school rules outside the renderer
School-specific fonts, sizes, margins, spacing, indentation and pagination MUST come from the
Template Model. Semantic paragraph styles, TOC layout, citation presentation, bibliography layout,
header/footer variants, borders and page-number display MUST also come from the Template Model and
MUST NOT be hard-coded in renderer business logic.

#### Scenario: Switch school template
- **WHEN** the same ThesisDocument is compiled with two valid school templates that differ in
  body spacing, citation mode and odd/even headers
- **THEN** the resulting RenderPlans and DOCX styles reflect each template without changing source Markdown or Parser behavior

## ADDED Requirements

### Requirement: Validate reusable paragraph style constraints
Reusable paragraph style fields SHALL use explicit supported units and compatible combinations,
including indentation, spacing, line spacing, outline level and pagination flags.

#### Scenario: Invalid fixed line spacing
- **WHEN** a paragraph style declares `line_spacing.type: fixed` without a supported length value
- **THEN** template loading fails with a field-specific validation error

#### Scenario: Contradictory first-line and hanging indentation
- **WHEN** one paragraph style declares both non-zero first-line and hanging indentation
- **THEN** template loading fails instead of emitting ambiguous Word indentation

### Requirement: Validate header footer and page-number variants
The Template Model SHALL validate first, odd and even header/footer variants, page distances,
paragraph styles, optional bottom borders and PAGE/NUMPAGES display rules.

#### Scenario: Invalid header border
- **WHEN** a header variant declares a border width without a supported length unit
- **THEN** template loading reports the complete border field path

#### Scenario: Page number disabled
- **WHEN** a section page-number format is `none`
- **THEN** template validation rejects a variant that requires PAGE or NUMPAGES output
