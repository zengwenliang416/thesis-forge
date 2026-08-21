# ThesisForge v2 Complete Loop Implementation Catalogue

This catalogue is subordinate to `LOOP.md` and `docs/THESISFORGE_V2_PRODUCT_SPEC.md`.

It is not a batch execution script. Codex discovers the next green slice from this catalogue, copies at most three executable items into `LOOP.md`, and completes one item per cycle.

## Global execution rules

1. One implementation item modifies at most three repository files.
2. New, deleted, renamed, moved, test, fixture, documentation, schema, workflow, configuration, generated and lock files all count.
3. If a fourth file is required, split before editing product code.
4. Every item ends green under its exact Verify command.
5. Do not commit intentionally failing normal tests.
6. No legacy compatibility, migration, fallback parser, hidden flag or dual source of truth.
7. Unknown semantics fail explicitly.
8. Maker and Checker are separate roles.
9. Remote PR, push, merge and release remain human-gated.
10. File paths below match the uploaded 2026-08-19 repository. If the repository has since changed, re-slice rather than silently widening scope.

## Dependency overview

```text
BuildReport visibility
        ↓
Mandatory project manifest
        ↓
Typed IR and single parser
        ↓
Review / Structure / Final Layout
        ↓
Compiler and DOCX completeness
        ↓
Capability closure, security, CI and release
```

---

# Milestone 1 — BuildReport and visible build errors

The current product collapses detailed build failures to strings. This milestone fixes the data contract before building the UI.

## V2-101 — Typed application BuildReport

- Files: `src/thesis_forge/application/contracts.py`, `tests/application/test_build_report_contract.py`
- Behavior: define typed build intent, outcome, stage status, diagnostic, log, output and report models; convert `BuildValidationError` without losing issues.
- Verify: `.venv/bin/python -m pytest tests/application/test_build_report_contract.py`
- Acceptance: validation issue code, severity, line, target, details and order survive; terminal message-only errors are not an application contract.

## V2-102 — Backend terminal failure reports

- Files: `src/thesis_forge/adapters/runtime.py`, `tests/adapters/test_build_report_events.py`
- Behavior: every validation, compile, render, finalize, permission, cancellation and transport failure emits a terminal typed BuildReport.
- Verify: `.venv/bin/python -m pytest tests/adapters/test_build_report_events.py`
- Acceptance: every failed report has `outcome`, `failedStage`, stages, diagnostics, primary diagnostic and sanitized logs.

## V2-103 — Frontend BuildReport transport types

- Files: `frontend/src/transport/buildEvents.ts`, `frontend/src/transport/buildEvents.test.ts`
- Behavior: parse BuildReport v2 and reject message-only terminal failure events.
- Verify: `pnpm --dir frontend test -- buildEvents.test.ts`
- Acceptance: no `any`; source spans, related locations, stage lifecycle, logs, output and stale state are guarded.

## V2-104 — Python protocol serialization helpers

- Files: `src/thesis_forge/adapters/dto.py`, `tests/adapters/test_build_report_dto.py`
- Behavior: serialize application BuildReport to the JSON Schema shape without dropping nullable fields or diagnostic parameters.
- Verify: `.venv/bin/python -m pytest tests/adapters/test_build_report_dto.py`
- Acceptance: success, validation failure, render failure and cancellation round-trip against protocol examples.

## V2-105 — Correct stage lifecycle emission

- Files: `src/thesis_forge/application/services.py`, `tests/application/test_build_stage_lifecycle.py`
- Behavior: emit stage started before work, succeeded only after completion, failed on error and skipped for downstream stages.
- Verify: `.venv/bin/python -m pytest tests/application/test_build_stage_lifecycle.py`
- Acceptance: entering validate does not mark validate successful; a validate failure marks compile/render/finalize/postflight skipped.

## V2-106 — Workspace BuildSession state

- Files: `frontend/src/state/workspace.ts`, `frontend/src/state/workspace.buildSession.test.ts`
- Behavior: replace message-only build state with one BuildSession holding current report, stages, badge counts and previous successful output.
- Verify: `pnpm --dir frontend test -- workspace.buildSession.test.ts`
- Acceptance: failure retains last successful output and marks it stale; new success replaces it and clears stale state.

## V2-107 — Workbench consumes terminal BuildReport

- Files: `frontend/src/components/WorkbenchApp.tsx`, `frontend/src/components/WorkbenchApp.buildReport.test.tsx`
- Behavior: reduce stage/report events into BuildSession and preserve all diagnostics instead of dispatching one message.
- Verify: `pnpm --dir frontend test -- WorkbenchApp.buildReport.test.tsx`
- Acceptance: manual and live-preview intents are distinguishable; failed stage and diagnostics reach state.

## V2-108 — Build Output panel core

- Files: `frontend/src/components/BuildOutputPanel.tsx`, `frontend/src/components/BuildOutputPanel.test.tsx`
- Behavior: render stage summary and All/Errors/Warnings/Raw logs views with primary diagnostic expanded.
- Verify: `pnpm --dir frontend test -- BuildOutputPanel.test.tsx`
- Acceptance: diagnostic code, stage, message, source, suggestion and copy action are visible; logs are selectable and copyable.

## V2-109 — Integrate Build Output into preview shell

- Files: `frontend/src/components/PreviewPanels.tsx`, `frontend/src/components/PreviewPanels.buildOutput.test.tsx`
- Behavior: make Build Output a first-class panel reachable from failure and normal inspection.
- Verify: `pnpm --dir frontend test -- PreviewPanels.buildOutput.test.tsx`
- Acceptance: no dependence on the single-line StatusStrip for detailed errors.

## V2-110 — Build button error badge

- Files: `frontend/src/components/ProductBar.tsx`, `frontend/src/components/ProductBar.test.tsx`
- Behavior: show error count beside Build and open Build Output on activation.
- Verify: `pnpm --dir frontend test -- ProductBar.test.tsx`
- Acceptance: badge is accessible, absent with zero errors and does not disable recovery actions.

## V2-111 — Build Output and badge styling

