# Task Brief: 004-optional-pyside6-workbench-shell

## Goal

Users can open the same light-theme `zh-CN` ThesisForge workbench in a browser
or a Tauri 2 shell on macOS and Windows, while all frontend behavior crosses a
versioned `WorkbenchTransport` boundary and the Python CLI remains independent.

## Parent Artifacts

- `openspec/changes/build-thesisforge-desktop-ui/requirements.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.md`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/handoff.md`

## Vertical Slice

Create the shared React workbench shell and its TypeScript workspace state,
exercise the same state-transition fixtures as the pure-Python reference, and
connect runtime-specific Web HTTP and Tauri sidecar transports to the existing
Python application services without duplicating compiler behavior.

## In Scope

- React 19, TypeScript, Vite, pnpm, Vitest, Testing Library, and Playwright
  workspace under `frontend/`.
- Light-theme product bar and responsive academic three-pane workbench with
  outline, Markdown editor, paper preview, diagnostics, template, build,
  progress, output, empty, loading, error, disabled, and permission shells.
- Keyboard focus order, `Ctrl/Cmd+K`, `Ctrl/Cmd+S`, `Ctrl/Cmd+B`, responsive
  mobile panel tabs, resizable desktop panels, and minimum-window behavior.
- Frontend-owned immutable workspace state, operation tokens, capability-aware
  actions, parity fixtures, versioned JSON DTOs, and `WorkbenchTransport`.
- `WebWorkbenchTransport` using the configured `/api/v1` HTTP boundary.
- `TauriWorkbenchTransport` using one Tauri command bridge.
- Thin Python DTO, Web HTTP, and JSON-lines sidecar adapters that delegate to
  `inspect_service`, `validation_service`, and `build_service`.
- Tauri 2 shell metadata and Rust command bridge for macOS/Windows with a
  managed Python sidecar protocol.
- Static Python/package isolation tests proving the existing CLI does not need
  Node.js, Rust, Tauri, or an HTTP server.

## Out Of Scope

- No PySide6/PyQt product dependency or second desktop component tree.
- No Parser, Validator, Compiler, numbering, bibliography, RenderPlan, DOCX, or
  template-model semantic changes.
- No build cancellation or streamed progress implementation beyond DTO seams;
  those remain Slice 007.
- No final template diagnostics behavior, renderer-neutral preview mapper, or
  diagnostic localization; those remain Slices 005 and 006.
- No autosave, recent files, multi-document tabs, accounts, database, AI,
  telemetry, public multi-tenant hosting, exact Word pagination, or dark mode.
- No claim that macOS/Windows installers are release-ready; release packaging
  and full cross-host E2E remain Slice 008.

## Files Allowed

- `package.json`
- `pnpm-lock.yaml`
- `frontend/**`
- `src-tauri/**`
- `src/thesis_forge/adapters/**`
- `src/thesis_forge/ui/**`
- `tests/test_adapters.py`
- `tests/test_architecture.py`
- `tests/test_frontend_contract.py`
- `tests/fixtures/workspace-state-v1.json`
- `README.md`

## Interfaces / Seams

- `WorkbenchTransport` is the only asynchronous runtime boundary imported by
  React state/components.
- `TransportDTOv1` uses JSON-safe primitives and never exposes Python classes,
  `pathlib.Path`, exceptions, `python-docx`, `lxml`, or renderer-private data.
- `WebWorkbenchTransport` owns HTTP request/response mapping.
- `TauriWorkbenchTransport` owns `invoke` mapping and never appears in shared
  components or workspace state.
- Python `WorkbenchAdapter` owns DTO validation/serialization and delegates
  domain work to injected application services.
- The Tauri shell owns native process lifecycle; the Python sidecar owns only
  line-delimited request dispatch.

## Components To Create

- `WorkbenchShell`, `ProductBar`, `OutlinePanel`, `MarkdownEditor`,
  `PaperPreview`, `DiagnosticsPanel`, `TemplateSelector`, `BuildProgress`, and
  `OutputFeedback`.
- TypeScript workspace reducer/store, selectors, operation tokens,
  capabilities, and parity fixture runner.
- `WorkbenchTransport`, `WebWorkbenchTransport`,
  `TauriWorkbenchTransport`, and `TransportDTOv1`.
- Python DTO serializer, HTTP WSGI adapter, sidecar JSON-lines dispatcher, and
  runtime-neutral application-service adapter.
- Tauri 2 Rust command bridge and desktop configuration.

## Components To Reuse

- Approved archived `academic-three-pane` visual contract.
- Pure-Python `WorkspaceController` state semantics.
- `LocalWorkspaceFileSystem`, `inspect_service`, `validation_service`,
  `build_service`, `BuildStage`, `ValidationIssue`, and atomic output behavior.

## Components To Extract

- Shared TypeScript DTOs, operation tokens, capability selection, workspace
  reducer/selectors, and transport error normalization.
- Shared Python DTO mapping and command dispatch used by both HTTP and sidecar
  adapters.
- Shared parity fixtures consumed by Python and TypeScript tests.

## API / Data Flow Contracts

- Protocol version: `thesisforge.workbench.v1`.
- Web routes are under `/api/v1` and operate on opaque Web workspace handles;
  service-local paths are never serialized to browser responses.
- Tauri requests may use user-selected native paths but cross the same command
  envelope and response/error schema.
- Inspect, validate, and build delegate to the existing application services.
- Results with stale operation tokens are ignored by TypeScript workspace
  state.

## State / Error / Empty / Loading Behavior

- Loading: components remain mounted, conflicting actions are disabled, and the
  current operation label is announced.
- Empty: Open is available; Save, Validate, and Build are disabled.
- Error: stable transport/domain error copy and a recovery action are visible.
- Disabled: editing shell remains visible while unavailable runtime capability
  actions are disabled.
- Permission: prior source/output state remains visible and the UI requests a
  writable destination or recovery action.

## TDD Requirement

- TDD route is `strict`.
- Write and execute failing frontend command, workspace parity, component,
  transport, Python adapter, Tauri contract, and CLI isolation tests before
  implementing each behavior batch.
- Record exact RED and GREEN command output in the task ledger and report.

## Verification Commands

- `pnpm --dir frontend install --frozen-lockfile`
- `pnpm frontend:test`
- `pnpm frontend:typecheck`
- `pnpm frontend:lint`
- `pnpm frontend:build`
- `pnpm frontend:e2e`
- `cargo test --manifest-path src-tauri/Cargo.toml`
- `cargo check --manifest-path src-tauri/Cargo.toml`
- `.venv/bin/python -m pytest tests/test_adapters.py
  tests/test_frontend_contract.py tests/test_architecture.py -q`
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
- Any implementation requires Python core/application imports of React, Tauri,
  HTTP framework, Node.js, or Rust.
- Browser DTOs require arbitrary native paths or expose service-local paths.
- A second frontend tree or PySide6/PyQt dependency appears.
- Shared components call `fetch`, Tauri `invoke`, Python, or compiler modules
  directly.
- Tauri packaging requires credentials, signing, paid services, or destructive
  host changes.

## Unsafe Assumptions

- A browser can read or save arbitrary native paths.
- Web and desktop source capabilities are identical.
- A frontend build proves runtime behavior.
- Tauri configuration alone proves sidecar request/response parity.
- Python and TypeScript state semantics stay aligned without shared fixtures.
- The CLI can safely depend on optional frontend or HTTP dependencies.
