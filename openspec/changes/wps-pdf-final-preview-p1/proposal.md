## Why

当前右侧预览是 RenderPlan 的快速结构投影，固定纸张宽度和简化内容不能复现 WPS 的字体
度量、分页、目录页码、浮动对象和页眉页脚。用户需要继续保留快速结构反馈，同时能在同一
工作台查看真实 Office 引擎导出的最终 PDF。

## What Changes

- 右侧增加“结构 / 实时版式”切换，并默认显示真实 PDF。
- Markdown 停止编辑约 900ms 后，以当前未保存文本自动生成一次性临时 DOCX/PDF。
- 构建成功后由可选 LibreOffice exporter 生成真实 PDF。
- 用户可关联 WPS 已导出的 PDF，作为 WPS 最终版式证据。
- 每个 PDF 显示真实引擎标签；刷新期间保留上一版，旧 revision 不能覆盖新内容。
- Web 通过受限 workspace 路由读取 PDF；Tauri 通过原生 picker/reader 读取 PDF。
- PDF 缺失或失败不影响 DOCX 构建结果。

## Capabilities

### New Capabilities

- `final-layout-pdf-preview`: engine-labelled final-layout PDF preview and stale-state handling.

### Modified Capabilities

- `cross-platform-workbench`: add shared Web/Tauri preview resolution and PDF selection flows.
- `offline-cli-pipeline`: optionally derive a non-authoritative PDF preview after DOCX publication.

## Impact

- Affected code: parser snapshot entrypoint, application contracts/services, PDF exporter,
  adapters, HTTP/Tauri bridge,
  frontend workspace state/components/transports, tests and user documentation.
- Dependencies: optional local LibreOffice runtime; no network dependency. Browser/WebView PDF
  display uses built-in viewer capability for P1.
- Security: PDF reads remain workspace-bound or user-selected; no arbitrary Web path access.
- Architecture: the deterministic DOCX pipeline remains unchanged and authoritative.
