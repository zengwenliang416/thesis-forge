# Development Handoff To Verify: docforge-project-format-v1

## Implemented Slices

- `001-project-contract`: strict `docforge.yaml` project contract and safe
  project-relative paths.
- `002-generic-document-domain`: renderer-neutral `ForgeDocument` pipeline.
- `003-python-package-cli`: sole `docforge` package, import, and CLI identity.
- `004-runtime-protocol`: shared Python, TypeScript, Rust, HTTP, sidecar, and
  Tauri workbench/BuildReport contract.
- `005-template-profiles`: generic and optional academic metadata bindings plus
  packaged `docforge-standard`.
- `006-workbench-desktop`: neutral DocForge workbench, desktop identity,
  installed macOS package, and Microsoft Word final preview.
- `007-repository-delivery`: active projects, documentation, CI, packaging,
  facticity, and release-grade macOS artifacts.
- `008-end-to-end-verification`: items 8.1 through 8.6 complete with the
  project-scoped SpecNav Verification Runtime ready and all current-HEAD task
  receipts passing.

## Files Changed

- Python domain, project, application, presentation, templates, CLI, adapters,
  sidecar, distribution, and verification code under `src/docforge`, `scripts`,
  and `pyproject.toml`.
- Shared runtime schema and fixtures under `protocol`.
- React/Vite workbench, transport/state, component tests, and Playwright
  acceptance under `frontend`.
- Tauri application, product identity, sidecar boundary, bundle metadata, and
  Rust tests under `src-tauri`.
- Generic and academic templates, examples, QA fixtures, repository
  documentation, CI, release workflows, and distribution contracts.
- OpenSpec task packets, reviews, validation ledgers, CodeGraph evidence, and
  installed macOS/Word evidence under this change.

## Requirements Covered

- One strict `docforge.project.v1` manifest with neutral source, output, and
  Review defaults and no obsolete compatibility path.
- One generic `ForgeDocument` semantic model and unchanged deterministic
  parse/validate/compile/render/finalize/postflight/preview ordering.
- Generic common metadata and optional typed academic profile resolved by
  template policy before RenderPlan construction.
- One DocForge package, CLI, workbench protocol, BuildReport schema, desktop
  identity, managed sidecar, examples, documentation, CI, and release naming.
- Safe project paths, cancellation, stale-result suppression, output
  authorization, atomic replacement, prior-output retention, and offline
  operation.
- Installed macOS DocForge application and Microsoft Word final-preview flow.

## Prototype Decisions Implemented

- Preserved the approved light-only Simplified Chinese three-pane workbench and
  responsive/mobile panel behavior.
- Reused the existing editor, outline, structural preview, diagnostics,
  template, progress, output, and final-preview components.
- Kept the arbitrary-Markdown importer and npm Agent Skill outside this
  breaking migration.
- Kept Microsoft Word as the target final-preview engine; no WPS fallback or
  compatibility branch was added.

## Components Created / Reused / Extracted

- Created strict DocForge project constants/models, typed metadata binding
  registry, generic template, runtime parity fixture, frontend identity
  constants, facticity checker, and installed acceptance receipt.
- Reused the existing parser, validator, compiler, RenderPlan, DOCX renderer,
  application services, HTTP adapter, sidecar, frontend shell, Tauri bridge,
  cancellation, authorization, and atomic-output mechanisms.
- Centralized project, protocol, filename, binding, product, sidecar, and
  release identities at their language or packaging boundaries instead of
  duplicating literals.

## API / Data Flow Changes

- Project entry is now a directory or `docforge.yaml`; bare Markdown and
  `thesisforge.yaml` are rejected.
- Public Python import and console command are solely `docforge`.
- Runtime requests use `docforge.workbench.v1`; BuildReport uses
  `docforge.build-report.v2`.
- Default data flow is
  `document.md -> ForgeDocument -> Validation -> Template -> RenderPlan ->
  build/document.docx`, with neutral Review outputs under `review/`.
- Desktop final preview authorizes only the build-derived Microsoft Word PDF
  associated with the current operation.

## Tests Added

- Project model, loader, path security, obsolete-contract rejection, parser
  purity, template binding, general/academic build, package, CLI, distribution,
  facticity, and active-fixture coverage.
- Python/TypeScript/Rust protocol parity, cancellation, stale result, build
  stage, output authorization, final-preview authorization, and negative
  compatibility vectors.
- Direct DOCX OOXML assertions for fields, bookmarks, OMML, sections, headers,
  footers, numbering, relationships, atomic replacement, and deterministic
  normalized output.
- Frontend unit, real HTTP, responsive, accessibility, browser matrix, Tauri,
  bundle, and installed macOS/Microsoft Word acceptance.

## Local Validation

- Python: `1379 passed`; Ruff passed.
- Frontend: typecheck, lint, production build, and `245` unit tests passed.
- Playwright: real Python HTTP `1 passed`; isolated shared matrix `16 passed`
  with `20` intentional skips.
- Rust: format/check passed; `14` project tests and `32` protocol-contract
  tests passed.
- Python wheel/sdist and isolated offline general/academic
  inspect/validate/review/build passed.
- macOS `DocForge.app`, `DocForge_0.1.0_aarch64.dmg`, managed sidecar,
  cancellation, build, reopen, and checksum verification passed.
- Installed Microsoft Word 16.112 generated and displayed the verified
  `document.preview.pdf`.
- Facticity reports zero active findings; strict OpenSpec validation passes.

## Known Risks

- The default Playwright port `4173` is occupied by an unrelated local process;
  the unchanged matrix passed on isolated port `4174`.
- Native Windows WebView2 remains a broader product-platform receipt, although
  Task 006 and A9 explicitly use installed macOS and Microsoft Word as their
  sensory gate.
- Local release artifacts are not a claim of external GitHub publication,
  signing, or notarization.
- Historical failure records remain append-only; eligible failures have
  current-HEAD retest adjudications and are not deleted or rewritten.
- The ExFAT source checkout cannot represent a `0600` Runtime authority key, so
  trusted verification runs from an APFS Git worktree at the same product HEAD.

## Items Requiring Six-Domain Verification

- Bind Task 001 through 008 evidence and A1 through A10 to the current committed
  HEAD with official task acceptance artifacts.
- Generate and explicitly approve the immutable case snapshot, then prepare and
  explicitly approve the successor generation.
- Run facticity, static, unit, redteam, E2E, and sensory domains through the
  locked project-scoped Runtime with `fallback_used: false`.
- Preserve and adjudicate prior failed attempts instead of deleting them.
- Validate installation, promotion, and archive gates.
- Stop before starting the separate arbitrary-Markdown-to-DocForge npm Agent
  Skill change.
