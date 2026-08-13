# Quality Review: 004-docs-verification

## Verdict

needs-fix

## Separation Of Concerns

- 文档与 sensory 产物位于 task 004 的 allowed files，未混入生产实现改动。
- 自动测试、LibreOffice 产物检查和 WPS sensory 是不同验证域；当前材料正确区分
  LibreOffice 与 WPS，但 lifecycle 状态错误地把缺失的 WPS 域推迟到 handoff 之后。

## Component Cohesion / Coupling

- `docs/ARCHITECTURE.md`、`docs/MAINTENANCE.md` 和 `docs/USER_MANUAL.md` 分别承担架构、
  维护和用户操作说明，内容边界合理。
- `sensory-review.md` 集中记录 artifact metadata、页面检查、UI 检查和非等价边界，
  结构清楚；缺陷是没有 WPS 对照 section 的实际当前证据。

## Test Quality

- `validation-log.jsonl` 有 Python、frontend、Rust、Ruff、OpenSpec 和 diff checks 的
  system-executed 摘要；OpenSpec strict 本次独立重跑通过，frontend build 本次通过。
- 本次独立 Vitest 定向重跑因外置卷环境下 13 个 fork worker 启动超时而没有执行测试，
  因此只能保留历史 system-executed 结果，不能声称本次重跑通过。
- 12 页 LibreOffice PDF 的 `pdfinfo`、`qpdf --check`、SHA-256 和 12 张逐页 PNG
  相互一致，LO 证据质量可接受；WPS 域完全缺失。

## Error Handling

- 文档明确说明 LibreOffice 缺失/失败不影响 DOCX，并给出 rebuild 或选择 WPS PDF
  的恢复动作，错误边界表达准确。
- 验证流程对关键缺证据的处理不合格：`context.json` 要求停止，但 report/ledger
  仍推进到 implementation complete with concerns，削弱了 gate 的可执行性。

## Reuse / Duplication

- 文档复用了现有完整 HUT 示例、模板和测试 runner，没有新增重复的验证实现。
- 页面截图和 sensory 记录围绕一个明确的 LibreOffice PDF，未发现把旧 WPS 产物或
  其他引擎产物伪装为当前证据。

## Complexity Delta

- 文档增量较大，但主要是已有功能的用户说明，不增加运行时复杂度。
- 验证矩阵覆盖多平台、多引擎和多运行时；缺少 WPS 当前产物意味着最昂贵、最易漂移
  的一格为空，不能用其余绿色检查抵消。

## Required Fixes

- 完成同一当前运行的 WPS PDF 导出、picker 导入和逐页对照，保留可追溯 artifact、
  hash、页数、时间和 sensory checklist。
- 修正 task/report/ledger/handoff 的状态一致性：A3 未完成时不得宣告 task 004 或
  development handoff 完成。
- WPS evidence 完成后重新运行最接近的自动检查，并在 validation log 中记录
  `attestation: "system-executed"` 或明确的 system-observed sensory 证据。
