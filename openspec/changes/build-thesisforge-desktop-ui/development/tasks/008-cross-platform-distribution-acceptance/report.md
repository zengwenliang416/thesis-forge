# Task Report: 008-cross-platform-distribution-acceptance

## Status

DONE_WITH_CONCERNS

## Files Changed

- Distribution and CI: `.github/workflows/distribution.yml`, `.gitignore`,
  `Makefile`, `package.json`, `pyproject.toml`,
  `scripts/build_sidecar.py`, `scripts/verify_desktop_distribution.py`, and
  `tests/test_desktop_distribution.py`.
- Desktop release: `src-tauri/Cargo.toml`, `src-tauri/Cargo.lock`,
  `src-tauri/src/lib.rs`, `src-tauri/tests/protocol_contract.rs`,
  `src-tauri/tauri.conf.json`, and `src-tauri/tauri.release.conf.json`.
- Browser acceptance: `frontend/e2e/acceptance.spec.ts`,
  `frontend/e2e/real-http.acceptance.ts`,
  `frontend/e2e/real-http.playwright.config.ts`, and
  `frontend/e2e/real_http_server.py`.
- Maintainer/user guidance: `README.md` and `docs/MAINTENANCE.md`.
- Lifecycle evidence: Slice 008 task packet, evidence files, acceptance status,
  task ledger, scope lock, and CodeGraph artifacts.

## What Changed

- Added a native-target-only PyInstaller build for the existing versioned
  Python sidecar, including required template and python-docx package data.
- Added a release-only Tauri `externalBin` configuration and Rust managed
  sidecar launch path while retaining explicit development/test overrides.
- Added strict distribution verification for host/target parity, sidecar
  pollution, offline inspect/validate/preview/build/cancel/reopen, ordered
  stages, prior-output preservation, valid DOCX output, isolated Web artifacts,
  and native bundle discovery.
- Added native macOS and Windows CI matrix definitions with separate Web,
  Python, sidecar, and desktop uploads. No cross-OS sidecar relabeling is
  allowed.
- Added a Windows-only installed-app gate that installs the native MSI, drives
  the installed Tauri WebView through external `tauri-driver`, keeps only the
  system file picker behind a test seam, executes real save/validate/build
  commands against the packaged sidecar, blocks sidecar sockets, strips
  credentials, and uploads screenshot plus JSON evidence.
- Added dedicated browser state/accessibility acceptance and a real Python HTTP
  adapter Playwright run with no route mocks.
- Documented runtime capabilities, installation, offline behavior, packaging,
  signing/notarization, checksums, troubleshooting, and the Windows evidence
  boundary.

## TDD Evidence

- Distribution RED covered missing release config, target-specific naming,
  native-host enforcement, package data, managed sidecar launch, artifact
  isolation, native workflow matrices, and release-file leakage.
- Focused distribution GREEN:
  `.venv/bin/python -m pytest tests/test_desktop_distribution.py -q` returned
  `12 passed`.
- Verifier review fixes added explicit rejection for cross-host verification,
  AppleDouble pollution in the sidecar directory, and Windows managed-sidecar
  discovery from the native `release/` directory.
- Quality-review RED added regressions for a Windows-capable real HTTP test
  interpreter and `socket.connect_ex` blocking; both failed before the fixes
  and returned `12 passed` after implementation.
- Installed-Windows acceptance RED returned two focused failures for the
  missing native WebDriver workflow and WDIO task files. The static contract,
  isolated WDIO typecheck, frozen lock install, and existing frontend
  regression are now green; native execution remains pending.
- Real HTTP RED failed because the test server did not exist. The first real
  integration run then surfaced genuine validator errors in an incomplete
  fixture. A minimal valid thesis fixture closed the real workflow with
  `1 passed`.
- Standard `pnpm frontend:e2e` now runs both the deterministic browser
  state/mock matrix and the separate real Python WSGI adapter project.

## Verification Commands

- `pnpm frontend:test` -> `53 passed`.
- `pnpm frontend:typecheck`, `pnpm frontend:lint`, and
  `pnpm frontend:build` -> passed.
- `pnpm frontend:e2e` -> `14 passed`, `16` intentional skips, plus real HTTP
  `1 passed`.
- Focused Python distribution/architecture set -> `26 passed`.
- `.venv/bin/python -m pytest -q` -> `244 passed`.
- `.venv/bin/ruff check .` -> all checks passed.
- `.venv/bin/python -m pip check` -> no broken requirements.
- Python wheel/sdist build and isolated verifier -> passed.
- Native frozen sidecar build and offline verifier -> passed.
- `cargo fmt`, `cargo test`, and `cargo check` -> passed; Rust protocol suite
  returned `6 passed`.
- `cargo tauri build --config src-tauri/tauri.release.conf.json --bundles
  app,dmg` -> rebuilt `.app` and `.dmg`.
- macOS distribution verifier -> passed for Web, sidecar, `.app`, managed
  sidecar, and `.dmg`.
- Strict OpenSpec validation -> one change passed.
- SpecNav development entry -> `ok:true`.
- CodeGraph sync/status -> index up to date.
- `git diff --check` -> passed.

## Concerns

- Windows `.msi` / NSIS build, installed workflow, keyboard/sensory review, and
  blocked-socket execution require a successful native Windows runner.
- Local macOS evidence and static workflow tests do not satisfy that external
  gate. Acceptance assertions `A1`, `A11`, and `A12` therefore remain failing.
- Production signing, Apple notarization, Microsoft Authenticode signing,
  public publication, and license selection remain intentionally outside this
  task.

## Scope Deviations

- None. Parser syntax, validator rules, template schema, compiler numbering,
  bibliography, renderer, DOCX/OOXML semantics, accounts, database, AI,
  telemetry, updater, signing, and publication were not changed.

## Follow-up Needed

- Push the reviewed branch and run `.github/workflows/distribution.yml` on the
  native Windows matrix, including the installed-app WDIO step.
- Retain the Windows verifier JSON, installer artifact checksums, and a
  user-aligned Windows interaction/sensory record.
- Only then mark tasks `8.1`, `8.4`, and `8.7` complete and move `A1`, `A11`,
  and `A12` to passing before the six-domain verification contract.

## Adjudication

Local implementation, Web acceptance, Python distribution, frozen sidecar, and
macOS native acceptance are complete and evidence-backed. The controller accepts
the Slice 008 implementation as `DONE_WITH_CONCERNS` but does not hand the
change to final verification because the three Windows-dependent acceptance
assertions remain open.
