# Quality Review: 007-repository-delivery

## Verdict

approved

## Review Scope

- Independent quality re-review of the current checkout on August 27, 2026,
  covering Task 007 items 7.1 through 7.5.
- The review is limited to repository-owned projects, documentation, facticity,
  packaging, CI, release collection, and macOS artifact verification. No
  external release publication was attempted.
- This review updates only this file. Unrelated dirty-worktree changes were
  preserved.

## Separation Of Concerns

- Active examples, fixtures, documentation, schemas, and QA surfaces consume
  the same `docforge.yaml` and `document.md` project contract. Historical
  OpenSpec evidence and explicit obsolete-input fixtures remain classified
  rather than being rewritten.
- `scripts/check_facticity.py` owns obsolete-identity scanning and
  active/historical/explicit-negative classification. Distribution inspection,
  frozen-sidecar verification, and release collection remain separate in
  `scripts/verify_distribution.py`, `scripts/verify_desktop_distribution.py`,
  and `scripts/prepare_release.py`.
- CI and Woodpecker workflows compose these validators and build steps without
  moving parsing, compilation, rendering, or DOCX behavior into repository
  migration scripts.
- The release workflow keeps source checkout, native build, artifact
  verification, evidence capture, and staged upload as distinct steps. It does
  not claim that local packaging proves GitHub publication.

## Component Cohesion / Coupling

- Identity and default-path values are centralized at the Python, TypeScript,
  Rust, and packaging boundaries, with contract tests checking their DocForge
  names and neutral filenames. The desktop verifier reuses the sidecar builder
  identity instead of introducing another sidecar-name authority.
- The facticity scanner reports allowed historical and explicit-negative
  findings instead of silently suppressing them, while the release verifiers
  focus on artifact shape, names, version binding, and runtime smoke behavior.
- The migration adds no alternate compatibility loader, alias, or parallel
  project-delivery path. Existing application services, fixtures, package
  checks, and release mechanisms are reused.
- Existing large orchestration files remain maintainability risks, but this
  slice does not introduce new cross-layer coupling or renderer dependency
  leakage.

## Test Quality

- The Task 007 focused suite passed:
  `PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_desktop_distribution.py tests/cli tests/project -q`
  -> `165 passed`.
- Facticity regression coverage passed with `4` tests. The repository scan
  returned `ok=true`, `activeFindingCount=0`, `allowedFindingCount=325`,
  `scannedFiles=332`, and `skippedFiles=43`; the remaining obsolete-domain
  findings are historical or explicit-negative.
- The real HTTP acceptance test passed:
  `pnpm --dir frontend exec playwright test --config
  e2e/real-http.playwright.config.ts` -> `1 passed`.
  `pnpm --dir frontend build`, Cargo check, scoped Ruff, and `git diff --check`
  also passed.
- Distribution tests cover obsolete package/schema/report names, wrong and
  symlinked release artifacts, AppleDouble pollution, missing executable
  sidecars, offline execution, cancellation, ordered build stages, and
  canonical `document.md`/`document.docx` wiring.
- A temporary clean-bundle replay passed DMG verification, the desktop
  verifier, the release collector, and SHA256 validation. It produced exactly
  the five expected release files: the DocForge DMG, wheel, source archive,
  `SHA256SUMS`, and `RELEASE_NOTES.md`.

## Error Handling

- Active facticity findings fail the scanner, while historical and
  explicit-negative references are retained in the report for review.
  Binary/unreadable files are reported as skipped rather than treated as
  silently clean.
- Release collection rejects version/tag mismatches, missing or duplicate
  artifacts, symlinked roots or artifacts, path escapes, stale output
  directories, and AppleDouble files.
- Frozen-sidecar verification rejects malformed protocol output, wrong
  BuildReport schemas or outcomes, missing build stages, non-executable
  sidecars, invalid DOCX output, and failed reopen checks. Its offline and
  cancellation paths preserve the prior successful output.
- The tag workflow verifies the fetched tag SHA and ancestry before building.
  macOS metadata cleanup runs after `hdiutil verify` and before release
  collection, matching the successful temporary replay.

## Reuse / Duplication

- Existing project fixtures, package/distribution checks, sidecar builder,
  desktop verifier, release collector, CI jobs, and checksum flow are reused
  rather than replaced with one-off migration tooling.
- Shared identity constants are used within each language boundary, and the
  Python, TypeScript, Rust, and packaging contract tests verify matching
  external names. Repeated literals in tests and release manifests are
  assertions or boundary-specific configuration, not additional production
  aliases.
- No obsolete package, command, manifest, protocol, sidecar, or default-output
  compatibility path remains active.

## Complexity Delta

- The change is broad in surface area but mostly converts existing
  repository-owned delivery inputs and names. New complexity is concentrated
  in the facticity report and release verification helpers, where the extra
  classification, isolation, checksum, and artifact checks are directly tied
  to the task contract.
- The isolated distribution verifier is substantially more involved because it
  materializes runtime wheels, installs a clean virtual environment, blocks
  network APIs, and runs both general and academic fixture flows. This is
  verification-only complexity and does not affect the product compile path.
- No new complexity budget issue or high-severity maintainability defect was
  found for this task. Existing large scripts and the Rust desktop
  orchestrator are non-blocking follow-up risks.

## Required Fixes

- None for the Task 007 quality slice.

## Non-Blocking Notes

- On the shared macOS checkout, `hdiutil verify` can create an ignored
  `._DocForge_0.1.0_aarch64.dmg` sidecar. A direct verifier run against that
  unclean directory can therefore fail before inspecting the real DMG. The
  release workflow deletes these files after DMG verification, and the
  clean temporary-copy replay passed the complete sequence.
- External Woodpecker staging, GitHub tag/upload, and release publication were
  intentionally not executed. They remain separately authorized operations.
- `acceptance.json` still records change-level assertions as `failing`;
  binding fresh trusted A4/A10 receipts to the final committed HEAD belongs to
  Task 008 and does not block this task-local quality approval.
