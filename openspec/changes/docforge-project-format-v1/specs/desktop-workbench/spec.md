## MODIFIED Requirements

### Requirement: Provide one cross-platform frontend
The project SHALL provide one React + TypeScript + Vite frontend that runs in a
Web browser and inside Tauri 2 packages for macOS and Windows. It MUST keep all
DocForge core imports and commands usable without Node.js, Rust, Tauri, or an
HTTP server.

#### Scenario: Launch each supported runtime
- **WHEN** the user opens the Web build or launches the macOS or Windows package
- **THEN** the same light-theme Simplified Chinese DocForge workbench and shared feature set open

#### Scenario: Use core without frontend toolchains
- **WHEN** Node.js, Rust, Tauri, and the HTTP adapter are absent and the user imports DocForge or runs a core CLI command
- **THEN** the import or command succeeds without importing the UI runtime

### Requirement: Use typed runtime transports
The frontend MUST depend on one versioned `WorkbenchTransport` contract using
`docforge.workbench.v1`. Web MUST use a thin HTTP adapter and Tauri MUST use a
command/sidecar adapter. Both Python adapters MUST call existing application
services and MUST NOT implement parsing, validation, numbering, compilation,
rendering, or finalization.

#### Scenario: Run through Web
- **WHEN** the browser requests project open, inspect, validate, review, or build
- **THEN** the HTTP adapter validates a DocForge DTO, calls the matching application service, and returns a serialized result

#### Scenario: Run through Tauri
- **WHEN** the desktop frontend requests project open, inspect, validate, review, or build
- **THEN** a Tauri command forwards a DocForge request to the managed Python sidecar and returns the same serialized contract

#### Scenario: Reject implementation leakage
- **WHEN** a transport response is inspected
- **THEN** it contains no pathlib, Python exception, python-docx, lxml, or renderer-private object

#### Scenario: Reject obsolete protocol
- **WHEN** Web, Tauri, or the frontend receives `thesisforge.workbench.v1`
- **THEN** the request or response is rejected without compatibility dispatch

### Requirement: Manage one explicit source lifecycle
The workbench MUST open one DocForge project through a directory or
`docforge.yaml`, show its manifest-resolved Markdown source, track dirty edits,
perform no autosave, and persist source changes only after an explicit Save,
Save As, workspace save, or download action supported by the current runtime.
It MUST NOT treat a bare Markdown file as a complete project.

#### Scenario: Open a project
- **WHEN** the user selects a readable DocForge project directory or manifest
- **THEN** the workbench loads one versioned source snapshot and derives outline, preview, and diagnostics from the manifest-resolved source

#### Scenario: Reject bare Markdown
- **WHEN** the user selects a Markdown file without a DocForge project
- **THEN** the workbench explains that a project manifest is required and does not synthesize one

#### Scenario: Edit without saving
- **WHEN** the user changes editor text
- **THEN** the workspace becomes dirty and Validate and Build remain disabled until save succeeds

#### Scenario: Atomic save fails
- **WHEN** a desktop atomic save or Web workspace/download action fails
- **THEN** the prior source or browser snapshot remains intact, dirty state remains visible, and the workbench exposes a recovery action

### Requirement: Build asynchronously and preserve valid output
The workbench SHALL show ordered build stages, support cooperative cancellation,
suppress stale results, and MUST preserve a previously valid output on
validation, permission, render, finalize, postflight, preview, cancellation, or
stale-operation failure.

#### Scenario: Successful build
- **WHEN** a valid saved project, valid template, and writable output are built
- **THEN** progress reports parse, validate, compile, render, finalize, postflight, and preview in order and the final neutral DOCX path is shown

#### Scenario: Cancel before finalize
- **WHEN** the current build is canceled before atomic output replacement
- **THEN** the operation reports cancellation and the prior output remains unchanged

#### Scenario: Ignore stale completion
- **WHEN** an older operation completes after a newer workspace operation starts
- **THEN** the older result does not replace current diagnostics, preview, progress, or output state

### Requirement: Remain accessible and preserve local-first desktop operation
All macOS and Windows flows MUST work with external sockets blocked and without
credentials, database, telemetry, AI, dark mode, or runtime locale switching.
Web flows MUST use only the configured DocForge HTTP endpoint. Every runtime
MUST support keyboard navigation, visible focus, programmatic labels,
sufficient contrast, responsive layout, and practical minimum-window resizing.

#### Scenario: Run with network blocked
- **WHEN** external sockets are blocked during desktop open, save, validate, review, preview, and build
- **THEN** macOS and Windows flows retain their specified behavior through the bundled local sidecar

#### Scenario: Use configured Web transport
- **WHEN** the workbench runs in a browser
- **THEN** it communicates only with the configured versioned DocForge HTTP endpoint and exposes browser capability limits honestly

#### Scenario: Keyboard-only operation
- **WHEN** the user operates project, template, diagnostics, panel, save, and build actions without a pointer
- **THEN** focus order and labels make every required action reachable and understandable

## ADDED Requirements

### Requirement: Present document workbench information
The shared React frontend SHALL implement the approved three-pane DocForge
workbench with product bar, project and document identity, outline, Markdown
editor, document-style structural preview, diagnostics, template selection,
build action, progress, and output feedback. Labels and filenames SHALL use
neutral document terminology rather than treating every project as a thesis.

#### Scenario: Populated general workspace
- **WHEN** a valid saved general project and `docforge-standard` are loaded
- **THEN** outline, editor, preview, diagnostics, template state, and build availability are visible together without academic-only labels

#### Scenario: Populated academic workspace
- **WHEN** a valid academic project and academic template are loaded
- **THEN** academic metadata appears only where the project and template require it

#### Scenario: Required workbench states
- **WHEN** the workspace is populated, loading, empty, error, disabled, or permission-blocked
- **THEN** the corresponding state has visible text, non-color status cues, and an applicable recovery action

## REMOVED Requirements

### Requirement: Present academic workbench information
The shared React frontend SHALL implement the approved academic three-pane
workbench with product bar, outline, Markdown editor, paper-style structural
preview, diagnostics, template selection, build action, progress, and output
feedback.

#### Scenario: Populated workspace
- **WHEN** a valid saved source and template are loaded
- **THEN** outline, editor, preview, diagnostics, template state, and build availability are visible together

#### Scenario: Required workbench states
- **WHEN** the workspace is populated, loading, empty, error, disabled, or permission-blocked
- **THEN** the corresponding state has visible text, non-color status cues, and an applicable recovery action
