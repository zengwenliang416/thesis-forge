# Quality Review: 004-optional-pyside6-workbench-shell

## Verdict

approved

## Separation Of Concerns

- `WorkbenchApp` owns asynchronous orchestration and state transitions.
- `WorkbenchShell` and extracted components render state and emit intent only.
- Web and Tauri implementations are isolated behind `WorkbenchTransport`.
- Python adapters own DTO validation/serialization and delegate compiler work
  to existing application services.
- Rust owns native dialog and sidecar process invocation only.

## Component Cohesion / Coupling

- The former single workbench component was split into the named product bar,
  status, panel, template, progress, and output components required by the
  task brief.
- Shared workspace reducer/selectors and DTOs are runtime-neutral.
- Runtime-specific code is limited to `transport/web.ts`,
  `transport/tauri.ts`, Tauri Rust, and Python HTTP/sidecar adapters.
- No frontend component imports `fetch`, `@tauri-apps/api`, Python, parser,
  compiler, renderer, python-docx, or lxml.

## Test Quality

- Final frontend unit coverage is `19` tests across reducer, transport, and
  component orchestration.
- Playwright executes launch, mobile navigation, viewport containment, complete
  Web open/edit/save/refresh/build, keyboard focus, and resize scenarios across
  desktop, minimum desktop, and mobile projects.
- Python adapter and architecture focused coverage is `20` tests; full
  regression is `191`.
- Cargo protocol coverage checks valid and invalid envelopes plus native UTF-8
  source mapping.
- Tests include observed RED states for every material fix in this slice.

## Error Handling

- Save failures preserve dirty editor text and leave retry actions available.
- Successful save followed by failed refresh preserves the saved snapshot and
  requires a successful refresh before Build can resume.
- Wrong protocol, malformed request types, incomplete frontend responses,
  permissions, application-stage failures, and unexpected adapter failures map
  to stable response kinds.
- Web workspace IDs and plain file names prevent browser-controlled native path
  serialization.

## Reuse / Duplication

- One DTO protocol is shared by Web, Tauri, Python HTTP, Python sidecar, and
  Rust request validation.
- One TypeScript reducer and shared parity fixture mirror the Python reference
  state contract.
- Inspect, validation, build, and atomic source writing reuse existing Python
  services and `LocalWorkspaceFileSystem`.
- No compiler, validation, numbering, bibliography, RenderPlan, renderer, or
  DOCX behavior is duplicated in frontend or adapters.

## Complexity Delta

- The slice adds three runtime surfaces, but coupling is contained by the
  transport and DTO boundaries.
- `WorkbenchApp` remains the largest frontend production module because it
  coordinates asynchronous operation generations; all view-heavy sections are
  extracted.
- The sidecar is request-scoped in this slice. Streaming and cooperative
  cancellation are intentionally deferred to Slice 007 rather than introducing
  premature process infrastructure.

## Required Fixes

- None. All identified correctness, protocol, cohesion, recovery, and
  responsive-layout findings were fixed before approval.
