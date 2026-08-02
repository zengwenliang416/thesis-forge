# Spec Review: 008-cross-platform-distribution-acceptance

## Verdict

blocked

## Missing Requirements

- Task `8.1` is incomplete because the complete example has not run through a
  packaged Windows Tauri target on a native Windows runner.
- Task `8.4` is incomplete because no native Windows `.msi` / NSIS artifact and
  verifier output exists.
- Task `8.7` is incomplete because six-domain verification cannot close while
  Windows runtime and sensory evidence are absent.
- Acceptance assertions `A1`, `A11`, and `A12` remain failing for the same
  reason. Browser, Python, sidecar, and macOS evidence cannot substitute for
  Windows execution.

## Extra Behavior

- None. The implementation adds distribution tooling, release configuration,
  CI, test-only Web hosting, acceptance tests, and documentation within the
  Slice 008 file boundary.

## Misunderstood Requirements

- None after review fixes. The task report explicitly distinguishes static
  Windows workflow coverage from executed Windows acceptance.
- `make verify` is now documented as the source/Web/sidecar gate, not a native
  installer gate.

## Cannot Verify From Diff

- A Windows runner must prove target-native PyInstaller output, Tauri MSI/NSIS
  creation, managed sidecar placement, offline protocol behavior, installer
  launch, keyboard/focus behavior, and runtime output.
- Production Apple notarization, Microsoft signing, publication, and license
  selection remain out of scope and were not attempted.

## Acceptance Assertions Verified

- `A2`, `A3`, `A4`, `A5`, `A6`, `A7`, `A8`, `A9`, and `A10`.
- `A1`, `A11`, and `A12` were reviewed but are intentionally not marked
  verified because their Windows clauses lack native evidence.

## Required Fixes

- Run `.github/workflows/distribution.yml` on `windows-2025`.
- Retain the Windows verifier JSON, MSI/NSIS checksums, job reference, and
  user-aligned native interaction/sensory evidence.
- Update tasks `8.1`, `8.4`, and `8.7`, then move `A1`, `A11`, and `A12` to
  passing and repeat this review.
