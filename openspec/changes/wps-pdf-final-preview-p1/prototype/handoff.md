# Prototype Handoff: wps-pdf-final-preview-p1

## Approved Branch Variant

- Branch: `ui-html`
- Variant: `dual-preview-final-layout-v1`
- Approval: user explicitly approved on `2026-08-11`.

## Screens Or Flows

- Existing ThesisForge workbench right rail with “结构预览 / 最终版式” switching.
- `FLOW-BUILD`: successful DOCX publication followed by optional engine-labelled PDF export.
- `FLOW-FINAL-PREVIEW`: resolve automatic PDF or select WPS PDF, render, and track freshness.

## Components To Create

- `PdfPreviewArtifact`
- `PdfPreviewExporter`
- `LibreOfficePdfPreviewExporter`
- `FinalLayoutPreview`
- `PreviewModeControl`

## Components To Reuse

- `ApplicationDependencies`
- `BuildResult`
- `WorkbenchCommandDispatcher`
- `WebWorkspaceRuntime`
- `WorkbenchHttpApp`
- `WorkbenchTransport`
- `WorkspaceState`
- `PaperPreview`
- `PanelHeader`

## Extraction Targets

- Reuse LibreOffice executable discovery and bounded process cleanup.
- Keep one strict final-preview descriptor and reducer state machine for Web and Tauri.
- Keep one object URL lifecycle for automatic and imported PDF bytes.

## API Contracts

- `PdfPreviewExporter.export(docx_path, pdf_path) -> PdfPreviewArtifact | None`
- `BuildResult.final_preview`
- `build-event:output.finalPreview`
- `GET /api/v1/workspaces/{workspace_id}/files/{file_name}`
- Tauri `pick_pdf_preview` and `read_pdf_preview`
- `WorkbenchTransport.resolveFinalPreview` and `pickFinalPreview`

## Data Flows

- DOCX output -> optional LibreOffice conversion -> PDF validation -> atomic derived artifact.
- Web preview descriptor -> workspace-bound GET -> PDF bytes -> object URL -> viewer.
- Desktop build request or picker -> restricted Tauri read -> PDF bytes -> object URL -> viewer.

## State Behavior

- Loading: building state keeps DOCX progress visible and explains that final PDF is pending.
- Empty: no build or selected PDF shows the build/select recovery actions.
- Ready: PDF renders with truthful `LibreOffice PDF` or `WPS PDF` label.
- Stale: prior PDF remains inspectable but displays an explicit “预览已过期” banner.
- Error: PDF failure does not hide successful DOCX output and offers rebuild/select actions.
- Disabled: missing Office exporter disables automatic PDF only, not the core build.
- Permission: Web workspace and Tauri picker/read failures are explicit and do not expose paths.

## Theme And Locale Policy

- Theme support: `light-only`
- Theme modes shown in prototype: `light`
- Theme toggle: intentionally omitted
- Internationalization: disabled
- Locales shown in prototype: fixed `zh-CN` copy
- Default locale: `zh-CN`
- Locale switcher: intentionally omitted

## Out Of Scope Items

- HTML reimplementation of Word/WPS pagination.
- Undocumented WPS UI/private API automation.
- Cross-engine pixel-identical claims.
- PDF editing, annotation, search and thumbnail navigation.
- Network conversion services.

## Required Tests

- Python exporter, PDF validation, atomic replacement and non-fatal failure tests.
- Runtime DTO and Web artifact security tests.
- Tauri picker/binary reader and path authorization tests.
- Frontend descriptor, reducer freshness, component state and object URL cleanup tests.
- Web/Tauri E2E and WPS page-by-page sensory comparison.

## Open Risks

- Browser/WebView native PDF controls can differ while page rendering remains authoritative.
- LibreOffice startup can add bounded latency.
- Large desktop PDFs cross Tauri binary IPC.
- WPS provenance is based on explicit user selection, not unreliable PDF metadata inference.
