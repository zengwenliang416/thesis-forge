# Task Brief: 005-template-selection-structured-diagnostics

## Goal

Users can select a school template, receive stable Simplified Chinese
diagnostics from the saved Markdown snapshot, filter and activate every issue,
and build only when validation contains no error-severity issue.

## Parent Artifacts

- `openspec/changes/build-thesisforge-desktop-ui/requirements.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.md`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/handoff.md`

## Vertical Slice

Connect the existing template resolver and validation service to the shared
React workbench through the existing versioned transport, map serialized
`ValidationIssue` values into deterministic `zh-CN` presentation models, and
complete the diagnostic-to-editor interaction and fatal build guard.

## In Scope

- Template selection for the document-declared template and the shipped V1
  template choices, with selection stored in shared workspace state.
- Revalidation of the current saved source after template selection without
  modifying Markdown.
- Versioned validate/build requests carrying the selected stable template ID
  while Web and Tauri continue to use the same transport DTO.
- Shared framework-neutral Python diagnostic localization used by the CLI and
  the headless Python UI reference.
- Shared TypeScript diagnostic presentation mapping for Web and Tauri,
  validated against the same contract fixture as Python.
- Stable diagnostic ordering, severity summary counts, all/error/warning/info
  filtering, active diagnostic state, and keyboard/pointer activation.
- Editor focus and selection of the diagnostic source line when present;
  no-line diagnostics remain activatable without changing editor selection.
- Build disabled when any current diagnostic has severity `error`; warnings and
  info remain buildable after validation.
- Real resolver/validation-service tests for valid, missing, malformed, and
  incompatible template inputs.

## Out Of Scope

- No changes to template YAML schema, resolver selection precedence, validator
  rules, severity semantics, compiler, renderer, numbering, bibliography, or
  DOCX behavior.
- No arbitrary browser-native template path picker or server filesystem
  disclosure. Final packaged template discovery remains Slice 008.
- No outline or renderer-neutral preview implementation; that remains Slice
  006.
- No streamed build progress, cancellation, output replacement changes, or
  final build recovery; those remain Slice 007.
- No runtime locale switching, dark mode, AI, accounts, database, telemetry,
  autosave, recent files, or multi-document tabs.

## Files Allowed

- `frontend/**`
- `src/thesis_forge/adapters/**`
- `src/thesis_forge/presentation/**`
- `src/thesis_forge/ui/**`
- `src/thesis_forge/cli.py`
- `tests/fixtures/diagnostics-zh-cn-v1.json`
- `tests/test_adapters.py`
- `tests/test_cli.py`
- `tests/test_frontend_contract.py`
- `tests/test_ui_controller.py`
- `tests/test_ui_models.py`
- `tests/test_architecture.py`

## Interfaces / Seams

- `validation_service(source, template_path=...)` remains the only validation
  entry used by adapters and continues to resolve templates through the
  existing `ValidationContext` and resolver.
- `CommandEnvelope.payload.templateId` is JSON-safe and optional; shared React
  code does not carry repository-relative template paths or call HTTP, Tauri,
  Python, resolver, or validator modules.
- `CommandEnvelope.payload.templatePath` remains an adapter-only compatibility
  seam for existing callers. The dispatcher rejects requests that select both
  `templateId` and `templatePath`.
- `SerializedDiagnostic` remains the transport contract for severity, code,
  message, line, target, and JSON-safe details.
- Python and TypeScript presentation mappers consume the same fixture contract
  and fall back to the original message for unknown codes.
- Diagnostic activation is a frontend intent that changes selection/focus only;
  it never changes source text.

## Components To Create

- Framework-neutral Python diagnostic presentation mapper.
- TypeScript diagnostic presentation mapper and selectors.
- Shared diagnostic localization parity fixture.
- Diagnostic filter controls, summary counts, and issue rows.
- Pure editor line-range navigation helper.

## Components To Reuse

- `resolve_template`, `ValidationContext.from_document`,
  `validation_service`, `ValidationIssue`, and deterministic validator ordering.
- Existing `WorkbenchTransport`, Web HTTP adapter, Tauri command/sidecar
  adapter, workspace reducer, `TemplateSelector`, `DiagnosticsPanel`,
  `MarkdownEditor`, and operation generation tokens.

## Components To Extract

- Extract the CLI-private diagnostic localization switch into one Python
  presentation utility before the UI reference needs the same copy.
- Keep TypeScript localization and diagnostic selectors outside React
  components so Web and Tauri cannot diverge.
- Keep editor line offset calculation outside `WorkbenchApp` and
  `MarkdownEditor`.

## API / Data Flow Contracts

- Selecting a template stores its stable ID and immediately dispatches
  `validate` for the current saved source with `templateId`.
- The Python adapter resolves `templateId` through `resolve_template` and
  `default_template_search_roots(source_path)`, then passes the controlled
  absolute path into the unchanged validation/build service seam.
- Source refresh dispatches inspect and validate from the same saved source
  reference and stores only the current generation's diagnostics.
- Validate/build requests use the selected template ID; a `null` selection
  delegates to the document front matter.
- Validation success maps every serialized diagnostic and preserves all
  severity/code/message/line/target fields.
- Error diagnostics block frontend Build before a build request is created;
  warning/info-only diagnostics do not.
- The backend build service remains the final fatal-validation authority and
  still prevents compile/render independently of the frontend guard.

## State / Error / Empty / Loading Behavior

- Loading: template and conflicting validation/build actions are disabled while
  the current operation remains visible.
- Empty: template selection and diagnostic filters are disabled until a source
  is open; the diagnostic empty state explains how to populate results.
- Error: transport or validation-stage failures retain source/template
  selection and expose the existing recovery action.
- Disabled: fatal diagnostics visibly explain why Build is unavailable; warning
  diagnostics do not disable it.
- Permission: existing source/template/diagnostic state is preserved and no
  source mutation occurs.

## TDD Requirement

- TDD route is `strict`.
- Write and execute failing mapper parity, reducer/selectors, component,
  transport, editor navigation, and real template validation tests before each
  implementation batch.
- Record exact RED and GREEN commands and outcomes in the task ledger and
  report.

## Verification Commands

- `pnpm frontend:test`
- `pnpm frontend:typecheck`
- `pnpm frontend:lint`
- `pnpm frontend:build`
- `pnpm frontend:e2e`
- `.venv/bin/python -m pytest tests/test_adapters.py tests/test_cli.py
  tests/test_frontend_contract.py tests/test_ui_controller.py
  tests/test_ui_models.py tests/test_architecture.py -q`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m pip check`
- `OPENSPEC_TELEMETRY=0 openspec validate
  build-thesisforge-desktop-ui --strict --json`
- `SPECNAV_CHANGE=build-thesisforge-desktop-ui OPENSPEC_TELEMETRY=0 node
  /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js
  --mode entry --json`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.
- Template selection requires changing resolver precedence or template schema.
- Frontend code needs direct filesystem, HTTP, Tauri, Python, parser, validator,
  compiler, renderer, DOCX, or OOXML access.
- Web template selection requires exposing arbitrary service-local paths.
- Diagnostic presentation drops or rewrites stable code, severity, line, or
  target values.
- Fatal build guarding relies only on the UI and weakens the application-layer
  validation gate.

## Unsafe Assumptions

- A selected template is valid because it appears in the selector.
- A template file exists because the frontend knows a relative path.
- Every diagnostic has a source line or known localization code.
- Warning diagnostics should block build.
- Frontend filtering may discard issues or change source text.
- A shallow transport success object proves diagnostic DTO validity.
