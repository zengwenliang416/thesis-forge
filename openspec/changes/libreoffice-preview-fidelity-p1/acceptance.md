# Acceptance Criteria: libreoffice-preview-fidelity-p1

## User-Visible Criteria

- 示例模板生成的一级、二级、三级标题在 DOCX 和 LibreOffice PDF 中均为黑色。
- macOS 安装系统宋体/黑体时，实时 PDF 正文不再退化为 Arial Unicode MS。
- 优化失败或字体缺失时，用户仍能正常构建和下载 DOCX。

## System Criteria

- LibreOffice 使用单次转换隔离 profile，字体替换不写入用户全局配置。
- 字体候选必须先通过本机可用性探测；未命中候选时不写无效替换项。
- Windows 不注入 macOS 专属字体名；Linux 只选择实际可用候选。
- PDF 转换继续使用有界超时、进程树清理、签名校验和原子替换。

## Data Criteria

- 输入 DOCX 的字节在 PDF 转换前后保持不变。
- 正式 DOCX 中 `宋体`、`黑体` 等模板字体声明保持不变。
- 隔离 profile 和替换配置在转换结束后清理。

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- Parser、Domain、Compiler、RenderPlan、DOCX Renderer 和 frontend 不依赖平台字体探测。

## Verification Surfaces

- Facticity: 对照需求、现有 PDF exporter 和真实 DOCX/PDF 字体清单。
- Static: Ruff、OpenSpec strict、diff check 和架构边界检查。
- Unit: 字体候选、profile XML、无候选降级、转换命令和模板标题颜色。
- Redteam: 探测命令缺失、超时、无效字体名、转换失败和输入 DOCX 不变。
- E2E: 使用完整论文样本生成有效 PDF，并运行 `pdffonts`。
- Sensory: 用户在 WPS 与右侧实时预览中检查正文、三级标题和分页差异。

## Unresolved Gaps

None.
