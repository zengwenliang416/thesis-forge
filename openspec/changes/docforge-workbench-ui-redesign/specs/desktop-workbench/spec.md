## MODIFIED Requirements

### Requirement: Present academic workbench information
The shared React frontend SHALL present a general `DocForge`
Markdown-to-Microsoft-Word document workshop rather than a thesis-only product.
It MUST keep a compact product command bar, document outline, Markdown editor,
Microsoft Word layout preview, contextual diagnostics, Word template selection,
build action, progress, and output feedback. Academic papers MAY remain one
supported document/template category but MUST NOT define the product's primary
identity or generic empty states.

#### Scenario: Populated desktop workspace
- **WHEN** a valid saved Markdown source and template are loaded at a desktop viewport
- **THEN** the DocForge command bar, outline, editor, Microsoft Word preview, diagnostics, template state, and build availability are visible in the approved dual-canvas hierarchy

#### Scenario: Required workbench states
- **WHEN** the workspace is populated, loading, empty, error, disabled, dirty, canceled, or permission-blocked
- **THEN** the corresponding state uses general document language, visible non-color status cues, and an applicable recovery or next action

#### Scenario: Mobile workspace
- **WHEN** the workbench is shown at the supported mobile breakpoint
- **THEN** the user can switch among outline, editor, preview, and diagnostics without horizontal overflow or inaccessible primary actions

#### Scenario: Preserve command behavior
- **WHEN** the user opens, saves, validates, selects a template, builds, cancels, changes preview mode, or selects a Microsoft Word PDF
- **THEN** the frontend invokes the same existing workspace callbacks and versioned transport contracts as before the redesign

#### Scenario: Presentation-only rename
- **WHEN** the visible product is labeled DocForge
- **THEN** the repository, CLI, Python package, domain types, template IDs, Tauri bundle identifier, and transport protocol remain unchanged
