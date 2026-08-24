# ThesisForge V2 Format Corpus

这是一个可离线编译的 ThesisForge V2 完整格式语料。它把同一组 Markdown
语义对象贯穿到 `ThesisDocument`、`RenderPlan`、Review 和 DOCX/OpenXML，
用于验证内容与格式分离，而不是验证某一个孤立的 `.docx` 文件。

## 文件

- `thesisforge.yaml`：严格的 `thesisforge.project.v2` 项目入口、模板选择和布局覆盖。
- `thesis.md`：富文本、章节、列表、图表、公式、代码、引用、脚注和语义区语料。
- `references.bib`：article、book、inproceedings 三类本地 BibTeX 条目。
- `assets/architecture.png`、`assets/model.png`：分别覆盖百分比和毫米图片宽度。
- `coverage-matrix.md`：从 source 到测试证据的逐项覆盖矩阵。

## 离线命令

```bash
.venv/bin/thesisforge inspect examples/v2-format-corpus
.venv/bin/thesisforge validate examples/v2-format-corpus --json
.venv/bin/thesisforge review examples/v2-format-corpus --output-dir /tmp/thesisforge-review
.venv/bin/thesisforge build examples/v2-format-corpus -o /tmp/v2-format-corpus.docx
.venv/bin/python -m pytest -q tests/acceptance/test_v2_format_corpus.py
```

`validate` 不应产生 error。验收测试会额外生成临时 DOCX，检查字段、书签、
OMML、脚注、表格、图片 extent、sections、header/footer 和 Review marker
隔离。CLI、parser、compiler、Review 和 DOCX renderer 均不需要网络或 AI 凭据。

## 重点覆盖

- 三个 H1 语义区域、H2/H3 标题、TOC、cover、front matter、main section、
  acknowledgements 和 achievements。
- 从 3 开始的 ordered list，以及至少三级的 nested unordered list。
- bold、italic、bold+italic、inline code、HTTP/mailto/autolink、inline math、
  citation locator、chapter/section/figure/table/equation/listing/algorithm
  cross-reference、soft break、hard break 和 footnote。
- 两张图片的 manifest width override：`75%` 和 `90mm`。
- 独立的 `E = mc^2`、`\frac` + `\sum`、`\begin{pmatrix}` 以及损失函数公式。
- 普通 fenced code、listing fence、algorithm fence，并验证代码字面量中的技术
  marker 不泄露到 reader-facing Review 文本。