- Files: `frontend/src/styles.css`
- Behavior: add clear error/warning/stage/stale styles without truncating the only available error detail.
- Verify: `pnpm --dir frontend build && git diff --check`
- Acceptance: long messages wrap; keyboard focus is visible; error count remains legible.

## V2-112 — Diagnostic source navigation

- Files: `frontend/src/state/editorNavigation.ts`, `frontend/src/components/BuildOutputPanel.tsx`, `frontend/src/components/BuildOutputPanel.navigation.test.tsx`
- Behavior: Locate Source focuses the editor at the diagnostic SourceSpan and keeps the diagnostic selected.
- Verify: `pnpm --dir frontend test -- BuildOutputPanel.navigation.test.tsx`
- Acceptance: line and column navigation works; diagnostics without source disable the action rather than failing.

## V2-113 — Retain stale successful preview in state

- Files: `frontend/src/state/preview.ts`, `frontend/src/state/preview.stale.test.ts`
- Behavior: retain the last successful preview descriptor after a failed attempt and relate it to the successful build ID.
- Verify: `pnpm --dir frontend test -- preview.stale.test.ts`
- Acceptance: failed output never overwrites the successful descriptor; cancellation has an explicit policy.

## V2-114 — Stale preview banner

- Files: `frontend/src/components/PreviewPanels.tsx`, `frontend/src/components/PreviewPanels.stale.test.tsx`
- Behavior: display a clear “last successful build” banner with failed stage and primary-error action.
- Verify: `pnpm --dir frontend test -- PreviewPanels.stale.test.tsx`
- Acceptance: stale preview cannot be mistaken for current output.

## V2-115 — Manual versus live-preview focus policy

- Files: `frontend/src/components/WorkbenchApp.tsx`, `frontend/src/components/WorkbenchApp.focusPolicy.test.tsx`
- Behavior: manual failure opens Errors and expands primary diagnostic; live-preview failure updates report/badge without stealing focus.
- Verify: `pnpm --dir frontend test -- WorkbenchApp.focusPolicy.test.tsx`
- Acceptance: repeated typing failures do not switch the active editor panel.

## V2-116 — Sanitized bounded backend logs

- Files: `src/thesis_forge/adapters/runtime.py`, `tests/adapters/test_build_log_sanitization.py`
- Behavior: capture ordered stage logs while bounding count/length and redacting unsafe absolute paths or secrets.
- Verify: `.venv/bin/python -m pytest tests/adapters/test_build_log_sanitization.py`
- Acceptance: known diagnostics remain structured; logs do not expose home directories, tokens or unbounded subprocess output.

## V2-117 — Office refresh failure detail

- Files: `src/thesis_forge/application/office_refresh.py`, `tests/application/test_office_refresh_diagnostics.py`
- Behavior: map Word/LibreOffice refresh failure to stable stage diagnostics with bounded command output.
- Verify: `.venv/bin/python -m pytest tests/application/test_office_refresh_diagnostics.py`
- Acceptance: missing executable, nonzero exit and timeout are distinguishable.

## V2-118 — PDF preview failure detail

- Files: `src/thesis_forge/application/pdf_preview.py`, `tests/application/test_pdf_preview_diagnostics.py`
- Behavior: map preview export, lock, timeout and unsupported-platform failures to typed diagnostics.
- Verify: `.venv/bin/python -m pytest tests/application/test_pdf_preview_diagnostics.py`
- Acceptance: DOCX success can coexist with preview failure and usable output metadata.

## V2-119 — Tauri sidecar terminal error contract

- Files: `src-tauri/src/lib.rs`, `src-tauri/src/build_report_tests.rs`
- Behavior: sidecar spawn, protocol and cancellation failures return a terminal BuildReport-compatible error rather than `Result<Value, String>` semantics.
- Verify: `cargo test --manifest-path src-tauri/Cargo.toml build_report`
- Acceptance: stable category/code/stage reach the frontend; no raw panic or opaque string is the only error.

## V2-120 — BuildReport protocol golden tests

- Files: `tests/contracts/test_build_report_schema.py`, `protocol/examples/build-success.json`, `protocol/examples/build-failed-render.json`
- Behavior: validate all golden examples against the schema and compare backend serialization.
- Verify: `.venv/bin/python -m pytest tests/contracts/test_build_report_schema.py`
- Acceptance: schema and runtime shape cannot drift silently.

## V2-121 — Build error desktop E2E fixture

- Files: `frontend/e2e/fixtures/build-errors.ts`, `frontend/e2e/build-errors.spec.ts`
- Behavior: exercise manual validation failure, source navigation, stale preview and live-preview non-focus-stealing.
- Verify: `pnpm --dir frontend exec playwright test e2e/build-errors.spec.ts`
- Acceptance: the user can discover and act on a build error without reading the status strip.

---

# Milestone 2 — Mandatory project manifest

## V2-201 — ProjectManifestV2 model

- Files: `src/thesis_forge/project/model.py`, `tests/project/test_manifest_model.py`, `src/thesis_forge/project/__init__.py`
- Behavior: define strict manifest schema with project, document, metadata, resources, render, layout, output and review sections.
- Verify: `.venv/bin/python -m pytest tests/project/test_manifest_model.py`
- Acceptance: unknown fields and invalid schema versions fail; paths remain typed project-relative values.

## V2-202 — Secure manifest loader

- Files: `src/thesis_forge/project/loader.py`, `tests/project/test_manifest_loader.py`
- Behavior: load a project directory or manifest path, reject bare Markdown, duplicate YAML keys and missing source.
- Verify: `.venv/bin/python -m pytest tests/project/test_manifest_loader.py`
- Acceptance: loader returns normalized project root and manifest path; errors use stable codes.

## V2-203 — Project path boundary policy

- Files: `src/thesis_forge/project/paths.py`, `tests/project/test_project_paths.py`
- Behavior: resolve source, assets, bibliography and output without traversal or symlink escape.
- Verify: `.venv/bin/python -m pytest tests/project/test_project_paths.py`
- Acceptance: `..`, absolute paths, symlink escape and remote URLs fail explicitly.

## V2-204 — Application project request contract

