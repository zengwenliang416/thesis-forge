## 1. Legacy-Compatible Paragraph Policy

**用户结果：** 模板维护者可以配置完整段落属性，现有 YAML 模板无需迁移且错误配置会得到精确诊断。

- [x] 1.1 定义严格的 `ParagraphStyleSpec`，覆盖字体、文字颜色、字号、粗斜体、对齐、左右/首行/悬挂缩进、段前段后、行距、孤行控制、段落同页、与下段同页、分页前、outline level 和文档网格对齐。（A1）
- [x] 1.2 为互斥或矛盾的首行/悬挂缩进、固定/多倍行距和非法枚举增加字段级 Pydantic 校验。（A1）
- [x] 1.3 让 `BodySpec` 与 `HeadingLevelSpec` 复用公共段落策略，同时保留现有必填字段和默认输出语义。（A1、A2）
- [x] 1.4 定义语义样式、TOC、参考文献、页眉页脚变体和页码显示所需的强类型模板模型。（A3、A4、A5、A6）
- [x] 1.5 兼容并规范化旧 `header.enabled/text/different_first_page`、footer 和现有页码配置。（A2、A6）
- [x] 1.6 增加现有内置 YAML、最小旧模板、新完整模板、未知字段和非法组合的模型测试。（A1、A2）
- [x] 1.7 验证 Template Model 不包含 DOCX、OOXML、Word style ID 或学校硬编码常量。（A7、A8）

## 2. Shared DOCX Paragraph Translation

**用户结果：** 正文与标题严格使用模板中的字体、缩进、段距、行距和分页控制，不再依赖 Word 默认值或重复实现。

- [x] 2.1 抽取共享 DOCX paragraph-style translator，统一应用字体、文字颜色、字号、强调、对齐、缩进、段距和行距。（A1）
- [x] 2.2 增加 `w:widowControl`、`w:keepNext`、`w:keepLines`、`w:pageBreakBefore`、`w:outlineLvl` 和 `w:snapToGrid` 的聚焦 OOXML helpers。（A1）
- [x] 2.3 使用目标样式字号解析 `em`，避免全局 12 pt 假设。（A1）
- [x] 2.4 将 Normal/body 和 Heading 1-3 迁移到共享 translator，并保持旧模板生成语义兼容。（A1、A2）
- [x] 2.5 为语义角色创建稳定内部 Word styles，但不允许模板直接提供 `w:styleId`。（A3、A7）
- [x] 2.6 增加 paragraph/style XML 测试，断言 `w:pStyle`、`w:spacing`、`w:ind`、分页属性、outline 和 grid 属性。（A1）
- [x] 2.7 增加两份不同模板生成样式不同、语义对象相同的确定性测试。（A8）

## 3. Abstract, Keywords And Semantic Roles

**用户结果：** 中文摘要、英文摘要、中文关键词、英文关键词和特殊章节可以独立配置样式，而不需要修改论文 Markdown 内容。

- [x] 3.1 在 RenderPlan 中定义封闭的 renderer-neutral `ParagraphRole`，并为 heading/paragraph instruction 增加兼容默认值。（A7）
- [x] 3.2 在 Compiler 中实现基于稳定 heading ID 的文档上下文状态机，识别中英文摘要、目录、参考文献、致谢和成果章节。（A3、A7）
- [x] 3.3 仅在匹配摘要上下文且标签位于段首时识别中英文关键词，保留原 inline runs 和文本。（A3）
- [x] 3.4 为缺失语义样式实现确定性的 body/heading fallback，不在 Renderer 中硬编码学校值。（A3、A8）
- [x] 3.5 增加中英文角色切换、章节退出、关键词标签、普通正文误判和重复构建的 Compiler/RenderPlan 测试。（A3、A7）
- [x] 3.6 增加完整摘要片段的 OOXML 测试，断言不同角色绑定不同稳定 Word styles。（A3）
- [x] 3.7 扩展架构测试，证明 Parser、Domain 和 RenderPlan 仍不依赖 `docx`、`lxml` 或 renderer。（A7、A8）

## 4. Configurable Real TOC

**用户结果：** 论文保留真实可更新的 Word 目录字段，同时 TOC 1-3 的缩进、行距、页码制表位和点引导符完全由模板控制。

- [x] 4.1 定义 TOC 标题与 TOC 1-3 样式配置，包括公共段落属性、页码 tab stop 和 leader。（A4）
- [x] 4.2 保留真实 `TOC` complex field 和 update-on-open 行为，不生成静态目录文本。（A4）
- [x] 4.3 创建或更新稳定的 `TOC 1`、`TOC 2`、`TOC 3` Word styles，并复用共享 paragraph translator。（A4）
- [x] 4.4 使用聚焦 OOXML helper 写入右对齐制表位和 dot leader。（A4）
- [x] 4.5 增加缺省 fallback、1-3 层不同缩进/行距和非法 tab/leader 配置测试。（A2、A4）
- [x] 4.6 增加 `styles.xml` 与 `document.xml` 测试，断言真实 TOC field、稳定 styleId、`w:tabs`、位置和 leader。（A4）

## 5. Citation And Bibliography Presentation

**用户结果：** 模板可以选择文内引用普通或上标显示，并配置参考文献标题与条目的字体、段距和两字符悬挂缩进。

