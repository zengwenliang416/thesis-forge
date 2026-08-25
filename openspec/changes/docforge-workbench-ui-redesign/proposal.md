## Why

The current workbench is functionally capable of editing Markdown, validating
content, selecting templates, previewing Microsoft Word output, and building
DOCX files, but its visible information architecture still presents the product
as an academic thesis compiler. The product now needs a general document
workshop that serves reports, proposals, manuals, contracts, and academic papers
without changing the deterministic compiler architecture.

## What Changes

- Rename the visible product brand to `DocForge` with the subtitle
  “Markdown → Word 文档工坊”.
- Replace thesis-only and school-only labels, empty states, accessibility labels,
  template labels, preview copy, and output copy with general document language.
- Recompose the desktop workbench into a compact command bar, document outline,
  Markdown editor, Microsoft Word layout preview, contextual diagnostics, and a
  narrow output status region.
- Keep the existing mobile outline/editor/preview/diagnostics panel navigation
  and make it match the new visual hierarchy.
- Keep current workspace state, template IDs, transport DTOs, preview/build
  flows, cancellation, Office PDF selection, and deterministic core services.
- Add focused component, responsive, browser, accessibility, and visual
  regression coverage for the redesigned shell.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `desktop-workbench`: Generalize the visible workbench from an academic thesis
  surface to a DocForge Markdown-to-Microsoft-Word document workshop while
  preserving the existing cross-runtime state and transport behavior.

## Impact

- Affected production files are limited to `frontend/src/components/`,
  `frontend/src/styles.css`, frontend tests, Playwright tests, and visible
  desktop application metadata or documentation where the product title is
  presented.
- No Python domain, Parser, Validator, Compiler, RenderPlan, DOCX Renderer,
  transport protocol, template ID, database, account, AI, or network behavior
  changes.
- No new runtime dependency is required; the frontend continues to use React,
  TypeScript, Vite, and the existing icon library.
