# Quality Review: 005-template-selection-structured-diagnostics

## Verdict

approved

## Separation Of Concerns

- Shared React owns template selection and diagnostic presentation without
  repository-relative paths or direct resolver/service access.
- The Python runtime adapter owns protocol compatibility and stable
  `templateId` resolution before delegating to existing application services.
- CLI and headless Python UI share one framework-neutral diagnostic
  presentation module.

## Component Cohesion / Coupling

- Diagnostic localization, sorting/filtering, editor line navigation, workspace
  state, and React rendering remain separate cohesive owners.
- The retained `templatePath` field is bounded to the transport DTO and Python
  adapter compatibility seam; current React requests do not use it.

## Test Quality

- The shared fixture covers `missing-template`, `ambiguous-template`,
  `invalid-bibliography`, and `resource-path-escape` in both Python and
  TypeScript parity tests.
- Tests cover stable-ID resolution independent of process cwd, selector
  conflict rejection, malformed DTOs, fatal/warning guards, empty-state
  disabled filters, keyboard/pointer activation, line focus, no-line behavior,
  stale suppression, and old-template reset on new source open.

## Error Handling

- Transport consumers reject incomplete or malformed serialized diagnostics.
- The dispatcher rejects conflicting selectors as a request error and preserves
  the application-layer fatal validation authority.
- Fatal diagnostics expose a visible, non-color-only Build-disabled reason.

## Reuse / Duplication

- Python diagnostic copy is shared by CLI and UI models.
- Python and TypeScript presentation implementations remain separate runtime
  owners but are constrained by one versioned parity fixture.

## Complexity Delta

- No maintained source file crosses 800 lines.
- The largest touched maintained source file is `WorkbenchApp.tsx` at 405
  lines; orchestration remains within its existing owner.
- One compatibility branch was added for `templatePath`; retirement is deferred
  to a future versioned protocol cleanup rather than silently breaking callers.
- Net entropy is stable with a bounded compatibility seam.

## Required Fixes

- Slice 005 has no remaining quality fixes after the adapter compatibility
  seam, shared localization fixture, error handling, and focused regression
  coverage were approved.

## Independent Validation

- Python adapter/UI/CLI review set -> `40 passed`.
- Frontend state/component/transport review set -> `31 passed`.
- Focused desktop Playwright fatal-template scenario -> `1 passed`.
- TypeScript typecheck and focused Ruff checks -> passed.

## Residual Risk

- New diagnostic codes require updating both presentation mappings and the
  shared fixture to prevent drift.
- Full retirement of `templatePath` requires an explicit protocol-version
  change outside this slice.
