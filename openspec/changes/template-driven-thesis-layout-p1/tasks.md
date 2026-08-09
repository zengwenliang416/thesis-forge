## 1. Strongly Typed Cover Policy

**用户结果：** 模板维护者可以通过 YAML 决定封面显示哪些内容、按什么顺序显示以及每一项的完整段落样式。

- [ ] 1.1 定义封面字段枚举、`CoverItemSpec` 和 `CoverSpec`，支持字段或静态文本、前后缀、空值策略和公共段落样式。
- [ ] 1.2 为字段/文本互斥、空静态文本、重复字段和未知字段增加精确模板校验。
- [ ] 1.3 提供与当前语义顺序等价的通用默认封面策略，并证明旧模板仍可加载。
- [ ] 1.4 更新 `docs/TEMPLATE_SPEC.md`，记录封面模型、默认值、约束和完整示例。

## 2. Renderer-Neutral Cover Rendering

**用户结果：** 同一份 Markdown 切换模板后，封面字段顺序、文字标签、字体、字号、对齐和间距会按模板变化。

- [ ] 2.1 为 `CoverInstruction` 提供稳定的语义字段读取接口，不加入 DOCX 或模板样式对象。
- [ ] 2.2 重构 DOCX cover renderer，按 `cover.items` 顺序渲染字段或静态文本并处理空值策略。
- [ ] 2.3 复用共享 paragraph-style translator 应用字体、颜色、字号、强调、对齐、缩进、段距、行距和分页属性。
- [ ] 2.4 移除封面固定字段循环、固定居中和硬编码空白段落。

## 3. HUT Template And Verification

**用户结果：** 湖南工业大学模板能够生成结构化、可编辑且样式由 YAML 控制的完整封面。

- [ ] 3.1 在 HUT YAML 中显式配置封面字段顺序、静态标签和各项样式，不在 Renderer 中加入学校值。
- [ ] 3.2 增加 Template Model、RenderPlan 和同内容双模板差异测试。
- [ ] 3.3 增加 DOCX OOXML 测试，断言封面段落顺序、文本、字体、字号、对齐和段距。
- [ ] 3.4 执行聚焦测试、完整 Python 测试、Ruff、OpenSpec strict validation 和 SpecNav handoff contract。