- Files: `src/thesis_forge/application/contracts.py`, `tests/application/test_project_request_contract.py`
- Behavior: inspect, validate, review and build accept one typed project request rather than a bare source path.
- Verify: `.venv/bin/python -m pytest tests/application/test_project_request_contract.py`
- Acceptance: project identity, intent, output and optional editor snapshot are represented without compatibility unions.

## V2-205 — Application services load projects

- Files: `src/thesis_forge/application/services.py`, `tests/application/test_project_services.py`
- Behavior: all core services resolve the manifest before parsing and share the same loaded project.
- Verify: `.venv/bin/python -m pytest tests/application/test_project_services.py`
- Acceptance: inspect/validate/build no longer directly treat the user path as Markdown.

## V2-206 — Validation resources come from manifest

- Files: `src/thesis_forge/core/validator.py`, `tests/core/test_manifest_resource_validation.py`
- Behavior: bibliography, template and asset resolution use loaded project data, not Markdown Front Matter.
- Verify: `.venv/bin/python -m pytest tests/core/test_manifest_resource_validation.py`
- Acceptance: Markdown cannot override template or bibliography paths.

## V2-207 — CLI project-only entry

- Files: `src/thesis_forge/cli.py`, `tests/cli/test_project_commands.py`
- Behavior: inspect, validate and build accept project directory/manifest and reject a bare `.md` path.
- Verify: `.venv/bin/python -m pytest tests/cli/test_project_commands.py`
- Acceptance: bare Markdown returns nonzero and `TF-PROJECT-ENTRY-001` or the approved stable equivalent.

## V2-208 — CLI machine-readable output

- Files: `src/thesis_forge/cli.py`, `tests/cli/test_json_reports.py`
- Behavior: validate and build can emit JSON diagnostics/BuildReport for automation.
- Verify: `.venv/bin/python -m pytest tests/cli/test_json_reports.py`
- Acceptance: stdout/stderr and exit codes are deterministic; failure JSON remains complete.

## V2-209 — Backend workbench project DTO

- Files: `src/thesis_forge/adapters/dto.py`, `tests/adapters/test_project_dto.py`
- Behavior: desktop requests identify project root/manifest plus current source snapshot.
- Verify: `.venv/bin/python -m pytest tests/adapters/test_project_dto.py`
- Acceptance: no old bare-source DTO variant remains.

## V2-210 — Tauri project selection command

- Files: `src-tauri/src/lib.rs`, `src-tauri/src/project_tests.rs`
- Behavior: open and authorize a project directory/manifest while respecting path boundaries.
- Verify: `cargo test --manifest-path src-tauri/Cargo.toml project`
- Acceptance: standalone Markdown selection is rejected; project source and manifest are returned.

## V2-211 — Frontend project transport

- Files: `frontend/src/transport/WorkbenchTransport.ts`, `frontend/src/transport/WorkbenchTransport.project.test.ts`
- Behavior: transport opens project identity and loads source snapshot using the v2 request.
- Verify: `pnpm --dir frontend test -- WorkbenchTransport.project.test.ts`
- Acceptance: Web/Tauri adapters share one typed project contract.

## V2-212 — Workspace ProjectIdentity

- Files: `frontend/src/state/workspace.ts`, `frontend/src/state/workspace.project.test.ts`
- Behavior: state tracks project root, manifest, active source and project display name instead of one uploaded file.
- Verify: `pnpm --dir frontend test -- workspace.project.test.ts`
- Acceptance: dirty/save/build permissions are based on a loaded project.

## V2-213 — Product bar opens projects

- Files: `frontend/src/components/ProductBar.tsx`, `frontend/src/components/ProductBar.project.test.tsx`
- Behavior: UI text and chooser open a project/manifest rather than a Markdown file.
- Verify: `pnpm --dir frontend test -- ProductBar.project.test.tsx`
- Acceptance: file accept text and accessible labels no longer claim standalone Markdown input.

## V2-214 — Workbench project load flow

- Files: `frontend/src/components/WorkbenchApp.tsx`, `frontend/src/components/WorkbenchApp.project.test.tsx`
- Behavior: open project, load `thesis.md`, save editor snapshot and pass project identity to all operations.
- Verify: `pnpm --dir frontend test -- WorkbenchApp.project.test.tsx`
- Acceptance: switching project clears unrelated diagnostics/report while preserving no stale path authorization.

## V2-215 — Orphan and type-mismatched overrides

- Files: `src/thesis_forge/core/validator.py`, `tests/core/test_object_overrides.py`
- Behavior: layout override target must exist and match the expected semantic object type.
- Verify: `.venv/bin/python -m pytest tests/core/test_object_overrides.py`
- Acceptance: missing figure ID and applying figure width to an equation are errors.

---

# Milestone 3 — Typed IR and one Markdown parser

## V2-301 — NodeId and complete SourceSpan

- Files: `src/thesis_forge/core/model.py`, `tests/core/test_source_identity.py`
- Behavior: every semantic node has stable internal identity and start/end file/line/column span.
- Verify: `.venv/bin/python -m pytest tests/core/test_source_identity.py`
- Acceptance: multi-line nodes and generated origins are representable.

## V2-302 — Replace Inline model

- Files: `src/thesis_forge/core/model.py`, `tests/core/test_inline_model.py`
- Behavior: introduce recursive Text, SoftBreak, HardBreak, Strong, Emphasis, InlineCode, Link, InlineMath, Citation, CrossReference and FootnoteReference.
- Verify: `.venv/bin/python -m pytest tests/core/test_inline_model.py`
- Acceptance: containers own child inline nodes; Strong is not a plain string.

## V2-303 — Replace basic Block model

- Files: `src/thesis_forge/core/model.py`, `tests/core/test_block_model.py`
- Behavior: Heading and Paragraph own inlines only; lists are recursive; BlockQuote and CodeBlock are typed.
- Verify: `.venv/bin/python -m pytest tests/core/test_block_model.py`
- Acceptance: no authoritative `text + inlines` duplication remains.

## V2-304 — Structured table model

- Files: `src/thesis_forge/core/model.py`, `tests/core/test_table_model.py`
- Behavior: Table owns caption inlines, columns, rows and cells with typed content/alignment.
- Verify: `.venv/bin/python -m pytest tests/core/test_table_model.py`
- Acceptance: no authoritative pipe-delimited `markdown` field remains.

