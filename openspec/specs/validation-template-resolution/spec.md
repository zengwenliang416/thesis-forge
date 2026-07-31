# validation-template-resolution Specification

## Purpose
TBD - created by archiving change build-thesisforge-v1-core. Update Purpose after archive.
## Requirements
### Requirement: Return structured validation issues
Validation SHALL return deterministic `ValidationIssue` objects with severity, code, message,
source line and target where applicable, and SHALL NOT use printing as its domain interface.

#### Scenario: Multiple document problems
- **WHEN** a document contains multiple independent validation failures
- **THEN** validation returns all safely collectable issues in stable order

### Requirement: Validate identifiers and references
Validation MUST report duplicate IDs, invalid ID prefixes and references to missing or
non-referencable targets as errors.

#### Scenario: Missing figure target
- **WHEN** a paragraph references `fig:missing` and no matching figure exists
- **THEN** validation returns a `missing-reference` error at the paragraph source line

### Requirement: Validate local resources and citations
Validation MUST verify referenced image files, bibliography files and citation keys using the
document source directory and configured local resource context.

#### Scenario: Missing image
- **WHEN** a figure source resolves to a missing local file
- **THEN** validation returns a `missing-image` error with the figure ID and source line

#### Scenario: Missing citation key
- **WHEN** a citation key is absent from the loaded bibliography
- **THEN** validation returns a `missing-citation` error with the citation source line

### Requirement: Validate structure and required metadata
Validation SHALL check heading hierarchy, required metadata and template-required structural
rules, with warnings and errors determined by explicit rule policy.

#### Scenario: Heading level jump
- **WHEN** heading level increases by more than one
- **THEN** validation returns a `heading-level-jump` warning

### Requirement: Load strongly typed school templates
Template loading SHALL validate page, body, heading, figure, table, equation, citation, section,
header and footer rules into a strongly typed Template Model.

#### Scenario: Valid school template
- **WHEN** a supported school YAML template is loaded
- **THEN** the loader returns a validated model whose defaults and explicit values are available to the Compiler

### Requirement: Validate explicit units
Template length values MUST include a supported unit and invalid or unsupported units MUST fail
template validation before rendering.

#### Scenario: Invalid margin unit
- **WHEN** a template declares a margin value without `mm`, `cm`, `pt` or another documented supported unit
- **THEN** template loading fails with a field-specific validation error

### Requirement: Keep school rules outside the renderer
School-specific fonts, sizes, margins, spacing, caption labels, numbering and page policies MUST
come from the Template Model and MUST NOT be hard-coded in renderer business logic.

#### Scenario: Switch school template
- **WHEN** the same ThesisDocument is compiled with two valid school templates
- **THEN** the resulting RenderPlans reflect each template without changing source Markdown or Parser behavior
