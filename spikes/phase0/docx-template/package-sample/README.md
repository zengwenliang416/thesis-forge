# package-sample — Template Package v2 最小样例（Phase 0 spike）

> 这是 `spikes/phase0/docx-template/` 的样例产物，**不是正式模板**。
> 用途：为 ADR-0002 提供「YAML + reference.docx + shell.docx」路线的实证对象。

## 结构

```text
package-sample/
├── template.yaml            # schema_version: 2 最小示例（引用 reference/shell，声明锚点）
├── reference.docx           # 样式/主题/页面设置来源（正文为空，仅 sectPr）
├── shell.docx               # 封面 + 原创性声明 + 目录锚点 tf_toc + 正文锚点 tf_body
├── assets/
│   └── logo.png             # 占位 logo（纯 stdlib 生成，字节确定）
├── fixtures/
│   └── minimal/thesis.md    # 最小论文源
├── provenance.yaml
└── README.md
```

## 生成方式（仓库根目录，全部可重复运行）

```bash
.venv/bin/python spikes/phase0/docx-template/build_reference.py   # → reference.docx
.venv/bin/python spikes/phase0/docx-template/build_shell.py       # → shell.docx + assets/logo.png
.venv/bin/python spikes/phase0/docx-template/merge_into_shell.py  # → output/merged.docx
```

- `reference.docx` 以 `templates/schools/hunan-university-of-technology/master-2026.yaml`
  为蓝本编程生成：TF Body / TF Heading 1-4 / TF Abstract / TF Bibliography /
  TF Figure Caption / TF Table Caption / TF Equation / TF Code Char 等样式
  （含 eastAsia 字体、字号、行距、首行缩进、段距）、A4 页面设置（边距、
  页眉页脚距离、docGrid lines 20pt）、默认页眉（校名 + 0.5pt 下边框）与
  页脚（PAGE 域）、fontTable 登记宋体/黑体、theme 沿用 python-docx 默认主题。
- `shell.docx` 以 reference.docx 为底构建：section 1（封面/声明/目录，
  页码 lowerRoman 从 1 起）、section 2（正文，页码 decimal 从 1 重启，
  独立页眉页脚）。`tf_body` / `tf_toc` 书签各唯一。

## 校验

```bash
.venv/bin/python qa/tools/openxml_validate.py spikes/phase0/docx-template/package-sample/reference.docx
.venv/bin/python qa/tools/openxml_validate.py spikes/phase0/docx-template/package-sample/shell.docx
.venv/bin/python qa/tools/openxml_validate.py spikes/phase0/docx-template/output/merged.docx
```

三者均为 13/13 通过；shell.docx 与 merged.docx 另经 soffice 无头转 PDF 冒烟。

详细实证结论见 `spikes/phase0/docx-template/REPORT.md`。
