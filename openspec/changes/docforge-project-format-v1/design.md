## Context

The product already presents itself as a general Markdown-to-Word workbench,
but the repository still encodes thesis-specific identity across the project
manifest, Python package, CLI, core aggregate, metadata, protocol schemas,
frontend fixtures, Tauri sidecar, default filenames, bundled examples, and
release packaging.

The current project boundary starts at `thesisforge.yaml` with
`thesisforge.project.v2`, resolves `thesis.md` and thesis-named outputs, and
constructs `ThesisDocument`. The same identity continues through
`thesisforge.workbench.v1` and `thesisforge.build-report.v2`. Academic metadata
is stored as the default metadata shape, so an ordinary document is forced
through a thesis-oriented contract even though the parser, compiler,
RenderPlan, and renderer are largely reusable.

This is a cross-cutting breaking migration. It must preserve the local-first,
deterministic, template-driven pipeline and security boundaries while removing
the obsolete public contract completely. Repository-owned projects can be
converted atomically; external automatic migration and compatibility aliases
are explicitly excluded.

## Goals / Non-Goals

**Goals:**

- Make `docforge.yaml` with `schema: docforge.project.v1` the only project
  entrypoint.
- Make ordinary documents the default through `document.type: general`,
  generic metadata, neutral filenames, and the bundled `docforge-standard`
  template.
- Retain academic documents through a typed optional `academic` profile and
  academic templates.
- Rename the public Python distribution/import package, CLI, domain aggregate,
  workbench protocol, build report identity, Tauri sidecar, application
  metadata, fixtures, and release assets to DocForge.
- Preserve one deterministic
  `Markdown -> ForgeDocument -> Validation -> Template -> RenderPlan -> DOCX`
  pipeline across CLI, HTTP, and Tauri.
- Preserve path confinement, cancellation, atomic output replacement,
  BuildReport stage ordering, Review/source-map behavior, final preview, and
  true OOXML rendering.

**Non-Goals:**

- Importing arbitrary Markdown into a generated DocForge project.
- Publishing the npm Agent Skill that will perform that later import.
- Automatically migrating external user projects.
- Supporting `thesisforge.yaml`, the `thesisforge` command, old Python imports,
  old protocol identifiers, or other compatibility aliases.
- Redesigning the workbench layout, adding theme or locale switching, or
  changing Markdown syntax.
- Changing numbering, bibliography formatting, OOXML field behavior, or Office
  finalization semantics beyond neutral identity and filenames.

## Decisions

### 1. Perform one repository-wide contract cutover

The migration SHALL replace the obsolete contracts in one change rather than
running old and new project loaders in parallel. `docforge.yaml`,
`docforge.project.v1`, the `docforge` command, the `docforge` Python package,
and DocForge protocol identifiers become authoritative together.

The alternative was a staged compatibility period with aliases and automatic
migration. That would duplicate loaders and protocol paths, make tests
ambiguous, and contradict the requirement to remove obsolete contracts.

### 2. Preserve protocol structure versions while changing their namespace

The workbench protocol becomes `docforge.workbench.v1`; the current BuildReport
shape becomes `docforge.build-report.v2`. The project schema is independently
versioned as `docforge.project.v1`.

The alternative was resetting every renamed protocol to v1. That would imply
that the BuildReport structure changed when this migration only changes its
public namespace. Keeping the existing structural version preserves accurate
schema history while still making old identifiers invalid.

### 3. Introduce a generic project model with explicit profiles

`document.source` defaults to `document.md`, `document.type` defaults to
`general`, and common metadata contains title, subtitle, authors,
organization, document date, version, and keywords. Thesis-only fields move to
an optional typed `academic` profile containing student, institution, degree,
advisor, and completion data.

Profiles are data supplied to validation and templates. Parser and renderer
code MUST NOT branch on `document.type`. An academic template may declare
academic profile requirements; `docforge-standard` must not.

The alternative was retaining the current metadata shape and making its fields
optional. That would keep academic concepts as the canonical model and allow
generic code to depend accidentally on thesis-only fields.

### 4. Rename the domain aggregate without changing semantic block identity

`ThesisDocument` becomes `ForgeDocument`. Existing block, inline,
source-location, stable-ID, bibliography, validation, and RenderPlan concepts
remain structurally compatible unless a focused compiler need requires an
explicit change.

