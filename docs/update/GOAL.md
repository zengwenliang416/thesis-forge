# GOAL — 完成剩余全部任务（Phase 3 收尾 → Phase 4 → 后续项）

> 本文件是自包含目标书：任何代理拿到本文件即可继续，无需其他上下文。
> 每完成一项，把对应 `[ ]` 改为 `[x]` 并在末尾「执行日志」追加一行。

## 环境

- 仓库：`/Volumes/zwl/open_sources/thesis-forge`（src 布局，Python ≥3.11，venv 在 `.venv/`）
- 测试：`.venv/bin/python -m pytest tests/ -q`（当前基线 787 passed / 1 env-failed）
- Lint：`.venv/bin/python -m ruff check .`（当前全净）
- 本机：macOS arm64，LibreOffice 26.2（soffice）、pandoc 3.8.2.1 已安装；**node 未安装**
- CLI 入口：`.venv/bin/thesisforge …`

## 不可破坏的约束（AGENTS.md 摘要）

- 离线确定性：`inspect/validate/build` 不得依赖网络、pandoc 或任何外部可执行文件；
- Parser/AST 不 import docx/lxml；学校样式只来自 Template Model；
- Word 能力必须真对象（TOC/SEQ/REF/OMML/书签…），不得文字伪造；
- 提交前 `pytest` 全绿 + `ruff check .` 无错；OOXML 改动配 XML 结构断言。

## 任务清单

### T1 [x] 环境守卫：node 缺失时原型 harness 测试应 skip 而非 fail

`tests/test_prototype_acceptance.py::test_prototype_logic_harness_preserves_offline_safe_build_contract`
直接 `subprocess.run(["node", …])`，在无 node 机器上 FileNotFoundError。
**做法**：仿照仓库内 soffice 测试的 skipif 模式（`shutil.which("node") is None` →
`pytest.skip("node not available")`）。不改变 node 存在时的断言语义。

### T2 [x] ADR-0002 补两段实施记录（Phase 3 第二、三切片）

ADR-0002 §7 现有记录止于 loader+lint L1/L2。需追加：

1. **切片 2：PackageEditor + lint L3 完整/L4/L5**——
   `templates/v2/package_editor.py`（shell 锚点合并、样式闭包搬运、rels/部件
   重映射、footnotes w:id 重映射、numbering 双侧重映射、确定性双跑字节一致）、
   `lint.py` L3 完整/L4/L5；`tests/test_template_v2_editor.py` 35 条。
   记录：API、合并台账结构、L3/L4/L5 规则清单、L5 集成缺口
   （v2 包尚未接入编译管线，fixture 冒烟走 parser/validator + reference.docx 探针）。
2. **切片 3：`.tftpl` 打包 + template migrate**——
   `templates/v2/pack.py`（确定性 entry 顺序、manifest.json sha256、Zip Slip
   与解压炸弹防护、pack 前 L1+L2 门禁）、`migrate.py`（v0.3→v2 骨架、三态
   台账、幂等、非空目录拒写）、CLI `template pack/verify/migrate`；
   `tests/test_template_v2_pack.py`。
   记录：manifest 结构、migrate 台账示例、退出码约定。

**验收**：ADR-0002 §7 有两段新记录，格式与现有记录一致；「已知遗留」清单
同步划掉已完成项。

### T3 [x] Phase 4：pandoc citeproc 可选外部 citation provider（ADR-0004 §2.4）

新增 `src/thesis_forge/bibliography/pandoc_provider.py`：

- `PandocCiteprocProvider` 实现 `CitationProvider` 协议（provider.py 顶部
  已预留进程边界约定：CSL JSON 通道、`probe_executable_version`、
  `ProviderInfo(available=False, diagnostics=…)`）。
- CSL 用官方 GB/T 7714-2025 numeric（本地副本
  `spikes/phase0/citation/corpus/china-national-standard-gb-t-7714-2025-numeric.csl`，
  SHA256 `3b5ab624…faf`，ADR-0004 §2.5）；加载时校验哈希，不符 →
  available=False + 诊断。
- pandoc 缺失 / CSL 哈希不符 / 子进程失败 / 输出不可解析 → 一律
  结构化诊断，不在 import 或编译中途抛错。
- 注册：`resolve_citation_provider(style, provider=…)` 增加显式 provider
  选择；内建 provider 保持默认与唯一离线路径。
- 测试 `tests/test_pandoc_provider.py`：真 pandoc 用例（28 条 corpus 子集
  抽样 ≥5 条与 golden/spike 结果对照）+ `skipif`（pandoc/soffice 同款
  探测模式）；无 pandoc 时 info() 诊断用 monkeypatch 假 executable 验证，
  全部离线可跑。

### T4 [x] Phase 4：pandoc 可选外部 math provider（ADR-0003 §2.4）

