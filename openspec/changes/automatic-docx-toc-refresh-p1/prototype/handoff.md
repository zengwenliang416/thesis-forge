# Prototype Handoff: automatic-docx-toc-refresh-p1

## Approved Branch Variant

- Approved branch: `component-seam`.
- Approved variant: `toc-field-office-refresh-seam-v1`.
- User approval recorded on August 10, 2026 through the explicit instruction “补齐这个缺口” after
  the automatic TOC defect and solution were presented.
- Promotion remains subject to the SpecNav development entry gate.

## Screens Or Flows

- No UI screen change.
- `FLOW-BUILD`: render temporary DOCX -> optional local Office refresh -> package validation ->
  atomic replace.

## Components To Create

- `DocumentRefresher`
- `LibreOfficeDocumentRefresher`
- cross-platform LibreOffice executable resolver
- isolated UNO refresh runner

## Components To Reuse

- `TocInstruction`
- `DocxRenderer`
- DOCX field helpers and `w:updateFields`
- `ApplicationDependencies`
- temporary output, package validation and atomic replace services

## Extraction Targets

- Keep one executable discovery implementation for macOS, Linux and Windows.
- Keep one isolated Office process/profile lifecycle.
- Keep one application refresher hook shared by CLI, Web and Tauri.

## API Contracts

- Existing `DocxRenderer.render(plan, output) -> Path`.
- New internal `DocumentRefresher.refresh(path) -> bool`.
- Existing `build_service(...) -> BuildResult`.
- Existing CLI, HTTP and Tauri build output contracts remain unchanged.

## Data Flows

- `TocInstruction` -> standalone title paragraph + following TOC field paragraph.
- Temporary DOCX -> optional LibreOffice hidden load -> index/field update -> same-file save.
- Refreshed or untouched temporary DOCX -> package validation -> atomic final output.

## State Behavior

- Loading: one bounded optional local Office process per build.
- Empty: documents without a TOC still use the same application pipeline without index changes.
- Error: optional refresh failure falls back to the valid rendered DOCX; mandatory package or
  replace failure remains a finalization error.
- Disabled: executable discovery miss disables refresh without disabling build.
- Permission: input read-only; explicit output, bounded temporary DOCX/profile and owned local
  process only.

## Theme And Locale Policy

- Theme support: `light-only`, no UI impact.
- Theme modes shown in prototype: none; component-seam branch.
- Theme toggle: intentionally omitted.
- Internationalization: disabled.
- Locales shown in prototype: fixed `zh-CN` contract text only.
- Default locale: `zh-CN`.
- Locale switcher: intentionally omitted.

## Out Of Scope Items

- Production UI and template editor changes.
- Parser, Domain, Compiler or RenderPlan page-number calculation.
- Static fake TOC text.
- Microsoft Word/WPS private automation.
- Mandatory LibreOffice installation or pixel-identical pagination.

## Required Tests

- Standalone TOC title and following real dirty field OOXML.
- macOS, Linux and Windows executable discovery.
- Missing runtime no-op and injected refresh call order.
- Startup, connection, update, save, timeout and corrupt-output failure protection.
- Cancellation and previous-output preservation.
- Real complete HUT build through local LibreOffice with cached TOC entry inspection.

## Open Risks

- LibreOffice startup latency and process cleanup.
- Office-suite pagination differences.
- Best-effort refresh status is not exposed in the current `BuildResult`.
