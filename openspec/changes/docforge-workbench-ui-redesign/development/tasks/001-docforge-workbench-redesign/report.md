# Task Report: 001-docforge-workbench-redesign

## Status

DONE_WITH_CONCERNS

## Files Changed

- `frontend/index.html`
- `frontend/src/components/{WorkbenchApp,WorkbenchShell,ProductBar,StatusStrip,WorkbenchPanels,PreviewPanels,ReviewPanel,OutputFeedback}.tsx`
- Focused component tests under `frontend/src/components`
- `frontend/src/styles.css`
- `frontend/e2e/{acceptance.spec,workbench.spec,real-http.acceptance,tauri-windows.acceptance}.ts`
- `src-tauri/tauri.conf.json`
- `design-qa.md`
- `openspec/changes/docforge-workbench-ui-redesign`

## What Changed

- Changed the visible product identity to `DocForge` with the subtitle
  `Markdown → Word 文档工坊` without renaming the repository, Python package,
  CLI, protocol, Tauri bundle identifier, or internal ThesisForge types.
- Moved the existing Word template selector into the compact product command
  bar while preserving the existing template ID and callback.
- Rebuilt the shared workbench as a desktop outline/editor/Word-preview canvas
  with contextual diagnostics and output status.
- Preserved minimum-desktop resizers and mobile outline/editor/preview/
  diagnostics routing through the existing state and callbacks.
- Replaced thesis-only and fallback-oriented visible copy with generic document
  production copy and Microsoft Word-specific preview labels.
- Added a 90-second timeout only to the real HTTP acceptance test because the
  existing LibreOffice preview contract allows up to 60 seconds; all success
  assertions remain unchanged.
- Rebuilt and installed the macOS application at
  `/Applications/ThesisForge.app` and opened `examples/v2-complete-thesis`.

## TDD Evidence

- Focused component tests were updated with the copy and template-selector
  relocation and now pass as part of 238 frontend tests.
- Playwright covers product identity, minimum desktop controls, mobile
  navigation without horizontal overflow, resizers, keyboard focus, open,
  edit, save, validate, build, cancel, template changes, diagnostics, and final
  preview behavior.
- The initial real HTTP run exceeded Playwright's default 30-second global
  timeout while the backend completed successfully within the existing preview
  contract. The single integration test now uses 90 seconds and passes without
  weakened transport, output, or ZIP assertions.
- CodeGraph evidence `ev-mt8ejd0i` traces ProductBar and WorkbenchShell through
  WorkbenchApp and the WorkbenchTransport boundary with matched confidence.

## Verification Commands

- `pnpm frontend:test` -> 20 files, 238 tests passed.
- `pnpm frontend:typecheck` -> passed.
- `pnpm frontend:lint` -> passed.
- `pnpm frontend:build` -> Vite production build passed.
- `pnpm frontend:e2e` -> 16 browser tests passed, 20 intentional matrix skips,
  and 1 real Python HTTP adapter test passed.
- `cargo fmt --manifest-path src-tauri/Cargo.toml -- --check` -> passed.
- `cargo test --manifest-path src-tauri/Cargo.toml` -> 6 Rust unit tests and 28
  protocol-contract tests passed.
- `OPENSPEC_TELEMETRY=0 openspec validate
  docforge-workbench-ui-redesign --strict --no-interactive --json` -> passed.
- `git diff --check` -> passed.
- `.venv/bin/python scripts/verify_desktop_distribution.py --target-triple
  aarch64-apple-darwin --platform macos --web-dist dist/web --bundle-root
  src-tauri/target/aarch64-apple-darwin/release/bundle` -> `.app`, `.dmg`,
  offline sidecar, cancellation, full build, valid DOCX, and reopen passed.
- Installed bundle probe -> process `35991`, executable SHA-256
  `0821e98c838fa58b656cccf512782314a5b25f95a1def5809c82b09e7272598b`.
- Generated and installed executables share Mach-O UUID
  `57D2FECE-3578-3CC4-A119-65F95F48BBCB`; their file hashes differ because the
  installed bundle was ad-hoc re-signed.
- Generated and installed sidecars share SHA-256
  `ea05c818878914232371b2fe186e5551bd60143265c2db0ff22fa512ed368f78`.
- Installed Word-preview screenshot SHA-256
  `ab5e4501a4bb9bdff2afc1f2f79fe65783e9cd2703b4625ac812a2f992db2133`.

## Concerns

- Windows native WebView2 acceptance requires `THESISFORGE_WINDOWS_SOURCE` and
  a Windows host. It remains intentionally unexecuted on this macOS machine;
  browser, real HTTP, Rust protocol, macOS packaging, installation, and
  Microsoft Word preview paths are directly verified.
- Cargo reported only incremental-cache hard-link fallback warnings on the
  external volume; compilation and all Rust tests passed.
- The installed app's main executable hash differs from the unsigned generated
  bundle after bundle-level ad-hoc signing. Matching Mach-O UUIDs and identical
  sidecar hashes establish that the installed app comes from the verified
  build rather than an older build.

## Scope Deviations

- None. Production implementation stayed inside the task allowlist.
- Unrelated generated files under `v2-rich-inline-renderplan-p1` and
  `template-v2-build-pipeline-p1` were not modified for or attributed to this
  task.

## Follow-up Needed

- Run `frontend/e2e/tauri-windows.acceptance.ts` on the prepared Windows
  acceptance host before a Windows release.

## Adjudication

The Windows-only prerequisite does not block the approved macOS delivery or
the shared Web/Tauri UI redesign. All required current-platform commands,
installed-app evidence, sensory evidence, and CodeGraph evidence pass.
