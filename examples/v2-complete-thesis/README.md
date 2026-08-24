# ThesisForge V2 完整示例项目

这是一个可以直接被 ThesisForge V2 打开的完整论文项目，不是单独的
Markdown 文件，也不是只提供一个生成后的 Word。

## 项目结构

```text
v2-complete-thesis/
├── thesisforge.yaml
├── thesis.md
├── references.bib
├── assets/
│   └── architecture.png
├── templates/
│   └── schools/example-university/2026.yaml
├── build/
│   ├── inspect.json
│   ├── validate.json
│   ├── review-result.json
│   ├── build-result.json
│   ├── openxml-report.json
│   ├── thesis.docx
│   ├── thesis.pdf
│   └── build-report.json
└── review/
    ├── thesis.review.md
    └── thesis.review-map.json
```

## 包含的语义

- 项目 manifest、完整元数据、模板选择和对象级图片宽度
- 可随项目携带的学校模板 YAML（字体、页边距、目录、章节、编号和页码策略）
- 中文摘要、英文摘要、章节和附录
- 标题层级、稳定 ID、粗体、斜体、行内代码和普通链接
- 行内公式、显示公式和公式交叉引用
- 有序/无序嵌套列表和引用块
- 图片、图题、图编号和图片资源
- GFM 表格、对齐、表题、表编号和表交叉引用
- `listing` 代码清单和 `algorithm` 算法块
- BibTeX 引用、脚注和参考文献
- Review Markdown、source map、BuildReport 和结构化 DOCX

## 构建

从仓库根目录执行：

```bash
ROOT="$(pwd)"

.venv/bin/python -m thesis_forge.cli inspect \
  examples/v2-complete-thesis

.venv/bin/python -m thesis_forge.cli validate \
  examples/v2-complete-thesis --json

.venv/bin/python -m thesis_forge.cli review \
  examples/v2-complete-thesis \
  --output-dir "$ROOT/examples/v2-complete-thesis/review"

.venv/bin/python -m thesis_forge.cli build \
  examples/v2-complete-thesis \
  -o "$ROOT/examples/v2-complete-thesis/build/thesis.docx" \
  --report-json "$ROOT/examples/v2-complete-thesis/build/build-report.json"
```

`thesis.md` 只保存可读论文内容，项目元数据、资源、模板和输出策略统一放在
`thesisforge.yaml`。不要把 YAML Front Matter 或旧的 `:::` 容器放回正文。
