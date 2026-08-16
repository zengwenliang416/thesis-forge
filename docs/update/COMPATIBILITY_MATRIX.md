# ThesisForge 兼容矩阵（Compatibility Matrix）

> 状态：Accepted（ADR-0006 配套文档）
> 日期：2026-08-15
> 关联：`docs/update/adr/ADR-0006.md`；风险 R-006 / R-007 / R-014 /
> R-015 / R-027 / R-028
> 证据基线：`spikes/phase0/fields/`（字段生命周期 spike）与
> `spikes/phase0/docx-template/`（模板合并 spike）首轮实测；
> `qa/results/<run-id>/` 承接后续正式 run 证据。

## 1. 承诺等级定义

模板包 `compatibility.target_apps` 与本矩阵共用三级承诺（另允许
`unsupported` 显式标注不支持；primary 恰允许一个，
`docs/update/TEMPLATE_PACKAGE_SCHEMA_V2.md` §3.2）：

| 等级 | 语义 | 验收标准 |
| --- | --- | --- |
| primary | 权威基准：版式、分页、字段求值以该应用为准；最终提交件必须在该应用验证 | ① no_repair_open pass（无修复提示）；② 字段刷新后 TOC/REF/SEQ/PAGE 全部正确；③ 目录/页码/页眉页脚/OMML 人工验收通过；④ 导出 PDF 正确；⑤ 每个 RC 留存截图/PDF/JSON 证据 |
| compatible | 可正常打开与编辑，承诺核心对象可用；已知差异逐项列出，不承诺与 primary 像素一致 | ① 打开无修复（自动不可测时人工确认闭环）；② 交叉引用/题注编号/页码保持可用；③ 已知差异清单无新增未评估项 |
| preview | 仅承诺可打开、可导出 PDF 用于预览与相对回归；不作最终版式权威 | ① headless 转 PDF 成功；② openxml_validate 通过；③ 视觉回归仅作相对比较（标注渲染引擎，R-028） |

## 2. 当前定级

| 应用 | 承诺等级 | 实测版本 | 证据日期 |
| --- | --- | --- | --- |
| Microsoft Word（macOS） | primary | 16.107.2 | 2026-08-15 |
| WPS Office（macOS） | compatible | 6.7.1 | 2026-08-15 |
| LibreOffice（macOS） | preview | 26.2.3.2 | 2026-08-15 |

Windows 版 Word 的 primary 验证、三应用其余 OS 组合为后续阶段扩展项；
模板包的 `review.verified_with` 必须包含 primary 应用（SCHEMA §3.21
L4 warning 约束）。

## 3. 能力矩阵（应用 × 能力）

| 能力 | Word 16.107.2（primary） | WPS 6.7.1（compatible） | LibreOffice 26.2.3.2（preview） |
| --- | --- | --- | --- |
| 打开无修复 | pass（附首开弹窗行为，见 §4.1） | pending-human-review | pass |
| 字段刷新（TOC/REF/SEQ/PAGE） | pass（实测刷新 0 失败；SEQ `\r` 钉值保留） | 未实测 | pass 但有改写（见 §4.3） |
| OMML 公式 | 待测（spike `spikes/phase0/omml/` 已产出结构证据，应用端验收待 Alpha） | 未实测 | 待测 |
| 页眉页脚（多节 + first/even/default） | pass（页码排版正确；Mac AppleScript 无 header/footer 对象模型，自动断言受限） | 未实测 | pass（刷新会重写部件，见 §4.3） |
| 页码格式（roman/decimal + 重启） | pass（导出 PDF 罗马/阿拉伯混排正确） | 未实测 | pass（PAGE cached 评估值出现过 0，见 §4.3） |
| 目录（TOC 域） | pass 但首开不自动填充（见 §4.1）；刷新后填充为真实条目 | 未实测 | finalizer 刷新后填充，但指令被改写 |
| 导出 PDF | pass（Word `save as PDF` 成功） | 未实测 | pass（headless 转换成功） |

「未实测/待测」项是 Alpha–Beta 期间按 `qa/catalog/cases/`（如
TF-D5-WRD-001）补齐的证据义务，不构成现状承诺。

## 4. 当前实测证据

### 4.1 Word 16.107.2

- **no-repair pass**：`complete-thesis-example.docx` 复核 pass
  （11.14s，未探测到对话框）；证据
  `spikes/phase0/fields/results/no-repair.json`。
- **首开弹窗行为（已知，非修复提示）**：带 `w:updateFields` 或
  `w:fldChar w:dirty` 的生成态文档首开必弹模态确认框
  「该文档包含的域可能引用了其他文件。是否更新该文档中的这些域？」；
  三格对照变体证明两者**各自独立触发**，全部剥掉后静默打开
  （3.41s/3.78s pass）。证据：`spikes/phase0/fields/results/no-repair-*.json`、
  `spikes/phase0/fields/REPORT.md` §4–§5。
- **字段刷新**：`update` TOC + 逐字段 `update field` 全部成功
  （complete 样本 update_log 计数 50）；TOC 填充为真实条目且指令保持
  `TOC \o "1-3" \h \z \u` 不变；全部 REF/SEQ 刷新前后 result 一致；
  SEQ `\r` 钉值在 F9 后仍生效（编译期编号权威语义）。点「否」拒绝
  更新时 TOC 为空且导出 PDF 不自动填充。证据：
  `spikes/phase0/fields/results/word-refresh.json`、
  `samples/*-word-declined.pdf`、`samples/*-word-refreshed.pdf`。
- **结构校验**：两份样本 openxml_validate 13/13 + 6 项 XPath 断言
  全过。证据：`spikes/phase0/fields/results/structure-checks.json`。

### 4.2 LibreOffice 26.2.3.2

