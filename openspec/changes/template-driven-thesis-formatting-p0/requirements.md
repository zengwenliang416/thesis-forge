# Requirements: template-driven-thesis-formatting-p0

## Summary

实现湖南工业大学硕士论文格式分析中确定的 P0 模板化能力，使学校 YAML 模板可以
完整控制正文段落、标题分页行为、中英文摘要与关键词、目录层级、引文与参考文献、
section 页面几何以及首页/奇数页/偶数页页眉页脚。所有学校规则必须通过强类型
Template Model 和 renderer-neutral RenderPlan 进入 DOCX Renderer。

## Users & Actors

- 论文作者：使用同一 Markdown 内容切换不同学校模板并生成 DOCX。
- 学校模板维护者：通过 YAML 配置论文版式，不修改 Renderer 代码。
- ThesisForge 开发者：维护 Template Model、Compiler/RenderPlan 和 OOXML helpers。
- 文档审核者：在 Microsoft Word、WPS 或 LibreOffice 中检查生成结果。

## In Scope

- 新增通用段落样式合同，支持中西文字体、字号、粗体、斜体、对齐、左右缩进、
  首行缩进、悬挂缩进、段前段后、单倍/多倍/固定行距、孤行控制、段落同页、
  与下段同页、分页前和是否对齐文档网格。
- `body` 继续作为必需的正文样式入口，并兼容现有模板；正文新增段前、段后和分页控制。
- 标题样式复用通用段落属性，并支持 outline level、行距、keep-with-next 和
  后续正文样式语义。
- 通过稳定 heading ID 和文档位置识别中文摘要、英文摘要、关键词、目录、参考文献、
  致谢、成果等特殊角色；不要求用户编写 Word 样式名。
- 模板可分别配置中文摘要标题/正文/关键词和英文摘要标题/正文/关键词。
- 模板可配置 TOC 标题、TOC 1-3 的段落样式、左缩进、右侧页码制表位和 leader。
- 模板可配置 inline citation 的 `superscript` 或 `inline` 显示模式。
- 模板可配置参考文献标题和条目的字体、字号、悬挂缩进、段前段后、行距和编号布局。
- `PageSpec` 支持页眉距离、页脚距离和可选文档行网格。
- section 支持首页、奇数页、偶数页页眉页脚变体；每个变体可配置文本、段落样式、
  页眉底边和是否显示 PAGE/NUMPAGES。
- 页码文本不再固定为“第 X 页 / 共 Y 页”，模板可配置前缀、后缀、是否显示总页数和对齐。
- Compiler/RenderPlan 在 DOCX 创建前解析语义样式角色；RenderPlan 不包含
  `python-docx`、`lxml` 或 raw OOXML 对象。
- Renderer 使用真实 Word styles、section/header/footer relationships、
  tab stops、borders、PAGE/NUMPAGES fields 和分页属性。
- 更新 `docs/TEMPLATE_SPEC.md`、内置模板和完整示例。
- 增加 Pydantic 模型测试、Compiler/RenderPlan 测试、OOXML 结构测试和完整构建测试。
- 所有 inspect/validate/build 路径保持离线、确定性且不修改源 Markdown。

## Out of Scope

- 中英文双语图表题注、图目录和表目录。
- 表格精确列宽、单元格边距、合并单元格、多级/重复表头和跨页控制。
- 公式 tab stop、右端编号格式、多行公式组和旧 MathType 导入。
- 页面组件化封面、声明页、签名线和绝对定位。
- 旧 `.doc`、EndNote `ADDIN` 和 MathType OLE/WMF 自动迁移。
- 前端模板编辑器、主题切换、国际化、数据库、网络服务或 AI 依赖。
- 承诺 Word、WPS 和 LibreOffice 逐像素或逐页完全一致。

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- Required UI decisions: no production UI changes. Existing template selection and build flows
  consume the expanded backend template contract without adding controls in this change.

## Theme & Locale Capability Impact

- Theme support: `light-only`.
- Theme toggle policy: `none`; no toggle is created or changed.
- Internationalization: `disabled`.
- Supported locales: `zh-CN`.
- Default locale: `zh-CN`.
- Prototype coverage: no new UI prototype is required; existing light/`zh-CN` workbench coverage
  remains the regression baseline.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Template Model receives additive strong types and defaults; no school values are hard-coded.
- Compiler resolves semantic roles and binds template style identifiers before rendering.
- RenderPlan remains renderer neutral; DOCX-specific properties are translated only in focused
  renderer helpers.
- Bibliography data loading/formatting remains independent of DOCX.
- No database, migration, network service, account, secret or AI dependency is introduced.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- `FLOW-VALIDATE` reports field-specific template errors for invalid paragraph, TOC,
  bibliography, page or header/footer configuration.
- `FLOW-BUILD` passes the same validated template through Compiler/RenderPlan to Renderer.
- Existing Web/Tauri DTOs continue selecting template files; no new transport contract is required.
- Failed rendering preserves the previous output and does not mutate source/template files.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Cohesion/coupling impact: Template Model owns policy, Compiler owns semantic role resolution,
  Renderer owns DOCX translation, and Bibliography owns citation data/text formatting.
- Shared extraction requirement: extract one reusable paragraph-style model and one DOCX paragraph
  formatting helper rather than duplicating body, heading, TOC, bibliography and header/footer logic.
- Header/footer variant selection and border creation remain focused section helpers.
- Existing font, unit and field helpers are reused.

## Unresolved Gaps

None. Scope, compatibility policy, semantic role source, template defaults, target Office clients,
architecture boundaries and verification surfaces are fixed for this change.
