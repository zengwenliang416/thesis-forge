# Prototype Question: template-driven-thesis-layout-p1

## Question

是否批准 `cover-policy-docx-seam-v1` 组件边界：Markdown Front Matter 只提供封面内容，
Template Model 通过有序 `CoverSpec.items` 表达布局与段落策略，RenderPlan 继续携带
renderer-neutral `CoverInstruction` 字符串，DOCX Renderer 复用共享 paragraph-style
translator 输出可编辑封面段落？

## Branch

`component-seam`

## Review Target

- Entry: `component/component-map.md`
- Variant: `cover-policy-docx-seam-v1`
- Required reviewer decision: 是否批准该模型边界、依赖方向、默认策略和测试边界作为
  P1 封面纵向切片的生产开发依据。

## Out of Scope

- Production implementation.
- UI、模板编辑器、主题和国际化变更。
- 绝对定位、文本框、Logo、形状、声明页和签名图片。
- 列表、代码清单、算法、复杂表格和富文本行内样式。
