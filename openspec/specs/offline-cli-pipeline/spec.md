# offline-cli-pipeline Specification

## Purpose
TBD - created by archiving change build-thesisforge-v1-core. Update Purpose after archive.
## Requirements
### Requirement: Inspect documents without side effects
`thesisforge inspect` SHALL parse the source and report metadata, blocks, IDs, references and
citations without modifying source files or creating build output.

#### Scenario: Inspect valid thesis
- **WHEN** a user runs inspect on a valid thesis
- **THEN** the command exits zero, emits the document structure and writes no production file

### Requirement: Validate documents with stable exit behavior
`thesisforge validate` SHALL report structured diagnostics, SHALL exit non-zero when any error is
present and SHALL allow warnings without failing.

#### Scenario: Warning-only validation
- **WHEN** validation returns warnings and no errors
- **THEN** the command displays the warnings and exits zero

### Requirement: Build through the complete compiler pipeline
`thesisforge build` SHALL load source, template, resources and bibliography, perform fatal
validation, compile a RenderPlan and render DOCX in that order.

#### Scenario: Successful build
- **WHEN** all inputs are valid
- **THEN** build exits zero and reports the final DOCX path

#### Scenario: Validation blocks rendering
- **WHEN** fatal validation errors exist
- **THEN** build exits non-zero without invoking the final output replacement

### Requirement: Operate offline and without AI credentials
Inspect, validate and build MUST run with network access disabled and without any AI API key.

#### Scenario: Offline execution
- **WHEN** the three core commands run in an environment with no network and no AI credentials
- **THEN** their supported local behavior remains available

### Requirement: Preserve valid output on failure
Build MUST write through a temporary file and atomically replace the requested output only after
successful render and package validation.

#### Scenario: Failed rebuild
- **WHEN** an existing valid output is present and a rebuild fails during rendering
- **THEN** the original output remains unchanged and temporary files are removed

### Requirement: Provide a complete end-to-end example
The repository SHALL include an example that exercises cover, abstracts, TOC, headings, figure,
three-line table, equation, cross-references, citations, bibliography, acknowledgements and appendix.

#### Scenario: Full example build
- **WHEN** the documented example build command is executed
- **THEN** it produces a DOCX whose package passes the required structure checks

### Requirement: Produce deterministic semantic output
Repeated builds with the same source, template and dependency versions MUST produce semantically
equivalent numbering, references, bibliography order and OOXML field instructions.

#### Scenario: Repeated build comparison
- **WHEN** the full example is built twice with identical inputs
- **THEN** normalized OOXML semantics for numbering, references and fields are equivalent
