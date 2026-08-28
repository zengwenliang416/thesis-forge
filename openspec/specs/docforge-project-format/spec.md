# docforge-project-format Specification

## Purpose
TBD - created by archiving change docforge-project-format-v1. Update Purpose after archive.
## Requirements
### Requirement: Use one DocForge project manifest
The system SHALL recognize `docforge.yaml` with
`schema: docforge.project.v1` as the only project manifest contract. A project
entrypoint SHALL be either a directory containing that manifest or the manifest
path itself.

#### Scenario: Open project directory
- **WHEN** a user opens a directory containing a valid `docforge.yaml`
- **THEN** the loader resolves that manifest as the project entrypoint

#### Scenario: Open manifest path
- **WHEN** a user opens a valid `docforge.yaml` path
- **THEN** the loader resolves its parent directory as the project root

#### Scenario: Reject obsolete project contract
- **WHEN** a user opens `thesisforge.yaml` or a manifest declaring `thesisforge.project.v2`
- **THEN** the loader returns a stable actionable project-contract error and does not use a compatibility loader

#### Scenario: Reject bare Markdown
- **WHEN** a user opens a Markdown file instead of a DocForge project entrypoint
- **THEN** the loader rejects it as an incomplete project and does not infer or create a manifest

### Requirement: Define neutral document and output defaults
The manifest SHALL default `document.source` to `document.md`,
`document.type` to `general`, DOCX output to `build/document.docx`, Review
Markdown to `review/document.review.md`, and the Review source map to
`review/document.review-map.json`.

#### Scenario: Resolve omitted defaults
- **WHEN** a valid manifest omits source, document type, output, and review path overrides
- **THEN** the resolved project uses all neutral default values

#### Scenario: Resolve explicit safe override
- **WHEN** a manifest supplies a safe project-relative Markdown source or output path
- **THEN** the project uses that explicit path instead of the default

### Requirement: Keep all project paths confined
The system MUST normalize every source, resource, template, bibliography,
output, and review path relative to the project root and MUST reject
absolute paths, remote URL schemes, traversal, NUL values, and symlink escapes.

#### Scenario: Reject traversal
- **WHEN** a manifest path contains a `..` segment that can leave the project
- **THEN** loading fails with a structured path-boundary diagnostic

#### Scenario: Reject symlink escape
- **WHEN** a project-relative path resolves through a symlink outside the project root
- **THEN** loading fails before the target is read or written

#### Scenario: Accept nested local resource
- **WHEN** a nested resource path resolves inside the project root
- **THEN** the loader returns its canonical confined path

### Requirement: Provide strict generic metadata
Common metadata SHALL be strongly typed and SHALL support title, subtitle,
authors, organization, document date, version, and keywords without requiring
academic fields. Unknown metadata fields MUST be rejected.

#### Scenario: Load minimal general metadata
- **WHEN** a general project declares only a title and author
- **THEN** the manifest loads without university, degree, advisor, student ID, or completion data

#### Scenario: Reject unknown generic metadata
- **WHEN** common metadata contains an undeclared field
- **THEN** manifest validation reports the exact unsupported field

### Requirement: Model academic data as an optional profile
Student, institution, degree, advisor, and completion data SHALL be accepted
only in a typed optional `academic` profile. The profile SHALL NOT be required
for a `general` document.

#### Scenario: Load academic profile
- **WHEN** a project declares a valid academic profile
- **THEN** validation and template resolution receive the typed profile values

#### Scenario: Reject malformed academic profile
- **WHEN** an academic profile contains an invalid field type or unknown field
- **THEN** manifest validation fails with a field-specific diagnostic

### Requirement: Preserve source and successful outputs on failure
Inspect and validate MUST NOT mutate the project. Review and build MUST write
through temporary files and MUST replace final outputs only after their
respective validation succeeds.

#### Scenario: Failed build with existing output
- **WHEN** `build/document.docx` exists and a rebuild fails
- **THEN** the existing DOCX remains unchanged and temporary files are removed

#### Scenario: Failed operation protects project inputs
- **WHEN** inspect, validate, review, or build fails
- **THEN** neither `docforge.yaml` nor the source Markdown is modified
