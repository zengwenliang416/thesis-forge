# Acceptance Criteria: wps-pdf-final-preview-p1

## User-Visible Criteria

- 用户可在同一右侧面板切换“结构”和“实时版式”，默认显示实时版式。
- 打开文稿后自动生成 PDF；编辑 Markdown 停止约 900ms 后自动刷新，无需先保存。
- 实时刷新使用当前编辑器文本，不写回源 Markdown，也不覆盖正式 DOCX。
- 更新期间上一版 PDF 保持可见，并显示“实时更新中”。
- 成功自动导出后显示真实 PDF，并明确显示 `LibreOffice PDF`。
- 用户可选择 WPS 已导出的 PDF，显示真实文件并明确显示 `WPS PDF`。
- 修改 Markdown 或切换模板后旧 PDF 先显示过期并自动刷新；打开其他文稿清空旧 PDF。
- 没有 Office 导出器或导出失败时，DOCX 仍可下载/打开，界面提供重新构建或选择 WPS PDF
  的恢复动作。

## System Criteria

- `PdfPreviewExporter.export(docx, pdf) -> PdfPreviewArtifact | None` 是 application protocol。
- 默认 LibreOffice exporter 支持 macOS、Linux 和 Windows executable discovery、隔离
  profile、hidden conversion、有界超时、进程清理和原子 PDF replacement。
- `BuildResult` 和 build transport 只返回 typed preview metadata，不泄露本地绝对路径。
- Web PDF 路由拒绝 traversal、非 workspace 文件、非 `.pdf` 名称和不存在的产物。
- Tauri PDF picker 只接受 `.pdf`，读取命令只读取用户选择或本次构建派生的 PDF。
- frontend 严格校验 preview descriptor，管理 object URL 创建与撤销。
- 新 revision 必须取消旧实时任务，旧 revision 的构建或读取结果不能覆盖当前 PDF。

## Data Criteria

- Markdown、YAML、BibTeX、图片和最终 DOCX 不因 PDF 失败而被修改或回滚。
- 实时预览以原 Markdown 路径解析相对图片、参考文献和模板，但只使用未保存文本快照。
- 自动 PDF 先写临时文件，验证 `%PDF-` signature 和非空大小后再原子替换。
- Web/Tauri 实时 DOCX/PDF 使用服务端 capability 绑定的唯一临时路径，并在读取、失败
  或取消后清理；Web 重启后按专属目录文件时间清扫过期孤儿产物。
- 失败构建不得把旧 PDF 标记为最新；成功 DOCX 但 PDF 失败返回 `unavailable/failed`。
- Web 响应使用 `application/pdf`、准确长度、`nosniff` 和 `no-store`。

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- Parser、Domain、Compiler、RenderPlan 和 DOCX Renderer 不依赖 PDF viewer、HTTP、Tauri、
  subprocess 或 WPS UI automation。
- Web/Tauri 不复制 Office 转换逻辑，React components 不直接调用 HTTP/Tauri invoke。

## Verification Surfaces

- Facticity: compare requirements, prototype state matrix, current contracts and final code paths.
- Static: Ruff, TypeScript, Rust, architecture tests, OpenSpec strict and `git diff --check`.
- Unit: exporter discovery/commands/failure safety, descriptors, reducer stale transitions, URL cleanup.
- Redteam: traversal, wrong extension, corrupt/empty PDF, timeout, stale build event and canceled build.
- E2E: Web automatic live PDF read; Tauri automatic live PDF read; debounce/stale revision;
  Web/Tauri WPS PDF selection flow.
- Sensory: compare one WPS-exported PDF in WPS and the right-side final preview page-by-page.

## Unresolved Gaps

None for P1.
