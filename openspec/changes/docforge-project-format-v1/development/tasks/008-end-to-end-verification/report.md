# Task Report: 008-end-to-end-verification

## Status

DONE_WITH_CONCERNS

Items 8.1 through 8.5 have current direct evidence. Item 8.6 remains blocked
because the selected project-scoped SpecNav Verification Runtime
`2.0.0-alpha.2` is not installed. Runtime installation requires separate
explicit user approval and no receipt has been fabricated.

## Files Changed

- Verification-focused tests, fixtures, QA contracts, and facticity tooling
  required to exercise the migrated DocForge surfaces.
- Task reports, reviews, ledger entries, validation logs, and installed macOS
  sensory evidence under this change.

## What Changed

- Replayed the complete Python, frontend, Playwright, Rust, distribution,
  desktop-package, facticity, OOXML, deterministic-output, and OpenSpec matrix.
- Exercised general and academic DocForge projects through offline
  inspect/validate/review/build flows.
- Verified the installed macOS DocForge workbench and Microsoft Word 16.112
  final-preview flow with content-addressed DOCX, PDF, screenshot, bundle, and
  DMG evidence.
- Classified all remaining ThesisForge or thesis-named occurrences as
  historical, explicit-negative, binary, or invalid; no invalid active
  finding remains.

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

## Concerns

- The project-selected SpecNav Verification Runtime is absent at
  `.specnav/runtime/verification/2.0.0-alpha.2`.
- Historical failed receipts must remain append-only and be adjudicated by the
  trusted verification lifecycle; they must not be deleted or rewritten into
  passing evidence.

## Scope Deviations

- The default Playwright port `4173` is occupied by an unrelated process. The
  same browser matrix was executed on isolated port `4174` without terminating
  that process.

## Follow-up Needed

- Commit the pre-Runtime implementation and lifecycle evidence so task
  acceptance can bind a clean HEAD.
- Obtain explicit approval before installing the locked project-scoped
  SpecNav Verification Runtime `2.0.0-alpha.2`.
- After installation, generate system receipts, task acceptance, A1 through
  A10 adjudication, all six verification domains, promotion, and archive gates.

## Adjudication

Items 8.1 through 8.5 are complete. Item 8.6 remains deliberately open at the
runtime-installation approval boundary; this report does not claim change-level
PASS or substitute prose for machine-authoritative receipts.
