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
Validation MUST verify image files, template resources, bibliography files, and
citation keys using the DocForge project root and confined manifest-resolved
resource context.

#### Scenario: Missing image
- **WHEN** a figure source resolves to a missing project-local file
- **THEN** validation returns a `missing-image` error with the figure ID and source line

#### Scenario: Missing citation key
- **WHEN** a citation key is absent from the manifest-resolved bibliography
- **THEN** validation returns a `missing-citation` error with the citation source line

#### Scenario: Resource escapes project
- **WHEN** a resource resolves outside the project root through traversal or a symlink
- **THEN** validation reports a path-boundary error before reading the escaped target

### Requirement: Validate structure and required metadata
Validation SHALL check heading hierarchy, common metadata, optional typed
profiles, and template-required structural or metadata rules, with warnings and
errors determined by explicit rule policy. A general template MUST NOT require
academic profile fields.

#### Scenario: Heading level jump
- **WHEN** heading level increases by more than one
- **THEN** validation returns a `heading-level-jump` warning

#### Scenario: General document omits academic profile
- **WHEN** a valid general document uses `docforge-standard` without an academic profile
- **THEN** validation reports no missing university, degree, advisor, student, or completion issue

#### Scenario: Academic template requires profile field
- **WHEN** an academic template declares a required academic profile field and that value is absent
- **THEN** validation returns a template-scoped metadata issue

### Requirement: Validate explicit units
Template length values MUST include a supported unit and invalid or unsupported units MUST fail
template validation before rendering.

#### Scenario: Invalid margin unit
- **WHEN** a template declares a margin value without `mm`, `cm`, `pt` or another documented supported unit
- **THEN** template loading fails with a field-specific validation error

### Requirement: Load strongly typed document templates
Template loading SHALL validate page, body, heading, figure, table, equation,
citation, section, header, footer, common metadata binding, and optional profile
binding rules into a strongly typed Template Model.

#### Scenario: Valid generic template
- **WHEN** the bundled `docforge-standard` template is loaded
- **THEN** the loader returns a validated model whose defaults and generic bindings are available to the Compiler

#### Scenario: Valid academic template
- **WHEN** a supported academic template is loaded
- **THEN** the loader returns its typed profile requirements without adding those requirements to general templates

### Requirement: Keep document-specific rules outside the renderer
The system MUST source fonts, sizes, margins, spacing, caption labels,
numbering, page policies, and metadata or profile bindings from the Template
Model and MUST NOT hard-code them in renderer business logic.

#### Scenario: Switch document templates
- **WHEN** the same `ForgeDocument` is compiled with two valid templates
- **THEN** the resulting RenderPlans reflect each template without changing source Markdown, Parser behavior, or renderer branching
