# Requirements: automatic-docx-toc-refresh-p1

## Summary

补齐 DOCX 自动目录纵向切片。Renderer 必须把可见“目录”标题与真实 Word TOC 域分成
两个独立段落；application build finalization 在本机存在兼容 LibreOffice 时自动计算并
保存目录条目和页码，不存在或刷新失败时保留有效、可编辑且标记为待更新的 TOC 域。

## Users & Actors

- 论文作者：构建后直接获得已填充目录，或在 Office 中手动更新仍然有效的目录域。
- Web、macOS 和 Windows 用户：通过共享 application service 获得相同目录行为。
- ThesisForge 开发者：维护 Renderer 的 OOXML 对象和 application 层 Office 刷新边界。
- 部署维护者：可选安装 LibreOffice 以启用自动刷新，不把它变成核心编译硬依赖。

## In Scope

- “目录”标题使用 `toc.title` 语义样式写入独立段落。
- TOC 域写入标题后的独立段落，保持 `TOC \o "1-3" \h \z \u`、dirty 标记和
  `w:updateFields=true`。
- 新增 application 层 Office refresher，发现 macOS、Linux 和 Windows 的 LibreOffice。
- 构建临时 DOCX 后、包校验和原子替换前，尝试通过隔离 LibreOffice profile 更新所有
  document indexes/fields 并保存回同一临时文件。
- LibreOffice 缺失、启动失败、连接失败、超时或更新失败均安全降级，不破坏渲染结果，
  不覆盖此前有效输出。
- refresher 通过 `ApplicationDependencies` 注入，单元测试不启动真实 Office。
- 增加 OOXML、调用顺序、跨平台发现、失败保护和真实 LibreOffice 端到端测试。
- 更新模板文档，说明模板控制 TOC 标题/条目样式，页码计算由兼容 Office 布局引擎完成。

## Out of Scope

- 在 Parser、Domain、Compiler 或 RenderPlan 中计算目录页码。
- 用静态普通文本伪造目录或移除真实 TOC 域。
- 要求每台机器必须安装 LibreOffice、Microsoft Word 或 WPS。
- 自动化 Microsoft Word/WPS 私有接口。
- 保证 Word、WPS 和 LibreOffice 逐像素或逐页完全一致。
- 新增 UI 开关、网络服务、数据库、AI、模板市场或账号能力。

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- No production UI change. CLI、Web 和 Tauri 继续调用同一 `build_service`；下载和本地文件
  流程不新增控件或状态。

## Theme & Locale Capability Impact

- Theme support: `light-only`.
- Theme toggle policy: `none`.
- Internationalization: `disabled`.
- Supported locales: `zh-CN`.
- Default locale: `zh-CN`.
- Prototype coverage: no UI prototype; component-seam review only.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Renderer 只创建真实 TOC OOXML，不负责启动进程或计算分页。
- application finalization 新增可选 Office refresh service，并在 package validation 与 atomic
  replace 之前运行。
- 核心构建仍离线、无网络、无 API Key、无数据库；LibreOffice 是本地可选增强能力。
- 无数据库、迁移、认证、权限或远程服务变更。

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- `FLOW-BUILD` 扩展为 render temporary DOCX -> optional Office refresh -> package validation ->
  atomic replace。
- Office refresh 缺失或失败不改变成功构建的公开返回契约；最终 DOCX 保留 dirty TOC 域，
  可由用户在 Word/WPS/LibreOffice 中更新。
- 取消检查继续位于 finalization 边界，旧输出只在全部强制校验成功后才原子替换。

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Cohesion/coupling impact: `renderer.py` 只分离标题与 field 段落；
  `application/office_refresh.py` 独立封装 executable discovery、隔离进程、UNO 更新和清理；
  `services.py` 只编排刷新时机。
- Shared extraction requirement: 提取一个可注入 `DocumentRefresher` protocol/callable 和一个
  默认 `LibreOfficeDocumentRefresher`，禁止把 subprocess/UNO 逻辑复制到 CLI、Web、
  Tauri adapter 或 DOCX Renderer。

## Unresolved Gaps

None for this slice.
