## 1. PDF Export And Build Contract

**用户结果：** 成功构建 DOCX 后可获得明确标注引擎的真实 PDF；Office 缺失或失败不影响
DOCX。

- [x] 1.1 新增 typed `PdfPreviewArtifact`、`PdfPreviewExporter` 和 `BuildResult.final_preview`。
- [x] 1.2 实现跨平台 `LibreOfficePdfPreviewExporter`、PDF 校验、临时输出和原子发布。
- [x] 1.3 接入共享 build service，并覆盖 success、missing、failure、timeout、invalid PDF。

## 2. Web And Tauri Artifact Access

**用户结果：** Web、macOS 和 Windows 都能安全读取自动 PDF，并能选择 WPS 导出的 PDF。

- [x] 2.1 扩展 runtime/build DTO，返回无私有路径的最终预览描述。
- [x] 2.2 新增 workspace-bound Web PDF route 和 traversal/content-type/cache 测试。
- [x] 2.3 新增 Tauri PDF picker/binary reader、自动派生路径限制和 Rust contract tests。
- [x] 2.4 扩展 Web/Tauri transport，统一解析自动 PDF 和用户选择的 WPS PDF。

## 3. Dual Preview UI And Freshness

**用户结果：** 右侧可切换快速结构预览与真实最终版式，并准确识别最新/过期状态。

- [x] 3.1 扩展 workspace reducer 的 preview mode、ready/stale/unavailable/failed 状态。
- [x] 3.2 实现可访问的模式切换、引擎标签、PDF viewer、恢复动作和 object URL 清理。
- [x] 3.3 修改 Markdown、模板、工作区和异步过期结果的状态测试。
- [x] 3.4 增加桌面/移动宽度、Web/Tauri E2E 和 WPS PDF sensory 对比证据。

## 4. Unsaved Live PDF Preview

**用户结果：** 打开文稿或停止编辑约 900ms 后，右侧自动显示当前未保存内容的真实 PDF，
无需手动构建，且不会覆盖源 Markdown 或正式 DOCX。

- [x] 4.1 增加保留原 source path 的文本快照解析入口，并复用 application build service。
- [x] 4.2 为 Web/Tauri 生成 capability 绑定的唯一临时 DOCX/PDF，在读取、失败或取消
  后清理，并为 Web 增加跨进程重启的过期孤儿清扫。
- [x] 4.3 实现 debounce、abort、revision 防旧结果覆盖和更新期间保留上一版 PDF。
- [x] 4.4 覆盖未保存文本、快速连续编辑、临时路径授权和清理测试。

## 5. Documentation And Complete Verification

**用户结果：** 用户手册准确说明结构预览、LibreOffice PDF、WPS PDF 和一致性边界。

- [x] 5.1 更新用户手册和架构文档，禁止把不同 Office 引擎描述为完全一致。
- [x] 5.2 执行 Python、frontend、Rust、HTTP、E2E、Ruff、OpenSpec、CodeGraph 和 diff 检查。
- [ ] 5.3 构建完整 HUT DOCX/PDF，并在 WPS 与右侧预览中逐页人工检查。
