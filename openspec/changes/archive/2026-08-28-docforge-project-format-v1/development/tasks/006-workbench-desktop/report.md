# Task Report: 006-workbench-desktop

## Status

DONE

Items 6.1 through 6.5 are implemented and covered by automated browser,
frontend, Python adapter, Rust contract, installed macOS, and Microsoft Word
evidence. The task contract requires installed macOS and Word sensory evidence;
native Windows WebView2 remains a broader product-platform follow-up, not a
Task 006 or A9 closure condition.

## Files Changed

- `frontend/src/components/WorkbenchApp.tsx`
- `frontend/src/components/ProductBar.tsx`
- `frontend/src/state/diagnostics.ts`
- `frontend/src/transport/{constants,WorkbenchTransport,dto,runtime,web}.ts`
- `frontend/e2e/{acceptance.spec,workbench.spec,real-http.acceptance,real-http.playwright.config,tauri-windows.acceptance}.ts`
- Frontend component, state, transport, and browser fixtures under
  `frontend/src/**/*.test.*` and `frontend/e2e`
- `frontend/package.json`
- Tauri desktop identity and project-boundary files under `src-tauri`
- `scripts/build_sidecar.py`, `scripts/verify_desktop_distribution.py`, and
  `tests/test_desktop_distribution.py`
- `tests/fixtures/diagnostics-zh-cn-v1.json`
- Task-local SpecNav frozen-test overrides under `openspec/.specnav/overrides`
- `openspec/changes/docforge-project-format-v1/development/tasks/006-workbench-desktop/evidence/macos-native-acceptance.json`
- `openspec/changes/docforge-project-format-v1/development/tasks/006-workbench-desktop/evidence/macos-native-acceptance.png`

## What Changed

- Project opening now requires the canonical `docforge.yaml` manifest and a
  `.md` or `.markdown` source. The frontend keeps rejecting bare Markdown and
  obsolete `thesisforge.yaml` input instead of synthesizing a project.
- The workbench uses DocForge/document terminology, neutral default filenames,
  and the `@docforge/workbench` package identity. The command bar exposes the
  `docforge-standard` template alongside existing academic choices.
- Frontend transport/state fixtures use `docforge.yaml`, `document.md`,
  `document.docx`, and the DocForge protocol constants. Obsolete protocol and
  manifest values remain only in explicit rejection vectors or required
  external acceptance seams.
- Tauri product metadata, sidecar naming, runtime environment variables, and
  project-path rejection tests use the DocForge identity. The adapter continues
  to delegate parsing, validation, compilation, rendering, and finalization to
  the existing application services.
- User-visible diagnostic strings that previously said “论文正文” or
  “论文资源目录” now use neutral “文档” terminology.

## TDD Evidence

- Component and transport tests cover project opening, manifest/source
  pairing, bare-Markdown rejection, obsolete-manifest rejection, neutral
  filenames, dirty/save/build state, stale operations, and output handling.
- The shared diagnostic localization fixture and `ProductBar` project fixture
  were updated with explicit Task 006 frozen-test overrides.
- The real HTTP acceptance uses `docforge-standard`, verifies the
  `X-DocForge-Adapter: python-wsgi` test header, saves through the Python
  HTTP adapter, validates, builds, and verifies the persisted
  `document.md`, `docforge.yaml`, and `document.docx` files.

## Verification Commands

- `pnpm typecheck` -> passed.
- `pnpm lint` -> passed.
- `pnpm test` -> `20` files, `245` tests passed.
- `pnpm exec playwright test --config e2e/real-http.playwright.config.ts`
  -> `1` real Python HTTP adapter test passed.
- `pnpm exec playwright test --config /tmp/thesis-forge-playwright.4174.config.cjs`
  -> `16` passed, `20` intentional matrix skips; the temporary config used
  port `4174` because the default port was occupied.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/adapters -q`
  -> `26` passed.
- `PYTHONPATH=src .venv/bin/python scripts/verify_desktop_distribution.py
  --platform macos --bundle-root src-tauri/target/release/bundle`
  -> `ok: true`; native aarch64 sidecar, offline inspect/validate/preview,
  cancellation, build, reopen, `.app`, and `.dmg` checks passed.
- Installed `DocForge.app` receipt
  -> project picker opened `/tmp/docforge-sensory-valid-006`, diagnostics were
  `0`, the build ended at `构建完成`,
  `/tmp/docforge-sensory-20260827-006/document.docx` was produced
  (`38,520` bytes), and Microsoft Word 16.112 produced
  `document.preview.pdf` (`67,545` bytes, valid `%PDF-` signature). The
  workbench reopened the project and displayed the generated Word preview.
  The updated receipt and screenshot are in
  `evidence/macos-native-acceptance.json`.
- `cargo fmt --check --manifest-path src-tauri/Cargo.toml`,
  `cargo check --manifest-path src-tauri/Cargo.toml`, and
  `cargo test --manifest-path src-tauri/Cargo.toml`
  -> format/check passed; `14` project tests and `32` protocol-contract tests
  passed.
- `git diff --check` -> passed.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/adapters
  tests/test_desktop_distribution.py -q`
  -> `62 passed in 0.81s`.

## Concerns

- The official `pnpm e2e` command did not enter Playwright: an unrelated
  Python `http.server` process (PID `83390`, another project's artifact
  directory) already listened on `127.0.0.1:4173`. The same `36`-test matrix
  passed on isolated port `4174`; the process was intentionally not killed.
- The earlier blocked AppleEvents attempt is superseded by the passing
  installed-app run on 2026-08-27. The current TCC record authorizes
  `com.docforge.workbench` to control `com.microsoft.Word`, and the passing run
  generated and displayed the Word PDF without a new prompt.
- No native Windows WebView2 sensory receipt is available. The delta spec keeps
  Windows as a supported product runtime, so that platform should still run
  its prepared CI acceptance job. However, Task 006 item 6.5 and the
  change-level sensory contract explicitly require the installed macOS package
  and Microsoft Word flow, which are both evidenced here.

## Scope Deviations

- `tests/fixtures/diagnostics-zh-cn-v1.json` was updated because it is the
  executable input contract for the frontend diagnostic localization. The
  change is limited to the one expected message and is recorded by a
  task-local frozen-test override.
- No new screen, layout, theme, locale switcher, compatibility alias, or
  fallback project path was introduced.

## Follow-up Needed

- Run `frontend/e2e/tauri-windows.acceptance.ts` on the prepared Windows host
  as a broader cross-platform product receipt.
- Task 008 must bind the macOS/Word receipt to A9 in the trusted verification
  lifecycle.

## Adjudication

The automated Task 006 slice and installed-macOS evidence satisfy items 6.1
through 6.5, including successful Microsoft Word PDF generation and display.
Windows remains an important product-platform verification surface, but it is
not listed as the Task 006 sensory acceptance gate.
