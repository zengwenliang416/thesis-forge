## ADDED Requirements

### Requirement: Validate ordered cover layout
The Template Model SHALL validate an ordered cover layout whose items select either one supported
metadata field or one literal text value and SHALL reject items that select both or neither.

#### Scenario: Metadata-backed cover item
- **WHEN** a template item selects `thesis.title` and supplies a paragraph style
- **THEN** template loading returns a typed cover item with that field and style

#### Scenario: Ambiguous cover item
- **WHEN** a template item supplies both `field` and `text`
- **THEN** template loading fails with a field-specific validation error

### Requirement: Keep cover school rules in templates
The system SHALL source cover item order, literal labels, prefixes, suffixes, empty-value behavior,
fonts, sizes, alignment, indentation and spacing from the Template Model, and the DOCX Renderer
MUST NOT hard-code those school rules.

#### Scenario: Switch cover templates
- **WHEN** the same Markdown Front Matter is built with two templates that order and style cover items differently
- **THEN** both templates produce their declared cover layout without changing the Markdown source
