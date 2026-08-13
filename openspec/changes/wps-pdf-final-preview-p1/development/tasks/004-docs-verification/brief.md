# Task Brief: 004-docs-verification

## Goal

用户手册准确说明双预览和 Office 引擎边界，完整 HUT 文稿在自动 PDF 与 WPS PDF 流程中
获得可重复的测试和人工证据。

## Parent Artifacts

- `openspec/changes/wps-pdf-final-preview-p1/requirements.md`
- `openspec/changes/wps-pdf-final-preview-p1/acceptance.md`
- `openspec/changes/wps-pdf-final-preview-p1/prototype/handoff.md`

## Vertical Slice

更新操作文档，运行全栈验证，生成完整 DOCX/PDF，并完成 WPS 与右侧最终预览逐页检查。

## In Scope

- 更新用户手册和维护/架构文档。
- 运行 Python、frontend、Rust、HTTP、E2E、Ruff、OpenSpec、CodeGraph 和 diff checks。
- 生成 HUT 验证产物与 sensory 记录。
- 完成任务报告、review、ledger 和 handoff。

## Out Of Scope

- 新生产功能、模板格式调整和 WPS 自动化。

## Files Allowed

- `docs/*`
- `output/verification/wps-pdf-final-preview-p1/*`
- `openspec/changes/wps-pdf-final-preview-p1/*`

## Interfaces / Seams

- Existing user manual.
- All completed slice verification commands.
- WPS manual PDF export and frontend final viewer.

## Components To Create

- Verification evidence and sensory report only.

## Components To Reuse

- Existing complete thesis example, HUT template and test runners.

## Components To Extract

- No new shared component is required; verification reuses the existing test runners and evidence formats.

## API / Data Flow Contracts

- Documented behavior must match actual engine labels, stale semantics and runtime recovery actions.

## State / Error / Empty / Loading Behavior

- Loading: document build and PDF generation steps are documented.
- Empty: no automatic exporter recovery is documented.
- Error: DOCX success versus PDF failure is explicitly separated.
- Disabled: missing LibreOffice guidance includes WPS PDF selection.
- Permission: Web and desktop file-access recovery is documented.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `pnpm --dir frontend test && pnpm --dir frontend build`
- `cargo test --manifest-path src-tauri/Cargo.toml`
- `OPENSPEC_TELEMETRY=0 openspec validate wps-pdf-final-preview-p1 --strict --no-interactive --json`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not call LibreOffice output WPS-equivalent.
- Do not claim sensory parity without opening the exact generated PDF.
