## 1. Template Source Classification

**用户结果：** `--template` 给出 `.yaml`、v2 包目录或 `.tftpl` 时自动判别格式，畸形来源得到结构化诊断；CLI 与 services 共用同一分类器。

- [ ] 1.1 新增 `application/template_source.py`：`classify_template_source(path)` 按 D1 规则返回 `v0.3` / `v2-dir` / `v2-tftpl` / `invalid`，不 import typer/CLI。
- [ ] 1.2 分类器边界单测：`.yaml`/`.yml` 文件、含 `template.yaml` 且 `schema_version: 2` 的目录、普通目录、`.tftpl` 文件、不存在/畸形输入。
- [ ] 1.3 `invalid` 分类输出结构化诊断（severity/code/target/message），CLI `--json` 可机读。

## 2. v2 → ThesisTemplate Pure Mapping

**用户结果：** v2 包的继承合并 resolved data 确定性映射为编译共用 `ThesisTemplate`，同输入双跑同输出；未知/缺失必填字段得到结构化映射错误。

- [ ] 2.1 新增 `templates/v2/mapping.py`：`to_thesis_template(package)` 纯函数，按 migrate 反向映射字段，不 import docx/lxml/renderers。
- [ ] 2.2 映射全字段覆盖单测 + 确定性双跑断言（S1）。
- [ ] 2.3 契约测试：v0.3 模板 → `migrate_template` → v2 包 → `to_thesis_template` → 与原 v0.3 `ThesisTemplate` 字段级语义等价。
- [ ] 2.4 缺失/未知必填字段抛 `TemplateMappingError`（severity/code/target）结构化负例测试。

## 3. Resolution Context And Package Loading

**用户结果：** 三种模板来源统一解析为一个携带 `ThesisTemplate` 与可选 shell/reference 路径的上下文；`.tftpl` 在受控临时目录解包并在构建后清理。

- [ ] 3.1 实现 `resolve_template_source` → `ResolvedTemplateContext`（template/package/path/error）；v0.3 委托既有 `resolve_template`，行为不变。
- [ ] 3.2 `.tftpl` 路径：复用 `unpack_package`/`verify_package` 的 Zip Slip、解压炸弹与 manifest sha256 对账防护，临时目录生命周期与 `temporary_output_path` 同款 scope 管理（D2）。
- [ ] 3.3 `ValidationContext` 增可选 `template_package` 槽，validator 模板样式检查行为不变。
- [ ] 3.4 临时目录清理与防护负例单测（恶意 `.tftpl` 拒绝、构建结束无残留，S4/D2-data）。

## 4. Build Wiring, Gates And Shell Merge

**用户结果：** v2 包驱动 build 全链路成功；L1+L2 门禁失败即结构化停止；有 shell.docx 时产物保留学校封面/声明/锚点，缺 `tf_body` 报 `missing-body-anchor`。

- [ ] 4.1 v2 来源在编译前跑 `lint_package(level="L2")`，has_errors → 结构化诊断并停止（S5）。
- [ ] 4.2 `build_service` 接线 D2 上下文；无 shell.docx 时退化为普通渲染，产物与 v0.3 同模板语义一致且双跑字节一致（U1/S3）。
- [ ] 4.3 有 shell.docx 时：render 到临时路径 → `merge_into_shell`（`tf_body` 必需，`tf_toc`/`tf_bibliography` 可选）→ 既有 finalization（LO 刷新 → openxml_validate → 原子发布）（U5/S2/S6）。
- [ ] 4.4 缺 `tf_body` 锚点 → `PackageMergeError` → `ApplicationStageError(FINALIZE)` 结构化报错并停止（U6）。

## 5. Validate And Inspect Wiring

**用户结果：** `validate`/`inspect` 接受 v2 包目录与 `.tftpl`，结果与 v0.3 模板语义一致；`template_id` 注册表保持 v0.3-only。

- [ ] 5.1 `_create_validation_context`/`ValidationContext.from_document` 的 template_path 经分类解析，v2 → 映射模板进 context（D5/U3）。
- [ ] 5.2 `template_id` 指向 v2 包 id 时报结构化「模板未找到」错误而非误导产物（U4）。
- [ ] 5.3 v0.3 模板路径零回归：现有模板解析相关测试全绿（S7）。

## 6. End-to-End Verification And Documentation

**用户结果：** migrate 产出的 HUT v2 包端到端驱动 build 并通过 openxml_validate；用户与架构文档准确描述 v2 消费行为。

- [ ] 6.1 E2E：HUT v2 包（目录与 `.tftpl` 两种形态）驱动 build，产物过 `qa/tools/openxml_validate.py` 与结构断言（含 shell 合并形态）。
- [ ] 6.2 v0.3/v2 同模板产物语义对照断言；确定性双跑字节一致（S1/S3）。
- [ ] 6.3 诊断结构化复查：门禁/映射/合并错误均带 severity/code/target 且 `--json` 可机读（D1-data）。
- [ ] 6.4 更新 TEMPLATE_PACKAGE_SPEC_V2/ADR-0002 的「build 消费」记录与相关文档。
- [ ] 6.5 Ruff、Python/frontend/Rust 检查与 openspec validate --strict 全绿。
- [ ] 6.6 合并产物在 Word/WPS/LibreOffice 至少一种人工抽查（manual-pending）。
