## 1. Preview Font Adaptation

用户结果：macOS 用户构建或编辑论文时，右侧 LibreOffice 实时 PDF 预览使用更接近模板意图的宋体正文和黑体标题，同时正式 DOCX 保持原始学校字体声明。

- [x] 1.1 Add a conversion-only DOCX package adapter for exact font-name attributes.
- [x] 1.2 Apply the verified macOS aliases inside the isolated LibreOffice profile.
- [x] 1.3 Preserve input bytes, timeout, process cleanup, PDF validation, and atomic replacement.

## 2. Example Heading Color

用户结果：示例学校模板生成的一至三级标题稳定为黑色，不再继承 Word/LibreOffice 主题蓝色，并继续保留中文字体配置。

- [x] 2.1 Add explicit black Heading 1 and Heading 2 colors and a complete black Heading 3 style.
- [x] 2.2 Add template and OOXML regression coverage for all three heading levels.

## 3. Verification

用户结果：用户获得经过完整自动测试、真实 PDF 字体审计和本机安装验证的可试用应用，并能按明确步骤自行检查实时预览。

- [x] 3.1 Run focused Python tests, Ruff, OpenSpec strict validation, and diff checks.
- [x] 3.2 Build the complete thesis fixture and audit PDF fonts, page count, and text extraction.
- [x] 3.3 Rebuild and install the macOS application, then provide concise manual test steps.
