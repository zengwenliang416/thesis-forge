# Development Handoff To Verify: wps-pdf-final-preview-p1

## Implemented Slices

- Optional validated LibreOffice PDF export after successful DOCX publication.
- Secure path-free Web and Tauri PDF artifact access.
- Shared dual-preview UI with freshness, recovery and Blob lifecycle handling.
- Documentation plus current HUT DOCX/LibreOffice PDF evidence.

## Files Changed

- Application, adapter, Tauri, frontend and test files listed in the four task
  reports.
- Documentation updates under `docs/`.
- Current evidence under
  `output/verification/wps-pdf-final-preview-p1/`.

## Requirements Covered

- `A1`: structural/final switching, real PDF Blob viewer and truthful engine
  labels are implemented and covered by component/E2E/browser evidence.
- `A2`: atomic validated best-effort LibreOffice export is implemented without
  changing DOCX success semantics.
- `A3`: shared Web/Tauri WPS selection and stale behavior are implemented;
  exact current WPS-exported PDF sensory remains for verification.

## Prototype Decisions Implemented

- Used a segmented `结构 / 最终版式` control.
- Preserved stale PDFs with an explicit warning instead of silently replacing
  or hiding them.
- Kept Office engine labels truthful and avoided WPS automation.
- Kept mobile preview as a dedicated workbench panel without horizontal
  overflow.

## Components Created / Reused / Extracted

- Created `PdfPreviewArtifact`, `PdfPreviewExporter`,
  `LibreOfficePdfPreviewExporter`, final-preview transport parsing,
  `PreviewModeControl`, `FinalLayoutPreview` and `usePdfObjectUrl`.
- Reused build service sequencing, Office process cleanup, workspace runtime,
  transport abstraction, panel shell and reducer generation guards.
- Extracted one adapter-level `final_preview_build_service` so the core/CLI
  default remains deterministic and preview-capable app runtimes opt in.

## API / Data Flow Changes

- Published DOCX -> optional validated `.preview.pdf` -> path-free descriptor.
- Web descriptor -> workspace-bound PDF GET -> bytes -> Blob URL.
- Tauri descriptor/selection -> authorized binary IPC -> bytes -> Blob URL.
- Source/template revision changes move a ready PDF to stale while stale
  operation generations are rejected.

## Tests Added

- Added exporter, build integration, path traversal, symlink, signature, DTO,
  Tauri command, transport, reducer, component and E2E coverage.
- Full results: Python `441 passed`; frontend `75 passed`; Playwright
  `16 passed / 20 intentional skips`; Rust `22 passed`.

## Local Validation

- Ruff, frontend typecheck/lint/build, Rust fmt/test, OpenSpec strict and
  `git diff --check` passed.
- Real HUT output: valid DOCX and LibreOffice 26.2.3.2 PDF, 12 A4 pages, qpdf
  clean, all pages visually inspected without clipping.
- Browser sensory: desktop and 390px final-layout interaction, no console
  warnings or horizontal overflow.

## Known Risks

- No exact WPS-exported PDF was available in this current run. LibreOffice
  pagination is not treated as WPS evidence.
- Native packaged macOS and Windows PDF viewer behavior is not yet target-host
  certified.
- CodeGraph index is advisory-stale relative to the dirty worktree and should
  be refreshed before verification claims.

## Items Requiring Six-Domain Verification

- Independently rerun static, unit, redteam, e2e and sensory domains from the
  committed state.
- Open an exact WPS-exported PDF through the native picker and compare every
  page in the right viewer.
- Run packaged macOS and native Windows acceptance, including permission
  failures and PDF viewer rendering.
