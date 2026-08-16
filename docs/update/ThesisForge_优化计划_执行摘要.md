# ThesisForge V1 Plan v2 — 执行摘要

## 一句话判断

当前版本已经是一个方向正确的“编译器骨架”，但原计划不足以支撑可交付 V1；必须先解决 Parser、模板、OMML、Word 字段和引用五个高风险闭环，再扩展学术对象和 UI。

## 保留的原则

- 离线优先；
- AI 可选；
- 结构与样式分离；
- AST/IR 与 DOCX 解耦；
- 真实 OOXML 对象；
- 学校模板可替换；
- 编译前可校验。

## 必须调整的七项决策

1. **V1 不再等于一个大里程碑列表**：拆成 Engineering Preview、Alpha、Beta、GA；
2. **Parser 不再继续正则扩张**：Phase 0 比较 Pandoc JSON AST 与纯 Python 方案；
3. **模型分成 Normalized IR 和 Resolved IR**：编号、引用、模板和字段解析集中到 Compiler；
4. **模板不再是单 YAML**：采用 YAML + `reference.docx` + optional `shell.docx`；
5. **字段有生命周期**：field code、cached result、update-on-open、finalizer；
6. **引用引擎可替换**：GB/T 7714-2025 依赖人工审校 golden corpus；
7. **质量采用六域证据制**：不仅测代码，还测 OOXML、视觉、办公软件兼容、离线、安全和可复现性。

## 推荐版本路线

| 版本 | 目标 |
|---|---|
| Engineering Preview | 证明 Parser/Template/OMML/Field/Citation 五条高风险链路 |
| Alpha | 一个真实学校模板完整编译，Word 无修复提示 |
| Beta | 三个代表性模板，六域测试和兼容矩阵完整 |
| V1 GA | CLI、离线包、模板工具、迁移、文档和发布门禁齐备 |
| V1.1 | 桌面 UI |
| V1.2 | AI Proposal/Diff/Approval 工作流 |

## Phase 0 最重要

Phase 0 不产出大量功能，而是产出不会返工的选择：

- Product Scope；
- Compatibility Matrix；
- Parser spike；
- `reference.docx/shell.docx` spike；
- 30–50 公式 OMML corpus；
- TOC/SEQ/REF/PAGE 字段 spike；
- 20–30 文献类型 GB/T corpus；
- OpenXML validator 和 Word no-repair-open；
- ADR-0001 至 ADR-0006。

Phase 0 没有通过，不进入大规模 Renderer 开发。

## 第一批实际任务

1. 冻结 regex Parser 的功能扩张；
2. 建立 full syntax fixture；
3. 跑 Pandoc JSON AST + source position spike；
4. 从一个真实学校 DOCX 制作 reference/shell 模板；
5. 生成真实 OMML、SEQ/REF/TOC/PAGE 样例；
6. 对比 Pandoc citeproc 与 citeproc-py；
7. 将 Markdown Spec、示例和 Parser contract 对齐；
8. 设计 Inline/Block/Region/Project 模型；
9. 设计 Template Package v2 Schema；
10. 建立第一个 E2E fixture 和 OOXML XPath 测试。

## 质量门槛

V1 GA 前必须证明：

- 规范支持项都有正向和负向 fixture；
- 关键对象有 OOXML 结构断言；
- DOCX 通过包验证且 Word 不修复；
- 三个模板在目标应用中有兼容证据；
- GB/T golden corpus 人工审校；
- 300 页压力样例有基线；
- 两次 clean build 的规范化结果一致；
- 无网络环境可安装和编译；
- 路径、模板包、外部关系和宏受到安全限制。

## 文档入口

- 完整计划：`V1_PLAN.md`
- 事实审计：`CURRENT_STATE_AUDIT.md`
- 模板设计：`TEMPLATE_PACKAGE_SPEC_V2.md`
- 六域质量：`QUALITY_STRATEGY.md`
- 风险台账：`RISK_REGISTER.md`
- 架构决策：`adr/`
