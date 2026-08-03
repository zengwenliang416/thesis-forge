## Why

ThesisForge 当前只能配置正文的基础字体、字号、首行缩进和行距，摘要、关键词、
目录层级、参考文献段落以及奇偶页眉页脚仍依赖普通样式、Word 默认值或 Renderer
硬编码。湖南工业大学硕士论文参考文档证明这些规则必须进入强类型学校模板，并由
renderer-neutral RenderPlan 驱动真实 OOXML 输出。

## What Changes

- 提取可复用的段落样式模型，统一描述字体、字号、对齐、缩进、段前段后、行距和分页控制。
- 扩展正文与标题配置，支持孤行控制、段落同页、与下段同页、分页前和文档网格策略。
- 为中文摘要、英文摘要、中文关键词、英文关键词和特殊不编号标题增加模板化语义样式。
- 配置 TOC 标题与 TOC 1-3 样式，包括缩进、行距、制表位和点引导线。
- 配置上标或行内引文，以及参考文献条目的字体、字号、悬挂缩进、间距和行距。
- 扩展 section 页面几何和页眉页脚模型，支持页眉/页脚距离、首页/奇数页/偶数页内容、
  样式、页眉底边和可配置页码显示。
- 增加模板兼容性、RenderPlan 角色、OOXML 结构和完整 DOCX 构建测试。
- 保持现有 Markdown 语法、离线编译链路、编号/引用合同和旧模板默认行为兼容。

## Capabilities

### New Capabilities

None. This change extends the existing thesis model, template-resolution,
RenderPlan/DOCX, bibliography, and offline-build capabilities.

### Modified Capabilities

- `thesis-markdown-model`: stable heading IDs and document structure identify abstract, keywords,
  TOC and special-heading roles without introducing DOCX details or new mandatory Markdown syntax.
- `validation-template-resolution`: school templates validate reusable paragraph styles, semantic
  role styles, TOC, bibliography, citation, page geometry and header/footer variants.
- `render-plan-docx`: RenderPlan carries renderer-neutral semantic style roles and the DOCX renderer
  emits the configured paragraph, TOC, section, header/footer, border and page-number OOXML.
- `bibliography-citations`: inline citation presentation and bibliography paragraph presentation are
  template driven while bibliography data loading and formatting remain DOCX independent.
- `offline-cli-pipeline`: the complete example and build verification cover the new P0 formatting
  configuration without network access or source mutation.

## Impact

- Affected code: `src/thesis_forge/templates/`, `src/thesis_forge/core/`,
  `src/thesis_forge/renderers/docx/`, template documentation, built-in templates, examples and tests.
- Public contracts: additive Template Model fields and typed RenderPlan style-role data; existing
  template files remain valid through explicit defaults.
- Dependencies: no new runtime dependency, database, network service or AI requirement.
- Compatibility: generated OOXML targets Microsoft Word and WPS as primary layout clients;
  LibreOffice remains a compatibility surface rather than a pixel-identical pagination guarantee.
- Non-goals: bilingual captions, list of figures/tables, advanced table geometry, equation layout,
  componentized cover/declaration pages, legacy `.doc`/MathType/EndNote import.
