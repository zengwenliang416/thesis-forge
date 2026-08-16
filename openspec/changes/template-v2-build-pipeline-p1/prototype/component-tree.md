# Component Seam Prototype — v2 Build Pipeline

## Component Tree

- CLI（`thesisforge build|validate|inspect --template <v2-dir|.tftpl>`）
  - `application.template-source`（新）：来源分类器 + ResolvedTemplateContext
    - `templates.v2.pack.unpack_package`（.tftpl → 受控临时目录，Zip Slip/炸弹防护）
    - `templates.v2.pack.verify_package`（manifest sha256 对账，L1–L3）
    - `templates.v2.lint.lint_package`（build 前 L1+L2 门禁）
    - `templates.v2.package.load_package`（继承合并 → ResolvedTemplatePackage）
    - `templates.v2.mapping.to_thesis_template`（新）：resolved_data → ThesisTemplate
  - `core.validator.ValidationContext`（+`template_package` 槽；模板样式检查不变）
  - `core.compiler.compile_document`（不变；消费映射后的 ThesisTemplate）
  - `renderers.docx.DocxRenderer`（不变；render 产物到临时路径）
  - `templates.v2.package_editor.merge_into_shell`（有 shell 时：render 后合并）
  - application finalization（不变：LO 刷新 → openxml_validate → 原子发布）

## Cohesion Check

- 分类器/上下文（template-source）：一个理由变化 = 模板来源的格式集与解析顺序；
  状态拥有者 = 无（纯函数 + 不可变 context）；副作用 = .tftpl 临时目录
  （TemporaryDirectory scope，调用方管理）。
- 映射（templates.v2.mapping）：一个理由变化 = v2 schema 与 v0.3 model 的字段
  漂移；状态拥有者 = 无（纯函数）；副作用 = 无。
- shell 合并接线（build 服务）：一个理由变化 = 合并时机与缺省策略；
  状态拥有者 = build 流程；副作用 = 产物路径替换（沿用 temporary_output_path）。

## Coupling Check

- Allowed imports：template-source → templates.v2（pack/lint/package/mapping）、
  templates.resolver（v0.3 委托）；mapping → templates.model、templates.v2.schema。
- Forbidden imports：mapping/template-source 不 import docx/lxml/renderers/CLI；
  core.validator 不 import templates.v2 实现（仅类型槽）。
- Public API：`classify_template_source(path)`、`resolve_template_source(...)`、
  `to_thesis_template(package)`。
- Extraction target：`application/template_source.py`、`templates/v2/mapping.py`
  （均为新模块，无既有组件提取）。
