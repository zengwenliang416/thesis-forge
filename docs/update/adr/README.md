# ThesisForge 架构决策记录（ADR）索引

> 范围：V1 优化计划 Phase 0 起的全部架构决策。
> 格式约定：标题 / 状态 / 日期 / 背景与问题 / 决策 / 决策理由（实证数据
> 精确到数字与文件）/ 备选方案与拒绝理由 / 后果（正面、负面、后续行动）/
> 关联（风险 ID、spike 报告、其他 ADR、设计文档）。
> 状态取值：`Proposed`（撰写/评审中）、`Accepted`（已接受）、
> `Superseded`（被后续 ADR 取代）。

| 编号 | 标题 | 状态 | 日期 | 主要依据 |
| --- | --- | --- | --- | --- |
| [ADR-0001](ADR-0001.md) | Parser 后端选型 —— markdown-it-py + 自研插件，IR 作为稳定契约 | Accepted | 2026-08-15 | `spikes/phase0/parser/REPORT.md`、`results/coverage.json`；R-001/R-002/R-003/R-018 |
| [ADR-0002](ADR-0002.md) | Template Package v2（reference.docx + 可选 shell.docx + 属性级 precedence + 显式迁移） | Accepted | 2026-08-15 | `spikes/phase0/docx-template/REPORT.md`；`docs/update/TEMPLATE_PACKAGE_SPEC_V2.md`；`docs/update/TEMPLATE_PACKAGE_SCHEMA_V2.md`（D-1/D-3/D-4/D-5/D-7）；R-004/R-005/R-012/R-020/R-026 |
| [ADR-0003](ADR-0003.md) | LaTeX→OMML 公式转换路线 —— 扩展手写子集 + Provider 抽象 | Accepted | 2026-08-15 | `spikes/phase0/omml/REPORT.md`、`results/coverage.json`、`results/omml_assertions.json`；R-008/R-024/R-002/R-016 |
| [ADR-0004](ADR-0004.md) | 引用引擎架构与 GB/T 7714 golden corpus（CitationProvider 接口 + 内建手写引擎扩展 + 可选 pandoc provider） | Accepted | 2026-08-15 | `spikes/phase0/citation/REPORT.md`、`results/comparison.json`、`golden/gbt7714-golden-v1.json`；R-010/R-011/R-024 |
| [ADR-0005](ADR-0005.md) | Word 字段生命周期与 finalizer 策略（TOC / SEQ / REF / PAGE） | Accepted | 2026-08-15 | `spikes/phase0/fields/REPORT.md`、`results/no-repair.json`、`results/word-refresh.json`、`results/lo-refresh-diff.json`；R-006/R-027/R-014/R-028/R-015 |
| [ADR-0006](ADR-0006.md) | 质量门禁、产品范围与兼容矩阵（六域证据制 + qa 门禁工具 + 分级兼容承诺 + V1 范围纪律） | Accepted | 2026-08-15 | `docs/update/QUALITY_STRATEGY.md`；`qa/README.md`、`qa/tools/openxml_validate.py`、`qa/tools/no_repair_open.py`；`spikes/phase0/fields/REPORT.md`；R-014/R-015/R-016/R-019/R-030 |

## 配套文档

- `docs/update/PRODUCT_SCOPE.md` — V1 产品范围与版本路线（ADR-0006 配套）
- `docs/update/COMPATIBILITY_MATRIX.md` — 兼容矩阵与承诺等级（ADR-0006 配套）

## 编号与维护规则

- 编号单调递增、永不复用；被取代的决策保留原文并把状态改为
  `Superseded`，在「关联」中指向后继 ADR。
- 每份 ADR 必须在「关联」一节回链：`docs/update/RISK_REGISTER.md`
  风险 ID、对应 spike 报告、相关设计文档与其他 ADR。
- 决策理由只引用可复现的实证（spike 报告、qa 工具输出、审计文档），
  数字须与来源文件一致；新证据推翻结论时新增 ADR，而不是改写旧文。
