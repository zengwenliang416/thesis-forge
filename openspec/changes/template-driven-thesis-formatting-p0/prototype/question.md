# Prototype Question: template-driven-thesis-formatting-p0

## Question

是否批准 `policy-role-docx-seam-v1` 组件边界：Template Model 只表达可验证的
排版策略，Compiler 只解析 renderer-neutral 语义角色，RenderPlan 只携带角色与稳定
内容，DOCX Renderer 通过一个共享 paragraph-style translator 将策略转换为 Word
styles、段落属性和必要的 OOXML？

## Branch

`component-seam`

## Review Target

- Entry: `component/component-map.md`
- Variant: `policy-role-docx-seam-v1`
- Required reviewer decision: 是否批准该公共 API、依赖方向、兼容层和测试边界作为 P0
  生产开发依据。

## Out of Scope

- Production implementation.
- 前端模板编辑器、主题切换和运行时国际化。
- 封面/声明页组件化、双语题注、图表目录、复杂表格和公式编号布局。
- `.doc`、MathType、EndNote 导入以及数据库、网络、AI 或部署行为。
