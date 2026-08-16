# ThesisForge V1 产品范围（Product Scope）

> 状态：Accepted（ADR-0006 配套文档）
> 日期：2026-08-15
> 关联：`docs/update/adr/ADR-0006.md`；风险 R-022 / R-023 / R-030；
> 上游：`docs/update/ThesisForge_优化计划_执行摘要.md`、
> `docs/update/QUALITY_STRATEGY.md` §13、`docs/V1_PLAN.md`

## 1. 目标用户与场景

V1 的目标用户是**中文学位论文作者**：本科生毕业论文与硕士学位论文
（含专业学位）。典型场景：

- 用 Markdown 撰写论文正文（图表、公式、脚注、交叉引用、文献引用）；
- 选择所在学校的模板包，执行 `thesisforge validate` / `thesisforge
  build` 得到符合学校格式规范的 DOCX；
- 在 Microsoft Word 中打开产物，确认目录/页码/交叉引用后提交；
- 学校规范改版或模板修正时，用 `template migrate` / 模板版本升级
  重建产物，构建可复现、可归因。

非目标用户（V1 不为其优化）：期刊投稿作者、英文论文为主的作者、
LaTeX 深度用户、需要多人实时协作的团队。

## 2. 范围清单

### 2.1 In-scope（V1）

- 中文学位论文（本科/硕士）单文档与多文件 include 工程；
- 受限学术 Markdown 子集（`docs/MARKDOWN_SPEC.md`）+ 严格诊断；
- Template Package v2：目录形态 + `.tftpl` 打包、reference.docx、
  shell.docx（Beta 起）、继承、provenance、lint L1–L5、显式迁移
  （ADR-0002）；
- 真实 OOXML 对象：TOC/SEQ/REF/PAGEREF/PAGE/NUMPAGES 字段、书签、
  OMML 公式、脚注、节、页眉页脚、三线表（AGENTS.md §1.5）；
- GB/T 7714-2025 顺序编码制参考文献（内建手写引擎 + golden corpus
  验收；pandoc 为可选外部 provider）（ADR-0004）；
- CLI：`inspect` / `validate` / `build` / `doctor` / `template lint、
  pack、verify、inspect、migrate`；
- 字段生命周期与 finalizer profiles（draft / final-auto / final-word，
  ADR-0005）；
- 六域质量门禁与兼容矩阵（ADR-0006、`COMPATIBILITY_MATRIX.md`）；
- 离线安装与离线构建（无网络、无 API Key，AGENTS.md §1.3）。

### 2.2 Out-of-scope（V1 明确不做）

| 项 | 处置 |
| --- | --- |
| 期刊排版（双栏、期刊模板） | 架构不阻断，V1 不投入 |
| 博士论文模板 | 扩展点保留（`document_types` 词表已含 `phd_thesis`），V1 不做官方模板 |
| LaTeX 输入（.tex 源） | 不做；LaTeX 仅作为公式语法 |
| 云协作 / 在线编辑 / 账号系统 | 不做；本地优先 |
| 模板市场 / 模板分发平台 | 不做；`.tftpl` 签名信任模型随之推迟（SCHEMA OQ-6） |
| 桌面 UI | V1.1（R-022：UI 后置，CLI/JSON contract 先稳定） |
| AI 写作/改稿/引用生成 | V1.2，且永不进入编译链路（R-023；AGENTS.md §1.3） |
| 著者-出版年制引用 | GB/T 7714-2025 官方 CSL 三件套已存在，V1 仅 numeric；author-date 视需求后置 |
| GB/T 7714-2015 compatibility profile | 决策推迟到首个真实学校模板需求（ADR-0004 §2.7） |
| 英文论文全链路（双语 locale 引用等） | 已知限制文档化（ADR-0004 §5），V1 不承诺 |

范围纪律（R-030）：任何新需求进入 V1 必须书面说明**替换哪个现有
优先级**；无法说明的一律归入 V1.1/V2 评估。保持核心扩展点，但不提前
实现所有场景。