## V2-305 — Rich thesis object model

- Files: `src/thesis_forge/core/model.py`, `tests/core/test_thesis_object_model.py`
- Behavior: Figure, Listing and Algorithm own typed captions/content; Equation and Footnote have complete source identity.
- Verify: `.venv/bin/python -m pytest tests/core/test_thesis_object_model.py`
- Acceptance: caption citations/cross-references/strong text are representable.

## V2-306 — DocumentIndex builder

- Files: `src/thesis_forge/core/index.py`, `tests/core/test_document_index.py`
- Behavior: derive ID, citation, reference and footnote indexes by traversing the immutable document.
- Verify: `.venv/bin/python -m pytest tests/core/test_document_index.py`
- Acceptance: duplicate IDs fail rather than overwrite; nested content is indexed.

## V2-307 — Remove manual document caches

- Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/core/compiler.py`, `tests/core/test_no_manual_caches.py`
- Behavior: remove `inline_content`, `cross_references`, `citations`, `footnote_references` and `register_inlines` as authoritative state.
- Verify: `.venv/bin/python -m pytest tests/core/test_no_manual_caches.py`
- Acceptance: compiler uses DocumentIndex/traversal.

## V2-308 — Validator consumes DocumentIndex

- Files: `src/thesis_forge/core/validator.py`, `tests/core/test_validator_document_index.py`
- Behavior: ID/reference/citation/footnote validation uses one derived index.
- Verify: `.venv/bin/python -m pytest tests/core/test_validator_document_index.py`
- Acceptance: nested caption/cell semantics are validated.

## V2-309 — Typed diagnostic codes and locations

- Files: `src/thesis_forge/core/model.py`, `src/thesis_forge/presentation/diagnostics.py`, `tests/core/test_diagnostics.py`
- Behavior: diagnostics use stable code/category/stage/parameters/SourceSpan/related locations.
- Verify: `.venv/bin/python -m pytest tests/core/test_diagnostics.py`
- Acceptance: duplicate definitions report both locations; presentation localizes without string-code chains becoming business logic.

## V2-310 — New markdown-it configuration

- Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_parser_config.py`
- Behavior: enable required CommonMark/GFM rules and remove legacy semantic equivalence configuration.
- Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_parser_config.py`
- Acceptance: emphasis, links, images, backticks, blockquote and fence are enabled; old private parser helpers are not imported.

## V2-311 — Standard inline conversion

- Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_inlines.py`
- Behavior: convert text, breaks, strong, emphasis, code, links and inline math to typed Inline nodes with SourceSpan.
- Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_inlines.py`
- Acceptance: ordinary newline becomes SoftBreak; explicit hard break is distinct.

## V2-312 — Academic inline conversion

- Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_semantic_inlines.py`
- Behavior: parse citation clusters, semantic internal links and footnote references.
- Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_semantic_inlines.py`
- Acceptance: normal links remain links; `#fig:*` targets become CrossReference with fallback label.

## V2-313 — Basic block conversion

- Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_blocks.py`
- Behavior: parse headings, paragraphs, nested lists, blockquotes and code blocks.
- Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_blocks.py`
- Acceptance: source spans and heading IDs are accurate.

## V2-314 — Standard image to Figure

- Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_figures.py`
- Behavior: parse `![caption](path){#fig:id}` as Figure and reject figure without valid ID.
- Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_figures.py`
- Acceptance: caption is typed inline content; width is not read from Markdown.

## V2-315 — GFM table and caption

- Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_tables.py`
- Behavior: parse structured rows/cells/alignment and the following `: caption {#tbl:id}` line.
- Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_tables.py`
- Acceptance: escaped pipes and inline semantics in cells work; malformed column counts fail.

## V2-316 — Display math and equation ID

- Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_equations.py`
- Behavior: parse display math plus following `{#eq:id}` as Equation and support unnumbered display math explicitly.
- Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_equations.py`
- Acceptance: duplicate or detached equation ID is diagnosed.

## V2-317 — Listing and algorithm fences

- Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_markdown_v2_fences.py`
- Behavior: parse fenced listing/algorithm attributes into typed nodes.
- Verify: `.venv/bin/python -m pytest tests/core/test_markdown_v2_fences.py`
- Acceptance: literal code markers remain literal; required IDs/titles follow the spec.

## V2-318 — Explicit legacy syntax rejection

- Files: `src/thesis_forge/core/parser_markdown_it.py`, `tests/core/test_legacy_source_rejection.py`
- Behavior: reject YAML Front Matter, legacy thesis containers and legacy `@fig:*` references before generic parsing.
- Verify: `.venv/bin/python -m pytest tests/core/test_legacy_source_rejection.py`
- Acceptance: diagnostics include replacement examples and do not flatten old syntax to text.

## V2-319 — Single parser backend API

- Files: `src/thesis_forge/core/parser_backend.py`, `tests/core/test_single_parser_backend.py`
- Behavior: remove parser registry and expose one production parser factory/type.
- Verify: `.venv/bin/python -m pytest tests/core/test_single_parser_backend.py`
- Acceptance: no CLI/env/parser-name switching remains.

## V2-320 — Delete hand-written legacy parser

- Files: `src/thesis_forge/core/parser.py`, `src/thesis_forge/core/__init__.py`, `tests/architecture/test_no_legacy_parser.py`
- Behavior: delete old parser implementation and public exports.
- Verify: `.venv/bin/python -m pytest tests/architecture/test_no_legacy_parser.py`
- Acceptance: repository import scan finds no production dependency on `core.parser`.

## V2-321 — Template v2 lint uses one parser

- Files: `src/thesis_forge/templates/v2/lint.py`, `tests/templates/test_v2_lint_parser.py`
- Behavior: template fixture/lint paths use the single v2 parser.
- Verify: `.venv/bin/python -m pytest tests/templates/test_v2_lint_parser.py`
- Acceptance: removing LegacyParserBackend does not break template tooling.

## V2-322 — Typed Inline RenderPlan

- Files: `src/thesis_forge/core/render_plan.py`, `tests/core/test_typed_inline_render_plan.py`
- Behavior: represent text style, links, math, citations, references and footnotes as typed runs.
- Verify: `.venv/bin/python -m pytest tests/core/test_typed_inline_render_plan.py`
- Acceptance: no generic payload dictionary is required for inline content.

## V2-323 — Typed Block RenderPlan

- Files: `src/thesis_forge/core/render_plan.py`, `tests/core/test_typed_block_render_plan.py`
- Behavior: represent all target blocks with typed resolved fields and source node identity.
- Verify: `.venv/bin/python -m pytest tests/core/test_typed_block_render_plan.py`
- Acceptance: table cells and rich captions carry typed runs.

## V2-324 — Compiler converts all inline nodes

- Files: `src/thesis_forge/core/compiler.py`, `tests/core/test_compile_inlines_v2.py`
- Behavior: compile every registered Inline and fail on unknown types.
- Verify: `.venv/bin/python -m pytest tests/core/test_compile_inlines_v2.py`
- Acceptance: caption/cell/list/footnote contexts share the same conversion.

## V2-325 — Compiler converts all block nodes

- Files: `src/thesis_forge/core/compiler.py`, `tests/core/test_compile_blocks_v2.py`
- Behavior: compile every registered Block and fail on unknown types.
- Verify: `.venv/bin/python -m pytest tests/core/test_compile_blocks_v2.py`
- Acceptance: no `_compile_block()` branch returns `None` for unsupported semantic content.

## V2-326 — Remove generic RenderNode from core

- Files: `src/thesis_forge/core/render_plan.py`, `src/thesis_forge/core/compiler.py`, `tests/architecture/test_no_render_node.py`
- Behavior: production RenderPlan accepts typed instructions only.
- Verify: `.venv/bin/python -m pytest tests/architecture/test_no_render_node.py`
- Acceptance: `RenderNode`, `payload` compatibility and `to_render_node` are absent.

## V2-327 — Remove DOCX legacy renderer fallback

- Files: `src/thesis_forge/renderers/docx/renderer.py`, `tests/renderers/docx/test_no_legacy_fallback.py`
- Behavior: unknown instructions fail as an internal diagnostic; debug text is never written to DOCX.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_no_legacy_fallback.py`
- Acceptance: `_render_legacy` and `[kind] {payload}` output are absent.

## V2-328 — Full parser/IR fixture contract

- Files: `tests/integration/test_v2_project_parse.py`, `tests/fixtures/v2-project/thesis.md`
- Behavior: parse the supplied all-capability v2 project into stable typed snapshots/assertions.
- Verify: `.venv/bin/python -m pytest tests/integration/test_v2_project_parse.py`
- Acceptance: every source capability in the registry is represented and source-mapped.

---

# Milestone 4 — Clean Review, Structure and Final Layout

## V2-401 — Review domain model and presenter entry

- Files: `src/thesis_forge/presentation/review.py`, `tests/presentation/test_review_projection.py`
- Behavior: create a typed ReviewDocument from resolved typed instructions without reparsing Markdown.
- Verify: `.venv/bin/python -m pytest tests/presentation/test_review_projection.py`
- Acceptance: Review blocks retain source NodeId/SourceSpan out-of-band.

## V2-402 — Review text, headings, lists and footnotes

- Files: `src/thesis_forge/presentation/review.py`, `tests/presentation/test_review_text_content.py`
- Behavior: project readable rich text, lists, links, citations, references and footnotes.
- Verify: `.venv/bin/python -m pytest tests/presentation/test_review_text_content.py`
- Acceptance: citation keys and cross-reference targets are not visible.

## V2-403 — Review figures, tables and equations

- Files: `src/thesis_forge/presentation/review.py`, `tests/presentation/test_review_objects.py`
- Behavior: project resolved labels, rich captions, structured cells, asset availability and math content.
- Verify: `.venv/bin/python -m pytest tests/presentation/test_review_objects.py`
- Acceptance: original local paths are not visible; safe asset handles are separate data.

## V2-404 — Review listing, algorithm, cover, TOC and bibliography

- Files: `src/thesis_forge/presentation/review.py`, `tests/presentation/test_review_regions.py`
- Behavior: cover all remaining typed instructions and semantic regions.
- Verify: `.venv/bin/python -m pytest tests/presentation/test_review_regions.py`
- Acceptance: no registered instruction lacks a Review projection.

## V2-405 — Partial Review on validation failure

- Files: `src/thesis_forge/application/services.py`, `tests/application/test_partial_review.py`
- Behavior: localized source errors do not suppress all readable content; unresolved content becomes explicit Review problems.
- Verify: `.venv/bin/python -m pytest tests/application/test_partial_review.py`
- Acceptance: missing image or citation still returns unaffected chapters and diagnostics.

## V2-406 — Review marker-leak contract

- Files: `tests/contracts/test_review_marker_leaks.py`, `tests/fixtures/v2-project/thesis.md`
- Behavior: scan normal Review content for Front Matter, `:::`, `{#`, raw citation keys, legacy references and absolute paths while excluding literal code.
- Verify: `.venv/bin/python -m pytest tests/contracts/test_review_marker_leaks.py`
- Acceptance: all technical markers are absent from visible normal content.

## V2-407 — Backend Review DTO

- Files: `src/thesis_forge/adapters/dto.py`, `tests/adapters/test_review_dto.py`
- Behavior: serialize ReviewDocument, source navigation and safe asset references.
- Verify: `.venv/bin/python -m pytest tests/adapters/test_review_dto.py`
- Acceptance: DTO does not expose original absolute paths.

## V2-408 — Frontend Review DTO guard

- Files: `frontend/src/transport/dto.ts`, `frontend/src/transport/dto.review.test.ts`
- Behavior: define and validate every Review block/content variant.
- Verify: `pnpm --dir frontend test -- dto.review.test.ts`
- Acceptance: unknown Review variants fail visibly rather than disappearing.

## V2-409 — Three preview modes in workspace

- Files: `frontend/src/state/workspace.ts`, `frontend/src/state/workspace.previewModes.test.ts`
- Behavior: support `review`, `structure` and `final-layout` as explicit modes.
- Verify: `pnpm --dir frontend test -- workspace.previewModes.test.ts`
- Acceptance: review is the content-focused default after project load unless product decision states otherwise.

## V2-410 — ReviewPanel component

- Files: `frontend/src/components/ReviewPanel.tsx`, `frontend/src/components/ReviewPanel.test.tsx`
- Behavior: render every Review DTO variant with source-selection hooks.
- Verify: `pnpm --dir frontend test -- ReviewPanel.test.tsx`
- Acceptance: IDs, keys and source paths are not rendered as visible text.

## V2-411 — KaTeX review math

- Files: `frontend/package.json`, `frontend/pnpm-lock.yaml`, `frontend/src/components/ReviewPanel.tsx`
- Behavior: render inline and display math in Review with safe error fallback.
- Verify: `pnpm --dir frontend install --frozen-lockfile && pnpm --dir frontend build`
- Acceptance: invalid math shows a readable diagnostic marker, not raw crash output.

## V2-412 — Preview mode tabs

- Files: `frontend/src/components/PreviewPanels.tsx`, `frontend/src/components/PreviewPanels.modes.test.tsx`
- Behavior: integrate Review, Structure, Final Layout and Build Output without conflating their purposes.
- Verify: `pnpm --dir frontend test -- PreviewPanels.modes.test.tsx`
- Acceptance: technical IDs remain in Structure only; Build Output remains reachable in every mode.

## V2-413 — Review and mode styling

- Files: `frontend/src/styles.css`
- Behavior: provide readable academic content layout, table overflow behavior, math, figures, stale banner and responsive modes.
- Verify: `pnpm --dir frontend build && git diff --check`
- Acceptance: no hidden overflow removes error or review content.

## V2-414 — Review uses unsaved editor snapshot

- Files: `frontend/src/components/WorkbenchApp.tsx`, `frontend/src/components/WorkbenchApp.reviewSnapshot.test.tsx`
- Behavior: refresh Review from the current editor snapshot without invoking heavy Office PDF build.
- Verify: `pnpm --dir frontend test -- WorkbenchApp.reviewSnapshot.test.tsx`
- Acceptance: typing updates Review; Final Layout remains based on successful builds.

## V2-415 — Review Markdown serializer

- Files: `src/thesis_forge/presentation/review_markdown.py`, `tests/presentation/test_review_markdown.py`
- Behavior: serialize clean generated Markdown with a generated-file warning and sanitized asset links.
- Verify: `.venv/bin/python -m pytest tests/presentation/test_review_markdown.py`
- Acceptance: visible semantic markers and absolute paths do not leak.

## V2-416 — Review source-map export

- Files: `src/thesis_forge/presentation/review_markdown.py`, `tests/presentation/test_review_source_map.py`
- Behavior: export generated line ranges to NodeId and SourceSpan.
- Verify: `.venv/bin/python -m pytest tests/presentation/test_review_source_map.py`
- Acceptance: every generated content block is traceable; generated-only blocks are labeled.

## V2-417 — CLI review command

- Files: `src/thesis_forge/cli.py`, `tests/cli/test_review_command.py`
- Behavior: `thesisforge review PROJECT --output-dir DIR` writes review Markdown and map.
- Verify: `.venv/bin/python -m pytest tests/cli/test_review_command.py`
- Acceptance: command accepts projects only and returns structured errors.

## V2-418 — Review desktop E2E

- Files: `frontend/e2e/review.spec.ts`, `frontend/e2e/fixtures/review-project.ts`
- Behavior: open v2 project, edit, view marker-free Review, switch Structure/Final Layout and navigate source.
- Verify: `pnpm --dir frontend exec playwright test e2e/review.spec.ts`
- Acceptance: visible Review contains no raw IDs/keys/paths.

---

# Milestone 5 — Compiler, Word objects and structural completeness

## V2-501 — Symbol table and resolved references

- Files: `src/thesis_forge/core/symbols.py`, `tests/core/test_symbol_table.py`
- Behavior: centralize public IDs, target types, display labels, numbering inputs and bookmark names.
- Verify: `.venv/bin/python -m pytest tests/core/test_symbol_table.py`
- Acceptance: duplicate/sanitized bookmark collisions fail before rendering.

## V2-502 — Template-driven numbering

- Files: `src/thesis_forge/core/compiler.py`, `tests/core/test_numbering_v2.py`
- Behavior: resolve chapter, figure, table, equation, listing and algorithm numbering from template policy.
- Verify: `.venv/bin/python -m pytest tests/core/test_numbering_v2.py`
- Acceptance: parser and renderer do not independently compute numbers.

## V2-503 — Semantic region resolver

- Files: `src/thesis_forge/core/regions.py`, `tests/core/test_region_resolver.py`
- Behavior: determine cover/front matter/TOC/main/bibliography/acknowledgement/appendix regions once.
- Verify: `.venv/bin/python -m pytest tests/core/test_region_resolver.py`
- Acceptance: region drives section, styles, headers, footers, page numbering and TOC inclusion.

## V2-504 — Manifest layout overrides in compiler

- Files: `src/thesis_forge/core/compiler.py`, `tests/core/test_manifest_layout_overrides.py`
- Behavior: apply validated object overrides such as figure width by semantic ID.
- Verify: `.venv/bin/python -m pytest tests/core/test_manifest_layout_overrides.py`
- Acceptance: Markdown source contains no layout width; override resolution is deterministic.

## V2-505 — Figure rich caption DOCX

- Files: `src/thesis_forge/renderers/docx/figures.py`, `tests/renderers/docx/test_figure_rich_caption.py`
- Behavior: render caption typed runs, fields, citations, references and styles.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_figure_rich_caption.py`
- Acceptance: no raw citation/reference marker appears in caption XML.

## V2-506 — Structured table rich cells DOCX

- Files: `src/thesis_forge/renderers/docx/tables.py`, `tests/renderers/docx/test_structured_table.py`
- Behavior: render structured headers/cells/alignment and typed cell content.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_structured_table.py`
- Acceptance: no pipe splitting in renderer; citations/math/strong in cells are preserved.

## V2-507 — Listing and algorithm rich DOCX

- Files: `src/thesis_forge/renderers/docx/renderer.py`, `tests/renderers/docx/test_listing_algorithm.py`
- Behavior: render listing/algorithm caption, numbering/bookmark and content using explicit styles.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_listing_algorithm.py`
- Acceptance: unsupported object policy is explicit; no plain debug fallback.

## V2-508 — Word field builder contract

- Files: `src/thesis_forge/renderers/docx/fields.py`, `tests/renderers/docx/test_fields_v2.py`
- Behavior: build typed TOC, SEQ, REF, PAGEREF, PAGE and NUMPAGES field structures with cached results.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_fields_v2.py`
- Acceptance: begin/separate/end structure is valid and Word-specific code stays in DOCX layer.

## V2-509 — Caption and cross-reference fields

- Files: `src/thesis_forge/renderers/docx/captions.py`, `tests/renderers/docx/test_caption_crossrefs.py`
- Behavior: generate sequence/bookmark/reference fields for figures, tables, equations, listings and algorithms.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_caption_crossrefs.py`
- Acceptance: reference result is readable before field refresh and updateable in Word.

## V2-510 — Math preflight

- Files: `src/thesis_forge/core/math.py`, `tests/core/test_math_preflight.py`
- Behavior: validate every supported inline/display formula before build and return source diagnostics for unsupported syntax.
- Verify: `.venv/bin/python -m pytest tests/core/test_math_preflight.py`
- Acceptance: validate success prevents later user-formula render failure.

## V2-511 — OMML coverage for required corpus

- Files: `src/thesis_forge/renderers/docx/math_provider.py`, `tests/renderers/docx/test_math_corpus_v2.py`
- Behavior: render the required formula corpus to editable OMML.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_math_corpus_v2.py`
- Acceptance: supported formulas are not images or plain text.

## V2-512 — Footnote graph integrity

- Files: `src/thesis_forge/core/validator.py`, `tests/core/test_footnote_integrity_v2.py`
- Behavior: reject duplicate/missing/nested invalid footnotes and define multiple-reference behavior.
- Verify: `.venv/bin/python -m pytest tests/core/test_footnote_integrity_v2.py`
- Acceptance: no dictionary overwrite; related definition locations are reported.

## V2-513 — Native DOCX footnote consistency

- Files: `src/thesis_forge/renderers/docx/footnotes.py`, `tests/renderers/docx/test_footnote_package_v2.py`
- Behavior: maintain document/footnotes relationships and reference IDs.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_footnote_package_v2.py`
- Acceptance: every reference resolves and reserved footnotes are valid.

## V2-514 — Bibliography semantic region

- Files: `src/thesis_forge/core/compiler.py`, `tests/core/test_bibliography_region.py`
- Behavior: generate one bibliography title/section/list according to region and template policy.
- Verify: `.venv/bin/python -m pytest tests/core/test_bibliography_region.py`
- Acceptance: no duplicate title and no orphan entry list without section semantics.

## V2-515 — Validate-build dry-run invariant

- Files: `src/thesis_forge/core/validator.py`, `tests/integration/test_validate_build_contract.py`
- Behavior: run shared compile preflight so user-input build errors are visible during validate.
- Verify: `.venv/bin/python -m pytest tests/integration/test_validate_build_contract.py`
- Acceptance: invalid width/table/image/math/bookmark/reference/footnote fails validate, not later render.

## V2-516 — OPC and relationship postflight

- Files: `src/thesis_forge/renderers/docx/package.py`, `tests/renderers/docx/test_package_relationships_v2.py`
- Behavior: validate required parts, content types, XML and relationship targets/IDs/external policy.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_package_relationships_v2.py`
- Acceptance: invalid package never atomically replaces prior successful output.

## V2-517 — Field, bookmark, style and numbering postflight

- Files: `src/thesis_forge/renderers/docx/package.py`, `tests/renderers/docx/test_package_semantics_v2.py`
- Behavior: validate bookmark pairs/names, field structure, style IDs, numIds, footnotes, sections and media.
- Verify: `.venv/bin/python -m pytest tests/renderers/docx/test_package_semantics_v2.py`
- Acceptance: structural Word repair risks are reported as `TF-DOCX-*` errors.

## V2-518 — Full all-capability DOCX E2E

- Files: `tests/integration/test_v2_project_build.py`, `tests/fixtures/v2-project/thesis.md`
- Behavior: validate and build the supplied fixture, inspect normalized OOXML and scan normal body text for unresolved markers.
- Verify: `.venv/bin/python -m pytest tests/integration/test_v2_project_build.py`
- Acceptance: all required objects exist, fields/bookmarks/OMML/footnotes are valid and markers are absent.

---

# Milestone 6 — Capability closure, security, quality gates and release

## V2-601 — Capability registry loader

- Files: `src/thesis_forge/core/capabilities.py`, `tests/contracts/test_capability_registry.py`
- Behavior: load and strictly validate `spec/format-capabilities.yaml`.
- Verify: `.venv/bin/python -m pytest tests/contracts/test_capability_registry.py`
- Acceptance: duplicate IDs, missing stages and missing evidence paths fail.

## V2-602 — Parser and IR handler coverage

- Files: `tests/contracts/test_parser_capability_coverage.py`, `spec/format-capabilities.yaml`
- Behavior: every registered source/IR capability has a parser/model implementation and evidence.
- Verify: `.venv/bin/python -m pytest tests/contracts/test_parser_capability_coverage.py`
- Acceptance: adding an Inline/Block without registry coverage fails.

## V2-603 — Review and DOCX handler coverage

- Files: `tests/contracts/test_output_capability_coverage.py`, `spec/format-capabilities.yaml`
- Behavior: every registered content capability has Review and DOCX handling or an explicit nonvisual policy.
- Verify: `.venv/bin/python -m pytest tests/contracts/test_output_capability_coverage.py`
- Acceptance: unknown output handlers cannot silently disappear.

## V2-604 — Goal verifier behavior contract

- Files: `scripts/verify_thesisforge_v2_goal.py`, `tests/contracts/test_goal_verifier.py`
- Behavior: verify v2 success, legacy rejection, review marker rules, BuildReport schema and DOCX structure.
- Verify: `.venv/bin/python -m pytest tests/contracts/test_goal_verifier.py`
- Acceptance: the verifier fails on each deliberately broken temporary fixture and passes on valid mocked/real outputs.

## V2-605 — Local quality targets

- Files: `Makefile`, `pyproject.toml`
- Behavior: add format check, type check, coverage/architecture/goal helper targets without putting the final failing stop-check into routine incremental verify.
- Verify: `make test && make lint && git diff --check`
- Acceptance: `make verify` remains a green incremental baseline; `make goal-check` may call stop-check only when requested.

## V2-606 — Frontend real lint and format tools

- Files: `frontend/package.json`, `frontend/pnpm-lock.yaml`, `frontend/eslint.config.js`
- Behavior: use TypeScript/React Hooks/accessibility/import-boundary lint rather than text regex only.
- Verify: `pnpm --dir frontend install --frozen-lockfile && pnpm --dir frontend lint`
- Acceptance: component-to-transport boundary rule is AST-based.

## V2-607 — Frontend test/build quality scripts

- Files: `frontend/package.json`, `frontend/tsconfig.app.json`, `frontend/src/vite-env.d.ts`
- Behavior: stabilize typecheck/test/build commands for new components and generated types.
- Verify: `pnpm --dir frontend typecheck && pnpm --dir frontend test && pnpm --dir frontend build`
- Acceptance: strict mode remains enabled; no broad `any` escape.

## V2-608 — Rust clippy and typed errors

- Files: `src-tauri/Cargo.toml`, `src-tauri/src/lib.rs`, `Makefile`
- Behavior: replace major `Result<_, String>` build paths with typed errors and add clippy `-D warnings` to verification.
- Verify: `cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets --all-features -- -D warnings`
- Acceptance: protocol conversion remains explicit and tested.

## V2-609 — Python CI required checks

- Files: `.github/workflows/ci-python.yml`
- Behavior: run Python 3.11/3.12 tests, lint, format, type, package and focused DOCX contracts on PR/main.
- Verify: `python - <<'PY'
import yaml
from pathlib import Path
yaml.safe_load(Path('.github/workflows/ci-python.yml').read_text())
PY`
- Acceptance: workflow is not manual-only and covers source, tests, templates and root config paths.

## V2-610 — Frontend and Rust CI required checks

- Files: `.github/workflows/ci-desktop.yml`
- Behavior: run frontend tests/type/lint/build/E2E smoke and Rust fmt/clippy/test/check.
- Verify: `python - <<'PY'
import yaml
from pathlib import Path
yaml.safe_load(Path('.github/workflows/ci-desktop.yml').read_text())
PY`
- Acceptance: supported OS matrix is explicit; artifacts/logs aid diagnosis.

## V2-611 — Goal-contract workflow

- Files: `.github/workflows/goal-contract.yml`
- Behavior: provide manually triggered/final-branch verification of `./stop-check.sh` without blocking incremental PRs before Open is empty.
- Verify: `python - <<'PY'
import yaml
from pathlib import Path
yaml.safe_load(Path('.github/workflows/goal-contract.yml').read_text())
PY`
- Acceptance: workflow cannot falsely pass by skipping full verification.

## V2-612 — Project security integration suite

- Files: `tests/security/test_project_security.py`, `tests/security/fixtures.py`
- Behavior: cover traversal, symlink escape, absolute/remote paths, duplicate YAML keys, oversized input and log redaction.
- Verify: `.venv/bin/python -m pytest tests/security/test_project_security.py`
- Acceptance: failures use stable diagnostics and do not access outside project root.

## V2-613 — DOCX security integration suite

- Files: `tests/security/test_docx_security.py`, `tests/security/docx_fixtures.py`
- Behavior: cover unexpected external relationships, malformed parts, package abuse and output replacement safety.
- Verify: `.venv/bin/python -m pytest tests/security/test_docx_security.py`
- Acceptance: unsafe output is rejected before replacing prior success.

## V2-614 — Performance regression harness

- Files: `tests/performance/test_build_profiles.py`, `tests/performance/generate_projects.py`
- Behavior: generate small/normal/large/image/citation/math/multi-file profiles and record bounded performance assertions.
- Verify: `.venv/bin/python -m pytest tests/performance/test_build_profiles.py -m 'not slow'`
- Acceptance: normal profile has a documented non-flaky budget; slow profiles remain separately runnable.

## V2-615 — README v2 workflow

- Files: `README.md`
- Behavior: describe only the manifest v2 project, three views, Build Output and project-only CLI.
- Verify: `! rg -n '::: (figure|table|equation|listing|algorithm|bibliography)|build .*\.md|inspect .*\.md' README.md && git diff --check`
- Acceptance: old source format is not presented as supported; breaking change is explicit.

## V2-616 — Agent instruction consolidation

- Files: `AGENTS.md`, `CLAUDE.md`
- Behavior: point both agents to the same normative spec/Loop/verification commands and remove contradictory old checks.
- Verify: `cmp -s AGENTS.md CLAUDE.md || diff -u AGENTS.md CLAUDE.md; git diff --check`
- Acceptance: either identical content or one canonical include/reference policy; no old parser compatibility instruction.

## V2-617 — Release and breaking-change notes

- Files: `CHANGELOG.md`, `docs/V2_RELEASE_NOTES.md`
- Behavior: document removed input format, no migration support, new project layout, BuildReport and review workflow.
- Verify: `test -s CHANGELOG.md && test -s docs/V2_RELEASE_NOTES.md && git diff --check`
- Acceptance: users are not led to expect automatic conversion of old projects.

## V2-618 — Final goal and repository verification

- Files: `LOOP.md`
- Behavior: after all implementation items are Done, run the real stop condition, record evidence and set Status to done.
- Verify: `./stop-check.sh`
- Acceptance: Open and Blocked are empty; goal verifier and full `make verify` pass; final Cycle log includes commit/test evidence.

---

# Human release checklist

After V2-618, a human performs:

1. inspect the final local commits and independent code review;
2. run Microsoft Word desktop acceptance on the full fixture;
3. run WPS acceptance and record differences;
4. confirm no Word repair prompt;
5. confirm Build Output behavior from a packaged desktop build;
6. confirm offline operation;
7. inspect licenses and SBOM;
8. push the branch;
9. open the PR;
10. merge and release only after required checks and human approval.
