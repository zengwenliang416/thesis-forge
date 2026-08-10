# Task Brief: 001-toc-field-structure

## Goal

用户构建的 DOCX 始终保留独立“目录”标题和下一段真实可编辑 TOC field，更新 field 不会
删除标题。

## Parent Artifacts

- `openspec/changes/automatic-docx-toc-refresh-p1/requirements.md`
- `openspec/changes/automatic-docx-toc-refresh-p1/acceptance.md`
- `openspec/changes/automatic-docx-toc-refresh-p1/prototype/handoff.md`

## Vertical Slice

从 `TocInstruction` 到 `document.xml` 完成一个可直接检查的 DOCX 结果：标题段落、
field 段落、dirty 标记和 update-fields 设置全部正确。

## In Scope

- 修改 `renderer.py` 的 `TocInstruction` 分支。
- 增加标题/field 分段、顺序、样式、field characters、dirty 和 update-fields OOXML 测试。
- 保留现有 TOC level style 生成行为。

## Out Of Scope

- Office executable discovery、UNO、subprocess 和 build finalization。
- Parser、Domain、Compiler、RenderPlan、模板 schema 和 UI。

## Files Allowed

- `src/thesis_forge/renderers/docx/renderer.py`
- `tests/test_docx_renderer.py`
- `openspec/changes/automatic-docx-toc-refresh-p1/development/tasks/001-toc-field-structure/*`
- `openspec/changes/automatic-docx-toc-refresh-p1/development/*.jsonl`

## Interfaces / Seams

- Existing `TocInstruction`.
- Existing `_semantic_word_style(..., "toc.title")`.
- Existing `add_complex_field` and `set_update_fields`.

## Components To Create

- No new production component.

## Components To Reuse

- `DocxRenderer`
- `add_complex_field`
- `set_update_fields`
- `TFTOCTitle` semantic style

## Components To Extract

- None; the change removes misuse of the existing field helper without duplicating it.

## API / Data Flow Contracts

- `TocInstruction -> standalone title paragraph -> following TOC field paragraph`.
- `DocxRenderer.render(plan, output) -> Path` remains unchanged.

## State / Error / Empty / Loading Behavior

- Loading: not applicable; synchronous in-memory rendering.
- Empty: the field result may be empty before Office refresh, but the field object remains valid.
- Error: existing `DocxRenderError` normalization remains unchanged.
- Disabled: not applicable.
- File access: only the explicit Renderer output path.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_docx_renderer.py -k toc`
- `.venv/bin/ruff check src/thesis_forge/renderers/docx/renderer.py tests/test_docx_renderer.py`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not assume WPS or Word will update fields on open.
- Do not use literal title text as a cached TOC field result.
