# Task Report: 005-template-selection-structured-diagnostics

## Status

DONE

## Files Changed

- `frontend/e2e/workbench.spec.ts`
- `frontend/src/components/{StatusStrip,WorkbenchApp,WorkbenchPanels,WorkbenchShell}.tsx`
- `frontend/src/state/{diagnostics,editorNavigation,workspace}.ts`
- `frontend/src/transport/dto.ts`
- `frontend/src/styles.css`
- `src/thesis_forge/presentation/**`
- `src/thesis_forge/ui/models.py`
- `src/thesis_forge/cli.py`
- `tests/fixtures/diagnostics-zh-cn-v1.json`
- `tests/test_adapters.py`
- `tests/test_ui_models.py`
- focused frontend component/state/transport tests

## What Changed

- Added saved-workspace template selection for document metadata, the base
  bachelor template, and the example university template. Shared React state
  and requests store stable template IDs; the Python adapter resolves them to
  controlled absolute paths before revalidating through the existing
  `validation_service`, `ValidationContext`, and resolver.
- Added one framework-neutral Python diagnostic localization utility and
  removed the prior CLI-private copy. The headless Python
  `DiagnosticViewModel` and CLI now use the same `zh-CN` presentation.
- Added one shared TypeScript diagnostic presentation module for Web and Tauri.
  Python and TypeScript mappings are checked against the same versioned fixture
  and preserve severity, code, line, target, and details.
- Added deterministic diagnostic ordering, all/error/warning/info counts and
  filters, active issue state, keyboard/pointer activation, and editor line
  focus without source mutation. No-line issues remain activatable without
  moving editor focus.
- Added complete serialized diagnostic validation. Validate consumers reject a
  success response that omits diagnostics or contains malformed severity,
  line, target, or details values.
- Added fatal-only frontend build guarding. Error diagnostics disable Build;
  warning/info-only diagnostics remain buildable. A visible status message
  states the fatal count and why Build is disabled. The existing application
  build validation gate remains unchanged and authoritative.
- Kept all four diagnostic filters visible but disabled before a source opens,
  and added explicit pointer activation coverage alongside keyboard activation.
- Added stale diagnostic suppression through the existing operation generation
  token and fixed new-source open so it cannot inherit a previous document's
  explicit template.
- Added real resolver/service tests for valid, missing, malformed, and
  semantically incompatible selected templates.

## TDD Evidence

- Initial Python RED: `4 failed, 1 passed` because known diagnostics still used
  raw English messages.
- Initial frontend RED: the diagnostic mapper module was absent and
  template-state, fatal-guard, malformed-DTO, selector, filter, and activation
  cases returned `4 failed, 19 passed` plus one failed suite.
- First GREEN: shared localization, state, DTO validation, template binding,
  filtering, activation, and line focus returned `25` frontend and `20`
  Python tests passing.
- Template matrix refinement found one over-strong test assumption: the stable
  `missing-template-style` payload legitimately uses `target` with empty
  details. The test was corrected without changing domain behavior.
- Review RED: `2 failed, 27 passed` exposed previous-template inheritance on
  new source open and validate consumers accepting missing diagnostics.
- Review GREEN: new-source reset and required validate diagnostics raised the
  focused frontend result to `29 passed`.
- E2E RED/GREEN: strict validate DTO handling exposed the old Playwright empty
  result mock; the mock was corrected and a real template/fatal/keyboard path
  was added, producing `9 passed` executed scenarios.
- Review-fix RED: stable `templateId`, fatal-disable copy, empty-state disabled
  filters, pointer activation, and selector-conflict tests failed against the
  original implementation.
- Review-fix GREEN: frontend unit tests increased to `31 passed`; focused
  Python adapter/UI tests increased to `25 passed`.

## Verification Commands

- `pnpm frontend:test` -> `31 passed`.
- `pnpm frontend:typecheck` -> passed.
- `pnpm frontend:lint` -> passed.
- `pnpm frontend:build` -> Vite production bundle built.
- `pnpm frontend:e2e` -> `9 passed`, `9` intentional viewport/runtime skips.
- focused Python command from the task brief -> `91 passed`.
- `.venv/bin/python -m pytest -q` -> `206 passed in 8.34s`.
- `.venv/bin/ruff check .` -> all checks passed.
- `.venv/bin/python -m pip check` -> no broken requirements.
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check` -> passed.
- `cargo test --manifest-path src-tauri/Cargo.toml` -> `4 passed`.
- `cargo check --manifest-path src-tauri/Cargo.toml` -> passed.
- browser sensory screenshot -> no horizontal overflow at `1440x980`;
  template, diagnostic, editor, preview, and disabled Build were visible.
- CodeGraph sync/context/claims -> 117 files, zero pending changes,
  `ev-ms9xt4u5`, all five development claims verified.
- JSON parsing and `git diff --check` -> passed before lifecycle closure.

## Concerns

- The selector's shipped template IDs are verified through the resolver and
  adapter tests. Bundling those YAML resources and proving their installed
  locations inside macOS/Windows packages remains Slice 008.
- Windows package execution cannot be verified on this macOS host and is not
  claimed by this slice.

## Scope Deviations

- None. Template schema, resolver precedence, validator rules, application
  fatal validation, compiler, renderer, bibliography, DOCX, database, account,
  AI, telemetry, and prototype artifacts were not changed.

## Follow-up Needed

- Slice 006 will map semantic outline and renderer-neutral preview data.
- Slice 008 will package template resources and run installed macOS/Windows
  path acceptance.

## Adjudication

Tasks `5.1` through `5.7` are complete with independent spec and quality
approval, direct evidence for `A4`, and supporting boundary evidence for `A7`,
`A10`, and `A12`. Whole-change verification and release remain incomplete
because Slices 006 through 008 are still open.
