# Spec Review: 003-dual-preview-ui

## Verdict

approved

## Missing Requirements

- 未发现 task 003 范围内缺失的可编码需求。
- 真实 WPS 导出 PDF 的人工逐页 sensory comparison 属于 task 004 的验证产物，不是
  task 003 UI/state 实现的剩余修复项。

## Extra Behavior

- 未发现超出 P1 的 PDF 编辑、搜索、缩略图、WPS 自动化或页面级排版模拟。
- picker replacement 失败时增加保留旧 PDF 并显示可恢复错误提示，符合“错误不应
  破坏已有有效产物”的既有状态语义。

## Misunderstood Requirements

- 先前 WPS ready 状态使用“当前构建”的来源混淆已修复。当前实现仅对自动
  LibreOffice 产物显示“当前构建”，显式选择的 WPS PDF 显示“当前预览”。
- 无头 Chromium 自动化只证明完整 PDF artifact 能通过 Web 流程进入 Blob viewer、
  保持 ready/stale 状态；它不被当作肉眼页面或跨 Office 引擎 sensory 证据。

## Cannot Verify From Diff

- 无法从 task 003 diff 或无头 Chromium 判断 WPS 与右侧 viewer 的逐页视觉一致性；
  该项继续由 task 004 使用当前 WPS 导出 PDF 验证。
- 原生 packaged macOS 和 Windows viewer 的肉眼表现仍需后续 sensory，但不阻塞
  task 003 的共享 React/state 实现验收。

## Acceptance Assertions Verified

- `A1`: 已核验结构/最终版式切换、完整一页 PDF fixture 经 Web route 进入 Blob
  iframe、`LibreOffice PDF` 标签、ready/stale 状态、编辑后 stale 转换以及 object
  URL 生命周期。单条 Playwright 当前运行通过。
- `A3`: 已核验 WPS descriptor 经 transport seam 进入共享 viewer、ready 文案为
  “当前预览”、source/template 变化后 stale、旧 selection result guard，以及
  replacement picker failure 保留已有 PDF。真实 WPS sensory 部分属于 task 004。

## Required Fixes

- No task 003 implementation fix is required after the WPS source-copy,
  replacement-failure, stale-state, object-URL, and complete-PDF E2E
  regressions passed.
