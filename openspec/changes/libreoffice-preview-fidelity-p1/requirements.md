# Requirements: libreoffice-preview-fidelity-p1

## Summary

提高 LibreOffice 生成的实时 PDF 预览在中文字体和标题颜色方面的忠实度。优化只作用于
一次性 LibreOffice 转换环境；正式 DOCX 继续保留学校模板声明的 `宋体`、`黑体` 等字体
名称，确保 Windows、WPS 和 Word 的文档语义不被 macOS 预览适配污染。

## Users & Actors

- 论文作者：希望右侧实时 PDF 中的正文和标题更接近模板配置。
- macOS 用户：本机通常安装 `Songti SC`、`STSong`、`Heiti SC` 等系统中文字体。
- Windows/Linux 用户：使用各自已安装字体，不能依赖 macOS 专属字体名称。
- 维护者：需要从实际 PDF 字体审计判断替换是否生效，而不是只检查 DOCX XML。

## In Scope

- 为每次 LibreOffice PDF 转换创建隔离 profile，并在其中写入可用的字体替换配置。
- 按平台和本机实际可用字体选择 `宋体`、`黑体` 的候选替代字体。
- 字体探测失败时安全退回 LibreOffice 默认转换，不影响 DOCX 构建成功。
- 示例学校模板的一至三级标题显式配置黑色，避免继承 Word 主题蓝色。
- 覆盖 profile 配置、跨平台候选选择、失败降级、PDF 有效性和正式 DOCX 不变测试。
- 使用真实论文 DOCX 生成 PDF，并通过 `pdffonts` 审计中文正文和标题字体。

## Out of Scope

- 修改用户全局 LibreOffice、Fontconfig 或操作系统字体设置。
- 修改已发布 DOCX 内的学校字体名称以迎合某一操作系统。
- 捆绑、复制或重新分发受版权保护的宋体、黑体或 macOS 系统字体。
- 承诺 LibreOffice 与 WPS/Word 逐像素、逐页完全一致。
- 替换 LibreOffice 引擎或引入商业文档转换依赖。

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- 不新增界面、控件或状态；现有 `LibreOffice PDF` 引擎标签保持不变。

## Theme & Locale Capability Impact

- Theme support: `light-only`。
- Theme toggle policy: `none`，不新增主题切换。
- Internationalization: `disabled`。
- Supported locales: `zh-CN`。
- Default locale: `zh-CN`。
- Prototype coverage: 无 UI 变化；使用逻辑/产物原型验证隔离 profile 与 PDF 字体结果。

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- 保持 `Markdown -> ThesisDocument -> Validation -> Template -> RenderPlan -> DOCX`。
- 字体适配仅位于 application 层的可选 PDF exporter，不进入 Parser、Domain、Compiler、
  RenderPlan 或 DOCX Renderer。
- 无数据库、网络服务、账号、迁移或持久状态。

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- 延续 `FLOW-LIVE-PREVIEW` 和 `FLOW-BUILD`：成功生成临时/正式 DOCX 后，以隔离
  LibreOffice profile 尝试 PDF 转换。
- 输入 DOCX 只读；字体替换配置与 profile 随单次转换清理。
- 转换失败仍返回既有 preview unavailable/failed 语义，不改变 DOCX 成功状态。

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Cohesion/coupling impact: 字体候选解析和 profile 配置属于
  `application/pdf_preview.py` 的 LibreOffice 集成职责。
- Shared extraction requirement: 提取纯函数生成替换配置，便于单元测试；不建立新的
  跨层服务或把平台字体逻辑复制到 Web/Tauri。

## Unresolved Gaps

None.
