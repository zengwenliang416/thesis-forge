# Acceptance Criteria: template-v2-build-pipeline-p1

## User-Visible Criteria

- U1: `thesisforge build --template <v2-dir>`（含 `template.yaml`、`schema_version: 2`）
  成功产出 DOCX；无 shell.docx 时产物与 v0.3 同模板产物语义一致。
- U2: `thesisforge build --template <x.tftpl>` 同效：解包 → manifest 对账 →
  L1+L2 门禁 → 编译；门禁失败以结构化诊断报错（exit 1/2），不产生输出文件。
- U3: `thesisforge validate --template <v2-dir|.tftpl>` 与 `inspect` 接受 v2 来源，
  结果与 v0.3 模板语义一致。
- U4: front matter `render.template_id` 解析保持 v0.3-only（id 注册表）；v2 包只经
  `--template` 显式路径选择，`template_id` 指向 v2 包 id 时报结构化「模板未找到」
  错误而非误导产物。
- U5: 包带 shell.docx 时产物保留 shell 的封面/原创性声明/目录锚点结构，
  正文渲染内容完整存在于 `tf_body` 锚点之后。
- U6: 包缺 `tf_body` 锚点时 build 报 `missing-body-anchor` 类结构化错误并停止。

## System Criteria

- S1: v2 → `ThesisTemplate` 映射为纯函数：同输入同输出（确定性双跑），
  且对 `load_package` 的继承合并 resolved data 完整覆盖编译所需字段。
- S2: 有 shell 合并产物通过 `qa/tools/openxml_validate.py` 全部检查。
- S3: 无 shell 时构建产物确定性：同输入双跑字节一致。
- S4: 恶意 `.tftpl`（Zip Slip 路径、解压炸弹）被防护拒绝并给出结构化诊断。
- S5: L1/L2 门禁失败（含 `.tftpl` manifest sha256 不符）→ build 停止，输出诊断。
- S6: 合并产物 finalization 顺序：LO 字段刷新（如可用）→ openxml_validate →
  原子替换输出。
- S7: v0.3 模板路径完全不变：现有 812 测试全绿（零回归）。

## Data Criteria

- D1: 映射错误与门禁诊断为结构化输出（severity/code/target/message），
  CLI `--json` 可机读。
- D2: `.tftpl` 解包目录生命周期受控：构建结束清理临时目录，不残留用户可见产物。

## Component Criteria

- C1: v2→`ThesisTemplate` 映射作为 `templates/v2` 新公共组件实现并被 build
  服务复用，不在 application/services 内复制映射逻辑。
- C2: 模板来源分类（v0.3 yaml / v2 dir / .tftpl）作为独立解析函数实现，
  CLI 与 services 共用同一分类器。

## Verification Surfaces

- Facticity: 映射组件与分类器的实现位置/公共 API 与 component-impact-map 声明一致。
- Static: `ruff check .` 无错；OOXML 改动配 XML 结构断言。
- Unit: 映射全字段覆盖单测；分类器边界单测（.yaml/.tftpl/目录/畸形输入）；
  门禁与解包防护单测。
- Redteam: 恶意 .tftpl（Zip Slip/炸弹/manifest 篡改）负例。
- E2E: HUT v2 包（migrate 产出）驱动 build 全链路；`openxml_validate` 全过；
  v0.3/v2 同模板产物语义对照。
- Sensory: 产物在 Word/WPS/LibreOffice 至少一种人工抽查（manual-pending 标注）。

## Unresolved Gaps

- 无（Q1–Q4 已定）。
