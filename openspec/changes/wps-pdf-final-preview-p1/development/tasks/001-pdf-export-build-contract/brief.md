# Task Brief: 001-pdf-export-build-contract

## Goal

成功 DOCX 构建可附带经过验证、真实标注 `LibreOffice PDF` 的最终预览；Office 缺失或
失败时 DOCX 仍成功。

## Parent Artifacts

- `openspec/changes/wps-pdf-final-preview-p1/requirements.md`
- `openspec/changes/wps-pdf-final-preview-p1/acceptance.md`
- `openspec/changes/wps-pdf-final-preview-p1/prototype/handoff.md`

## Vertical Slice

从已发布 DOCX 到 typed `BuildResult.final_preview` 打通自动 PDF 导出、校验、原子发布和
失败降级。

## In Scope

- 新增 `application/pdf_preview.py` 的 artifact、protocol 和 LibreOffice exporter。
- 复用 LibreOffice runtime discovery/process cleanup。
- 扩展 `BuildResult`、`ApplicationDependencies` 和 `build_service`。
- 增加 exporter 与 build integration 测试。

## Out Of Scope

- HTTP/Tauri 文件读取、React UI、WPS 自动化和文档更新。
- Parser、Domain、Compiler、RenderPlan 和 DOCX Renderer。

## Files Allowed

- `src/thesis_forge/application/*`
- `tests/test_pdf_preview.py`
- `tests/test_application_services.py`
- `openspec/changes/wps-pdf-final-preview-p1/development/tasks/001-pdf-export-build-contract/*`
- `openspec/changes/wps-pdf-final-preview-p1/development/*.jsonl`

## Interfaces / Seams

- `PdfPreviewExporter.export(docx_path, pdf_path)`.
- `BuildResult.final_preview`.
- Existing LibreOffice executable discovery and bounded process cleanup.

## Components To Create

- `PdfPreviewArtifact`
- `PdfPreviewExporter`
- `LibreOfficePdfPreviewExporter`

## Components To Reuse

- `ApplicationDependencies`
- `build_service`
- `discover_libreoffice_executable`
- application atomic output helpers

## Components To Extract

- Shared LibreOffice command/process utilities only when required by both refresh and PDF export.

## API / Data Flow Contracts

- Published DOCX -> temporary PDF -> signature/size validation -> atomic `.preview.pdf`.
- PDF failure returns no ready artifact and never raises a DOCX build failure.

## State / Error / Empty / Loading Behavior

- Loading: remains inside existing `finalize` progress stage.
- Empty: no exporter or no output yields `final_preview=None`.
- Error: timeout, crash, missing output or invalid PDF is a non-fatal preview miss.
- Disabled: missing LibreOffice disables automatic PDF only.
- Permission: derived PDF write failure is reported unavailable without altering DOCX.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_pdf_preview.py tests/test_application_services.py`
- `.venv/bin/ruff check src/thesis_forge/application tests/test_pdf_preview.py tests/test_application_services.py`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not assume LibreOffice is installed or conversion success implies a valid PDF.
- Do not label any non-WPS artifact as WPS PDF.
