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

### Requirement: Provide one cross-platform frontend
The project SHALL provide one React + TypeScript + Vite frontend that runs in a
Web browser and inside Tauri 2 packages for macOS and Windows. It MUST keep all
core CLI imports and commands usable without Node.js, Rust, Tauri, or an HTTP
server.

#### Scenario: Launch each supported runtime
- **WHEN** the user opens the Web build or launches the macOS or Windows package
- **THEN** the same light-theme Simplified Chinese workbench and shared feature set open

#### Scenario: Use core without frontend toolchains
- **WHEN** Node.js, Rust, Tauri, and the HTTP adapter are absent and the user imports ThesisForge or runs a core CLI command
- **THEN** the import or command succeeds without importing the UI runtime

### Requirement: Use typed runtime transports
The frontend MUST depend on one versioned `WorkbenchTransport` contract. Web
MUST use a thin HTTP adapter and Tauri MUST use a command/sidecar adapter. Both
Python adapters MUST call existing application services and MUST NOT implement
parsing, validation, numbering, compilation, rendering, or finalization.

#### Scenario: Run through Web
- **WHEN** the browser requests inspect, validate, or build
- **THEN** the HTTP adapter validates a versioned DTO, calls the matching application service, and returns a serialized result

#### Scenario: Run through Tauri
- **WHEN** the desktop frontend requests inspect, validate, or build
- **THEN** a Tauri command forwards a versioned request to the managed Python sidecar and returns the same serialized contract

#### Scenario: Reject implementation leakage
- **WHEN** a transport response is inspected
- **THEN** it contains no pathlib, Python exception, python-docx, lxml, or renderer-private object

### Requirement: Manage one explicit source lifecycle
The workbench MUST open one Markdown workspace, show its saved content, track
dirty edits, perform no autosave, and persist source changes only after an
explicit Save, Save As, workspace save, or download action supported by the
current runtime.

#### Scenario: Open a source
- **WHEN** the user selects a readable desktop file or browser workspace input
- **THEN** the workbench loads one versioned snapshot and derives outline, preview, and diagnostics from it

#### Scenario: Edit without saving
- **WHEN** the user changes editor text
- **THEN** the workspace becomes dirty and Validate and Build remain disabled until save succeeds

#### Scenario: Atomic save fails
- **WHEN** a desktop atomic save or Web workspace/download action fails
- **THEN** the prior source or browser snapshot remains intact, dirty state remains visible, and the workbench exposes a recovery action

### Requirement: Reuse deterministic application services
Every runtime adapter MUST call the existing inspect, validation, and build
application services and MUST NOT duplicate Markdown parsing, validation rules,
numbering, bibliography, compilation, rendering, or package finalization.

#### Scenario: Refresh a saved workspace
- **WHEN** a saved source or selected template changes
- **THEN** the transport calls application services and maps serialized results into frontend view models

#### Scenario: Fatal validation
- **WHEN** validation returns one or more error-severity issues
- **THEN** compile and render are not called and Build remains unavailable

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

### Requirement: Expose structured diagnostics and preview
Diagnostics MUST display severity, stable code, message, source line, and target,
and the preview MUST be derived from renderer-neutral typed data rather than
DOCX or OOXML implementation objects.

#### Scenario: Activate a diagnostic
- **WHEN** the user activates a diagnostic with a source line
- **THEN** the editor focuses the corresponding line without changing the source

#### Scenario: Generate preview
- **WHEN** inspection and validation complete for a saved source
- **THEN** the frontend preview mapper produces a structural paper view without receiving python-docx, lxml, or raw OOXML

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

### Requirement: Remain accessible and preserve local-first desktop operation
All macOS and Windows flows MUST work with external sockets blocked and without
credentials, database, telemetry, AI, dark mode, or runtime locale switching.
Web flows MUST use only the configured ThesisForge HTTP endpoint. Every runtime
MUST support keyboard navigation, visible focus, programmatic labels, sufficient
contrast, responsive layout, and practical minimum-window resizing.

#### Scenario: Run with network blocked
- **WHEN** external sockets are blocked during desktop open, save, validate, preview, and build
- **THEN** macOS and Windows flows retain their specified behavior through the bundled local sidecar

#### Scenario: Use configured Web transport
- **WHEN** the workbench runs in a browser
- **THEN** it communicates only with the configured versioned ThesisForge HTTP endpoint and exposes browser capability limits honestly

#### Scenario: Keyboard-only operation
- **WHEN** the user operates file, template, diagnostics, panel, save, and build actions without a pointer
- **THEN** focus order and labels make every required action reachable and understandable
