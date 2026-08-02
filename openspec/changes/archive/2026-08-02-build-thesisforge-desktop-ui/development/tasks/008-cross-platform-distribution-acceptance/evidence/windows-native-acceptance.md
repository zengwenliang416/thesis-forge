# Windows Native Acceptance

Date: 2026-08-02

## Failed Run 30747667110

- Workflow:
  `https://github.com/zengwenliang416/thesis-forge/actions/runs/30747667110`
- Commit: `f17128167f3136062c455e54cd6642dc779e86c0`
- The native Windows job passed Web distribution, Python distribution, the
  target-native frozen sidecar, offline sidecar verification, Tauri MSI/NSIS
  bundle construction, desktop distribution verification, and MSI installation.
- Windows Installer event `1033` recorded ThesisForge `0.1.0` installation with
  status `0` under `C:\Program Files\ThesisForge`.
- The installed `thesisforge-desktop.exe` launched successfully. WebView2
  exposed a loopback-only CDP endpoint on `127.0.0.1:9222`, and the captured
  process command line included the expected remote-debugging arguments.
- Playwright connected to the real installed Tauri WebView and confirmed
  `__TAURI_INTERNALS__` plus the shared ThesisForge workbench.

## Failure

- The installed acceptance timed out at
  `frontend/e2e/tauri-windows.acceptance.ts:243` while waiting for the editor to
  contain the complete thesis fixture after clicking `打开 Markdown 文稿`.
- The evidence proves that CDP was healthy. The failure was limited to the
  page-level monkey patch used to replace the native `pick_source` command.
- No DOCX, screenshot, or passing `windows-native-acceptance.json` was produced,
  so `A1`, `A11`, and `A12` remain blocked.

## TDD Fix

- RED:
  `cargo test --manifest-path src-tauri/Cargo.toml --test protocol_contract`
  failed because `acceptance_source_override` did not exist.
- RED:
  `.venv/bin/python -m pytest tests/test_desktop_distribution.py -q` returned
  one failure because the Windows acceptance did not define
  `THESISFORGE_WINDOWS_ACCEPTANCE_SOURCE`.
- GREEN:
  the Rust picker now reads the explicit acceptance source only when that
  environment variable is present; ordinary launches still use the system file
  picker.
- GREEN:
  Rust protocol tests returned `11 passed` and desktop distribution tests
  returned `20 passed`.
- Full local regression returned Python `254 passed`, frontend unit `53 passed`,
  browser `14 passed` with `16` intentional skips, real HTTP `1 passed`, and
  Rust protocol `11 passed`. Production build, Ruff, lint, typecheck, Cargo
  fmt/check, pip check, strict OpenSpec, CodeGraph sync, and whitespace checks
  passed.

## Failed Run 30749186790

- Fix commit: `e1ecf8f`
- Workflow:
  `https://github.com/zengwenliang416/thesis-forge/actions/runs/30749186790`
- The native source override succeeded: the editor loaded the fixture, accepted
  keyboard focus, moved to the end, and received the acceptance marker.
- Web, Python, frozen sidecar, offline verification, MSI/NSIS construction,
  desktop distribution verification, MSI installation, installed app launch,
  loopback WebView2 CDP, and process capture all passed again.
- The installed acceptance then timed out waiting for the `保存文稿` secondary
  button to become visible.

## Responsive Toolbar Root Cause

- `ProductBar` always renders the save and validate controls, but the approved
  responsive contract hides non-open secondary actions at CSS viewport widths
  of `1120px` or less.
- The Windows runner kept the native app alive and the editor accepted the
  marker, so this was not a picker, crash, or CDP failure.
- The native window is configured as `1440x900`, but Windows DPI scaling can
  expose a CSS viewport inside the compact-toolbar breakpoint. The acceptance
  script incorrectly required the hidden control to be visible instead of
  exercising the existing keyboard save path.

## Responsive Acceptance TDD Fix

- RED:
  `.venv/bin/python -m pytest tests/test_desktop_distribution.py -q` returned
  `1 failed, 19 passed` because the acceptance lacked the responsive
  visibility branch, `Ctrl+S` fallback, and failure evidence artifacts.
- GREEN:
  the Windows script now waits for `dirty`, clicks save when visible, otherwise
  uses the existing `Ctrl+S` user path, and records whether validation used the
  visible button or the real post-save preview refresh.
