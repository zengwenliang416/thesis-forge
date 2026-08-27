## 1. DocForge Project Contract

**User outcome:** Users can open a strict `docforge.yaml` project with neutral
document defaults, generic metadata, optional academic data, and unchanged path
security.

- [x] 1.1 Add failing manifest-model tests for `docforge.project.v1`, `document.md`, neutral output and Review defaults, generic metadata, optional academic profile, unknown fields, and obsolete contract rejection.
- [x] 1.2 Replace the project manifest model with the strict DocForge v1 schema and centralize Python project identity and default filename constants.
- [x] 1.3 Update project entrypoint discovery to accept only a directory or `docforge.yaml` and return stable diagnostics for bare Markdown and obsolete manifests.
- [x] 1.4 Preserve and extend project-relative path tests for absolute, remote, traversal, NUL, and symlink-escape rejection across source, resources, output, and Review paths.
- [x] 1.5 Create minimal general and academic DocForge project fixtures and pass the focused project model, loader, path, and application-service tests.

## 2. Generic Document Domain

**User outcome:** General and academic Markdown use one neutral document model
without exposing Word, template, transport, or academic-only implementation
details in the parser and core.

- [x] 2.1 Add failing public-model tests for `ForgeDocument`, stable semantic IDs, source locations, deterministic parsing, and absence of the `ThesisDocument` export.
- [x] 2.2 Rename the core aggregate to `ForgeDocument` and update parser backends and parser results without changing Markdown syntax or semantic block and inline types.
- [x] 2.3 Update validator, application-service, compiler, bibliography, Review, preview, and BuildReport type boundaries to consume `ForgeDocument`.
- [x] 2.4 Add architecture tests that keep parser and core imports free of DOCX, OOXML, renderer, transport, UI, template-profile branching, and AI dependencies.
- [x] 2.5 Pass focused parser, validator, compiler, bibliography, Review, preview, and domain-model regressions for both general and academic fixtures.

## 3. DocForge Python Package And CLI

**User outcome:** Users install and invoke DocForge through the `docforge`
package and command, with no active `thesisforge` import or command alias.

- [x] 3.1 Add failing distribution, import, CLI help, and console-entrypoint tests for the DocForge package and `docforge` command.
- [x] 3.2 Move the Python import package from `thesis_forge` to `docforge` and update internal imports, package discovery, typed resources, and test imports in bounded batches.
- [x] 3.3 Expose `docforge inspect`, `validate`, `review`, and `build` over shared project application services with neutral filenames and DocForge diagnostics.
- [x] 3.4 Remove obsolete Python package and `thesisforge` CLI entrypoints rather than retaining aliases, shims, loaders, or fallback imports.
- [x] 3.5 Pass package build, wheel-content, clean-environment install, import, CLI, and offline execution tests.

## 4. Shared Runtime Protocol

**User outcome:** Browser and desktop users receive the same DocForge project,
diagnostic, preview, progress, cancellation, and build-result behavior.

- [x] 4.1 Add failing parity fixtures for `docforge.workbench.v1`, `docforge.build-report.v2`, project identity, neutral filenames, ordered stages, diagnostics, output, and final preview.
- [x] 4.2 Centralize and migrate Python HTTP and sidecar DTO validation, serialization, BuildReport schemas, and application dispatch to the DocForge protocol.
- [x] 4.3 Centralize and migrate TypeScript DTOs, runtime guards, Web transport, build events, workspace fixtures, and error handling to the DocForge protocol.
- [x] 4.4 Centralize and migrate Rust Tauri request validation, sidecar dispatch, output authorization, final preview authorization, and protocol tests to DocForge identities.
- [x] 4.5 Reject old workbench and BuildReport identifiers at every runtime boundary without dispatching services or authorizing outputs.
- [x] 4.6 Pass Python, TypeScript, and Rust cross-runtime parity, cancellation, stale-result, ordered-stage, and preview-authorization tests.

## 5. Generic And Academic Templates

