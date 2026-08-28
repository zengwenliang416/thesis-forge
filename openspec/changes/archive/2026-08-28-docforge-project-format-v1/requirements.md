# Requirements: docforge-project-format-v1

## Summary

Replace the thesis-centric public and internal product contract with a generic
DocForge document project contract. The result must support ordinary documents
as the default while retaining academic theses as an explicit profile and
template family.

## Users & Actors

- Authors importing or maintaining Markdown documents.
- Authors producing academic papers or theses through an academic profile.
- CLI users, desktop users, and web workbench users opening the same project.
- Template authors defining generic or document-type-specific presentation.
- Maintainers packaging the Python runtime, frontend, Tauri application, and CI.

## In Scope

- The only project manifest is `docforge.yaml`.
- The manifest schema is `docforge.project.v1`.
- The conventional source filename is `document.md`; `document.source` may
  reference another safe project-relative `.md` or `.markdown` path.
- Neutral defaults are `build/document.docx`,
  `review/document.review.md`, and `review/document.review-map.json`.
- The public command is `docforge`; the Python distribution/import package and
  desktop sidecar/runtime identifiers use DocForge naming.
- The workbench protocol is versioned under a DocForge identifier.
- The core document aggregate uses a neutral domain name rather than
  `ThesisDocument`.
- `document.type` is a stable non-empty identifier and defaults to `general`.
- Common metadata supports title, subtitle, authors, organization, document
  date, version, and keywords without requiring academic fields.
- Student, institution, degree, advisor, and completion data belong to an
  optional typed `academic` profile.
- `docforge-standard` is bundled and builds a document with no academic profile.
- Existing parser, validator, compiler, RenderPlan, bibliography, DOCX renderer,
  Review, BuildReport, cancellation, atomic output, and path-security behavior
  continue through the renamed contracts.
- Repository-owned examples, fixtures, tests, documentation, desktop packaging,
  and CI are converted in the same change.
- Obsolete ThesisForge manifests, schema identifiers, protocol identifiers, and
  CLI/package names are rejected or absent; no compatibility alias is added.

## Out of Scope

- Markdown-to-DocForge project importing and npm Agent Skill implementation.
- DOCX-to-Markdown or DOCX-to-project conversion.
- Automatic migration of external user projects.
- Database, account, collaboration, template marketplace, or cloud storage.
- Dark mode, theme switching, new locales, or a redesigned workbench layout.
- Changes to numbering semantics, OOXML field implementation, or Office
  finalization behavior except neutral output names.

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- Required UI decisions: preserve the approved DocForge workbench visual
  language; replace thesis-specific labels, default filenames, file filters, and
  project identity text only. No new screen or layout is introduced.

## Theme & Locale Capability Impact

- Theme support: `light-only`
- Theme toggle policy: explicitly omit
- Internationalization: `disabled`
- Supported locales: `zh-CN`
- Default locale: `zh-CN`
- Prototype coverage: no new prototype is required; sensory verification must
  cover the existing desktop and mobile DocForge workbench in light mode and
  `zh-CN` after terminology changes.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Required architecture/database decisions: preserve the same dependency
  direction and offline deterministic pipeline while renaming the public
  package, CLI, project/domain contracts, and generic metadata boundary. No
  database is introduced. Academic metadata becomes a typed optional profile,
  not renderer or parser special casing.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- Required data-flow decisions: CLI, HTTP, and Tauri continue to use the same
  application services and typed requests. Project open flows accept a directory
  or `docforge.yaml`, reject bare Markdown and obsolete manifests, and return
  neutral project/source/output identities.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Cohesion/coupling impact: generic document and project contracts remain in the
  core/project layers; academic profile interpretation belongs to typed metadata
  and templates; adapters may not translate into a second domain model.
- Shared extraction requirement: centralize project constants, default
  filenames, protocol version, and public product identity instead of repeating
  string literals across Python, TypeScript, Rust, tests, and packaging scripts.

## Unresolved Gaps

- None.