- GREEN:
  a new `minimum-desktop-chromium` Playwright regression proves that the
  intentionally hidden save control still persists through `Ctrl+S` and returns
  the workbench to the synchronized populated state.
- Failure handling now writes `windows-native-failure.png`,
  `windows-native-failure.html`, and `windows-native-failure.json` before
  closing WebView2.
- Full local regression returned Python `254 passed`, frontend unit `53 passed`,
  browser `15 passed` with `18` intentional skips, real HTTP `1 passed`, and
  Rust protocol `11 passed`. Production build, Ruff, lint, typecheck, Cargo
  fmt/check, pip check, strict OpenSpec, CodeGraph sync, and whitespace checks
  passed.

## Failed Run 30750899399

- Fix commit: `a3453bc`
- Workflow:
  `https://github.com/zengwenliang416/thesis-forge/actions/runs/30750899399`
- Web, Python, frozen sidecar, offline verification, MSI/NSIS construction,
  desktop distribution verification, MSI installation, installed app launch,
  loopback WebView2 CDP, native source opening, and complete fixture loading all
  passed.
- The installed acceptance focused the textarea through the real `Ctrl+K`
  shortcut, but Playwright's WebView2 CDP `type()` sequence did not insert the
  acceptance marker.
- Failure JSON recorded a `1028x749` CSS viewport, active `TEXTAREA`, shell
  state `populated`, disabled hidden save button, editor length `3469`, and
  `hasAcceptanceMarker: false`.
- The screenshot and captured HTML confirmed the complete fixture remained
  unchanged. This rules out the picker, React reducer, save command, sidecar,
  and installed package as the failure source.

## Controlled Input TDD Fix

- The minimum-desktop Playwright regression now follows the same acceptance
  path: `Ctrl+K` focuses the controlled editor, the original source is
  preserved while text is appended, the workbench enters `dirty`, the
  responsive toolbar hides save, and `Ctrl+S` persists the exact edited text.
- The installed Windows acceptance uses Playwright `fill()` for the controlled
  textarea because WebView2 CDP can acknowledge key events without inserting
  their text. It separately verifies that the marker entered the DOM and that
  React changed the shell to `dirty` before exercising the real save shortcut.
- Fix commit `9e84381` passed `254` Python tests, `20` desktop distribution
  tests, `53` frontend unit tests, `15` browser tests with `18` intentional
  skips, `1` real HTTP test, and `11` Rust protocol tests.
- Ruff, frontend lint/typecheck/build, Cargo fmt/check, pip check, strict
  OpenSpec validation, CodeGraph sync, and Git whitespace checks passed.

## Failed Run 30752527630

- Fix commit: `9e84381`
- Workflow:
  `https://github.com/zengwenliang416/thesis-forge/actions/runs/30752527630`
- macOS completed successfully. Windows passed Web, Python, frozen sidecar,
  offline verification, MSI/NSIS construction, desktop distribution
  verification, MSI installation, installed app launch, CDP, native source
  opening, controlled editor input, marker insertion, and dirty-state
  transition.
- Failure JSON recorded shell state `dirty`, editor length `3505`,
  `hasAcceptanceMarker: true`, and a present, enabled, responsive-hidden save
  button.
- The acceptance failed because Playwright `getByRole()` excludes the hidden
  button from its role query, so `save.count()` returned `0` even though the
  captured DOM contained exactly one `aria-label="保存文稿"` button.

## Hidden Control Locator TDD Fix

- The minimum-desktop regression now proves the save control has count `1`,
  remains hidden, and remains enabled before `Ctrl+S` persists the exact edited
  text.
- The installed Windows acceptance locates responsive-hidden save and validate
  controls through their stable `aria-label` DOM selectors. Visible controls
  still use click interaction; hidden save continues through the real
  `Ctrl+S` path.
- Fix commit `3144dba` passed `254` Python tests, `20` desktop distribution
  tests, `53` frontend unit tests, `15` browser tests with `18` intentional
  skips, `1` real HTTP test, and `11` Rust protocol tests.
- Ruff, frontend lint/typecheck/build, Cargo fmt/check, pip check, strict
  OpenSpec validation, CodeGraph sync, and Git whitespace checks passed.

## Billing-Blocked Run 30753977917

