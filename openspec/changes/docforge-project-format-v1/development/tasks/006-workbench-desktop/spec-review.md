# Spec Review: 006-workbench-desktop

## Verdict

approved

## Missing Requirements

- None for the Task 006 scope. Items 6.1 through 6.4 are supported by the
  current frontend, Rust, adapter, and distribution tests: project opening
  requires `docforge.yaml` plus a Markdown source, bare Markdown and obsolete
  manifests/protocols are rejected, neutral DocForge identities are used, and
  the approved three-pane workbench remains intact.
- Item 6.5 is covered by the installed macOS receipt and the responsive browser
  matrix. The receipt records the installed `DocForge.app` opening a
  `docforge.yaml` project with `document.md`, zero diagnostics, completed
  `document.docx` output, accessibility labels, and a displayed Microsoft Word
  16.112 PDF preview. The browser matrix records the applicable desktop,
  minimum-desktop, and mobile checks.
- The desktop-workbench delta spec describes a cross-platform product, but the
  Task 006 brief and change-level sensory acceptance gate require the installed
  macOS workbench and Microsoft Word flow. Native Windows WebView2 remains a
  broader product-platform follow-up, not a missing Task 006 closure
  requirement.

## Extra Behavior

- No unrequested screen, layout, dark-mode, locale, or Markdown lifecycle
  change was found.
- Obsolete protocol, manifest, and external acceptance identifiers are kept
  only where they are explicit negative vectors or required external test
  seams; no compatibility dispatch or project fallback was added.

## Misunderstood Requirements

- None found. `templateId: null` continues to mean “use the project-declared
  template”; the generic `docforge-standard` template is available as an
  explicit command-bar selection without overriding that project declaration
  on open.

## Cannot Verify From Diff

- The current Web and Rust tests do not prove Windows WebView2 behavior. No
  Windows installed-package receipt exists on this macOS host; that evidence
  belongs to the prepared Windows CI/product follow-up.
- `acceptance.json` still records the change-level assertions as `failing` with
  null evidence references. This review verifies only the Task 006 slices of
  those assertions and does not close the change-level acceptance ledger.
- The clean bundle-verifier retry passed earlier in this review, but a serial
  closeout rerun found the ignored `._DocForge_0.1.0_aarch64.dmg` AppleDouble
  sidecar again and exited with code `1`. The installed macOS receipt remains
  an earlier system-executed pass; current release-directory hygiene must be
  cleaned or regenerated before the Task 007 release handoff.
- The default `pnpm --dir frontend e2e` port is an existing environment
  contention point. The current three-project browser matrix passed on the
  isolated `4174` configuration with intentional skips only where a test is
  not applicable to that viewport.

## Acceptance Assertions Verified

- `A1` Task 006 slice: the real Python HTTP acceptance and installed macOS
  receipt open a project identified by `docforge.yaml` and resolve
  `document.md`; Rust project tests also cover directory and manifest-path
  opening. This is not a claim that the change-level A1 ledger is closed.
- `A2` Task 006 slice: the real HTTP general project declares
  `docforge-standard`, has no academic profile, and completes explicit save,
  validate, and DOCX build. The task review does not overclaim the
  change-level inspect/review E2E assertion.
- `A4` Task 006 slice: frontend and Rust transport/project tests reject
  obsolete manifest, schema, protocol, and unsafe project-boundary inputs
  without compatibility dispatch. Repository-wide facticity remains outside
  this task-local review.
- `A5` Task 006 slice: shared frontend/Rust/Python identity constants and
  contract tests define `document.md`, `build/document.docx`,
  `document.review.md`, and `document.review-map.json`, with matching
  `docforge.workbench.v1` and `docforge.build-report.v2` identities; the real
  HTTP and installed macOS receipts verify the source and DOCX output defaults.
- `A9` Task 006 slice: the installed macOS receipt and screenshot verify neutral
  DocForge identity, filenames, diagnostics, accessibility labels, three-pane
  layout, DOCX build, and Microsoft Word PDF generation/display. Native Windows
  behavior is recorded as a broader follow-up, not as an A9 requirement for
  this task review.

## Required Fixes

- None for the Task 006 spec review. The global acceptance statuses and
  task-ledger history remain unchanged; a later verification lifecycle must
  bind the task-local receipts to the change-level assertions.

## Validation Evidence

- `PYTHONPATH=src .venv/bin/python -m pytest tests/adapters tests/test_desktop_distribution.py -q`
  -> `62 passed in 2.57s`.
- `pnpm --dir frontend typecheck` -> passed.
- `pnpm --dir frontend lint` -> passed.
- `pnpm --dir frontend test` -> `20` files and `245` tests passed.
- `pnpm --dir frontend build` -> production Vite build passed.
- `pnpm --dir frontend exec playwright test --config e2e/real-http.playwright.config.ts`
  -> `1 passed` through the real Python HTTP adapter.
- `pnpm --dir frontend exec playwright test --config playwright.4174.config.ts`
  -> `16 passed`, `20` intentional viewport skips, `0` failures; the mobile
  project passed its applicable workbench checks.
- `cargo fmt --check --manifest-path src-tauri/Cargo.toml` -> passed.
- `cargo check --manifest-path src-tauri/Cargo.toml` -> passed.
- `cargo test --manifest-path src-tauri/Cargo.toml`
  -> `14` project tests and `32` protocol-contract tests passed.
- `PYTHONPATH=src .venv/bin/python scripts/verify_desktop_distribution.py --platform macos --bundle-root src-tauri/target/release/bundle`
  -> the clean retry returned `ok: true`; the later serial closeout rerun
  returned `exit 1` because the ignored
  `._DocForge_0.1.0_aarch64.dmg` AppleDouble sidecar reappeared in the DMG
  directory. The release-directory hygiene issue is recorded as a Task 007
  handoff follow-up, not as a failure of the installed macOS/Word receipt.
- `evidence/macos-native-acceptance.json` -> installed macOS receipt checked
  on 2026-08-27; `document.docx` is `38,520` bytes and Microsoft Word 16.112
  generated/displayed a valid `67,545` byte `%PDF-` preview.
- `git diff --check -- openspec/changes/docforge-project-format-v1/development/tasks/006-workbench-desktop/spec-review.md`
  -> passed.
