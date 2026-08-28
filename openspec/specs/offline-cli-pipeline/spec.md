# offline-cli-pipeline Specification

## Purpose
TBD - created by archiving change build-thesisforge-v1-core. Update Purpose after archive.
## Requirements
### Requirement: Inspect documents without side effects
`docforge inspect` SHALL open a DocForge project, parse its resolved source, and
report generic metadata, optional profiles, blocks, IDs, references, and
citations without modifying project inputs or creating build output.

#### Scenario: Inspect valid general project
- **WHEN** a user runs inspect on a valid general DocForge project
- **THEN** the command exits zero, emits the document structure, and writes no production file

### Requirement: Validate documents with stable exit behavior
`docforge validate` SHALL open a DocForge project, report structured
diagnostics, exit non-zero when any error is present, and allow warnings without
failing.

#### Scenario: Warning-only validation
- **WHEN** validation returns warnings and no errors
- **THEN** the command displays the warnings and exits zero

### Requirement: Build through the complete compiler pipeline
`docforge build` SHALL load the project source, template, resources, optional
bibliography, generic metadata, and optional profile, perform fatal validation,
compile a RenderPlan, and render DOCX in that order.

#### Scenario: Successful build
- **WHEN** all project inputs are valid
- **THEN** build exits zero and reports the final DOCX path

#### Scenario: Validation blocks rendering
- **WHEN** fatal validation errors exist
- **THEN** build exits non-zero without invoking final output replacement

### Requirement: Operate offline and without AI credentials
DocForge inspect, validate, review, and build MUST run with network access
disabled and without any AI API key.

#### Scenario: Offline execution
- **WHEN** the four core commands run in an environment with no network and no AI credentials
- **THEN** their supported local behavior remains available

### Requirement: Preserve valid output on failure
Build MUST write through a temporary file and atomically replace the
manifest-resolved or explicitly requested output only after successful render
and package validation.

#### Scenario: Failed rebuild
- **WHEN** an existing valid output is present and a rebuild fails during rendering
- **THEN** the original output remains unchanged and temporary files are removed

### Requirement: Provide a complete end-to-end example
The repository SHALL include a general DocForge example and an academic
DocForge example that together exercise common metadata, optional academic
metadata, headings, figures, three-line tables, equations, cross-references,
citations, bibliography, sections, and appendices.

#### Scenario: Full example builds
- **WHEN** the documented general and academic example build commands are executed
- **THEN** both produce DOCX packages that pass their required structure checks

### Requirement: Produce deterministic semantic output
The pipeline MUST produce semantically equivalent numbering, references,
bibliography order, stage lifecycle, and OOXML field instructions for repeated
builds with the same DocForge project, template, and dependency versions.

#### Scenario: Repeated build comparison
- **WHEN** a complete project is built twice with identical inputs
- **THEN** normalized document semantics, numbering, references, fields, and report stage order are equivalent
