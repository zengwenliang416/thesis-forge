# Prototype Handoff: docforge-project-format-v1

## Approved Branch Variant

- Branch: `component-seam`
- Variant: `single-docforge-pipeline`
- Approval: explicitly approved by the user on 2026-08-26.

## Screens Or Flows

- Project open resolves a directory or `docforge.yaml`, validates the strict
  manifest and confined paths, then loads the manifest-selected Markdown.
- Inspect, validate, review, and build share the same application services.
- General and academic projects enter the same `ForgeDocument` pipeline.
- Build proceeds through parse, validate, compile, render, finalize,
  postflight, and preview; fatal validation stops before rendering.
- Old manifest, schema, package, command, protocol, and BuildReport identities
  fail at their owning entry boundary without compatibility dispatch.

## Components To Create

- Per-language DocForge project and protocol identity constants.
- Strict `DocForgeProjectManifest` with generic metadata and optional typed
  academic profile.
- `ForgeDocument` as the only public core document aggregate.
- Cross-language DocForge protocol fixtures.
- Bundled `docforge-standard` template.

## Components To Reuse

- Project-relative path normalization and symlink containment.
- Markdown parser, semantic blocks and inlines, source locations, stable IDs,
  references, citations, and bibliography configuration.
- Validator, template resolver, compiler, numbering, bookmarks, bibliography,
  RenderPlan, DOCX renderer, Review, BuildReport, finalization, postflight,
  preview, cancellation, and atomic output services.
- React workbench component tree, workspace state, `WorkbenchTransport`, HTTP
  adapter, and Tauri command bridge.

## Extraction Targets

- Manifest name, schema, source, output, Review, protocol, and BuildReport
  constants at each Python, TypeScript, and Rust boundary.
- Shared protocol fixtures that assert parity across all runtimes.
- Strict common metadata and optional academic profile models.
- Template-owned generic and academic metadata bindings.
- One safe project path resolver per owning runtime boundary.

## API Contracts

- Project entry: directory or `docforge.yaml`.
- Project schema: `docforge.project.v1`.
- Core aggregate: `ForgeDocument`.
- Public Python import and command identity: `docforge`.
- Workbench protocol: `docforge.workbench.v1`.
- Build report schema: `docforge.build-report.v2`.
- Default source: `document.md`.
- Default outputs: `build/document.docx`,
  `review/document.review.md`, and
  `review/document.review-map.json`.

## Data Flows

- `docforge.yaml -> strict project model -> confined paths -> Markdown and resources`.
- `Markdown -> ForgeDocument -> validation -> template resolution -> RenderPlan -> DOCX`.
- Generic metadata flows through typed common bindings.
- Academic data flows only through the optional academic profile and templates.
- CLI, HTTP, and Tauri intents flow through shared application services and one
  serialized DocForge contract.
- Successful output flows through atomic replacement, postflight, and optional
  Microsoft Word or supported Office final preview.

## State Behavior

- Loading: preserve current workbench project and operation loading state.
- Empty: require a DocForge project and explain that bare Markdown needs the
  later importer.
- Error: show structured project, validation, permission, transport, render,
  finalization, postflight, and preview failures.
- Disabled: keep validate and build unavailable for dirty or invalid workspace
  state according to the current lifecycle.
- Permission: preserve explicit local workspace and output authorization with
  no path-boundary bypass.

## Theme And Locale Policy

- Theme support: light-only.
- Theme modes shown in prototype: the component-seam prototype has no visual
  canvas; production remains light mode only.
- Theme toggle: intentionally omitted.
- Internationalization: disabled.
- Locales shown in prototype: the component-seam prototype has no visible copy;
  production remains Simplified Chinese `zh-CN`.
- Locale switcher: intentionally omitted.

## Out Of Scope Items

- Arbitrary Markdown importing and the npm Agent Skill.
- Automatic migration of external projects.
- Compatibility aliases or dual loaders.
- UI layout redesign, dark mode, locale switching, database, accounts, cloud
  storage, or template marketplace.
- Changes to Markdown syntax, numbering semantics, OOXML fields, or Office
  finalization behavior beyond neutral identity.

## Required Tests

- Project manifest, metadata, profile, defaults, obsolete contract, and path
  redteam tests.
- `ForgeDocument`, parser, validator, compiler, bibliography, Review, and
  architecture boundary tests.
- Python package, CLI, offline, wheel, and clean-install tests.
- Python, TypeScript, and Rust protocol parity, cancellation, stale result,
  BuildReport, and final-preview authorization tests.
- Generic and academic template and E2E builds.
- OOXML structural, deterministic output, atomic replacement, installed macOS,
  accessibility, responsive, and Microsoft Word sensory tests.
- Repository facticity checks for all obsolete active identities.

## Open Risks

- The Python package move can leave mixed import graphs; use bounded slices and
  clean-install verification.
- Protocol constants can diverge across languages; require shared parity
  fixtures before adapter changes close.
- Broad term replacement can damage historical evidence or valid academic
  prose; classify every remaining occurrence rather than deleting blindly.
- Immediate compatibility removal breaks external projects; document the
  breaking change without silently migrating user files.
