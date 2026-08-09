## 1. Strongly Typed List Policy

**用户结果：** 模板维护者可以通过 YAML 配置有序和无序列表每一层的编号、项目符号、
对齐、缩进及完整段落样式。

- [ ] 1.1 定义 ordered/unordered level models、语义编号格式枚举和 `ListSpec`。
- [ ] 1.2 为格式、marker、1 至 9 层边界、绝对缩进和悬挂缩进几何增加精确校验。
- [ ] 1.3 提供与当前 9 层 Renderer 行为等价的通用默认策略，并证明旧模板仍可加载。
- [ ] 1.4 更新 `docs/TEMPLATE_SPEC.md`，记录列表模型、默认值、层级回退、约束和完整示例。

## 2. Template-Driven DOCX Lists

**用户结果：** 同一份 Markdown 切换模板后，Word 中的编号格式、项目符号、缩进和列表
正文样式会按模板变化，同时保留原始列表语义和起始编号。

- [ ] 2.1 重构 DOCX list helper，接收强类型模板策略并把语义格式映射为真实 numbering OOXML。
- [ ] 2.2 保留 Markdown 非 1 起始编号，并对超出策略深度的项确定性复用最后一层。
- [ ] 2.3 在列表段落加入 inline runs 后复用共享 paragraph-style translator。
- [ ] 2.4 移除固定 bullet tuple、固定 decimal、固定对齐和固定缩进。

## 3. HUT Template And Verification

**用户结果：** 湖南工业大学模板能够生成结构化、可编辑且列表格式全部由 YAML 控制的
完整论文。

- [ ] 3.1 在 HUT YAML 中显式配置 ordered/unordered 多级策略和学校段落样式。
- [ ] 3.2 增加 Template Model、RenderPlan、起始编号、层级回退和同内容双模板差异测试。
- [ ] 3.3 增加 DOCX OOXML 测试，断言 `numFmt`、`lvlText`、`lvlJc`、`ind`、`numPr` 和列表段落样式。
- [ ] 3.4 执行聚焦测试、完整 Python 测试、Ruff、OpenSpec strict validation 和 SpecNav handoff contract。
