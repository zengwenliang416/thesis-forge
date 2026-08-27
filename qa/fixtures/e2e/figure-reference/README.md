# figure-reference — D4 域端到端夹具

本目录是 `qa/` 下首个端到端（E2E）论文工程夹具，对应用例
`TF-D4-REF-001`（见 `qa/catalog/cases/TF-D4-REF-001.yaml`），服务于
`docs/update/QUALITY_STRATEGY.md` 第 4 节用例目录模型与第 8 节 OpenXML/OPC 门禁。

## 内容

```text
figure-reference/
├── docforge.yaml       # 项目入口、元数据、资源和模板选择
├── document.md         # 论文源文件（两章 + 摘要/参考文献/致谢）
├── references.bib      # 最小 BibTeX（2 条，均被正文引用）
└── images/             # 纯 stdlib 生成的小 PNG（见下）
    ├── pipeline.png    # 96x64 RGB，被 fig:pipeline 引用
    └── dashboard.png   # 96x64 RGB，被 fig:dashboard 引用
```

`document.md` 覆盖的语义对象：

- 2 张图：`fig:pipeline`（第一章）、`fig:dashboard`（第二章），验证按章编号
  （`SEQ TF_Figure_1` / `SEQ TF_Figure_2`）；
- 1 张三线表：`tbl:metrics`（对齐分隔行 + 右对齐列）；
- 1 个编号公式：`eq:score`；
- 正文交叉引用 `@fig:…` / `@tbl:…` / `@eq:…`（含同段多处引用）；
- 2 条引文（`fixture-compile-2025`、`fixture-fields-2024`）与
  `::: bibliography` marker；
- 1 个脚注（`fixture-note`）；
- 摘要 / 关键词（`chap:abstract-zh`）、参考文献、致谢特殊章节。

模板使用仓库既有 `templates/schools/example-university/2026.yaml`，由
`docforge.yaml` 中的 `render.template_id: example-university-2026` 选择。

## 图片生成方式

`images/` 下两张 PNG 由 Python 标准库（`zlib` + `struct`）手写 PNG 块生成，
96x64、8-bit RGB、无滤波，不依赖任何第三方图像库，可随时重新生成。

## 消费方

- `tests/test_qa_e2e.py::test_figure_reference_pipeline_passes_structural_gates`：
  parse → validate → compile → render（不走 finalizer），随后运行
  `qa/tools/openxml_validate.py` 全部检查与 XPath/field 语义断言；
  报告 JSON 落在 pytest `tmp_path`，不写入 `qa/results/`。
- 正式 run 的证据目录约定见 QUALITY_STRATEGY 第 6 节。
