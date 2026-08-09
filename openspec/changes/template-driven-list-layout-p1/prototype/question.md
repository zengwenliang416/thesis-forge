# Prototype Question: template-driven-list-layout-p1

## Question

是否批准 `list-policy-docx-seam-v1` 组件边界：Markdown 和 `ListInstruction` 继续只表达
列表语义，Template Model 通过 ordered/unordered 多级策略表达格式与段落样式，DOCX
Renderer 复用共享 paragraph-style translator，并在 `lists.py` 内把语义编号格式翻译为
真实 Word numbering OOXML？

## Branch

`component-seam`

## Review Target

- Entry: `component/component-map.md`
- Variant: `list-policy-docx-seam-v1`
- Required reviewer decision: 是否批准该模型边界、依赖方向、默认策略、层级回退和测试
  边界作为列表纵向切片的生产开发依据。

## Out of Scope

- Production implementation.
- UI、模板编辑器、主题和国际化变更。
- 修改 Markdown 语法、Parser、Domain Model 或 RenderPlan 列表结构。
- 图片项目符号、复选框列表、超过 9 层和 raw OOXML 模板字段。