**User outcome:** Ordinary documents build with `docforge-standard` and no
fabricated academic data, while academic templates retain typed academic
metadata behavior.

- [x] 5.1 Add failing template and validation tests for generic metadata bindings, optional academic profile bindings, and template-scoped required fields.
- [x] 5.2 Extend the typed template and compiler binding boundary so common metadata and optional profiles resolve before RenderPlan construction.
- [x] 5.3 Create and package `docforge-standard` with deterministic styles and no university, degree, advisor, student, or completion placeholders.
- [x] 5.4 Adapt repository-owned academic templates to read the typed `academic` profile without parser or renderer document-type branching.
- [x] 5.5 Build general and academic fixtures and verify template package validity, RenderPlan neutrality, visible metadata, and absence of fabricated academic content.

## 6. Workbench And Desktop Identity

**User outcome:** The installed workbench opens DocForge projects and presents
neutral document terminology while preserving the approved layout,
accessibility, responsive behavior, and Microsoft Word preview flow.

- [x] 6.1 Update project picker and open flows to accept a directory or `docforge.yaml`, resolve `document.md`, and explain rejection of bare Markdown and obsolete projects.
- [x] 6.2 Replace active thesis-specific labels, filenames, empty states, diagnostics, help, template text, and output copy with neutral DocForge document terminology.
- [x] 6.3 Rename Tauri application metadata, bundle identifiers, sidecar executable, product-owned environment variables, installer names, and release assets to DocForge.
- [x] 6.4 Update component and browser tests for general and academic project states without changing the approved three-pane layout, light-only theme, or `zh-CN` policy.
- [x] 6.5 Install the macOS package and complete desktop and mobile sensory checks for project opening, diagnostics, build progress, neutral filenames, accessibility, and Microsoft Word final preview.

## 7. Repository-Owned Projects And Delivery

**User outcome:** Examples, documentation, CI, installers, and release downloads
all demonstrate the same DocForge project format instead of mixed old and new
contracts.

- [x] 7.1 Convert active examples and canonical fixtures to `docforge.yaml`, `document.md`, neutral build and Review filenames, and the appropriate general or academic template.
- [x] 7.2 Update active user and maintainer documentation, schemas, protocol references, commands, screenshots, and test instructions to DocForge terminology while preserving historical archive evidence.
- [x] 7.3 Update build scripts, sidecar packaging, distribution allowlists, CI checks, and release workflows to package and verify DocForge artifacts.
- [x] 7.4 Add repository facticity checks that fail on obsolete active manifest, schema, command, package, protocol, sidecar, default filename, or release identifiers.
- [x] 7.5 Build release-grade macOS artifacts and verify installer contents, application launch, bundled sidecar, version metadata, checksums, and downloadable asset names.

## 8. End-To-End Verification

**User outcome:** The breaking migration is proven across security, deterministic
compilation, real DOCX structures, runtime parity, installed Office behavior,
and release packaging before the Markdown importer skill begins.

- [x] 8.1 Run focused Python project, parser, validation, template, compiler, renderer, Review, BuildReport, adapter, CLI, package, and distribution tests with Ruff.
- [x] 8.2 Run frontend typecheck, lint, unit, browser, responsive, accessibility, and real HTTP tests plus Rust format, check, unit, and Tauri integration tests.
- [x] 8.3 Run CLI and runtime E2E inspect, validate, review, and build flows for complete general and academic DocForge projects with network and AI credentials unavailable.
- [x] 8.4 Validate generated DOCX packages for fields, bookmarks, OMML, sections, headers, footers, numbering, relationships, atomic replacement, and deterministic normalized OOXML.
- [x] 8.5 Classify every remaining ThesisForge or thesis-named occurrence as historical or invalid, remove all invalid active occurrences, and attach evidence to acceptance assertions A1 through A10.
- [ ] 8.6 Re-run SpecNav development, six-domain verification, installation, promotion, and archive contracts and stop before the separate Markdown-to-DocForge npm Agent Skill change.
