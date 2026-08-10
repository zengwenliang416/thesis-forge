# Task Brief: 003-build-finalization-verification

## Goal

CLI、Web 和 Tauri 共用的 build flow 在发布 DOCX 前尝试刷新目录，并在刷新后执行包校验
和原子替换；完整 HUT 论文具有可见目录条目和页码。

## Parent Artifacts

- `openspec/changes/automatic-docx-toc-refresh-p1/requirements.md`
- `openspec/changes/automatic-docx-toc-refresh-p1/acceptance.md`
- `openspec/changes/automatic-docx-toc-refresh-p1/prototype/handoff.md`

## Vertical Slice

把已验证的 Renderer 和 refresher 接入 application finalization，覆盖成功、缺失、失败、
损坏、取消和旧输出保护，并完成文档与真实 HUT DOCX 验收。

## In Scope

- `ApplicationDependencies` 注入 document refresher。
- `build_service` 在 render 后、package validation 前调用 refresher。
- 增加调用顺序、no-op、failure、corrupt-output、cancellation 和 prior-output tests。
- 更新 `docs/TEMPLATE_SPEC.md`。
- 本机真实 LibreOffice 完整 HUT 构建和 OOXML/package 检查。
- 完整 pytest、Ruff、OpenSpec、CodeGraph 和 SpecNav handoff。

## Out Of Scope

- 新增 UI 配置、公开 DTO 字段或 `BuildResult` warning。
- Word/WPS private automation、安装器和部署变更。

## Files Allowed

- `src/thesis_forge/application/services.py`
- `src/thesis_forge/application/office_refresh.py`
- `tests/test_application_services.py`
- `tests/test_docx_renderer.py`
- `docs/TEMPLATE_SPEC.md`
- `output/verification/automatic-docx-toc-refresh-p1/*`
- `openspec/changes/automatic-docx-toc-refresh-p1/**`

## Interfaces / Seams

- `ApplicationDependencies.document_refresher`.
- `render -> refresh -> validate package -> replace output`.
- Existing progress stages and `BuildResult` contract remain unchanged.

## Components To Create

- No additional production component beyond task 002.

## Components To Reuse

- `DocumentRefresher`
- `temporary_output_path`
- `validate_docx_package`
- `replace_output`
- existing cancellation and progress boundaries

## Components To Extract

- None; keep orchestration in `build_service` and runtime mechanics in `office_refresh.py`.

## API / Data Flow Contracts

- `FLOW-BUILD`: render temporary DOCX -> optional refresh -> mandatory validate -> atomic replace.
- Optional refresh failure keeps the Renderer output; mandatory validation failure preserves prior output.

## State / Error / Empty / Loading Behavior

- Loading: existing `FINALIZE` progress stage covers refresh and publication.
- Empty: no LibreOffice or no document indexes still produces valid DOCX.
- Error: optional refresher errors do not fail build; invalid post-refresh package does.
- Disabled: injected no-op refresher supports deterministic tests and hosts without Office.
- File access: only the build temporary DOCX, owned profile and explicit final output.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_docx_renderer.py -k toc`
- `.venv/bin/python -m pytest tests/test_application_services.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `OPENSPEC_TELEMETRY=0 openspec validate automatic-docx-toc-refresh-p1 --strict --no-interactive --json`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not assume successful refresher return implies a valid DOCX; package validation is mandatory.
- Do not assume LibreOffice pagination exactly matches Word or WPS.
- Do not alter existing progress-stage count or public build DTOs in this slice.
