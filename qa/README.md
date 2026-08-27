# qa/ — DocForge 质量基础设施

本目录承载 DocForge 六域质量策略（见 `docs/update/QUALITY_STRATEGY.md`）的
用例目录、测试夹具、基线、工具与运行证据。Phase 0 仅建立骨架与门禁工具，
正式用例和基线随后续阶段逐步填充。

## 目录结构

```text
qa/
├── catalog/            # 机器可读测试用例目录
│   └── cases/          # 正式用例定义（TF-D<域>-<领域>-<序号>.yaml，ID 永不复用）
├── fixtures/           # 测试输入夹具
│   ├── parser/         # D1 解析器正负例 Markdown
│   ├── templates/      # D3 模板正负例 YAML / 模板包
│   ├── e2e/            # 端到端论文工程（小型、可入 Git）
│   └── stress/         # D6 性能压力夹具（large / image-heavy 等）
├── baselines/          # 黄金基线（更新需人工审查，不得在 CI 自动接受）
│   ├── xml/            # 规范化 XML 片段 / semantic manifest
│   ├── citations/      # 引文与参考文献渲染 golden corpus
│   └── visual/         # 页面截图视觉基线（按区域划分）
├── tools/              # 质量门禁 CLI 工具（见下）
└── results/            # 各次 run 的证据（results/<run-id>/）
```

## 工具

### openxml_validate.py — DOCX（OOXML/OPC）结构校验

对 `.docx` 做结构门禁校验：ZIP 完整性、`[Content_Types].xml`、relationship
目标存在性与重复 ID、XML well-formed、`w:document` 根元素、书签配对、
field 配对、media 对应、sectPr、styles/numbering/footnotes 引用一致性。

```bash
.venv/bin/python qa/tools/openxml_validate.py output/document.docx
.venv/bin/python qa/tools/openxml_validate.py output/document.docx --json report.json
```

退出码：`0` 全部通过；`1` 存在失败项；`2` 文件不可读。

### no_repair_open.py — 三办公软件「无修复打开」验证（macOS）

验证 Word / WPS / LibreOffice 能否无修复提示地打开生成的 `.docx`，
输出 JSON 证据（应用、版本、结果、耗时、备注）。被测文件不会被修改，
Word/WPS 侧打开后一律「关闭不保存」。

```bash
.venv/bin/python qa/tools/no_repair_open.py output/document.docx
.venv/bin/python qa/tools/no_repair_open.py output/document.docx --apps word,libreoffice
.venv/bin/python qa/tools/no_repair_open.py output/document.docx --json evidence.json
```

- LibreOffice：headless 转 PDF 成功即 pass（可进 CI，需本机有 `soffice`）；
- Microsoft Word：AppleScript 打开/关闭不保存，模态修复对话框视为 fail；
- WPS：无可靠脚本接口，结果为 `pending-human-review`，需人工确认。

退出码：`0` 全部通过；`1` 存在失败（`pending-human-review` 不算失败）；`2` 文件不可读。

### visual_diff.py — 视觉回归最小闭环（QUALITY_STRATEGY §9）

对比两份 PDF：页数一致性 + 文本层 diff（pdftotext）判 P0；光栅逐页
哈希（pdftoppm，120dpi 灰度）不一致只标 `needs-review`（对渲染器版本
敏感，须人工审后更新基线）。基线是 `qa/baselines/visual/<name>/manifest.json`
（逐页文本/光栅哈希 + 工具版本 + 变更台账），不存二进制 PDF，按 manifest
内 recipe 再生。

```bash
.venv/bin/python qa/tools/visual_diff.py <baseline.pdf> <candidate.pdf> [--json r.json]
.venv/bin/python qa/tools/visual_diff.py --update-baseline <pdf> <基线目录> \
    --reason "…" --reviewer "…" [--issue "…"]   # §9.3 台账字段必填
```

退出码：`0` 无 P0 差异；`1` 存在 P0 差异（页数不一致/整行内容丢失新增）；
`2` 输入或工具错误。首个基线：`qa/baselines/visual/complete-thesis-hut/`
（complete-thesis + HUT master-2026 final-auto 产物，12 页）。
对应测试：`tests/test_visual_diff.py`（程序化最小 PDF，pdftotext 缺失时 skip）。

## 约定

- 用例 ID 规范：`TF-D<domain>-<area>-<sequence>`，定义见 QUALITY_STRATEGY 第 4 节；
- 大型 DOCX/PDF/截图不进主分支，只保留 `run.json` 与摘要，二进制走 CI artifact；
- 基线更新必须记录原因、reviewer 与影响范围（QUALITY_STRATEGY 第 9.3 节）；
- 工具仅依赖标准库 + lxml（项目既有依赖），不得在代码中硬编码 `/tmp`。
