# Quality Review: 008-cross-platform-distribution-acceptance

## Verdict

approved

## Separation Of Concerns

- PyInstaller build mechanics stay in `scripts/build_sidecar.py`; runtime
  protocol smoke and artifact checks stay in
  `scripts/verify_desktop_distribution.py`.
- Tauri managed-sidecar launch remains in the Rust adapter boundary. React
  continues to call only the typed `WorkbenchTransport`.
- The real HTTP acceptance host is test-only and delegates API behavior to the
  production Python adapter rather than implementing a second compiler path.
- Parser, validator, template, compiler, bibliography, renderer, DOCX, and
  OOXML owners are unchanged.

## Component Cohesion / Coupling

- Target naming, native-host validation, package-data selection, and the frozen
  entrypoint have one build owner.
- Offline environment stripping, protocol execution, native bundle discovery,
  pollution checks, and evidence output have one verifier owner.
- Release-only `externalBin` configuration does not disturb the base
  development config or explicit executable/Python overrides.
- Web, Python, sidecar, macOS, and Windows artifact roots remain separate.

## Test Quality

- Focused distribution tests cover release config, native target names,
  cross-host rejection, package data, Windows release-sidecar discovery,
  workflow matrices, managed-sidecar use, output isolation, secret/path
  leakage, AppleDouble pollution, and cross-platform real HTTP interpreter
  selection.
- Browser tests cover required states, keyboard/focus, contrast, resize,
  reduced motion, success, cancel, retry, and fatal diagnostics.
- The separate real HTTP project proves open, save, preview/validate, build,
  workspace persistence, and DOCX production without Playwright route mocks.
- The frozen sidecar verifier executes inspect, validate, preview, cancel,
  ordered build, prior-output preservation, DOCX package validation, and reopen
  with credentials removed and outbound connect/connect_ex blocked.
- Full local regression returned Python `242`, frontend unit `53`, browser
  matrix `14`, real HTTP `1`, and Rust protocol `6` passing tests.

## Error Handling

- Build and verifier subprocess failures preserve stdout/stderr details.
- Missing, polluted, non-executable, cross-host, malformed protocol, invalid
  DOCX, and missing native artifact states fail explicitly.
- Managed sidecar termination, stderr, JSON decoding, and build stream events
  map to bounded Rust errors.
- Cancellation continues to preserve the prior output.

## Reuse / Duplication

- The frozen executable invokes the existing
  `thesis_forge.adapters.sidecar` entrypoint and shared dispatcher.
- Web real-adapter acceptance uses the existing `WorkbenchHttpApp` and
  `WebWorkspaceRuntime`.
- CI calls repository scripts instead of duplicating verifier logic in YAML.
- No second frontend, protocol, application service, or compiler/rendering
  implementation was introduced.

## Complexity Delta

- Complexity is concentrated in two independently testable distribution
  scripts and the already isolated Tauri process boundary.
- The Playwright acceptance host is intentionally small and not part of the
  shipped product.
- Review found two concrete gaps: Unix-only Python path selection and missing
  `connect_ex` blocking. Both received failing regression tests, minimal fixes,
  and green reruns.
- A reviewer concern that Tauri resolved `beforeBuildCommand` from
  `src-tauri/` was rejected by direct evidence: the final
  `cargo tauri build --config ...` successfully executed the existing command
  and rebuilt both native bundles.

## Required Fixes

- None in the current implementation diff.
- Windows native runtime evidence remains a specification/operations gate, not
  a hidden code-quality approval.