## 3. 优先级定义

沿用 QUALITY_STRATEGY §14 的缺陷分级（S1–S4）之外的**需求优先级**：

| 优先级 | 定义 | 例子 | 门禁含义 |
| --- | --- | --- | --- |
| P0 | 阻断 V1 核心价值闭环：没有它论文不能正确编译或产物不被 Word 接受 | Parser 契约、Template Package v2、OMML、字段生命周期、GB/T 引用、Word no-repair | P0 用例全过是 Beta/GA 的必要条件 |
| P1 | 重要但有 workaround，或只影响部分模板/平台 | WPS 兼容证据、视觉回归基线、性能基准、多文件 include 完善 | Beta 要求 P1 通过率达标；GA 不允许未豁免的 S1/S2 缺陷 |
| P2 | 体验与生态改进，可推迟到 V1.x | UI 交互细节、模板市场准备、额外引用样式 | 不进入 V1 发布门禁 |

每个 P0/P1 需求必须至少关联一个 `qa/catalog/cases/` 正式用例
（QUALITY_STRATEGY §4）。

## 4. 版本路线与出入准则

路线（执行摘要「推荐版本路线」）：Engineering Preview → Alpha → Beta →
V1 GA → V1.1（桌面 UI）→ V1.2（AI Proposal/Diff/Approval）。

| 版本 | 目标 | 进入准则 | 出口准则 |
| --- | --- | --- | --- |
| Engineering Preview | 证明 Parser/Template/OMML/Field/Citation 五条高风险链路 | Phase 0 启动即进入 | P0 spike 用例完成；五链路证据可用；无未决架构阻断项；ADR-0001～0006 全部 Accepted（QUALITY_STRATEGY §13） |
| Alpha | 一个真实学校模板完整编译，Word 无修复提示 | Preview 出口达成；Template Package v2 loader/lint 可用 | 一个模板 full E2E；D1–D4 P0 用例通过；Word 打开无修复提示（no_repair_open 证据）；已知限制写入文档（QUALITY_STRATEGY §13） |
| Beta | 三个代表性模板，六域测试与兼容矩阵完整 | Alpha 出口达成；shell.docx 合并（PackageEditor）解锁 | 三模板验收；D1–D6 P0 全过；P1 通过率达标；兼容矩阵证据完整（含 WPS 人工确认）；无未豁免 S1（QUALITY_STRATEGY §13） |
| V1 GA | CLI、离线包、模板工具、迁移、文档与发布门禁齐备 | Beta 出口达成；RC 候选通过全部发布门禁 | 全部 release blocker 关闭；仅批准的 allowlist；可复现/离线/打包测试通过（两次 clean build 规范化结果一致）；GB/T golden corpus 9 条 pending-human-review 人工定稿；300 页压力基线；文档与模板作者工作流完整；证据归档冻结并带哈希（执行摘要「质量门槛」+ QUALITY_STRATEGY §13） |
| V1.1 | 桌面 UI | GA 发布；CLI/JSON contract 冻结（R-029） | UI 与 CLI E2E 一致性测试通过；UI 不直接调用内部对象（service facade，R-022） |
| V1.2 | AI Proposal/Diff/Approval 工作流 | V1.1 稳定；AI 治理设计评审通过 | AI 不在编译链路（离线构建无 AI 依赖）；proposal 全部可追踪、可拒绝；引用需验证（R-023） |

说明：

- 任何版本出口以证据为准（六域证据制，ADR-0006）；「代码已实现」
  不构成出口（RISK_REGISTER §5 风险关闭标准同理）。
- Phase 0 未通过不进入大规模 Renderer 开发（执行摘要）。
- 范围变更流程：提出 → 书面说明替换的优先级 → 更新本文件与
  RISK_REGISTER R-030 状态 → gate 评审确认。
