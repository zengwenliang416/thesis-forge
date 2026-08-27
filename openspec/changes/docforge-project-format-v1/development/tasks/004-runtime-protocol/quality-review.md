# Quality Review: 004-runtime-protocol

## Verdict

approved

- Final re-review performed against the current checkout after the previous
  two blockers were fixed.
- Rust and Python now agree on the `docforge-live-preview-` capability
  namespace, and malformed or forged output cannot revoke existing preview
  authorization.
- `run_build` rejects a non-build operation before preview authorization state
  is mutated. No remaining Task 004 quality blocker was found.

## Separation Of Concerns

- Python and TypeScript adapters continue to delegate parsing, validation,
  compilation, rendering, and finalization to the existing application
  services. No second parser/compiler path or obsolete protocol dispatch path
  was introduced.
- Rust owns the Tauri protocol envelope, filesystem boundary, cancellation
  bridge, and preview authorization. Parser, validator, compiler, and DOCX
  renderer responsibilities remain in the application/sidecar layers.
- Rust live-preview generation, ID extraction, directory validation, and PDF
  cleanup use `LIVE_PREVIEW_PREFIX` at
  `src-tauri/src/lib.rs:32,604-616,811-881`. A direct cross-boundary probe
  accepted a `docforge-live-preview-<32hex>.docx` descriptor in
  `DesktopRuntime` and rejected the obsolete `thesisforge-live-preview-`
  shape.

## Component Cohesion / Coupling

- Runtime identity and default-path values are centralized independently at
  the Python, TypeScript, and Rust boundaries, and the Rust identity tests
  load the shared runtime fixture.
- `validate_and_prepare_build_preview_authorization` now enforces
  `operation == "build"` at `src-tauri/src/lib.rs:1023-1030`, validates the
  complete live-preview capability at `src-tauri/src/lib.rs:1031-1041`, and
  only then calls `prepare_build_preview_authorization` at line 1043.
  Authorization invalidation is therefore separated from request rejection.
- The helper is small and focused on the build-only state transition; no
  broad refactor or new adapter abstraction was introduced.

## Test Quality

- Current focused evidence is green: Python `140` tests, frontend `20` files
  with `243` tests, and the full Rust suite with `14` project tests plus `32`
  protocol-contract tests.
- `forged_live_preview_output_does_not_revoke_existing_preview_authorization`
  at `src-tauri/src/project_tests.rs:202-252` proves an unknown capability
  preserves the prior PDF authorization.
- `invalid_build_operation_does_not_revoke_existing_preview_authorization`
  at `src-tauri/src/project_tests.rs:256-312` proves a valid capability paired
  with `operation: "inspect"` is rejected before the prior authorization is
  revoked.
- The Rust namespace test asserts `docforge-live-preview-` at
  `src-tauri/tests/protocol_contract.rs:689-711`; the independent Python
  probe confirms that the same descriptor is accepted by `DesktopRuntime`.
- The shared fixture does not encode the live-preview namespace, so adding an
  executable cross-language namespace parity case would reduce future drift
  risk. This is non-blocking because both runtime validators and the
  cross-boundary probe currently agree.
- The real HTTP browser flow remains blocked before HTTP dispatch by the
  Task 006 picker migration and is not a Task 004 transport failure.

## Error Handling

- Obsolete workbench and BuildReport identities are rejected before preview
  authorization, and the focused tests cover those failures.
- Invalid live-preview IDs, mismatched output paths, and non-desktop output
  shapes are rejected before old preview authorization can be revoked.
- Invalid build operations are rejected before `prepare_build_preview_authorization`;
  the new regression confirms the previous derived PDF remains resolvable.
- Valid build starts continue to revoke the previous derived authorization,
  while failed or canceled builds retain the intended stale-preview behavior.

## Reuse / Duplication

- Existing application services, typed DTOs, HTTP transport, Tauri bridge,
  cancellation state, and preview authorization state are reused correctly.
- The Rust live-preview prefix is centralized across active generation,
  extraction, validation, cleanup, and protocol-test paths.
- The repeated prefix in the Rust test is an assertion of the external
  contract, not a second production authority. No obsolete compatibility
  alias or fallback dispatch path remains.

## Complexity Delta

- The changed orchestration remains understandable and the validation helper
  is small. No parser, renderer, or application-service responsibility leaked
  into the transport layer.
- The relevant files remain large (`src-tauri/src/lib.rs`: `1,264` lines;
  `src/docforge/adapters/runtime.py`: `1,513` lines), exceeding the quality
  guideline that files over `800` lines deserve organization work. This is a
  non-blocking existing complexity risk and does not prevent approval of this
  focused protocol slice.

## Required Fixes

- None for Task 004.
- Non-blocking follow-up: add the live-preview namespace to the shared parity
  fixture or an executable cross-language parity test.
- Task 006 should complete the UI picker and remaining product-owned desktop
  terminology migration; Task 008 should rerun the real HTTP and installed
  desktop flows afterward.
