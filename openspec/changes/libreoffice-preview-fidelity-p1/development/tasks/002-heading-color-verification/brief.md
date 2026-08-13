# Task Brief: 002-heading-color-verification

## Goal

示例模板的一至三级标题在 DOCX 中显式为黑色，完整论文的 LibreOffice PDF 通过字体、
页数和文本审计，并交付可在本机试用的 macOS 应用。

## Parent Artifacts

- `openspec/changes/libreoffice-preview-fidelity-p1/requirements.md`
- `openspec/changes/libreoffice-preview-fidelity-p1/acceptance.md`
- `openspec/changes/libreoffice-preview-fidelity-p1/prototype/handoff.md`

## Vertical Slice

从模板 YAML 到模板模型、Heading OOXML、完整论文 PDF 和已安装应用，完成标题颜色与
真实预览保真的端到端验证。

## In Scope

- 为 Heading 1/2 增加显式黑色，为 Heading 3 补齐黑体、字号、黑色和加粗配置。
- 增加模板加载与 Heading 1/2/3 OOXML 颜色回归。
- 运行完整 Python、Ruff、OpenSpec 和 diff 验证。
- 构建完整论文并用 `pdffonts`、`pdfinfo`、`pdftotext` 审计。
- 构建并覆盖安装 macOS 应用，提供人工测试步骤。

## Out Of Scope

- 新 UI、模板 schema、Renderer 逻辑、字体捆绑和 WPS/Word 自动化。
- 代理执行 UI sensory；用户自行完成界面对照。

## Files Allowed

- `templates/schools/example-university/2026.yaml`
- `tests/test_template.py`
- `tests/test_docx_renderer.py`
- `tests/test_acceptance.py`
- `output/verification/libreoffice-preview-fidelity-p1/*`
- `openspec/changes/libreoffice-preview-fidelity-p1/development/tasks/002-heading-color-verification/*`
- `openspec/changes/libreoffice-preview-fidelity-p1/development/*.jsonl`

## Interfaces / Seams

- Existing `ThesisTemplate` heading styles.
- Existing semantic DOCX style renderer and OOXML style definitions.
- Existing complete-thesis build and macOS packaging commands.

## Components To Create

- No new production component.
- Verification artifacts for the complete DOCX/PDF and installed app.

## Components To Reuse

- Existing template loader and `StyleSpec.color`.
- Existing semantic heading style rendering.
- Existing CLI build, LibreOffice preview exporter, frontend and Tauri packaging.

## Components To Extract

- None; the template already owns heading formatting and tests reuse existing OOXML helpers.

## API / Data Flow Contracts

- `template YAML -> ThesisTemplate -> semantic heading styles -> styles.xml`.
- `complete Markdown -> published DOCX -> preview exporter -> audited PDF`.

## State / Error / Empty / Loading Behavior

- Loading: existing realtime-preview behavior remains unchanged.
- Empty: not applicable to explicit heading styles.
- Error: failed validation or packaging blocks installation completion.
- Disabled: missing LibreOffice would block real PDF evidence, not DOCX build.
- Permission: installation writes only the built app into `/Applications`.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest -p no:cacheprovider tests/test_template.py tests/test_docx_renderer.py tests/test_pdf_preview.py tests/test_acceptance.py`
- `.venv/bin/python -m pytest -p no:cacheprovider`
- `.venv/bin/ruff check .`
- `OPENSPEC_TELEMETRY=0 openspec validate libreoffice-preview-fidelity-p1 --strict --no-interactive --json`
- `pdffonts <pdf> && pdfinfo <pdf> && pdftotext <pdf> -`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not infer heading color from rendered appearance; inspect OOXML.
- Do not infer font success from DOCX declarations; inspect the real PDF.
- Do not claim UI verification; provide the user with exact manual test steps.
