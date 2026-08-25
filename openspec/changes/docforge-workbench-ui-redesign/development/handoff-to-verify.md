# Development Handoff To Verify: docforge-workbench-ui-redesign

## Implemented Slices

- Visible DocForge brand and generic Markdown-to-Word product language.
- Compact command bar with existing Word template, open, save, check, cancel,
  and DOCX build contracts.
- Desktop outline/editor/Microsoft Word preview canvas with contextual
  diagnostics and output state.
- Minimum-desktop resizers and mobile four-panel navigation.
- macOS packaging, installation, and current Microsoft Word PDF preview.

## Files Changed

- Production UI and tests under `frontend/src/components`, `frontend/e2e`,
  `frontend/src/styles.css`, and `frontend/index.html`.
- Visible desktop metadata in `src-tauri/tauri.conf.json`.
- `design-qa.md` and this change's SpecNav evidence.

## Requirements Covered

- `A1`: visible DocForge general document-workshop identity.
- `A2`: unchanged open/save/check/template/build/cancel/preview transport flow.
- `A3`: approved 1440x1024 three-pane hierarchy and diagnostics.
- `A4`: mobile four-panel navigation without horizontal overflow.
- `A5`: no UI dependency introduced into document compilation layers.

## Prototype Decisions Implemented

- Approved `dual-canvas-docforge` hierarchy, light editorial palette, compact
  command bar, simultaneous desktop panes, and mobile semantic tabs.
- Prototype fixtures, mock data, inline scripts, and hard-coded document
  content were not promoted.

## Components Created / Reused / Extracted

- Reused `WorkbenchApp`, `WorkbenchShell`, `ProductBar`, `StatusStrip`,
  `OutlinePanel`, `MarkdownEditor`, `DualPreviewPanel`, `DiagnosticsPanel`,
  `OutputFeedback`, `PanelHeader`, workspace selectors, diagnostics
  presentation, preview state, and existing Lucide icons.
- No parallel shell, state layer, transport hook, editor dependency, or new
  design-system abstraction was created.

## API / Data Flow Changes

- None. DTOs, protocol version, reducer action semantics, template IDs, build
  intents, output descriptors, Office PDF callbacks, and final-preview
  resolution remain unchanged.

## Tests Added

- Updated focused ProductBar, WorkbenchApp, Preview, Review, build-flow, and
  project-flow component tests.
- Updated desktop/minimum-desktop/mobile Playwright acceptance and workbench
  coverage.
- Preserved the real Python HTTP adapter acceptance with a contract-aligned
  per-test timeout.

## Local Validation

- Frontend: 238 unit tests, typecheck, lint, production build, 16 browser E2E,
  20 intentional matrix skips, and 1 real HTTP E2E passed.
- Desktop: Rust format check, 6 unit tests, and 28 protocol tests passed.
- Spec: strict OpenSpec validation and `git diff --check` passed.
- Visual: desktop and mobile production screenshots passed `design-qa.md`.
- Installed app: `/Applications/ThesisForge.app` is running and the captured
  window shows DocForge plus `Microsoft Word PDF` and `当前 Word 预览`.
- Distribution: the macOS verifier passed `.app`, `.dmg`, offline sidecar,
  cancellation, complete build, DOCX validity, and reopen. Generated and
  installed executables share Mach-O UUID
  `57D2FECE-3578-3CC4-A119-65F95F48BBCB`.
- CodeGraph: `ev-mt8ejd0i` matched the task claim.

## Known Risks

- Windows native WebView2 acceptance was not run on macOS because it requires
  a Windows host and `THESISFORGE_WINDOWS_SOURCE`.
- Internal ThesisForge bundle/package/protocol names intentionally remain
  unchanged under the approved presentation-only rename.
- The installed app is bundle-level ad-hoc signed, so its main executable file
  hash differs from the generated bundle. Matching Mach-O UUID and sidecar
  SHA-256 identify the same verified build.

## Items Requiring Six-Domain Verification

- Confirm factual scope against the actual diff and CodeGraph evidence.
- Confirm static/unit/E2E evidence recorded in `validation-log.jsonl`.
- Confirm desktop/mobile screenshots against the approved reference.
- Confirm installed macOS app evidence and the Microsoft Word preview labels.
- Carry the Windows-only acceptance prerequisite as a platform release risk,
  not as a passed check.
