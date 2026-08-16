# Component Map — v2 Build Pipeline Seams

## Proposed Shared Components

- `templates.v2.mapping`：`to_thesis_template(package: ResolvedTemplatePackage) ->
  ThesisTemplate`。以继承合并后的 resolved_data 为输入，反向 migrate 映射
  （字段剥离 + 重命名 + 枚举对齐），未知/缺必填 → 结构化 TemplateMappingError。
  探针实证：直接 model_validate 失败 28 项（20 extra_forbidden / 5 missing /
  3 model_type）即映射工作清单；契约测试 v0.3→migrate→v2→map 语义等价。
- `application.template-source`：`classify_template_source(path) -> kind` +
  `resolve_template_source(explicit_path, template_id, search_roots) ->
  ResolvedTemplateContext`（template + package + path + error）。v0.3 委托
  既有 resolver；v2 走 unpack（.tftpl）/load/lint 门禁/映射。

## Reused Components

- `templates.v2.load_package`（探针实证：sample 与 HUT migrate 包均可加载）
- `templates.v2.lint_package`（L1+L2 门禁；sample 探针 0 issue）
- `templates.v2.unpack_package` / `verify_package`（.tftpl 往返探针通过）
- `templates.v2.merge_into_shell`（探针实证：真实 rendered.docx 合并成功，
  39KB 产物）
- `templates.resolver`（v0.3 路径原样委托）

## Hooks

- 无（无 UI/事件钩子）。

## Utilities / Services

- Utilities：`classify_template_source`、`to_thesis_template`（纯函数）。
- Services：`build_service`/`validation_service`/`inspect_service` 经
  template-source 消费 ResolvedTemplateContext；build 在有 shell 时在
  FINALIZE 前插入 merge_into_shell。
