## Why

ThesisForge P0 已将论文主体样式迁移到学校模板，但封面字段顺序、空行和居中方式仍由
DOCX Renderer 固定。学校模板维护者无法仅修改 YAML 复现不同学校的封面结构，因此
继续补齐模板驱动能力时，封面是第一个必须打通的纵向切片。

## What Changes

- 新增强类型封面布局模型，以有序条目描述封面字段或静态文本。
- 每个封面条目可以配置前后缀、空值策略和完整公共段落样式。
- 封面内容继续来自 Markdown Front Matter；Parser 不读取学校格式。
- DOCX Renderer 按模板顺序渲染封面，不再固定字段顺序、空白段落或居中方式。
- 湖南工业大学模板显式声明封面条目和样式，并增加模型、Compiler、OOXML 和完整构建测试。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `validation-template-resolution`: school templates validate ordered cover items, content sources,
  prefixes, suffixes, empty-value behavior and paragraph styles.
- `render-plan-docx`: the DOCX renderer consumes renderer-neutral cover content and template cover
  policy to create the configured editable paragraphs.
- `offline-cli-pipeline`: complete offline builds demonstrate a template-driven cover without
  mutating Markdown or template inputs.

## Impact

- Affected code: Template Model, DOCX cover renderer, built-in school templates, template
  documentation, examples and focused tests.
- Public contract: additive `cover` template section; existing templates receive a deterministic
  generic default layout.
- Dependencies: no new runtime dependency, network, database, AI service or platform API.
- Architecture: preserves `Markdown -> ThesisDocument -> Validation -> Template -> RenderPlan ->
  DOCX`; no DOCX object enters Parser, Domain Model or RenderPlan.
