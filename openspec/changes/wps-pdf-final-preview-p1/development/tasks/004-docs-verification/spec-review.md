# Spec Review: 004-docs-verification

## Verdict

needs-fix

## Missing Requirements

- `A3` 要求在 sensory 中逐页比较一个 WPS 导出的 PDF 在 WPS 与右侧最终预览中的
  显示。当前运行只有 LibreOffice 26.2.3.2 生成的 12 页 HUT PDF；task report、
  `sensory-review.md` 和 `validation-log.jsonl` 均明确记录没有当前运行的 WPS PDF。
- task 004 brief 的 vertical slice 要求“完成 WPS 与右侧最终预览逐页检查”，
  `context.json` 的 stop condition 要求任一 acceptance assertion 缺少当前运行直接
  证据即停止。任务却被记录为 `DONE_WITH_CONCERNS` 并生成 development handoff，
  不符合该停止条件。
- `tasks.md` 的 4.3 仍为未完成，与 task report/ledger 的 implementation complete
  表述不一致；该状态不能支持完整开发 handoff。

## Extra Behavior

- 文档增加了完整用户手册及 HTML/图片资产，范围仍在 `docs/*` allowed files 内，
  未发现借文档任务修改生产实现。
- LibreOffice PDF 的 12 页 PNG、hash、metadata 和 qpdf 记录是有效的 LO sensory
  辅助证据，但不是 WPS assertion 的替代证据。

## Misunderstood Requirements

- 将 WPS 逐页 sensory 移交给后续 six-domain verification，与 task 004 自身目标和
  stop condition 冲突。该任务被规划为“documentation, complete verification and
  WPS sensory evidence”，不是只准备验证材料。
- 不能因为 LibreOffice PDF 与 DOCX 同源、页面检查通过，就推断 WPS 分页、字体度量、
  目录、浮动对象或页眉页脚等价。当前文档正确声明了非等价边界，但 handoff 时机仍然
  错误。

## Cannot Verify From Diff

- 无当前运行 WPS 导出 PDF、WPS 打开记录、picker 选择记录、右侧 viewer 页面对照或
  page-by-page checklist，因此无法验证 `A3`。
- 无原生 Windows 和 packaged macOS viewer sensory；task report 已把它们列为后续
  gate，不能在本开发 handoff 中视为已完成。

## Acceptance Assertions Verified

- `A1`: 已核验文档准确区分结构预览、`LibreOffice PDF`、`WPS PDF` 和 stale/recovery
  语义；task 004 的当前浏览器 sensory 仅覆盖 empty state，不构成完整 A1 页面证据。
- `A2`: 已核验当前 HUT DOCX/PDF 的 SHA-256、LibreOffice producer、12 个页面、
  A4 metadata 和 `qpdf --check`；这只支持 LibreOffice 当前产物，不支持 WPS 等价。
- `A3`: 已核验并确认未满足；当前运行没有 WPS 导出 PDF，也没有 WPS 与右侧预览的
  逐页 sensory comparison。

## Required Fixes

- 从同一当前 HUT DOCX 在 WPS 中真实导出 PDF，保存其 provenance、hash、页数和生成
  时间；不得复制、重命名或复用 LibreOffice PDF。
- 通过 Web/Tauri 规定的 picker 选择该 WPS PDF，在 WPS 和右侧最终预览中逐页比较，
  记录封面、摘要、目录、正文、图表、公式、参考文献、致谢、附录、页眉页脚和页码。
- 在 A3 直接证据完成前，将 task 004 与 development handoff 保持未完成/needs-fix；
  证据完成后再同步 report、task 状态和 handoff。
