# Task Brief: 001-preview-font-adaptation

## Goal

macOS 用户的 LibreOffice 实时 PDF 使用已验证的宋体和黑体替代字体，而正式 DOCX 和
Windows/Linux 转换行为保持不变。

## Parent Artifacts

- `openspec/changes/libreoffice-preview-fidelity-p1/requirements.md`
- `openspec/changes/libreoffice-preview-fidelity-p1/acceptance.md`
- `openspec/changes/libreoffice-preview-fidelity-p1/prototype/handoff.md`

## Vertical Slice

从输入 DOCX 到一次性适配副本、LibreOffice 转换、PDF 校验和原子发布，完成一个可独立
测试的预览字体适配流程。

## In Scope

- 在 `application/pdf_preview.py` 中新增纯平台字体别名解析。
- 使用 `zipfile` 重打包一次性 DOCX，只改 OOXML 精确字体属性值。
- macOS 映射 `宋体 -> Source Han Serif SC`、`黑体 -> PingFang SC`。
- 保留现有超时、进程清理、PDF 校验、旧 PDF 保留和原子替换。
- LibreOffice 目录刷新后恢复渲染器生成的样式和字体表，避免污染正式 DOCX。
- 覆盖属性级替换、正文文本不变、跨平台分支、输入字节不变和清理测试。

## Out Of Scope

- 模板 schema、Renderer、Web/Tauri/React 和 Office refresh 的公开 contract。
- 字体捆绑、全局 LibreOffice 配置、WPS/Word 自动化和跨引擎像素等价。

## Files Allowed

- `src/thesis_forge/application/pdf_preview.py`
- `src/thesis_forge/application/office_refresh.py`
- `tests/test_pdf_preview.py`
- `tests/test_application_services.py`
- `output/verification/libreoffice-preview-fidelity-p1/*`
- `openspec/changes/libreoffice-preview-fidelity-p1/development/tasks/001-preview-font-adaptation/*`
- `openspec/changes/libreoffice-preview-fidelity-p1/development/*.jsonl`

## Interfaces / Seams

- Existing `PdfPreviewExporter.export(docx_path, pdf_path)`.
- Internal pure `preview_font_aliases(platform)` seam.
- Existing isolated LibreOffice profile and process lifecycle.
- Existing `refresh_document_safely` build-finalization boundary.

## Components To Create

- Pure platform font alias resolver.
- Preview-only disposable DOCX package adapter.

## Components To Reuse

- `LibreOfficePdfPreviewExporter`
- `LibreOfficeDocumentRefresher`
- `discover_libreoffice_executable`
- `start_office_process`
- `terminate_office_process_tree`
- Existing PDF validation and atomic replacement flow.

## Components To Extract

- Keep exact OOXML attribute rewriting in one helper; do not duplicate ZIP or alias logic.

## API / Data Flow Contracts

- `source DOCX -> optional macOS adapted DOCX -> LibreOffice -> validated PDF`.
- Adaptation failure returns preview unavailable and never mutates source DOCX or prior PDF.

## State / Error / Empty / Loading Behavior

- Loading: existing valid PDF remains until atomic replacement succeeds.
- Empty: non-macOS or an empty alias map converts the source DOCX directly.
- Error: adaptation or conversion failure returns `None` and preserves prior output.
- Disabled: missing LibreOffice remains a no-op for preview only.
- Permission: only the source DOCX is read; adapted DOCX and profile are temporary.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest -p no:cacheprovider tests/test_pdf_preview.py`
- `.venv/bin/python -m pytest -p no:cacheprovider tests/test_application_services.py -k refresh`
- `.venv/bin/ruff check src/thesis_forge/application/pdf_preview.py src/thesis_forge/application/office_refresh.py tests/test_pdf_preview.py tests/test_application_services.py`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not assume unrestricted string replacement is safe for thesis text.
- Do not assume macOS font aliases are valid on Windows or Linux.
- Do not assume a zero LibreOffice exit code proves a valid PDF.
