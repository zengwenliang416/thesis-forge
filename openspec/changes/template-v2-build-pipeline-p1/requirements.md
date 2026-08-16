# Requirements: template-v2-build-pipeline-p1

## Summary

Template Package v2（ADR-0002，目录或 `.tftpl`）接入编译管线：`build/validate/inspect`
的模板选择面接受 v2 包来源（与 v0.3 单 YAML 并存、自动判别），v2 模板数据映射为编译
共用模型驱动渲染；包带 `shell.docx` 时渲染产物经 PackageEditor 锚点合并进 shell，
产物保留学校真实封面/声明/目录结构，然后走现有 finalization。

## Users & Actors

- CLI 用户（论文作者/学校模板维护者）：通过 `--template` 或 front matter
  `template:` 显式给出 v2 包目录或 `.tftpl` 文件路径。
- 现有 v0.3 用户：行为完全不变（回归约束）。

## In Scope

- 模板来源自动判别：值指向「含 `template.yaml` 且 `schema_version: 2` 的目录」或
  「`.tftpl` 文件」→ v2 包；指向 `.yaml/.yml` 文件 → v0.3（既有行为）。
- `build/validate/inspect` 三命令同面支持 v2 来源；v2 包经 `--template` 显式路径
  选择（front matter 仅 `render.template_id` id 注册表，保持 v0.3-only）。
- `.tftpl` 消费：隔离临时目录解包（复用 pack 的 Zip Slip / 解压炸弹防护与
  manifest sha256 对账），build 前跑 L1+L2 门禁，失败即结构化诊断并停止。
- v2 → 编译模型映射：`TemplatePackageSpec` 的继承合并后 resolved data 映射为
  `ThesisTemplate`（`templates/v2` 内新增纯函数，与 migrate 的 v0.3→v2 映射对应，
  确定性、无副作用）。
- shell 合并：包带 `shell.docx` 时，渲染产物经 `merge_into_shell` 合并进 shell
  锚点（`tf_body` 必需，`tf_toc`/`tf_bibliography` 可选，缺失锚点按既有
  `missing-body-anchor` 语义报错）；合并产物继续走 finalization（LO 字段刷新 →
  openxml_validate → 原子发布）。无 shell.docx 时退化为普通渲染、不报错。
- reference.docx 仅作 L5/校验资产（沿用 lint），不参与产物样式。
- 端到端验证：`migrate` 产出的 HUT v2 包驱动 build，产物过
  `qa/tools/openxml_validate.py` 与结构断言；无 shell 时与 v0.3 同模板产物
  语义一致且确定性双跑字节一致。

## Out of Scope

- front matter `template_id` 注册表解析（`templates/schools/` 按 id 找 v0.3）保持
  v0.3-only；v2 包只走显式路径。
- reference.docx 作为产物基文档（渲染器基文档路径不变）。
- expected/manifest.json 的 XPath 级产物断言（ADR-0002 已知遗留，另行立项）。
- 把 `templates/schools/` 真实模板迁移为 v2 包（依赖 `template migrate` 的独立遗留）。
- 任何 UI/Web/Tauri 变更。

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- 无 UI 变更；CLI 输入面扩展（参数语义）不触及 UI design spec。

## Theme & Locale Capability Impact

- Theme support: `none`（CLI 无主题概念）
- Theme toggle policy: `theme-toggle:none`
- Internationalization: `disabled`（CLI 诊断沿用现有 zh 消息，不在本切片扩展）
- Supported locales: `locales:none`
- Default locale: `default-locale:zh-CN`（沿用现有 CLI 消息语言）
- Prototype coverage: `none`（无 UI 原型需求）

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- 新增 `templates/v2/mapping`（v2 spec → `ThesisTemplate` 纯函数映射）：
  只读 Template Package v2 模型，无 DOCX/Parser 依赖。
- application services 的模板来源解析层扩展：来源分类（v0.3 yaml / v2 dir /
  .tftpl）→ 统一产出 `ThesisTemplate` 给既有 validate/compile 主链；
  v2 附带 shell/reference 路径随 `TemplateSource` 上下文传递到 build 服务。
- finalization 顺序不变，合并发生在渲染后、finalization 前。

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- 无 frontend-backend 数据流变更（CLI 本地流水线）。

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- 复用：`templates/v2` 的 `load_package`/`lint_package`/`unpack_package`/
  `verify_package`/`merge_into_shell` 与 `templates/resolver` 的既有解析入口。
- 新增组件：`templates/v2` 内 v2→v0.3 映射纯函数（公共 API 命名待开发阶段
  确定，按 component-impact-map 记录）。
- 禁止依赖：mapping 不依赖 `docx`/`lxml`/Renderer；services 不反向依赖 CLI。

## Unresolved Gaps

- 无（Q1–Q4 已定：自动判别 / 有 shell 必合并 / reference 仅校验资产 /
  三命令同面 + 门禁；template_id 保持 v0.3-only）。
