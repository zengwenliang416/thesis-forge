# Acceptance Criteria: automatic-docx-toc-refresh-p1

## User-Visible Criteria

- 构建结果的“目录”标题始终独立存在，更新 TOC 域不会删除或替换标题。
- 本机存在兼容 LibreOffice 时，构建完成的 DOCX 已包含可见目录条目和页码。
- 本机没有 LibreOffice 或刷新失败时，构建仍生成可打开 DOCX，用户可在 Office 中手动
  更新真实目录域。
- CLI、Web、macOS 和 Windows 通过共享 application service 获得一致行为。

## System Criteria

- Renderer 在独立 `TFTOCTitle` 段落写入普通文本“目录”，并在下一段写入真实 TOC
  complex field。
- TOC field 保持 begin/separate/end、dirty 标记、合法 field instruction 和
  `w:updateFields=true`。
- application finalization 在 Renderer 之后、package validation 和 atomic replace 之前
  调用注入的 document refresher。
- 默认 refresher 能发现 macOS、Linux 和 Windows 常见 LibreOffice executable。
- LibreOffice 使用隔离 user profile、hidden load、有界超时和确定性进程清理。
- 刷新失败是安全 no-op；package validation 或 atomic replace 的强制失败语义不变。

## Data Criteria

- Markdown、模板和资源输入不得被修改。
- Office refresher 只修改 application 创建的临时 DOCX。
- 刷新失败或构建取消时不得覆盖此前有效 output，也不得遗留临时 DOCX/profile/process。
- 没有兼容 Office 引擎时，TOC instruction 和待更新标记仍可从 DOCX OOXML 验证。

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- Parser、Domain、Compiler 和 RenderPlan 不新增 Office、subprocess、UNO 或分页依赖。
- Renderer 不启动 LibreOffice，application adapters 不复制 Office 自动化逻辑。

## Verification Surfaces

- Facticity: compare requirements, component seam, Renderer OOXML and application flow.
- Static: Ruff, architecture checks, strict OpenSpec validation and `git diff --check`.
- Unit: TOC paragraph separation, field XML, executable discovery, no-op/failure handling and call order.
- Redteam: missing executable, invalid candidate, timeout, crashed process, corrupt refreshed package and cancellation.
- E2E: build the complete HUT thesis with real LibreOffice and inspect cached TOC entries plus package validity.
- Sensory: open the refreshed HUT DOCX in WPS/LibreOffice and inspect title, entries, leaders and page numbers.

## Unresolved Gaps

None for this slice.
