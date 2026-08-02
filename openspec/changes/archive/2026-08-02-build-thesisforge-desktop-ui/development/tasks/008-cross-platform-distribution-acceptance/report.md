# Task Report: 008-cross-platform-distribution-acceptance

## Status

DONE

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
- Built ARM64 MSI and NSIS artifacts on a native Windows 11 ARM VM, installed
  both package formats, and verified the installed main executable and managed
  sidecar are PE `0xAA64`.
- Ran the MSI-installed Tauri application through the complete example with the
  VM adapter disconnected, application sockets blocked, and credentials/proxy
  variables removed. The real WebView2 workbench saved, validated, built, and
  produced the retained screenshot, process capture, JSON evidence, and DOCX.
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
  regression are green.
- Real HTTP RED failed because the test server did not exist. The first real
  integration run then surfaced genuine validator errors in an incomplete
  fixture. A minimal valid thesis fixture closed the real workflow with
  `1 passed`.
- Standard `pnpm frontend:e2e` now runs both the deterministic browser
  state/mock matrix and the separate real Python WSGI adapter project.

## Windows Native Gate

- Native Windows 11 ARM64 MSI and NSIS artifacts were generated and retained by
  hash; the MSI installed to `C:\Program Files\ThesisForge`.
- The installed app and managed sidecar are ARM64 PE files and byte-identical to
  their verified build inputs.
- With Parallels `net0` disconnected, the installed app completed open, edit,
  explicit save, validate, and five-stage DOCX build in the logged-in user
  desktop session.
- The Windows distribution verifier independently returned `ok: true` for Web,
  sidecar, cancellation, build, reopen, MSI, NSIS, and managed sidecar.
- Detailed evidence is retained in
  `evidence/windows-native-acceptance.md`,
  `evidence/windows-native-manifest.json`,
  `evidence/windows-native-acceptance.json`,
  `evidence/windows-native-acceptance.png`, and
  `evidence/windows-native-thesis.docx`.

## Verification Commands

- Final `make verify` on August 2, 2026 -> exited `0`.
- `pnpm frontend:test` -> `53 passed`.
- `pnpm frontend:typecheck`, `pnpm frontend:lint`, and
  `pnpm frontend:build` -> passed.
- `pnpm frontend:e2e` -> `15 passed`, `18` intentional matrix skips, plus real
  HTTP `1 passed`.
- `.venv/bin/python -m pytest` -> `256 passed`.
- `.venv/bin/ruff check .` -> all checks passed.
- `.venv/bin/python -m pip check` -> no broken requirements.
- Python wheel/sdist build and isolated verifier -> passed.
- Native frozen sidecar build and offline verifier -> passed.
- `cargo fmt`, `cargo test`, and `cargo check` -> passed; Rust protocol suite
  returned `11 passed`.
- `cargo tauri build --config src-tauri/tauri.release.conf.json --bundles
  app,dmg` -> rebuilt `.app` and `.dmg`.
- macOS distribution verifier -> passed for Web, sidecar, `.app`, managed
  sidecar, and `.dmg`.
- Windows ARM64 sidecar verifier -> passed offline for inspect, preview,
  validate, cancel, ordered build, DOCX validation, reopen, MSI, NSIS, and
  managed sidecar.
- MSI-installed Windows native acceptance -> passed through real WebView2 CDP
  with source persistence, validation, build, sensory capture, and retained
  DOCX.
- Strict OpenSpec validation -> one change passed.
- SpecNav development entry -> `ok:true`.
- CodeGraph sync/status -> index up to date.
- `git diff --check` -> passed.

## Concerns

- Production signing, Apple notarization, Microsoft Authenticode signing,
  public publication, and license selection remain intentionally outside this
  task.
- Windows evidence is ARM64-specific; x86_64 Windows remains a compatibility
  target for the native workflow rather than an independently executed local
  package in this change.
- GitHub Actions billing remains unavailable, so remote matrix reproducibility
  was not used as a completion gate. Local native macOS and Windows execution
  plus full repository verification are the release authority for this
  local-only closure.

## Scope Deviations

- None. Parser syntax, validator rules, template schema, compiler numbering,
  bibliography, renderer, DOCX/OOXML semantics, accounts, database, AI,
  telemetry, updater, signing, and publication were not changed.

## Follow-up Needed

- Complete local-only operations readiness and archive gates using the green
  six-domain receipt.
- Treat a future GitHub matrix rerun as supplementary reproducibility evidence,
  not as a blocker for the already completed local native acceptance.

## Adjudication

Web, Python, macOS, and Windows distribution and native workflow acceptance are
complete and evidence-backed. Assertions `A1` through `A12` are passing, the
12 user-aligned cases are mapped across all six domains, and Slice 008 is ready
for local-only operations closure.
