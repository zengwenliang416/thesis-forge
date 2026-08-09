# Requirements: template-driven-list-layout-p1

## Summary

实现模板驱动论文列表纵向切片。Markdown 继续只表达列表语义和起始序号，学校 YAML 模板
负责各层编号格式、项目符号、对齐、缩进和段落样式；DOCX Renderer 将模板策略翻译为
真实 Word numbering 对象，不再固定列表版式。

## Users & Actors

- 论文作者：使用标准 Markdown 有序和无序列表，不写学校版式参数。
- 学校模板维护者：通过 YAML 配置多级列表格式，不修改 Renderer。
- ThesisForge 开发者：维护 Template Model、renderer-neutral RenderPlan 和 DOCX 翻译。
- 文档审核者：在 Word 或 WPS 中检查编号、项目符号、缩进和正文排版。

## In Scope

- 新增 `ListSpec`，分别包含 ordered 和 unordered 多级策略。
- 每种列表必须声明 1 至 9 个层级；Markdown 深度超过模板层级时复用最后一层策略。
- 有序层级支持 `decimal`、`lower_letter`、`upper_letter`、`lower_roman` 和
  `upper_roman` 语义编号格式。
- 有序层级支持 `prefix`、`suffix`、marker alignment、绝对左缩进和悬挂缩进。
- 无序层级支持非空 `marker`、marker alignment、绝对左缩进和悬挂缩进。
- 每层复用完整 `ParagraphStyleSpec` 配置列表文本和段落排版。
- Markdown `start` 和 item ordinal 继续决定首层有序列表的起始编号。
- 通用默认精确复现当前 9 层 decimal、项目符号循环和缩进行为。
- HUT 模板显式声明学校列表规则，不在 Renderer 中加入学校值。
- 增加模板校验、RenderPlan 中立性、OOXML 和完整离线构建测试。
- 更新 `docs/TEMPLATE_SPEC.md` 和内置模板。

## Out of Scope

- 修改 Markdown 列表语法、AST 或稳定 ID 规则。
- 自动推断学校列表规则或从现有 DOCX 反向导入样式。
- 自定义图片项目符号、Wingdings 字体、复选框列表或任意 raw OOXML。
- 在一个连续列表块内动态切换多个 numbering policy。
- Word、WPS 和 LibreOffice 逐像素一致。

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- No production UI change. Existing template selection and build flows consume the additive YAML
  contract.

## Theme & Locale Capability Impact

- Theme support: `light-only`.
- Theme toggle policy: `none`.
- Internationalization: `disabled`.
- Supported locales: `zh-CN`.
- Default locale: `zh-CN`.
- Prototype coverage: no UI prototype; component-seam review only.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- Template Model owns list policy; RenderPlan owns list semantics; DOCX Renderer owns numbering.xml
  translation and paragraph application.
- Parser and Domain remain independent of Template Model and DOCX modules.
- No database, migration, network, account, secret or AI dependency.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- `FLOW-VALIDATE` reports field-specific list template errors.
- `FLOW-BUILD` passes the validated template and renderer-neutral list instruction through the
  existing compile/render flow.
- Existing Web and Tauri DTOs are unchanged.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Reuse `ParagraphStyleSpec` and the shared DOCX paragraph-style translator.
- Add typed ordered/unordered level models under `ThesisTemplate`; do not expose `w:numFmt`,
  `w:lvlText` or other OOXML names in YAML.
- Keep `ListInstruction` free of Template Model, python-docx, lxml and raw OOXML.

## Unresolved Gaps

None for this slice.
