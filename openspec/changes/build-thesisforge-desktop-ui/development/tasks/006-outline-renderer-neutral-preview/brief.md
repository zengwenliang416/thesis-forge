# Task Brief: 006-outline-renderer-neutral-preview

## Goal

Users can inspect a stable semantic outline and paper-like structural preview
from the same saved Markdown snapshot, select content across outline, preview,
and editor, and always see that the preview does not represent final Word
pagination.

## Parent Artifacts

- `openspec/changes/build-thesisforge-desktop-ui/requirements.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.md`
- `openspec/changes/build-thesisforge-desktop-ui/design.md`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/handoff.md`

## Vertical Slice

Add a renderer-neutral application preview service that reuses parse,
validation, and compile boundaries without invoking the DOCX renderer. Map its
validated document, issues, and optional typed `RenderPlan` into one versioned,
JSON-safe presentation DTO consumed by the shared React workbench.

## In Scope

- A `PreviewResult` application contract containing the validated
  `ThesisDocument`, `ValidationContext`, diagnostics, and an optional typed
  `RenderPlan`.
- A `preview_service` that parses and validates once, compiles only when no
  fatal issue exists and a template is available, and never renders or writes
  an output file.
- Framework-neutral Python presentation models and mapper for outline items,
  preview blocks, inline references/citations/footnotes, diagnostic markers,
  source lines, numbering labels, and explicit unsupported states.
- A versioned `preview` adapter operation shared by Web and Tauri transports.
- Strict TypeScript DTO validation before preview data enters workspace state.
- Shared React outline and paper-preview components with keyboard and pointer
  activation.
- One active content selection shared by outline, preview, and editor source
  focus.
- Stale preview suppression through the existing operation generation token.
- Visible empty, loading, validation-blocked, ready, and unsupported preview
  states.
- Persistent copy stating `结构预览不代表 Word 最终分页。`

## Out Of Scope

- No DOCX generation, conversion, OOXML parsing, Office embedding, or exact
  page-count/pagination claims.
- No changes to parser syntax, semantic ID rules, validation rules, template
  schema/resolution precedence, compiler numbering, bibliography semantics,
  renderer behavior, or DOCX output.
- No image decoding or arbitrary file reads in React. Figure previews use
  serialized source metadata and explicit availability states only.
- No build progress, cancellation, output replacement, packaging, release, AI,
  accounts, database, telemetry, autosave, or multi-document state.

## Files Allowed

- `frontend/src/components/**`
- `frontend/src/state/**`
- `frontend/src/transport/**`
- `frontend/src/styles.css`
- `frontend/e2e/**`
- `src/thesis_forge/application/**`
- `src/thesis_forge/adapters/**`
- `src/thesis_forge/presentation/**`
- `tests/fixtures/preview-workbench-v1.json`
- `tests/test_preview_presentation.py`
- `tests/test_application_services.py`
- `tests/test_adapters.py`
- `tests/test_frontend_contract.py`
- `tests/test_architecture.py`

## Interfaces / Seams

- `preview_service(source, template_path=...)` is the only new application
  entrypoint. Adapters do not call `compile_document` directly.
- `PreviewResult.plan` is `None` when fatal validation issues exist or the
  template is unavailable; the service does not weaken validation.
- The Python presentation mapper accepts domain/application results and emits
  dictionaries containing JSON primitives only.
- Shared React receives only the serialized preview DTO through
  `WorkbenchTransport`; components do not call HTTP, Tauri, Python, parser,
  validator, compiler, renderer, DOCX, or OOXML modules.
- Outline and preview entries share one `selectionId`, optional stable
  `semanticId`, and source line. Anonymous content uses a deterministic
  snapshot-local fallback ID derived by the mapper.
- The existing `templateId` adapter resolution remains unchanged and applies
  equally to validate, preview, and build operations.

## Preview Coverage

- Cover, section break, TOC, heading, paragraph, ordered/unordered list.
- Figure, table, equation, listing, algorithm, and footnote definition.
- Inline cross-reference, citation, and footnote-reference runs.
- Bibliography entries and numbering labels already resolved by the compiler.
- Legacy or unknown `RenderNode` values as explicit `unsupported` blocks.

## State / Error / Empty / Loading Behavior

- Empty: outline and preview explain that a saved Markdown source is required.
- Loading: previous content remains stable while conflicting actions are
  disabled; stale responses cannot replace it.
- Validation blocked: outline and diagnostics remain available, preview states
  why a typed render plan was not produced.
- Ready: outline and preview render in compiler order and share activation.
- Unsupported: the item remains visible with its kind and an explicit
  unsupported message instead of being dropped or rendered as ordinary text.
- Dirty: the last saved outline/preview remains visible but Validate/Build stay
  disabled until explicit save refreshes the snapshot.

## TDD Requirement

- TDD route is `strict`.
- Add and execute failing application-service, mapper/golden, adapter/DTO,
  reducer, component, stale-result, selection-sync, and architecture tests
  before production implementation.
- Add new focused test files rather than extending the existing 809-line
  `WorkbenchApp.test.tsx`.
- Record exact RED and GREEN commands and outcomes in the task ledger and
  report.

## Pre-Edit Complexity Check

- `src/thesis_forge/application/services.py`: add the application-owned service
  and reuse existing parse/validate/compile helpers.
- `src/thesis_forge/adapters/runtime.py`: add one thin operation branch and one
  mapper call; do not compile or duplicate preview mapping here.
- `frontend/src/components/WorkbenchApp.tsx`: keep orchestration changes small;
  extract preview DTO/state/component behavior into dedicated owners.
- `frontend/src/components/WorkbenchApp.test.tsx`: do not add new scenarios;
  create separate Slice 006 tests.
- Decision: add owner files and extract preview panels where needed.

## Verification Commands

- `pnpm frontend:test`
- `pnpm frontend:typecheck`
- `pnpm frontend:lint`
- `pnpm frontend:build`
- `pnpm frontend:e2e`
- `.venv/bin/python -m pytest tests/test_application_services.py
  tests/test_preview_presentation.py tests/test_adapters.py
  tests/test_frontend_contract.py
  tests/test_architecture.py -q`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check`
- `cargo test --manifest-path src-tauri/Cargo.toml`
- `cargo check --manifest-path src-tauri/Cargo.toml`
- `OPENSPEC_TELEMETRY=0 openspec validate
  build-thesisforge-desktop-ui --strict --json`
- `SPECNAV_CHANGE=build-thesisforge-desktop-ui OPENSPEC_TELEMETRY=0 node
  /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js
  --mode entry --json`
- `git diff --check`

## Stop Conditions

- Preview requires invoking `DocxRenderer`, creating DOCX/OOXML objects, or
  writing an output package.
- Adapter or React code needs to call parser, validator, compiler, renderer, or
  filesystem owners directly.
- The slice requires changing parser IDs, compiler numbering, template schema,
  validator semantics, bibliography semantics, or renderer behavior.
- Serialized output leaks `Path`, Python class names, exceptions,
  python-docx/lxml objects, raw OOXML, or renderer-private payloads.
- Unsupported instructions are silently dropped or presented as supported.
- Outline and preview cannot share a deterministic selection/source-location
  contract.

## Unsafe Assumptions

- Every heading or render instruction has a semantic ID or source line.
- A valid inspection result guarantees validation or compilation success.
- A typed render plan implies exact Word pagination.
- Figure source metadata can be treated as a browser-readable URL.
- Unknown `RenderNode` values can be ignored safely.
- UI stale suppression can be replaced by request completion order.