- [x] 5.1 为 `CitationSpec` 增加默认 `inline` 的 presentation mode，并保持引用数据与文本格式化合同不变。（A2、A5）
- [x] 5.2 在 DOCX inline run 创建阶段实现 citation superscript，不把 Word 属性放入 bibliography formatter。（A5）
- [x] 5.3 为参考文献标题和条目增加语义样式与确定性 fallback。（A5）
- [x] 5.4 使用共享 paragraph translator 渲染 bibliography entry 的悬挂缩进、段距和行距。（A5）
- [x] 5.5 增加 inline/superscript 引用、连续引用、locator、参考文献顺序和无 DOCX bibliography 单元测试。（A5）
- [x] 5.6 增加 `document.xml` / `styles.xml` 测试，断言 `w:vertAlign w:val="superscript"` 与参考文献 `w:ind` hanging 属性。（A5）

## 6. Page Geometry And Header/Footer Variants

**用户结果：** 模板可以配置页眉页脚距离、首页/奇数页/偶数页内容、页眉底边和页码显示，且不会继承上一 section 的过期内容。

- [x] 6.1 扩展 `PageSpec`，支持 header distance、footer distance 和可选 document grid。（A6）
- [x] 6.2 实现 default/first/even header/footer 变体模型，支持文本、段落样式、底边和页码显示策略。（A6）
- [x] 6.3 将旧 header/footer 配置规范化到变体模型，并保持现有“第 X 页 / 共 Y 页”默认输出。（A2、A6）
- [x] 6.4 实现模板驱动 PAGE/NUMPAGES 前后缀、分隔符、总页数开关和对齐，不固定中文页码文本。（A6）
- [x] 6.5 统一配置初始和新增 section，显式 unlink/clear 已配置或禁用的 first/default/even 变体。（A6）
- [x] 6.6 当声明 even 变体时写入 `w:evenAndOddHeaders`，并正确生成 first/default/even header/footer relationships。（A6）
- [x] 6.7 实现 header bottom border、`w:pgMar` header/footer distance、`w:docGrid` 和 `w:pgNumType` OOXML。（A6）
- [x] 6.8 增加继承泄漏、禁用变体、首页差异、奇偶页、纯 PAGE、PAGE+NUMPAGES、格式/restart 和非法组合测试。（A6）
- [x] 6.9 增加 section/settings/header/footer XML 测试，断言关系、距离、边框、字段代码和奇偶页设置。（A6）

## 7. School Template, Documentation And Complete Build

**用户结果：** 论文作者可以选择一份湖南工业大学 P0 模板，构建覆盖正文、摘要、目录、参考文献和奇偶页眉页脚的完整可编辑 DOCX。

- [x] 7.1 更新 `docs/TEMPLATE_SPEC.md`，完整记录所有新增字段、默认值、兼容规则、枚举、单位和示例。（A2、A8）
- [x] 7.2 新增湖南工业大学 P0 YAML 模板，所有学校字体、尺寸、行距、边框和页码值仅存在于模板。（A8）
- [x] 7.3 更新完整论文示例，覆盖稳定摘要/目录/参考文献 heading ID、中英文关键词、引文和多 section 内容。（A3、A4、A5、A6）
- [x] 7.4 增加 inspect/validate/build 离线端到端测试，证明输入 Markdown、YAML、BibTeX 和图片不被修改。（A8、A9）
- [x] 7.5 解包完整 DOCX 并断言 `styles.xml`、`document.xml`、`settings.xml`、section properties、relationships 和 header/footer parts。（A9）
- [x] 7.6 重复构建并比较 RenderPlan 与规范化 OOXML，证明同输入输出确定。（A8、A9）
- [x] 7.7 使用两份有效模板构建同一论文，证明样式不同但编号、引用、书签和语义内容等价。（A8、A9）

## 8. Regression, Office Review And Handoff

**用户结果：** 维护者和审核者可以通过完整自动化证据与真实 Office 客户端确认 P0 功能可用、可维护且不会破坏既有编译能力。

- [ ] 8.1 执行聚焦模板、Compiler、RenderPlan、bibliography 和 DOCX renderer 测试并记录系统执行证据。（A1-A9）
- [ ] 8.2 执行完整 `.venv/bin/python -m pytest`、`ruff check .`、包构建、`pip check`、`git diff --check` 和 OpenSpec validation。（A8、A9）
- [ ] 8.3 执行 CodeGraph claims/impact 验证并复核学校值、DOCX import 和重复格式转换逻辑。（A7、A8）
- [ ] 8.4 使用 Microsoft Word 或 WPS 打开完整 P0 DOCX，审阅正文节奏、中英文摘要/关键词、目录、参考文献、奇偶页眉和页码。（A10）
- [ ] 8.5 记录 Word/WPS 感官审阅证据，并将 LibreOffice 转换结果仅作为兼容性补充证据。（A10）
- [ ] 8.6 完成每个纵向切片的 report、spec review、quality review、validation ledger 和 drift check。（A1-A10）
- [ ] 8.7 更新 `acceptance.json` 的 A1-A10 状态与证据引用，并让 development handoff contract 达到 `ok:true`。（A1-A10）