The alternative was creating a second generic aggregate beside
`ThesisDocument`. That would force adapters and services to translate between
two domain models and violate the single-pipeline constraint.

### 5. Centralize identity and default constants at each language boundary

Python, TypeScript, and Rust each receive one authoritative module for product
identity, manifest/schema names, protocol identifiers, and neutral default
filenames. Cross-language fixtures assert equality at transport and packaging
boundaries.

A single generated multi-language constants file was considered but rejected
for this migration because it would add a new generation toolchain and failure
mode. Per-language constants plus shared fixtures provide explicit ownership
with lower complexity.

### 6. Keep project path resolution and output safety unchanged

All manifest paths remain normalized project-relative values. Absolute paths,
URL schemes, traversal, NUL values, and symlink escapes remain rejected.
Default outputs resolve to `build/document.docx`,
`review/document.review.md`, and
`review/document.review-map.json`. Render and Review write through temporary
files and replace targets only after successful validation.

The alternative was allowing absolute output paths for convenience. That
would weaken the current project boundary and complicate desktop authorization.

### 7. Convert repository-owned fixtures before removing old symbols

Implementation proceeds in vertical slices: project constants/model, domain
aggregate, application services, CLI/package, protocol/adapters, template,
workbench copy, fixtures/docs/packaging, then obsolete-identifier facticity.
Each slice updates its tests before the next removes dependent old symbols.

A blind repository-wide search-and-replace was rejected because `thesis` can
still be valid academic content, historical OpenSpec evidence, or template
terminology. Only active public/runtime contracts are prohibited.

## Risks / Trade-offs

- [Risk] The package and import rename touches most Python modules and can leave
  mixed import graphs. -> Mitigation: move by bounded package slices, run import
  and focused tests after each slice, and finish with an active-runtime
  obsolete-identifier audit.
- [Risk] Protocol constants can diverge across Python, TypeScript, and Rust. ->
  Mitigation: centralize per language and add parity fixtures exercised by all
  three test suites.
- [Risk] Removing compatibility immediately makes external projects unusable.
  -> Mitigation: document the breaking change and a manual format conversion;
  do not silently accept or mutate obsolete projects.
- [Risk] Generic metadata can become an untyped catch-all. -> Mitigation: use
  strict typed common metadata and a strict typed academic profile with unknown
  fields rejected.
- [Risk] Academic behavior may leak into renderer branching during extraction.
  -> Mitigation: templates own required metadata and formatting; architecture
  tests keep parser/core/renderer dependency boundaries explicit.
- [Risk] Broad renaming can alter historical evidence or unrelated active
  changes. -> Mitigation: use exact-path edits, preserve archived OpenSpec and
  unrelated dirty worktree content, and classify every remaining old term.
- [Trade-off] Per-language constants duplicate a small set of values. Their
  parity is test-enforced to avoid a more complex code-generation system.

## Migration Plan

1. Add failing contract tests for `docforge.yaml`, `docforge.project.v1`,
   neutral defaults, generic metadata, academic profiles, and obsolete
   contract rejection.
2. Replace the project model and loader with the DocForge v1 contract while
   retaining existing path-security implementation.
3. Rename `ThesisDocument` to `ForgeDocument` and update parser, validator,
   compiler, bibliography, Review, and application service types.
4. Rename the Python distribution/import package and expose only the
   `docforge` CLI.
5. Rename protocol identities to `docforge.workbench.v1` and
   `docforge.build-report.v2` across Python, shared schemas, TypeScript, Rust,
   and fixtures.
6. Add `docforge-standard` and separate generic metadata bindings from the
   optional academic profile.
7. Convert the React workbench terminology, Tauri identity/sidecar,
   repository-owned examples, tests, docs, CI, and release packaging.
8. Run focused unit and redteam tests, cross-runtime parity tests, full
   Python/frontend/Rust checks, general and academic E2E builds, OOXML
   structure validation, installed macOS sensory verification, and a
   facticity audit of obsolete active identifiers.

Rollback is source-control rollback of the complete migration before a release.
There is no runtime dual-format rollback path. Failed builds continue to retain
the last successful document output.

## Open Questions

None.
