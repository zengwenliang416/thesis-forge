## Context

- 现状：`build/validate/inspect` 的模板来源只有 v0.3 单 YAML ——
  `ValidationContext.from_document`（core/validator.py）读 front matter
  `render.template_id` + `--template` 显式路径，经 `resolve_template`
  （templates/resolver.py）产出 `ThesisTemplate`。front matter 没有路径型
  `template:` 字段（只有 id）。
- v2（ADR-0002）已有完整能力：`load_package`（继承合并 → `ResolvedTemplatePackage`：
  template/TemplatePackageSpec、reference_docx、shell_docx、resolved_data）、
  `lint_package`（L1–L5）、`unpack_package`/`verify_package`（.tftpl 防护 +
  manifest 对账）、`merge_into_shell`（PackageEditor 锚点合并）。
- 缺口：v2 包无法驱动 build；shell.docx 封面/声明/锚点在产物中不可用。

## Goals / Non-Goals

Goals:
- `--template` 接受 v2 包目录 / `.tftpl`，自动判别格式（.yaml → v0.3）。
- `.tftpl` 解包（防护 + manifest 对账）→ L1+L2 门禁 → 编译主链不变。
- v2 resolved data → `ThesisTemplate` 纯函数映射，编译/渲染共用。
- 有 shell.docx 必合并（render 后、finalization 前）；无 shell 退化。
- validate/inspect 同面支持 v2；v0.3 路径零回归。

Non-Goals:
- `template_id` 注册表解析 v2 包（保持 v0.3-only；v2 只走显式路径）。
- reference.docx 作为产物基文档（仅 L5/校验资产）。
- expected/manifest.json XPath 产物断言（另立项）。
- templates/schools/ 真实模板迁移（依赖 template migrate 的独立遗留）。

## Decisions

### D1 模板来源分类器（application/template_source.py）

- `classify_template_source(path) -> "v0.3" | "v2-dir" | "v2-tftpl" | "invalid"`：
  - `.yaml`/`.yml` 文件 → v0.3（既有路径，行为不变）；
  - `.tftpl` 文件 → v2-tftpl；
  - 目录：含 `template.yaml` 且 `schema_version: 2` → v2-dir；否则 invalid。
- CLI 与 services 共用；分类器不 import typer/CLI。

### D2 v2 解析上下文（ResolvedTemplateContext）

- `resolve_template_source(explicit_path, template_id, search_roots) -> ResolvedTemplateContext`
  - v0.3：委托既有 `resolve_template`（不变）。
  - v2-dir：`load_package(dir)`。
  - v2-tftpl：在受控临时目录 `unpack_package`（TemporaryDirectory 生命周期
    由调用方管理：build 用 temporary 输出同款 scope），再 `load_package`。
  - 上下文携带：`template: ThesisTemplate`（映射后）、`package:
    ResolvedTemplatePackage | None`（shell/reference 路径）、`path`、错误。
- `ValidationContext` 增可选 `template_package` 槽（validator 导入
  templates 系类型，无新依赖方向）。

### D3 v2 → ThesisTemplate 映射（templates/v2/mapping.py）

- `to_thesis_template(package: ResolvedTemplatePackage) -> ThesisTemplate`：
  以继承合并后的 `resolved_data` 为准，字段名反向映射 v2 → v0.3
  （对照 migrate.py 的 v0.3→v2 映射表反向实现）。
- 纯函数、确定性；不 import docx/lxml/renderers。
- 契约测试：v0.3 模板 → `migrate_template` → v2 包 → `to_thesis_template`
  → 与原 v0.3 `ThesisTemplate` 语义等价（字段级断言）。
- 未知/缺失必填字段 → 结构化 `TemplateMappingError`（severity/code/target）。

### D4 build 接线与 shell 合并

- `build_service`：模板解析走 D2 上下文；render 到临时路径后，若
  `context.package.shell_docx` 存在 → `merge_into_shell(shell, rendered,
  output_temp)`，再走既有 finalization（refresh_document_safely →
  package_validator → replace_output）。无 shell → 现状。
- 缺 `tf_body` 锚点 → `PackageMergeError`（missing-body-anchor）→
  ApplicationStageError(FINALIZE) 结构化报错。
- L1+L2 门禁：v2 来源在 load 前 `lint_package(level="L2")`，has_errors →
  结构化诊断（复用 CLI template lint 的输出形状）。

### D5 validate/inspect 接线

- `_create_validation_context` / `ValidationContext.from_document` 的
  template_path 参数改经 D1/D2 分类解析：v2 → 映射模板进 context，
  `template_package` 槽随行；validator 行为不变（模板样式检查同 v0.3）。
- `template_id` 路径完全不变（resolve_template 原逻辑）。

## Risks / Trade-offs

- 映射字段漂移（v2 schema 与 v0.3 model 演进不同步）→ D3 契约测试 +
  字段级断言兜底；migrate 往返测试锁定。
- .tftpl 解包目录生命周期泄漏 → D2 用与 `temporary_output_path` 同款
  scope 管理；D2 验收（临时目录构建后清理）。
- shell 合并产物与 LO 刷新兼容性 → 合并先行于 finalization；e2e 过
  openxml_validate（S2）；Word/WPS 人工抽查标 manual-pending（Sensory）。
- v2 门禁严于 v0.3（L1+L2）→ 仅在 v2 来源生效，v0.3 无感知（S7 回归）。

## Migration Plan

- 无数据迁移；v0.3 路径不动。templates/schools/ 真实模板迁移为 v2 是
  独立遗留（依赖 template migrate，另立项）。
- 文档：TEMPLATE_SPEC（v0.3 不变）；TEMPLATE_PACKAGE_SPEC_V2/ADR-0002
  补「build 消费」记录。
