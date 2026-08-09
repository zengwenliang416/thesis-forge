## Why

ThesisForge 已能从 Markdown 编译有序和无序列表，但编号格式、项目符号、对齐和缩进仍由
DOCX Renderer 固定。学校模板维护者无法仅修改 YAML 复现不同学校的列表规范，因此需要
把列表布局纳入现有强类型模板策略。

## What Changes

- 新增强类型列表策略，分别描述有序和无序列表的多级格式。
- 有序列表层级支持语义编号格式、前后缀、对齐、左缩进、悬挂缩进和完整段落样式。
- 无序列表层级支持项目符号、对齐、左缩进、悬挂缩进和完整段落样式。
- DOCX Renderer 将语义格式映射为真实 Word numbering 对象，并为列表段落应用公共样式。
- 通用默认精确复现当前 9 层行为，旧模板无需迁移；HUT 模板显式声明学校列表规则。
- 增加模型校验、OOXML、非 1 起始编号、双模板差异和完整离线构建测试。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `validation-template-resolution`: school templates validate ordered and unordered list levels,
  semantic numbering formats, markers, indentation and paragraph styles.
- `render-plan-docx`: the DOCX renderer consumes renderer-neutral list instructions and template
  list policy to create editable numbering definitions and styled list paragraphs.
- `offline-cli-pipeline`: complete offline builds demonstrate template-driven ordered and
  unordered lists without mutating Markdown or template inputs.

## Impact

- Affected code: Template Model, DOCX list numbering helper, DOCX renderer, built-in school
  templates, template documentation and focused tests.
- Public contract: additive `list` template section; existing templates receive deterministic
  defaults equivalent to current output.
- Dependencies: no new runtime dependency, network, database, AI service or platform API.
- Architecture: preserves `Markdown -> ThesisDocument -> Validation -> Template -> RenderPlan ->
  DOCX`; raw OOXML remains isolated in the DOCX Renderer.