- **no-repair / 导出 PDF pass**：两份样本 headless 转 PDF 成功
  （351,940 / 139,451 字节）。证据：
  `spikes/phase0/fields/results/no-repair.json`。
- **finalizer（headless 刷新）已知限制**（`spikes/phase0/fields/
  REPORT.md` §6，证据 `results/lo-refresh-diff.json`）：
  - ~~TOC 指令被改写为 `TOC \f \o "1-3" \h`（丢 `\z \u`，新增 `\f`）~~
    **已修复（2026-08-15）**：finalizer 刷新后把 TOC 指令还原为编译期
    原指令（`office_refresh._restore_field_instructions`）；
  - ~~SEQ `\r` 钉值被剥掉（刷新后 Word 端 F9 恢复顺序重算）~~
    **已修复（2026-08-15）**：刷新后按种类+文档顺序还原 SEQ 指令的
    `\r N` 钉值；字段数量/种类对不上时整体回滚；
  - `w:updateFields` 被移除（刷新后 Word 首开不再弹窗）——保留为收益；
  - 页眉页脚部件被整体重写（字段在 footer 部件间重新分布）——
    仍为已知差异，字段指令未变、openxml_validate 通过；
  - 新增 `__RefHeading___Toc…` 书签（complete 19 个 / minimal 1 个）——
    保留（LO 生成的 TOC 超链接目标，书签配对校验通过）；
  - PAGE cached 被写为评估值，minimal 样本封面节出现 `PAGE cached=0`；
  - ~~**刷新后 openxml_validate 失败**：LO 引用的 TOC1-3 / IndexLink /
    FootnoteCharacters 样式未在渲染器 styles.xml 定义~~
    **已修复（2026-08-15）**：TOC1-3 段落样式恒定义（Phase 1），渲染器
    再无条件定义 Index Link / Footnote Characters 字符样式
    （`styles.LO_REFRESH_CHARACTER_STYLE_NAMES`）；刷新后
    openxml_validate 13/13 通过（`tests/test_lo_finalizer.py`）。
- 用途限定：draft/final-auto finalizer 执行器；不作最终
  版式权威（R-028，final-word 为 GA 权威最终件路径）。

### 4.3 WPS 6.7.1

- **pending-human-review**：wpsoffice 无可靠脚本接口判断修复提示，
  `qa/tools/no_repair_open.py` 只能打开并标 `pending-human-review`
  （`qa/README.md`；fields spike 未纳入自动结论，报告 §4）。本轮
  实测版本 6.7.1 已安装并打开样本，人工确认结论待 RC 检查单闭环。
- 后续：WPS 打开无修复、页码与交叉引用可用性纳入 Beta 出口
  （TF-D5-WPS-004 类用例，QUALITY_STRATEGY §2 D5）。

## 5. 已知差异清单

| # | 差异 | 影响 | 证据/出处 | 处置 |
| --- | --- | --- | --- | --- |
| 1 | Word 首开弹「字段更新确认框」（updateFields 与 dirty 各自独立触发） | draft 产物「双击即开」受打扰；自动化场景阻塞 150s | `spikes/phase0/fields/REPORT.md` §4–§5 | finalizer profiles 决策（ADR-0005）；no_repair_open 改进弹窗分类 |
| 2 | ~~LO finalizer 改写 TOC 指令、剥 SEQ `\r`~~、移除 updateFields、重写页眉页脚 | final-auto 产物与生成态语义有差异 | `results/lo-refresh-diff.json` | **前两项已修复（2026-08-15，刷新后指令还原）**；updateFields 移除为保留收益；页眉页脚重写为残留差异；final-word 为权威最终件路径（R-006/R-027 退路） |
| 3 | ~~LO 刷新后 openxml_validate 失败（TOC1-3/IndexLink/FootnoteCharacters 未定义）~~ | ~~final-auto 产物暂不能过同一套门禁~~ | `results/lo-refresh-diff.json`；报告 §6 | **已修复（2026-08-15）**：渲染器无条件补齐上述样式；刷新后 openxml_validate exit=0（`tests/test_lo_finalizer.py` 回归） |
| 4 | Word 对空 TOC 不自动填充、导出 PDF 也不填充 | 拒绝更新的用户看到空目录 | `samples/*-word-declined.pdf`；报告 §5 | final-auto 填充 TOC cached；或 draft 明确提示（ADR-0005） |
| 5 | LO 对「该节不显示页码」的评估与 Word 语义可能不一致（PAGE cached=0） | preview 级中间态页码显示 | 报告 §6 | 接受为 preview 差异；Word 显示时按节语义重算 |
| 6 | Mac Word AppleScript 无 header/footer 对象模型，`get story range` 仅覆盖第 1 节 | 页脚字段自动断言覆盖不全 | 报告 §5 局限、§10.3 | 以导出 PDF 物理证据兜底 |
| 7 | WPS 无脚本接口，修复提示只能人工判断 | 兼容证据依赖人力 | `qa/README.md`；报告 §4 | RC 检查单人工确认；保持 compatible 而非 primary |

## 6. 维护规则

- 每次 RC 重跑三应用证据并更新 §2 版本与 §3 矩阵；证据 JSON 落
  `qa/results/<run-id>/`（qa/README.md 约定：大型二进制走 CI
  artifact，`run.json` 与摘要长期保留）。
- 新增已知差异必须有证据文件与处置列；升级承诺等级（如 WPS
  compatible → 更深承诺）需对应能力行全部有证据。
- LibreOffice 证据仅作相对回归，必须标注渲染引擎（R-028）；不使用
  LO 页数作为唯一权威（R-028 退路）。
- 目标应用版本升级导致的回归按缺陷分级处理（QUALITY_STRATEGY §14），
  S1/S2 阻断发布。
