# DocForge Workbench Design QA

Date: 2026-08-25

## Scope

- Visible product name: `DocForge`
- Product subtitle: `Markdown → Word 文档工坊`
- Reference:
  `openspec/changes/docforge-workbench-ui-redesign/assets/docforge-workbench-reference.png`
- Production screenshots:
  - `openspec/changes/docforge-workbench-ui-redesign/verification/desktop-1440x1024.png`
  - `openspec/changes/docforge-workbench-ui-redesign/verification/mobile-390x844.png`
  - `openspec/changes/docforge-workbench-ui-redesign/verification/installed-macos-word-preview.png`

## Desktop 1440x1024

- Top command bar keeps the brand, document identity, Word template selector,
  open, save, validate, and DOCX generation controls visible without overlap.
- The outline, Markdown editor, and Word preview remain visible as one
  three-column workbench.
- The diagnostics drawer remains inside the viewport and does not get pushed
  below long preview content.
- Measured document size: `1440x1024`.
- Horizontal overflow: `false`.
- Vertical page overflow: `false`.
- Workspace status: `文档、模板与预览已同步`.

## Mobile 390x844

- The compact header keeps the `DF` mark, `DocForge`, open, and DOCX generation
  controls visible without overlap.
- Outline, editor, preview, and diagnostics remain available through the
  four-tab mobile navigation.
- The Word preview panel fits the viewport and scrolls internally.
- Measured document size: `390x844`.
- Horizontal overflow: `false`.
- Vertical page overflow: `false`.
- Workspace status: `文档、模板与预览已同步`.

## Findings

- Fixed a desktop height regression where a long structure preview expanded
  the page beyond the viewport and pushed the diagnostics drawer below the
  first screen.
- The fix gives `.app-shell` a definite `100dvh` height so the workbench grid
  constrains long content to panel-level scrolling.
- Added a Playwright regression assertion that the populated desktop shell and
  document remain within the viewport.
- Rebuilt and installed `/Applications/ThesisForge.app`; the installed window
  shows the visible `DocForge` name while the internal bundle display name and
  identifier remain unchanged by the approved presentation-only rename.
- The installed-app screenshot directly shows `Microsoft Word PDF`,
  `当前 Word 预览`, `Microsoft Word 桌面`, and a rendered multi-page Word PDF.

## Result

final result: passed
