# Task Report: 008-end-to-end-verification

## Status

DONE

Items 8.1 through 8.6 have current direct evidence. The selected
project-scoped SpecNav Verification Runtime `2.0.0-alpha.2` is installed on
APFS, its authority key has real mode `0600`, doctor reports
`readiness=ready`, and all current-HEAD development commands have signed
system-executed receipts with `fallback_used=false`.

## Files Changed

- Verification-focused tests, fixtures, QA contracts, and facticity tooling
  required to exercise the migrated DocForge surfaces.
- Task reports, reviews, ledger entries, validation logs, and installed macOS
  sensory evidence under this change.

## What Changed

- Replayed the complete Python, frontend, Playwright, Rust, distribution,
  desktop-package, facticity, OOXML, deterministic-output, and OpenSpec matrix.
- Replayed all `33` task commands against Git HEAD
  `26344ca4489d60715550f14b774b22ddc4cc491b`; all passed and each receipt is
  bound to its evidence log by SHA-256 and HMAC.
- Exercised general and academic DocForge projects through offline
  inspect/validate/review/build flows.
- Verified the installed macOS DocForge workbench and Microsoft Word 16.112
  final-preview flow with content-addressed DOCX, PDF, screenshot, bundle, and
  DMG evidence.
- Classified all remaining ThesisForge or thesis-named occurrences as
  historical, explicit-negative, binary, or invalid; no invalid active
  finding remains.
- Preserved historical failed receipts and appended formal retest
  adjudications without deleting or rewriting prior evidence.

## TDD Evidence

- The full Python suite covers project security, parser/domain purity,
  validation, templates, compiler, RenderPlan, DOCX OOXML structures,
  bibliography, Review, BuildReport, adapters, CLI, package, distribution,
  deterministic normalization, atomic replacement, and failure retention.
- Frontend and Rust suites cover shared protocol identity, cancellation, stale
  completion, output authorization, accessibility, responsive states, browser
  transport, Tauri project boundaries, and managed sidecar behavior.
- Installed sensory evidence records canonical project open, zero diagnostics,
  build completion, `document.docx`, Microsoft Word PDF generation, neutral
  labels, three-pane layout, and accessibility labels.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest -q`
  -> `1379 passed in 131.99s`.
- `.venv/bin/ruff check src tests scripts qa`
  -> passed.
- `pnpm --dir frontend typecheck`, `lint`, `test`, and `build`
  -> passed; `20` files and `245` tests passed.
- Real Python HTTP Playwright acceptance
  -> `1 passed`.
- Isolated browser matrix on port `4174`
  -> `16 passed`, `20` intentional skips.
- Rust format/check/test
  -> passed; `14` project tests and `32` protocol-contract tests passed.
- Python wheel/sdist build and isolated distribution verification
  -> passed for offline general and academic inspect/validate/review/build.
- Desktop distribution verification
  -> passed for `DocForge.app`,
  `DocForge_0.1.0_aarch64.dmg`, managed sidecar, offline commands,
  cancellation, build, and reopen.
- Facticity
  -> `ok: true`, `activeFindingCount: 0`,
  `allowedFindingCount: 325`, `scannedFiles: 332`; 12 obsolete-domain
  references are classified as historical or explicit-negative.
- Installed macOS + Microsoft Word receipt
  -> `document.docx` 38,520 bytes, SHA-256
  `f475bfc557dbfa0ef83d53a6a3af6b08804013a71fffb667026c9414b01b1948`;
  `document.preview.pdf` 67,545 bytes, SHA-256
  `d903b8a0dbf9c883d8bef686947fb6ddb0cb6ffded169d684340a06d33ea0cd7`.
- `OPENSPEC_TELEMETRY=0 openspec validate docforge-project-format-v1
  --strict --no-interactive --json`
  -> `1` passed, `0` failed.
- SpecNav evidence runner
  -> `33` current-HEAD commands present, `0` remaining, `0` failed,
  `fallback_used=false`.

## Concerns

- Native Windows WebView2 remains broader platform evidence; this change's
  sensory contract uses installed macOS DocForge and Microsoft Word.
- Local release artifacts do not prove external GitHub publication, signing,
  or notarization.

## Scope Deviations

- The default Playwright port `4173` is occupied by an unrelated process. The
  same browser matrix was executed on isolated port `4174` without terminating
  that process.
- The repository volume is ExFAT and cannot represent the Runtime authority
  key as mode `0600`; trusted verification therefore runs in an APFS Git
  worktree at the same committed product HEAD. No permission check was
  relaxed.

## Follow-up Needed

- Materialize official task acceptance artifacts from the signed receipts.
- Generate the immutable six-domain case snapshot and obtain explicit approval
  for its exact id and SHA-256 before activation.
- Complete generation approval, execution, reporting, promotion, and archive
  without starting the separate Markdown-to-DocForge npm Agent Skill change.

## Adjudication

Items 8.1 through 8.6 are complete at the development handoff boundary.
Change-level PASS remains controlled by immutable snapshot approval, successor
generation approval, six-domain execution, and machine-authoritative
promotion/archive gates; this report does not substitute prose for those
artifacts.
