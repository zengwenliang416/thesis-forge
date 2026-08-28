# docforge-runtime-contract Specification

## Purpose
TBD - created by archiving change docforge-project-format-v1. Update Purpose after archive.
## Requirements
### Requirement: Expose DocForge package and CLI identity
The Python distribution and import package SHALL use DocForge naming, and the
only public command SHALL be `docforge`. The runtime MUST NOT expose a
`thesisforge` command or import alias.

#### Scenario: Invoke DocForge CLI
- **WHEN** a user runs `docforge inspect`, `docforge validate`, `docforge review`, or `docforge build`
- **THEN** the command invokes the shared DocForge application services

#### Scenario: Reject obsolete CLI
- **WHEN** an installed distribution is inspected for console entrypoints
- **THEN** no `thesisforge` command is registered

#### Scenario: Import package without UI toolchains
- **WHEN** a caller imports the DocForge core package without Node.js, Rust, Tauri, or an HTTP server installed
- **THEN** the import succeeds without loading frontend or desktop dependencies

### Requirement: Use one versioned workbench protocol
The runtime SHALL require CLI adapters, Python HTTP and sidecar adapters,
TypeScript transports, and Rust Tauri commands to agree on
`docforge.workbench.v1` and SHALL reject the old
`thesisforge.workbench.v1` identifier.

#### Scenario: Dispatch matching request
- **WHEN** an adapter receives a complete request with `docforge.workbench.v1`
- **THEN** it validates and dispatches the typed operation

#### Scenario: Reject old protocol
- **WHEN** an adapter receives `thesisforge.workbench.v1`
- **THEN** it returns a stable unsupported-protocol failure without dispatching an application service

### Requirement: Preserve BuildReport structure under DocForge identity
Build events SHALL use `docforge.build-report.v2` for the existing typed
BuildReport structure and SHALL preserve ordered stage lifecycle, diagnostics,
bounded logs, output identity, and final preview data.

#### Scenario: Complete successful build
- **WHEN** a build completes successfully
- **THEN** its completed event contains a `docforge.build-report.v2` report with ordered stages and the neutral output path

#### Scenario: Reject old report identity
- **WHEN** TypeScript or Rust receives a report using `thesisforge.build-report.v2`
- **THEN** report validation rejects it and does not authorize the output or final preview

### Requirement: Keep runtime transports behaviorally identical
HTTP and Tauri adapters MUST validate the same command envelopes, call the same
application services, serialize the same diagnostics and preview models, and
preserve cancellation and stale-result rules.

#### Scenario: Transport parity
- **WHEN** equivalent inspect, validate, review, or build requests are sent through HTTP and Tauri
- **THEN** both transports return contract-equivalent results apart from runtime-specific file authorization fields

#### Scenario: Cancel build
- **WHEN** a client cancels an active build by request ID
- **THEN** the adapter propagates cooperative cancellation and a stale completion cannot replace current state

### Requirement: Rename desktop and release runtime identity
The desktop and release runtime SHALL use DocForge naming for Tauri product
metadata, bundle identifiers, sidecar names, application display text,
product-owned environment variables, installer filenames, and release assets.

#### Scenario: Inspect installed macOS package
- **WHEN** the packaged macOS application and bundled sidecar are inspected
- **THEN** their product identity and executable names are DocForge and no active ThesisForge runtime identity remains

### Requirement: Centralize runtime identity constants
Each language boundary SHALL define one authoritative set of project, protocol,
report, and default-filename constants, and shared fixtures MUST verify parity
across Python, TypeScript, and Rust.

#### Scenario: Cross-language contract test
- **WHEN** contract parity tests load the Python, TypeScript, and Rust expectations
- **THEN** manifest name, schema, protocol, report identity, and neutral defaults match exactly
