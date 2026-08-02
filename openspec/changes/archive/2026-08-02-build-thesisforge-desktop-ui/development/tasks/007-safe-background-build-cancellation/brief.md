# Task Brief: 007-safe-background-build-cancellation

## Goal

Users can start a DOCX build without freezing the shared workbench, see ordered
`parse`, `validate`, `compile`, `render`, and `finalize` progress, cancel or
retry safely, and keep the last valid output when a build is canceled, stale,
or fails.

## Parent Artifacts

- `openspec/changes/build-thesisforge-desktop-ui/requirements.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.md`
- `openspec/changes/build-thesisforge-desktop-ui/design.md`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/handoff.md`

## Vertical Slice

Add cooperative cancellation to the existing deterministic build application
service, expose one versioned renderer-neutral build-event contract through
cancellable Web and Tauri runners, and bind ordered progress, cancellation,
retry, stale suppression, actionable failures, and successful output feedback
to the shared React workbench.

## In Scope

- A backward-compatible `should_cancel` predicate on `build_service`.
- Cancellation checks before each expensive stage and immediately before final
  atomic replacement.
- A typed application cancellation error carrying the active build stage.
- Prior-output preservation and temporary-file cleanup for cancellation,
  callback failure, validation failure, renderer failure, package validation
  failure, and atomic replacement failure.
- One versioned build-event DTO for `progress`, `success`, and `error` events.
- A streaming adapter runner that invokes the same `build_service` used by the
  CLI and existing adapters.
- A cancellable Web build endpoint and streamed event reader.
- An asynchronous Tauri command/sidecar runner that forwards sidecar events
  without blocking the UI thread.
- One frontend `runBuild` transport contract shared by Web and Tauri.
- Workspace state for ordered progress, last valid output, build error kind,
  cancellation, retry, and current operation generation.
- Repeated-build-click suppression while the current build is active.
- Stale suppression for progress, success, error, cancellation, and output
  events from older operation generations.
- User-visible progress, cancel/retry controls, final output identity, and
  actionable validation, permission, render, finalize, transport, and
  cancellation failures.

## Out Of Scope

- No forced sidecar/worker termination or process-wide cancellation.
- No parser syntax, semantic ID, validation-rule, template-schema,
  compiler-numbering, bibliography, renderer, DOCX, or OOXML changes.
- No exact Word pagination or preview changes.
- No autosave, multi-document jobs, persistent build queue, account, database,
  AI, telemetry, signing, notarization, installer, or release implementation.
- No runtime-specific orchestration inside React components.
- No macOS/Windows packaging acceptance; that remains Slice 008.

## Files Allowed

- `frontend/src/components/**`
- `frontend/src/state/**`
- `frontend/src/transport/**`
- `frontend/src/styles.css`
- `frontend/e2e/**`
- `src/thesis_forge/application/contracts.py`
- `src/thesis_forge/application/services.py`
- `src/thesis_forge/adapters/**`
- `src/thesis_forge/ui/controller.py`
- `src-tauri/src/**`
- `src-tauri/tests/**`
- `tests/test_application_services.py`
- `tests/test_adapters.py`
- `tests/test_http_adapter.py`
- `tests/test_sidecar.py`
- `tests/test_ui_controller.py`
- `tests/test_frontend_contract.py`
- `tests/test_architecture.py`

## Interfaces / Seams

- `build_service(..., should_cancel=None)` remains source-compatible for CLI,
  tests, and adapters that do not opt into cancellation.
- Cancellation is cooperative. A third-party renderer call may finish, but a
  cancellation observed afterward prevents package replacement.
- Application code owns cancellation boundaries. Adapters do not reimplement
  parse, validation, compile, render, package validation, or replacement.
- Build events contain JSON primitives and stable public error kinds only; they
  never expose Python exceptions, `Path`, domain objects, renderer objects, or
  OOXML.
- `WorkbenchTransport.runBuild(request, callbacks, signal)` is the only React
  build runner. Components do not call Fetch, Tauri, sidecar, or Python.
- Every event carries the request ID. Workspace state additionally gates every
  event by operation kind and generation.
- The last valid output is independent from current build loading/error state
  and is replaced only by a current successful build.

## Components To Create

- Python `BuildCanceledError` and cancellation-boundary helper.
- Python build-event serializer/runner.
- Dedicated TypeScript build-event DTO validator owner.
- Dedicated workspace build-state tests and React build-flow tests.

## Components To Reuse

- Existing `BuildStage`, `ApplicationStageError`, `BuildValidationError`,
  `build_service`, temporary output context, and atomic `replace_output`.
- Existing versioned command envelope and source/output presentation rules.
- Existing `OperationToken`, reducer stale check, diagnostics mapper, product
  bar, status strip, and workbench transport selection.
- Existing Web workspace authorization and Tauri managed-sidecar executable
  resolution.

## Components To Extract

- Extract build-event DTO validation from the already large
  `frontend/src/transport/dto.ts`.
- Extract build progress/output presentation instead of adding Slice 007
  scenarios to `WorkbenchApp.test.tsx`.
- Keep component orchestration thin; if build lifecycle handling expands
  `WorkbenchApp`, move it into one build-operation helper/hook.

## API / Data Flow Contracts

- Build request reuses the current versioned command envelope with operation
  `build`, a request ID, saved source reference, selected template, and output
  reference.
- Event envelope:
  `{"protocol","requestId","type":"progress","stage"}` for ordered progress;
  `{"protocol","requestId","type":"success","result"}` for the one final
  result; and `{"protocol","requestId","type":"error","error"}` for the one
  terminal failure.
- Error kinds are `validation`, `permission`, `render`, `finalize`,
  `canceled`, and `transport`; messages remain actionable fixed `zh-CN`
  presentation input.
- A stream emits zero or more progress events followed by exactly one terminal
  success or error event.
- Web uses a cancellable HTTP request whose response body is an incrementally
  consumed event stream; disconnect/abort flips the request cancellation
  predicate.
- Tauri uses an asynchronous command and managed sidecar event stream; dropping
  or aborting the frontend run marks that request canceled without terminating
  unrelated work.
- Stale events are ignored by both request ID at the transport edge and
  generation token in workspace state.

## State / Error / Empty / Loading Behavior

- Loading: retain the last valid output, show the latest ordered stage, disable
  duplicate Build, and enable Cancel.
- Empty: Build remains disabled until a saved source and output destination are
  available.
- Error: show validation, render, finalize, or transport recovery copy; retain
  the last valid output and enable Retry when workspace guards permit.
- Disabled: dirty, fatal diagnostics, missing output, unavailable builder, or
  another active build disables Build with an explicit reason.
- Permission: report that the output destination is not writable, preserve the
  last valid output, and offer destination recovery.
- Canceled: do not display success, do not replace output, retain the last valid
  output, and expose Retry.
- Stale: old progress, success, error, output, and cancellation events produce
  no state change.

## TDD Requirement

- TDD route is `strict`.
- Run focused application, adapter, reducer, transport, component, browser, and
  Tauri tests in RED before production implementation.
- Cover cancellation before every stage and before final replacement, including
  cancellation observed after an uninterruptible renderer call.
- Cover callback, renderer, package validation, replacement, stream, and
  transport failures plus prior-output preservation and temporary cleanup.
- Add dedicated Slice 007 frontend tests; do not add scenarios to the existing
  large `WorkbenchApp.test.tsx`.

## Verification Commands

- `pnpm frontend:test`
- `pnpm frontend:typecheck`
- `pnpm frontend:lint`
- `pnpm frontend:build`
- `pnpm frontend:e2e`
- `.venv/bin/python -m pytest tests/test_application_services.py
  tests/test_adapters.py tests/test_http_adapter.py tests/test_sidecar.py
  tests/test_ui_controller.py tests/test_frontend_contract.py
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

- Scope lock mismatch.
- Cancellation requires killing a shared sidecar/worker or bypassing atomic
  replacement.
- Runtime adapters need to duplicate application build stages or renderer
  behavior.
- React needs direct Fetch, Tauri, sidecar, Python, filesystem, or renderer
  ownership.
- The event stream cannot guarantee one terminal event or request identity.
- Stale events can still replace progress, errors, or a prior valid output.
- The slice requires parser, validator, template, compiler, renderer, DOCX, or
  release-surface changes.

## Unsafe Assumptions

- `AbortSignal` alone prevents final output replacement in the Python process.
- A renderer call can always be interrupted safely.
- Canceling one request permits terminating the whole sidecar process.
- Arrival order is sufficient without request ID and generation checks.
- An HTTP disconnect is always observed before final replacement.
- A current progress event implies that a later terminal event is still current.
- Clearing current operation state is sufficient cancellation.
- A failed or canceled rebuild may clear the last successful output.
