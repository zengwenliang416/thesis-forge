# Prototype Question: template-v2-build-pipeline-p1

## Question

是否批准 `v2-build-pipeline-seams-v1` 组件边界：模板来源分类器（v0.3 yaml /
v2 目录 / .tftpl 自动判别）+ `templates.v2.mapping.to_thesis_template`
（resolved_data → ThesisTemplate 反向映射）+ build 的 shell 合并接线
（render 后、finalization 前经 `merge_into_shell` 锚点合并）作为生产开发依据？
映射字段差集与接缝可行性以 `component/seam_probe_results.json` 实证为准。

## Branch

`component-seam`

## Review Target

- Entry: `component/component-map.md`
- Variant: `v2-build-pipeline-seams-v1`
- Probe evidence: `component/seam_probe_results.json`（真实 API 调用结果：
  sample 包 load/lint/tftpl 往返/merge 全通；HUT migrate 包 26/11/5；
  resolved_data 直接 validate 28 错误 = 映射工作清单）
- Required reviewer decision: 是否批准分类器/映射/shell 合并三个接缝的
  依赖方向、映射策略（反向 migrate 映射 + 契约测试）、门禁顺序
  （解包 → manifest 对账 → L1/L2 → 编译）与测试边界作为生产开发依据。

## Out of Scope

- Production implementation（原型不改生产代码）。
- reference.docx 作为产物基文档（Q3 决策：仅校验资产）。
- template_id 注册表解析 v2（Q4 决策：v0.3-only）。
