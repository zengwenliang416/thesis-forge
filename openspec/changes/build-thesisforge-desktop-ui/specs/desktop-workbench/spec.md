## ADDED Requirements

### Requirement: Keep approved prototype evidence archive-safe
The project MUST retain executable tests for the approved academic workbench
prototype after its originating OpenSpec change is archived, without recreating
an active change or mutating archive evidence.

#### Scenario: Run tests after archive
- **WHEN** the V1 core change exists only under `openspec/changes/archive/`
- **THEN** the prototype harness, artifact, and browser-evidence tests locate the archived change and pass

#### Scenario: Ambiguous archive evidence
- **WHEN** zero or multiple archive directories match the approved V1 core change
- **THEN** the test fails with an explicit archive-evidence discovery error

### Requirement: Provide an optional local desktop entrypoint
The package SHALL expose `thesisforge-ui` through the optional `ui` dependency
extra and MUST keep all core CLI imports and commands usable when PySide6 is not
installed.

#### Scenario: Launch with UI dependencies
- **WHEN** the user installs the `ui` extra and runs `thesisforge-ui`
- **THEN** a local light-theme Simplified Chinese workbench opens without network or credentials

#### Scenario: Use core without UI dependencies
- **WHEN** PySide6 is absent and the user imports ThesisForge or runs a core CLI command
- **THEN** the import or command succeeds without importing the UI runtime

### Requirement: Manage one explicit local source lifecycle
The workbench MUST open one local Markdown source, show its saved content, track
dirty edits, perform no autosave, and write source changes only after explicit
Save or Save As.

#### Scenario: Open a source
- **WHEN** the user selects a readable Markdown file
- **THEN** the workbench loads the saved text and derives outline, preview, and diagnostics from that source path

#### Scenario: Edit without saving
- **WHEN** the user changes editor text
- **THEN** the workspace becomes dirty and Validate and Build remain disabled until save succeeds

#### Scenario: Atomic save fails
- **WHEN** Save or Save As cannot atomically replace the requested file
- **THEN** the prior source remains intact, dirty state remains visible, and the workbench exposes a recovery action

### Requirement: Reuse deterministic application services
The UI MUST call the existing inspect, validation, and build application
services and MUST NOT duplicate Markdown parsing, validation rules, numbering,
bibliography, compilation, rendering, or package finalization.

#### Scenario: Refresh a saved workspace
- **WHEN** a saved source or selected template changes
- **THEN** the controller calls application services and maps their typed results into UI view models

#### Scenario: Fatal validation
- **WHEN** validation returns one or more error-severity issues
- **THEN** compile and render are not called and Build remains unavailable

### Requirement: Present academic workbench information
The UI SHALL implement the approved academic three-pane workbench with product
bar, outline, Markdown editor, paper-style structural preview, diagnostics,
template selection, build action, progress, and output feedback.

#### Scenario: Populated workspace
- **WHEN** a valid saved source and template are loaded
- **THEN** outline, editor, preview, diagnostics, template state, and build availability are visible together

#### Scenario: Required workbench states
- **WHEN** the workspace is populated, loading, empty, error, disabled, or permission-blocked
- **THEN** the corresponding state has visible text, non-color status cues, and an applicable recovery action

### Requirement: Expose structured diagnostics and preview
Diagnostics MUST display severity, stable code, message, source line, and target,
and the preview MUST be derived from renderer-neutral typed data rather than
DOCX or OOXML implementation objects.

#### Scenario: Activate a diagnostic
- **WHEN** the user activates a diagnostic with a source line
- **THEN** the editor focuses the corresponding line without changing the source

#### Scenario: Generate preview
- **WHEN** inspection and validation complete for a saved source
- **THEN** the preview mapper produces a structural paper view without importing python-docx or lxml

### Requirement: Build asynchronously and preserve valid output
The workbench SHALL show ordered build stages, support cooperative cancellation,
suppress stale results, and MUST preserve a previously valid output on
validation, permission, render, finalize, cancellation, or stale-operation
failure.

#### Scenario: Successful build
- **WHEN** a valid saved source, valid template, and writable output are built
- **THEN** progress reports parse, validate, compile, render, and finalize in order and the final DOCX path is shown

#### Scenario: Cancel before finalize
- **WHEN** the current build is canceled before atomic output replacement
- **THEN** the operation reports cancellation and the prior output remains unchanged

#### Scenario: Ignore stale completion
- **WHEN** an older operation completes after a newer workspace operation starts
- **THEN** the older result does not replace current diagnostics, preview, progress, or output state

### Requirement: Remain accessible, offline, and local-only
All desktop flows MUST work without sockets, credentials, database, telemetry,
AI, dark mode, or runtime locale switching, and the workbench MUST support
keyboard navigation, visible focus, programmatic labels, sufficient contrast,
and practical minimum-window resizing.

#### Scenario: Run with network blocked
- **WHEN** sockets are blocked during open, save, validate, preview, and build
- **THEN** all local desktop flows retain their specified behavior

#### Scenario: Keyboard-only operation
- **WHEN** the user operates file, template, diagnostics, panel, save, and build actions without a pointer
- **THEN** focus order and labels make every required action reachable and understandable
