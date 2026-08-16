# Phase 0 Gate 核对记录

> 日期：2026-08-15
> 依据：`ThesisForge_优化计划_执行摘要.md`（Phase 0 产物清单、第一批实际任务、质量门槛）
> 结论：**Phase 0 通过（含已登记豁免项），允许进入 Phase 1。**

## 1. Phase 0 产物核对

| 计划要求的产物 | 状态 | 证据 |
|---|---|---|
| Product Scope | ✅ | `docs/update/PRODUCT_SCOPE.md` |
| Compatibility Matrix | ✅ | `docs/update/COMPATIBILITY_MATRIX.md`（Word 16.107.2 / WPS 6.7.1 / LibreOffice 26.2.3.2 实测证据） |
| 事实审计 | ✅ | `docs/update/CURRENT_STATE_AUDIT.md`（15 项债务清单 D-01~D-15） |
| Parser spike | ✅ | `spikes/phase0/parser/`（REPORT.md + results/coverage.json；现有 parser 15 全/2 部分/1 不支持，pandoc 10/7/1 且无 sourcepos，markdown-it-py 9/7/2） |
| reference.docx/shell.docx spike | ✅ | `spikes/phase0/docx-template/`（两条路线均成立，merged.docx openxml_validate 13/13、双跑字节一致；package-sample/ 样例包） |
| 30–50 公式 OMML corpus | ✅ | `spikes/phase0/omml/`（50 条 corpus；项目子集 24/50=48%，pandoc 49/50，latex2mathml+XSLT 49/50；sample.docx 结构断言全过） |
| TOC/SEQ/REF/PAGE 字段 spike | ✅ | `spikes/phase0/fields/`（字段清单、变体矩阵、Word/LO 刷新实证；Word 首开弹窗由 updateFields/dirty 各自独立触发） |
| 20–30 文献类型 GB/T corpus | ✅ | `spikes/phase0/citation/`（28 条 corpus + 2025 numeric CSL（官方仓库、SHA256 已记录）；pandoc 28/28、citeproc-py 5/28；golden 19 通过 / 9 条 pending-human-review） |
| OpenXML validator + Word no-repair | ✅ | `qa/tools/openxml_validate.py`（13 项检查）、`qa/tools/no_repair_open.py`（Word/LibreOffice pass 实测，WPS pending-human-review） |
| ADR-0001 至 ADR-0006 | ✅ | `docs/update/adr/`（0001 Parser 后端、0002 Template Package v2、0003 OMML 转换、0004 引用引擎、0005 字段生命周期、0006 质量门禁/范围/兼容 + README 索引） |

## 2. 第一批实际任务核对

| 任务 | 状态 | 证据 |
|---|---|---|
| 1. 冻结 regex Parser 功能扩张 | ✅ | ADR-0001（冻结维护成文）；`docs/MARKDOWN_SPEC.md` 已标注 |
| 2. full syntax fixture | ✅ | `qa/fixtures/parser/full-syntax.md`（`tests/test_qa_e2e.py` 验证可解析） |
| 3. Pandoc JSON AST + source position spike | ✅ | `spikes/phase0/parser/`（sourcepos 与 citations 扩展互斥为关键发现） |
| 4. 真实学校 DOCX 制作 reference/shell 模板 | ✅（豁免） | 无真实学校官方 DOCX 可用；以 HUT 模板 YAML 为蓝本编程生成（`spikes/phase0/docx-template/package-sample/`），登记为豁免项 |
| 5. 真实 OMML、SEQ/REF/TOC/PAGE 样例 | ✅ | `spikes/phase0/omml/output/`、`spikes/phase0/fields/samples/` |
| 6. Pandoc citeproc vs citeproc-py 对比 | ✅ | `spikes/phase0/citation/results/comparison.md`（5/28 一致率，citeproc-py 引擎级缺陷） |
| 7. Markdown Spec、示例、Parser contract 对齐 | ✅ | `docs/MARKDOWN_SPEC.md` 更新（不支持构造与降级行为成文）；examples 死配置移除；`tests/test_parser_contract.py` 31 项契约测试 |
| 8. Inline/Block/Region/Project 模型设计 | ✅ | `docs/update/IR_MODEL_DESIGN.md`（四层模型 + Normalized/Resolved IR + SourceMap） |
| 9. Template Package v2 Schema 设计 | ✅ | `docs/update/TEMPLATE_PACKAGE_SCHEMA_V2.md`（D-1 precedence、搬运清单、L1–L5 lint、迁移设计） |
| 10. 首个 E2E fixture + OOXML XPath 测试 | ✅ | `qa/fixtures/e2e/figure-reference/` + `tests/test_qa_e2e.py`（构建→openxml_validate→XPath 断言全链）；`qa/catalog/` 种子（15 需求 / 8 用例 / 2 套件 + build_catalog.py） |

## 3. 测试与 lint 基线（2026-08-15 实测）

- `pytest tests/ -q`：**529 passed, 4 failed**（基线 482 → +47 项新增测试）。
- `ruff check .`：新增文件（qa/、spikes/、新测试）全部干净。

### 已登记偏差（均为 Phase 0 之前存在，非本次引入）

| 偏差 | 根因 | 处置 |
|---|---|---|
| 4 项 pytest 失败（test_pdf_preview ×3、test_application_services ×1） | 本机 `/private/tmp` 被删除、`/tmp` 悬空；`office_refresh.py:592`/`pdf_preview.py:567` darwin 硬编码 `/tmp` 无回退（债务 D-09） | 环境修复：`sudo mkdir -p /private/tmp && sudo chmod 1777 /private/tmp`；代码回退逻辑列入 Phase 1 修复（Phase 0 边界冻结核心源码） |
| `ruff check .` 3 个 I001 | `tmp/` 下用户临时脚本 import 排序（add_docx_hyperlinks.py、prepare_word_ready.py、run_word_export.py），早于本次工作 | 保持现状；如需全绿可 `ruff check --fix tmp/` 或将 tmp/ 加入 lint 排除，留待用户决定 |
| golden corpus 9 条 pending-human-review | GB/T 7714-2025 人工审校 | GA 前定稿（ADR-0004 后续行动） |
| WPS 验证 pending-human-review | WPS 无可靠脚本接口 | COMPATIBILITY_MATRIX 已按 pending 登记，人工确认流程见 qa/README.md |

## 4. 风险台账联动

Phase 0 结果已回写 `RISK_REGISTER.md`（§6 Phase 0 回写）：R-001/R-002 选型关闭；R-004/R-005/R-006/R-008/R-010/R-011 决策落地、实施排入后续 Phase；R-014/R-015/R-016 门禁工具就绪；R-024 MML2OMML.XSL 因许可证拒绝。

## 5. Phase 1 入口行动项（按 ADR）

1. ADR-0001：ParserBackend 协议定义 + 现有 parser 包装为 legacy 后端；markdown-it-py 插件开发（container/footnote/citation/crossref）与双后端 diff 门禁。
2. ADR-0005：TOC cached 条目生成（修 D-11）；修复 D-09 `/tmp` 回退。
3. ADR-0003：按失败榜扩 LaTeX 子集（\begin 环境、\int、\left/\right、\mathrm/\text、函数上下标文法）；修两个保真度 bug 与 \eta 遗漏。
4. ADR-0004：CitationProvider 接口 + 手写 GB/T 引擎扩类型/et al/全角标点。
5. ADR-0002：Template Package v2 loader/lint L1–L2 起步（reference.docx 仅 Alpha）。
6. ADR-0006：PR 门禁接线（openxml_validate + XPath E2E 进 CI 快速层）。
