# Component Seam Prototype

## Component Tree

- Runtime adapters
  - `docforge` CLI
  - Python HTTP adapter
  - Python sidecar adapter
  - TypeScript `WorkbenchTransport`
  - Rust Tauri command bridge
- Shared application services
  - project open
  - inspect
  - validate
  - review
  - build
- Project boundary
  - DocForge project constants
  - strict manifest model
  - generic metadata
  - optional academic profile
  - safe project-relative paths
- Core document pipeline
  - Markdown parser
  - `ForgeDocument`
  - Validator
  - Template resolver
  - Bibliography
  - Compiler
  - RenderPlan
  - DOCX renderer
  - Finalize, postflight, and preview
- Templates
  - `docforge-standard`
  - academic template family

## Cohesion Check

- One reason to change: project identity and path policy change in the project
  boundary; Markdown semantics change in core; presentation rules change in
  templates; OOXML mechanics change in the renderer.
- State owner: one request-scoped application context owns the resolved project,
  source snapshot, document, diagnostics, RenderPlan, progress, and output.
- Side effects: only project loader reads project inputs, explicit save writes
  source, Review writes Review outputs, and build finalization atomically
  replaces the requested DOCX and derived preview.

## Coupling Check

- Allowed imports: adapters -> application -> project/core/template/compiler ->
  RenderPlan -> renderer.
- Forbidden imports: parser/core -> template, renderer, transport, UI, or AI;
  renderer -> project manifest, Markdown parser, document profile, transport,
  or UI; adapters -> renderer internals.
- Public API: resolved project values, `ForgeDocument`, `ValidationIssue`,
  RenderPlan, application request/results, DocForge protocol DTOs, and output
  descriptors.
- Extraction target: per-language identity constants, shared protocol fixtures,
  typed generic and academic metadata bindings, and one safe path resolver.

## Case Matrix

| Case | Project Boundary | Core Pipeline | Runtime Boundary | Expected Result |
| --- | --- | --- | --- | --- |
| General | valid DocForge v1, no academic profile | one `ForgeDocument` pipeline | DocForge protocol | succeeds |
| Academic | valid DocForge v1 with academic profile | same `ForgeDocument` pipeline | DocForge protocol | succeeds |
| Obsolete manifest | ThesisForge manifest/schema | not entered | not dispatched | rejected |
| Unsafe resource | traversal or symlink escape | not entered | not dispatched | rejected |
| Old protocol | valid project | application not dispatched | ThesisForge protocol | rejected |
| Fatal validation | valid project | stops at validation | structured failure | prior output preserved |
