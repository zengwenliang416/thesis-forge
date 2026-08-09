## ADDED Requirements

### Requirement: Validate template-driven list policies
The Template Model SHALL validate separate ordered and unordered list policies with 1 to 9 levels
and SHALL reject unsupported formats, empty markers, relative indentation and invalid indentation
geometry.

#### Scenario: Valid ordered and unordered levels
- **WHEN** a template declares a lower-roman ordered level and a non-empty unordered marker with absolute indentation
- **THEN** template loading returns typed ordered and unordered level policies

#### Scenario: Unsupported ordered format
- **WHEN** a template declares an ordered format outside the supported semantic enum
- **THEN** template loading fails with a field-specific validation error

#### Scenario: Empty marker
- **WHEN** an unordered level declares an empty or whitespace-only marker
- **THEN** template loading fails with a field-specific validation error

#### Scenario: Invalid level count or geometry
- **WHEN** a list policy has zero levels, more than 9 levels, relative indentation or hanging indentation greater than left indentation
- **THEN** template loading fails before compilation

### Requirement: Preserve deterministic list defaults
Templates that omit `list` SHALL receive a deterministic 9-level policy semantically equivalent to
the previous fixed DOCX Renderer behavior.

#### Scenario: Load legacy template without list section
- **WHEN** a valid existing template omits `list`
- **THEN** its typed default contains decimal ordered levels, the previous bullet cycle and the previous indentation values

### Requirement: Keep school list rules in templates
The system SHALL source list formats, markers, alignment, indentation and paragraph styles from the
Template Model, and the DOCX Renderer MUST NOT hard-code school-specific list rules.

#### Scenario: Switch list templates
- **WHEN** the same Markdown is built with two templates that declare different list policies
- **THEN** both builds preserve list semantics and render their declared presentation
