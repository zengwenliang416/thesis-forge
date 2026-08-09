# Requirements: template-driven-thesis-layout-p1

## Summary

实现模板驱动论文封面纵向切片，使 Markdown Front Matter 继续负责论文内容，学校 YAML
模板负责封面字段顺序、静态文字、标签、空值行为和完整段落样式。DOCX Renderer 必须
消费强类型模板策略，不再固定字段顺序、居中方式或空白段落。

## Users & Actors

- 论文作者：只维护论文元数据和正文，不在 Markdown 中写学校版式。
- 学校模板维护者：通过 YAML 调整封面结构和样式，不修改 Renderer。
- ThesisForge 开发者：维护 Template Model、renderer-neutral RenderPlan 和 DOCX 翻译。
- 文档审核者：在 Word 或 WPS 中检查生成封面的内容、顺序和排版。

## In Scope

- 新增有序 `CoverSpec.items` 模型。
- 每个条目必须选择一个受支持的 metadata field 或一个静态文本值。
- 条目支持 `prefix`、`suffix`、`skip_if_empty` 和完整 `ParagraphStyleSpec`。
- 支持学校模板重新排序、隐藏或添加封面静态文本。
- 提供确定性的通用默认封面策略，并让 HUT 模板显式声明全部学校规则。
- Compiler/RenderPlan 继续仅携带封面语义字符串，不携带模板样式或 DOCX 对象。
- Renderer 复用共享段落样式 translator，不新增第二套格式转换。
- 增加模板校验、RenderPlan、OOXML 和离线完整构建测试。
- 更新 `docs/TEMPLATE_SPEC.md` 和内置模板。

## Out of Scope

- 绝对定位、浮动文本框、形状、Logo、背景图和签名图片。
- 声明页、授权书和任意新增 section 角色。
- 修改 Markdown Front Matter 语法。
- 列表、代码清单、算法、复杂表格和富文本行内样式；这些作为后续独立切片。
- Word、WPS 和 LibreOffice 逐像素一致。

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- No production UI change. Existing template selection and build flows consume the additive YAML
  contract.

## Theme & Locale Capability Impact

- Theme support: `light-only`.
- Theme toggle policy: `none`.
- Internationalization: `disabled`.
- Supported locale: `zh-CN`.
- Prototype impact: none.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Template Model owns cover policy; Compiler owns metadata resolution; RenderPlan owns semantic
  values; Renderer owns DOCX translation.
- Parser and Domain remain independent of template and DOCX modules.
- No database, migration, network, account, secret or AI dependency.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- `FLOW-VALIDATE` reports field-specific cover template errors.
- `FLOW-BUILD` passes the validated template and renderer-neutral cover instruction through the
  existing compile/render flow.
- Existing Web and Tauri DTOs are unchanged.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Reuse `ParagraphStyleSpec` and the shared DOCX paragraph style translator.
- Extend `ThesisTemplate` with `CoverSpec`; do not duplicate cover formatting primitives.
- Keep `CoverInstruction` free of `python-docx`, `lxml`, raw OOXML and Word style IDs.

## Unresolved Gaps

None for this slice.
