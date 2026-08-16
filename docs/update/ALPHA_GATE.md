# Alpha Gate 评估报告（2026-08-16）

Alpha 定义（执行摘要 / QUALITY_STRATEGY §13）：**一个真实学校模板完整编译，
Word 无修复提示**，判据四条——one template full E2E / D1–D4 P0 cases pass /
Word opens without repair / known limitations documented。

## 结论

**达成（含 2 项 manual-pending）**。机器可判定项全部通过；两项需要真人
参与的验证按流程标注 manual-pending，不阻塞 Alpha（列入 GA 前清单）。

## 证据

环境：macOS arm64（darwin 25.5.0）、LibreOffice 26.2.3.2、Word 16.107.2、
WPS 6.7.1、项目 venv（`.venv`）。证据产物保留在 `/tmp/alpha-gate/`（本地），
关键结果摘录如下；复跑命令逐条给出。

### 1. 真实学校模板完整 E2E — PASS

```bash
.venv/bin/thesisforge build examples/complete-thesis/thesis.md \
    --template templates/schools/hunan-university-of-technology/master-2026.yaml \
    -o /tmp/alpha-gate/thesis-final-auto.docx
# → ✓ 已生成 DOCX（exit 0，约 6.5s）
```

`build_service` 的 FINALIZE 阶段内建 final-auto（LibreOffice 无头字段刷新，
ADR-0005），即本产物已经过 LO 刷新 + 刷新后结构校验（不通过则不落盘）。

### 2. D1–D4 P0 用例 — PASS（4/4 自动化）

| 用例 | 域 | 状态 | 自动化 |
|---|---|---|---|
| TF-D1-SYN-001 全语法解析 | D1 | active | `tests/test_qa_e2e.py::test_full_syntax_parser_fixture_parses_all_block_kinds` |
| TF-D2-ID-001 重复 ID 诊断 | D2 | active | `tests/test_qa_e2e.py::test_duplicate_id_fixture_reports_structured_diagnostic`（本次补夹具 `qa/fixtures/parser/duplicate-id.md`） |
| TF-D2-REF-004 缺失引用诊断 | D2 | active | `tests/test_qa_e2e.py::test_missing_reference_fixture_reports_structured_diagnostic`（本次补夹具 `qa/fixtures/parser/missing-reference.md`） |
| TF-D4-REF-001 图表引用 E2E | D4 | active | `tests/test_qa_e2e.py::test_figure_reference_pipeline_passes_structural_gates` |

CLI 实测：`thesisforge validate qa/fixtures/parser/duplicate-id.md` → exit 1 +
`duplicate-id`（target `fig:dup`）；`missing-reference.md` → exit 1 +
`missing-reference`×2（target `fig:ghost`）。目录 `qa/catalog/index.json`
已重建：8 用例 / 15 需求 / 0 未覆盖。

### 3. 结构校验 — PASS

```bash
.venv/bin/python qa/tools/openxml_validate.py /tmp/alpha-gate/thesis-final-auto.docx
# → exit 0，13/13 检查全部 pass
```

### 4. Word 打开无修复 — PASS（1 项 manual-pending）

```bash
.venv/bin/python qa/tools/no_repair_open.py /tmp/alpha-gate/thesis-final-auto.docx \
    --json /tmp/alpha-gate/no-repair.json   # → exit 0
```

| 应用 | 版本 | 结果 | 备注 |
|---|---|---|---|
| Word | 16.107.2 | **pass** | 打开成功并「关闭不保存」；System Events 无辅助功能权限，降级为仅依据 open 成败判断（见 manual-pending ②） |
| LibreOffice | 26.2.3.2 | **pass** | headless 导出 PDF 成功（405969 字节，12 页） |
| WPS | 6.7.1 | pending-human-review | 已打开，但无脚本接口判断修复提示（见 manual-pending ①） |

### 5. finalizer 语义保持 — PASS

`tests/test_lo_finalizer.py` 集成测试（真 soffice）：LO 刷新后 SEQ `\r`
钉值保持、TOC 指令还原为编译期原指令、`openxml_validate` 13/13 通过
（ADR-0005 §7 实施记录）。

### 6. 已知限制已文档化 — PASS

- `docs/update/COMPATIBILITY_MATRIX.md` §4.2：LO finalizer 已知差异（页眉
  页脚部件被整体重写但指令未变；PAGE cached 评估值含封面节 `0`，接受为
  preview 差异；final-word 为 GA 权威路径）；
- ADR-0004 §2.6：golden corpus 9 条 pending-human-review（GA 前人工定稿）；
- ADR-0002 §9：`templates/schools/` 两份 v0.3 模板正式迁移 `.tftpl` 待办。

### 7. 视觉回归基线 — PASS（首建）

```bash
soffice --headless --convert-to pdf --outdir /tmp/alpha-gate thesis-final-auto.docx
.venv/bin/python qa/tools/visual_diff.py --update-baseline \
    /tmp/alpha-gate/thesis-final-auto.pdf qa/baselines/visual/complete-thesis-hut \
    --reason "Alpha gate 首建" --reviewer "zwl"
# → 12 页；自比 exit 0（无 P0 差异）
```

### 8. 回归基线

`.venv/bin/python -m pytest tests/ -q` → **806 passed, 1 skipped**
（skip 为 node 缺失的环境守卫，`tests/test_prototype_acceptance.py`）；
`.venv/bin/python -m ruff check .` → 无错。

## Manual-pending（GA 前清单）

1. **WPS 修复提示人工确认**：真人打开 `/tmp/alpha-gate/thesis-final-auto.docx`
   （或重新 build），确认无修复对话框、页码与交叉引用可用（TF-D5-WPS-004）；
2. **Word System Events 权限复验**：授予辅助功能权限后重跑
   `no_repair_open.py`，让模态修复对话框检测生效（当前为降级判定）；
3. golden corpus 9 条 pending-human-review 定稿（ADR-0004 §6.4）。
