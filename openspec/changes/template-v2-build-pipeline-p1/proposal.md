## Why

ADR-0002 的 Template Package v2（`.tftpl` 打包、L1–L5 lint、PackageEditor
shell 合并、migrate）已全部落地并有 CLI 工具，但编译管线仍只消费 v0.3 单
YAML 模板：`build/validate/inspect` 的模板选择面（front matter `template:`
字段与 `--template` 参数）只能解析 `ThesisTemplate`。ADR-0002 §8「已知遗留」
第一条即「v2 包接入编译管线（build 消费 ResolvedTemplatePackage）」——
真实学校的 v2 包（目录或 `.tftpl`）目前无法直接驱动 `thesisforge build`，
shell.docx 封面/声明/锚点能力在产物中完全不可用。

## What Changes

- 模板选择面扩展：front matter `template:` 字段与 `--template` 参数接受
  v2 包目录或 `.tftpl` 文件，与 v0.3 单 YAML 并存，自动判别格式。
- `.tftpl` 消费：build 时解包到隔离临时目录（复用 pack 的 Zip Slip /
  解压炸弹防护与 manifest 对账），build 前跑 L1+L2 门禁。
- v2 → 编译模型映射：`TemplatePackageSpec`（含继承合并后的 resolved data）
  映射为编译/渲染共用的 `ThesisTemplate`（reverse mapping，与 migrate 的
  v0.3→v2 映射对应），编译主链不变。
- shell 合并：包带 `shell.docx` 时，渲染产物经 `PackageEditor/merge_into_shell`
  合并进 shell 锚点（`tf_body` 必需，`tf_toc`/`tf_bibliography` 可选），
  产物保留学校真实封面/原创性声明/目录锚点；无 shell 时退化为普通渲染。
- reference.docx 与 finalization：reference.docx 的角色与 LO 字段刷新 /
  openxml_validate / 原子发布的行为按需求阶段决策（见 requirements）。
- 端到端验证：真实 v2 包（migrate 产出的 HUT 包）驱动 build，产物过
  openxml_validate 与结构断言，且与 v0.3 同模板产物语义一致。

## Capabilities

### New Capabilities

- `template-v2-build`: build/validate/inspect 消费 Template Package v2
  （目录或 `.tftpl`），含 v2→v0.3 映射与 shell 合并。

### Modified Capabilities

- `offline-cli-pipeline`: 模板选择面接受 v2 包来源，编译主链与 finalization
  行为不变或按需求决策扩展。
- `template-v2-package`: 增加 build 消费侧的映射与门禁接线（L1+L2 前置、
  manifest 对账、shell 合并入口）。

## Impact

- Affected code: templates/v2（mapping、build 接线）、application services
  （模板来源解析）、CLI（`--template` 语义）、renderers（shell 合并产物
  路径）、tests（端到端 + 映射单测 + 结构断言）。
- Public contract: `build/validate/inspect` 的输入面扩展（模板来源可以是
  v2 包）；输出 DOCX 契约在无 shell 时不变，有 shell 时产物承载 shell
  结构（封面/声明/锚点）。
- Dependencies: 无新增 Python 包依赖；`.tftpl` 解包与校验全离线确定性。
- Architecture: 保持 `Markdown -> ThesisDocument -> Validation -> Template
  -> RenderPlan -> DOCX`；v2 只是 Template 来源的第二种格式，编译主链与
  renderer-neutral 计划不变。
