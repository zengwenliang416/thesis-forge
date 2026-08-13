# Quality Review: 003-dual-preview-ui

## Verdict

approved

## Separation Of Concerns

- React components 只通过 `WorkbenchTransport` 获取自动或用户选择的 PDF bytes，没有
  直接调用 HTTP 或 Tauri invoke。
- reducer 管理 revision、request key 和 freshness，`usePdfObjectUrl` 管理 Blob URL
  创建/撤销，展示组件负责状态和恢复动作，职责边界清楚。

## Component Cohesion / Coupling

- `PreviewModeControl`、`FinalLayoutPreview` 和 `usePdfObjectUrl` 各自保持单一职责，
  Web/Tauri 共用同一 viewer 和状态机。
- WPS ready 文案现在由 descriptor engine 派生为“当前预览”，不再把手工导入产物
  与自动构建产物耦合。

## Test Quality

- reducer/component 测试覆盖 WPS ready 文案、source/template stale、旧异步结果
  guard、object URL revoke、picker replacement failure 保留已有 bytes 和 viewer。
- Playwright 使用包含 catalog、pages、page、content stream、font、xref 和 trailer
  的完整一页 PDF；指定 desktop Chromium 用例当前运行 `1 passed`，覆盖自动 PDF
  Blob viewer 和编辑后 stale。
- 本次外置卷上的 Vitest 定向运行有组件测试超过默认 5 秒而 timeout，但没有功能断言
  失败；同次相关运行其余 19 个测试通过，三项修复中的 reducer 保留行为通过，且
  validation log 有完整 frontend suite 的 system-executed green 记录。

## Error Handling

- replacement picker 失败且已有 ready/stale PDF 时，reducer 保留 descriptor、bytes
  和原状态，仅附加错误消息并清除 request key；viewer 继续可见并提供重新选择动作。
- 没有既有 PDF 时，picker failure 仍进入明确 failed 状态。旧 build/selection
  结果继续受 generation、revision 和 request key 约束。

## Reuse / Duplication

- 一个 strict `FinalPreviewDescriptor`、一个 object URL hook、一个 reducer 状态机和
  一个 transport seam 被自动 PDF 与 WPS PDF 共用。
- 未发现 React 内复制 runtime locator、Office 转换逻辑或 Web/Tauri 分叉 viewer。

## Complexity Delta

- 新状态机复杂度集中在 `FinalPreviewState` 和对应 reducer events，测试覆盖关键
  freshness、replacement 和错误分支，复杂度与双预览需求相称。
- 完整 PDF fixture 由小型确定性生成函数构造，没有引入 PDF viewer 依赖或生产复杂度。

## Required Fixes

- No task 003 quality fix is required; the reducer, transport seam, viewer
  component, and object-URL lifecycle remain separated and covered by current
  tests.