- Fix commit: `3144dba`
- Workflow:
  `https://github.com/zengwenliang416/thesis-forge/actions/runs/30753977917`
- Both Windows and macOS matrix jobs failed before any step started. GitHub
  recorded `runner_id: 0`, zero billable milliseconds, and one annotation per
  job stating that recent account payments failed or the Actions spending
  limit must be increased.
- This run did not execute checkout, tests, packaging, installation, or native
  acceptance, so it is an external GitHub billing gate rather than evidence
  for or against commit `3144dba`.
- This run remains useful failure provenance, but it is not a completion gate.
  The user explicitly selected local native development and testing as the
  acceptance authority instead of GitHub Actions.

## Local Native Acceptance Pass

- Authority date: `2026-08-02`.
- Native host: Windows 11 Pro ARM64 in Parallels VM `报销必备 (1)`.
- Product under test:
  `C:\Program Files\ThesisForge\thesisforge-desktop.exe`, installed from the
  generated ARM64 MSI.
- The VM network adapter `net0` was disconnected. The application also ran with
  `THESISFORGE_BLOCK_NETWORK=1`, proxy/API-key/token variables removed, and only
  loopback WebView2 CDP enabled on `127.0.0.1:9222`.
- Task Scheduler launched the acceptance under the logged-in
  `PB82\wenliang_zeng` interactive token with Node `v22.18.0`; the captured root
  application PID was `1632`, and its WebView2 child used the same user profile.
- The installed Tauri application exposed `__TAURI_INTERNALS__`, runtime
  `tauri`, the `本地桌面` label, and the shared light-theme `zh-CN` workbench.
- Playwright opened the copied complete example, focused the editor through
  `Ctrl+K`, appended `<!-- windows native acceptance -->`, observed the dirty
  state, saved the source, validated it, built DOCX, and observed
  `构建完成`.
- The final workbench state was `populated`, the viewport was `1156x900`, the
  reduced-motion rule was present, and the screenshot shows the outline,
  Markdown editor, structure preview, template selector, runtime label, and
  completed build state.
- Generated DOCX:
  `development/tasks/008-cross-platform-distribution-acceptance/evidence/windows-native-thesis.docx`,
  `187088` bytes, SHA-256
  `765158a6952de5f400a9c99bc685442db613844286f7187940479d462c32e10b`.
- Direct package inspection confirmed TOC, SEQ, REF, PAGE fields, paired
  bookmarks, drawing/media, table, OMML, footnotes, headers, footers, and three
  sections.

## Native Installer And Distribution Evidence

- MSI:
  `22564864` bytes, SHA-256
  `f775a887682ee7a9ee1a0d2312c799e307e20e4bf9bde2ca9b82655def420276`.
- NSIS:
  `21263132` bytes, SHA-256
  `9692f39d61bf990b6c6da2d8f5ce224d2ed92b91c84280deedc474380a9cf60c`.
- MSI summary template: `Arm64;0`; installed app and sidecar both report PE
  machine `0xAA64`.
- Installed app:
  `9486848` bytes, SHA-256
  `a906edb5d55e8ef4efa2432f1716382a101b77497cb136edbffbb1668b37412f`.
- Installed sidecar:
  `19236629` bytes, SHA-256
  `6b60553f925706edc9dab8b2ee326dc8a9f6c9425f13d0064384e16ac32136a0`.
- MSI registration records ThesisForge `0.1.0` under
  `C:\Program Files\ThesisForge`; the earlier NSIS install records the same
  version under the current user's local application directory.
- The disconnected Windows verifier returned `ok: true` for the ARM64 sidecar,
  Web production build, MSI, NSIS, and managed sidecar. It reran
  inspect/preview/validate, cancellation, ordered five-stage build, valid DOCX,
  reopen, credential removal, and outbound socket blocking.

## Evidence Files

- `windows-native-acceptance.json`
- `windows-native-task-result.json`
- `windows-native-manifest.json`
- `windows-native-acceptance.png`
- `windows-native-thesis.docx`
- `windows-processes-before-stop.json`
- `windows-cdp-endpoint.json`
- `windows-distribution-verifier-result.json`
- `windows-distribution-verifier.log`

The Windows guest local clock displayed the future date `2026-08-03`; host date
authority and every recorded UTC timestamp remain on `2026-08-02`.