新增 `src/thesis_forge/core/math_pandoc.py`（或按现有 math 模块形态就近放置，
先读 `core/math.py` 与 spike `spikes/phase0/omml/` 的调用方式再定）：

- LaTeX → `m:oMath` 片段转换 provider：子进程调 pandoc，产出仅 oMath 片段；
  编号/书签/`\r` 钉值/REF 包装仍由 `renderers/docx/equations.py` 承担
  （包装点不迁移）。
- `doctor`/info 探测 + 版本记录 + 失败结构化诊断；不进默认编译路径
  （默认仍是手写子集引擎）。
- 测试：真 pandoc 用例（corpus 抽样 ≥10 条，断言产出根元素为 `m:oMath`
  且可被 lxml 解析）+ skipif；离线单测覆盖不可用诊断与失败路径。

### T5 [x] Alpha gate 评估报告（真实学校模板编译证据）

新增 `docs/update/ALPHA_GATE.md`：按执行摘要的 Alpha 定义
（一个真实学校模板完整编译，Word 无修复提示）逐条评估：

- 用 `templates/schools/hunan-university-of-technology/master-2026.yaml`
  编译 `examples/complete-thesis/thesis.md`（final-auto）；
- 跑 `qa/tools/openxml_validate.py` 与 `qa/tools/no_repair_open.py`；
- 记录证据（命令 + 退出码 + 产物路径）与未达项（如需真人 Word/WPS
  人工验证的项明确标注 manual-pending）。

### T6 [x] 视觉回归工具落地（QUALITY_STRATEGY 范围内的最小闭环）

先读 `docs/update/QUALITY_STRATEGY.md` 视觉回归一节确认范围，再实现
`qa/tools/visual_diff.py`：PDF 页数一致性 + 文本层 diff（离线确定性），
可选 pdftoppm/ghostscript 光栅哈希（存在才启用）；配 `qa/baselines/`
清单与 README 用法。测试用 `qa/fixtures` 或 examples 产物做离线自测
（skipif 保护外部工具）。

### T7 [x] 终验

- `.venv/bin/python -m pytest tests/ -q` 全绿（node skip 后 0 failed）；
- `.venv/bin/python -m ruff check .` 无错；
- 本文件全部勾选 + 执行日志补齐。

## 执行日志

- 2026-08-16：GOAL 建立。前置修复已完成（LO finalizer 由上会话完成；
  PackageEditor/pack/migrate 三处半成品收尾 + 3 个测试失败修复 + ruff 清零）。
- 2026-08-16 T1：node skip 守卫落地（`shutil.which` → `pytest.skip`），全套 8 passed / 1 skipped。
- 2026-08-16 T2：ADR-0002 追加 §8（PackageEditor + lint L3 完整/L4/L5）与 §9（.tftpl 打包 + migrate）；
  pack/verify/migrate CLI 实测 exit 0，migrate 台账 migrated=20 / manual-required=6 / dropped=5。
- 2026-08-16 T3：`bibliography/pandoc_provider.py` 落地；对拍 spike 基线 8/9 逐字节一致
  （zh-map 为有意改进：CSL JSON 通道产出 GB/T 2025 原生 [CM]）；11 测试全绿；ADR-0004 补记。
- 2026-08-16 T4：`renderers/docx/math_provider.py`（OMML 属渲染层语义，不回写 core）；
  `render_equation` 增 keyword-only `omml_provider`，包装点不迁移；corpus 抽样 12 条 + 结构断言；
  6 测试全绿；ADR-0003 §8 记录。
- 2026-08-16 T5：`docs/update/ALPHA_GATE.md`——四判据全过（Word 16.107.2 pass / LO 26.2.3.2 pass /
  WPS 6.7.1 pending-human-review）；补建 2 条 D2 P0 负例夹具并自动化（TF-D2-ID-001 /
  TF-D2-REF-004 转 active+automated），目录重建 8 用例 / 0 未覆盖。
- 2026-08-16 T6：`qa/tools/visual_diff.py`（页数+文本层 P0、光栅哈希 needs-review、§9.3 台账）；
  首个基线 `qa/baselines/visual/complete-thesis-hut/`（12 页，自比 exit 0）；qa/README 增用法；
  5 测试（程序化最小 PDF + skipif）。
- 2026-08-16 T7 终验：`.venv/bin/python -m pytest tests/ -q` → **811 passed, 1 skipped**（node 环境守卫）；
  `.venv/bin/python -m ruff check .` → 全净。
- 2026-08-16 提交：全量工作树按功能分批落库 10 个提交（parser 双后端 / math 扩展 / citation
  provider / TOC cached / LO finalizer / template v2 / QA 门禁 / docs 归档 + 2 个 chore/fix），
  每个提交独立可构建，终验 812 passed + ruff 全净。
