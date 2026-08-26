"""QA E2E 结构门禁测试（对应用例 TF-D4-REF-001 / TF-D1-SYN-001 /
TF-D2-ID-001 / TF-D2-REF-004）。

对测试内的标准 V2 项目走完整编译管线
（canonical parser backend → validate → compile → render，不走 finalizer），
随后运行 qa/tools/openxml_validate.py 全部检查，并用 zipfile + lxml
做 XPath/field 语义断言。证据 JSON 落在 pytest tmp_path，不写入 qa/results/。
"""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from docforge.bibliography import resolve_citation_provider
from docforge.core.compiler import compile_document
from docforge.core.index import DocumentIndex
from docforge.core.parser_backend import create_parser_backend
from docforge.core.render_plan import (
    BibliographyInstruction,
    FootnoteDefinitionInstruction,
)
from docforge.core.validator import ValidationContext, validate_document
from docforge.renderers.docx import DocxRenderer

ROOT = Path(__file__).resolve().parents[1]
OPENXML_VALIDATE = ROOT / "qa" / "tools" / "openxml_validate.py"
PARSER = create_parser_backend()
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

E2E_MANIFEST = """schema: thesisforge.project.v2
project:
  id: qa-e2e-v2
  language: zh-CN
document:
  source: thesis.md
metadata:
  title:
    zh: QA E2E 结构门禁夹具
  author:
    name: 质量夹具
  institution:
    university: 示例大学
  degree:
    name: 工学硕士
  advisor:
    name: 示例导师
resources:
  root: .
  assets: images
  bibliography: refs/references.bib
render:
  template_id: example-university-2026
  citation_style: gbt7714-2025-numeric
"""

E2E_SOURCE = """# 摘要 {#chap:abstract}

# 绪论 {#chap:introduction}

系统总体管线如[图](#fig:pipeline)所示。确定性编译方法已有充分研究
[@fixture-compile-2025]，字段级验证思路参见[@fixture-fields-2024]。[^fixture-note]

![确定性编译管线示意](images/pipeline.png){#fig:pipeline}

# 实验与分析 {#chap:experiments}

实验结果见[图](#fig:dashboard)、[表](#tbl:metrics)和[式](#eq:score)。

![质量指标结果面板](images/dashboard.png){#fig:dashboard}

| 指标 | 通过数 |
| --- | ---: |
| 书签配对 | 13 |
| 字段配对 | 13 |
: 结构校验核心指标 {#tbl:metrics}

$$
S = \\alpha P + \\beta R
$$
{#eq:score}

# 参考文献 {#chap:references}

[^fixture-note]: 本脚注用于覆盖脚注定义与引用的结构校验路径。
"""

BIBLIOGRAPHY_SOURCE = """@article{fixture-compile-2025,
  author  = {Smith, Jane and Zhang, Wei},
  title   = {Deterministic Compilation for Academic Documents},
  journal = {Journal of Document Engineering},
  year    = {2025},
  volume  = {12},
  number  = {3},
  pages   = {101--120}
}

@article{fixture-fields-2024,
  author  = {Doe, John},
  title   = {Field-Level Validation of DOCX Pipelines},
  journal = {Document Systems Review},
  year    = {2024},
  volume  = {8},
  number  = {2},
  pages   = {10--18}
}
"""

FULL_SYNTAX_SOURCE = """# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

传统排版依赖手工调整 [@smith2025]，确定性编译可降低成本
[@smith2025; @wang2024]。[^note]

如[图](#fig:model)所示，并参见[表](#tbl:results)、[式](#eq:loss)、
[算法](#alg:train)、[代码](#lst:predict)、[章节](#sec:background)与
[绪论](#chap:introduction)。

行内数学 $E = m c^2$ 与普通文本混排。[^long]

![模型总体结构](images/model.png){#fig:model}

| 模型 | AUROC |
| --- | ---: |
| A | 0.91 |
| B | 0.94 |
: 实验结果 {#tbl:results}

$$
L=-\\sum_i y_i \\log \\hat y_i
$$
{#eq:loss}

```algorithm {#alg:train title="训练流程"}
输入：训练集 D
1. 初始化参数
2. 读取数据
```

```python {#lst:predict title="预测函数"}
def predict(x):
    return model(x)
```

## 列表示例 {#sec:lists}

- 第一项
  - 第二级项目
- 第三项

3. 从 3 开始
4. 下一项

# 参考文献 {#chap:references}

[^note]: 这是普通脚注。
[^long]: 第一行。
    第二行（续行）。
"""

DUPLICATE_ID_SOURCE = """# 重复 ID 负例 {#chap:dup-case}

![第一处重复 ID 的示例图](images/model.png){#fig:dup}

![第二处重复 ID 的示例图](images/model.png){#fig:dup}
"""

MISSING_REFERENCE_SOURCE = """# 交叉引用目标缺失负例 {#chap:missing-ref-case}

正文引用[图](#fig:ghost)，但全文没有 ID 为 `fig:ghost` 的图。

![真实存在的示例图](images/model.png){#fig:real}
"""

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

EXPECTED_BOOKMARKS = (
    "tf_fig_pipeline",
    "tf_fig_dashboard",
    "tf_tbl_metrics",
    "tf_eq_score",
)
EXPECTED_SEQ_INSTRUCTIONS = (
    "SEQ TF_Figure_1",
    "SEQ TF_Figure_2",
    "SEQ TF_Table_2",
    "SEQ TF_Equation_2",
)
EXPECTED_REF_TARGETS = EXPECTED_BOOKMARKS

REF_INSTRUCTION_RE = re.compile(r"^REF (\S+)")


def _write_e2e_project(root: Path) -> Path:
    image_root = root / "images"
    image_root.mkdir(parents=True)
    for name in ("pipeline.png", "dashboard.png"):
        (image_root / name).write_bytes(PNG_BYTES)
    bibliography_root = root / "refs"
    bibliography_root.mkdir()
    (root / "thesis.md").write_text(E2E_SOURCE, encoding="utf-8")
    (root / "thesisforge.yaml").write_text(E2E_MANIFEST, encoding="utf-8")
    (bibliography_root / "references.bib").write_text(
        BIBLIOGRAPHY_SOURCE,
        encoding="utf-8",
    )
    return root / "thesis.md"


def _build_fixture_docx(output: Path, tmp_path: Path):
    """canonical parser → validate → compile → render（不走 finalizer）。"""
    source = _write_e2e_project(tmp_path / "qa-e2e-project")
    document = PARSER.parse_file(source)
    context = ValidationContext.from_document(
        document,
        template_roots=(ROOT / "templates",),
    )
    issues = validate_document(document, context)
    errors = [issue for issue in issues if issue.severity == "error"]
    assert not errors, f"夹具校验存在错误: {[(i.code, i.target) for i in errors]}"
    assert context.template is not None, "模板未成功解析"
    plan = compile_document(
        document,
        template=context.template,
        template_path=context.template_path,
        bibliography_database=context.bibliography_database,
        citation_formatter=resolve_citation_provider(context.manifest_citation_style),
    )
    DocxRenderer().render(plan, output)
    return document, plan


def _xml_part(path: Path, part: str):
    with ZipFile(path) as package:
        return etree.fromstring(package.read(part))


def _field_instructions(document_xml) -> tuple[str, ...]:
    return tuple(
        " ".join(text.split())
        for text in document_xml.xpath(".//w:instrText/text()", namespaces=NS)
    )


def test_figure_reference_pipeline_passes_structural_gates(tmp_path: Path):
    output = tmp_path / "figure-reference.docx"
    report_path = tmp_path / "openxml-report.json"
    document, plan = _build_fixture_docx(output, tmp_path)
    assert output.is_file()

    document_index = DocumentIndex.from_document(document)
    assert {"fixture-compile-2025", "fixture-fields-2024"} <= {
        key for citation in document_index.citations for key in citation.keys
    }
    assert {
        reference.label for reference in document_index.footnote_references
    } == {"fixture-note"}
    bibliography_nodes = [
        node for node in plan.nodes if isinstance(node, BibliographyInstruction)
    ]
    assert len(bibliography_nodes) == 1
    assert [(entry.key, entry.ordinal) for entry in bibliography_nodes[0].entries] == [
        ("fixture-compile-2025", 1),
        ("fixture-fields-2024", 2),
    ]
    assert sum(
        isinstance(node, FootnoteDefinitionInstruction) for node in plan.nodes
    ) == 1

    result = subprocess.run(
        [sys.executable, str(OPENXML_VALIDATE), str(output), "--json", str(report_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    # 证据 JSON 必须落在 tmp_path，不写入 qa/results/
    assert report_path.is_file()
    assert report_path.parent == tmp_path
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert report["summary"]["failed"] == 0
    assert {check["status"] for check in report["checks"]} == {"pass"}

    document_xml = _xml_part(output, "word/document.xml")
    bookmark_names = set(
        document_xml.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
    )
    for name in EXPECTED_BOOKMARKS:
        assert document_xml.xpath(
            ".//w:bookmarkStart[@w:name=$name]",
            namespaces=NS,
            name=name,
        ), f"缺少书签 {name}"

    instructions = _field_instructions(document_xml)
    for seq in EXPECTED_SEQ_INSTRUCTIONS:
        assert any(instruction.startswith(seq) for instruction in instructions), (
            f"缺少 SEQ 字段 {seq}"
        )

    ref_targets = {
        match.group(1)
        for instruction in instructions
        if (match := REF_INSTRUCTION_RE.match(instruction))
    }
    for target in EXPECTED_REF_TARGETS:
        assert f"REF {target} \\h" in instructions, f"缺少 REF 字段 {target}"
    assert ref_targets <= bookmark_names, (
        f"REF 指向不存在的书签: {sorted(ref_targets - bookmark_names)}"
    )

    assert any(
        instruction.startswith("TOC ") and '\\o "1-3"' in instruction
        for instruction in instructions
    ), "缺少含 \\o \"1-3\" 的 TOC 字段"

    with ZipFile(output) as package:
        package_names = set(package.namelist())
        footer_parts = sorted(
            name
            for name in package_names
            if name.startswith("word/footer") and name.endswith(".xml")
        )
    assert "word/footnotes.xml" in package_names, "缺少脚注部件"
    footnotes_xml = _xml_part(output, "word/footnotes.xml")
    assert len(
        document_xml.xpath(".//w:footnoteReference", namespaces=NS)
    ) == 1, "正文缺少脚注引用对象"
    assert len(
        footnotes_xml.xpath(".//w:footnote[not(@w:type)]", namespaces=NS)
    ) == 1, "脚注部件缺少脚注定义"
    paragraph_texts = [
        "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
        for paragraph in document_xml.xpath(".//w:body/w:p", namespaces=NS)
    ]
    assert all(
        marker not in "\n".join(paragraph_texts)
        for marker in ("[@fixture-compile-2025]", "[@fixture-fields-2024]")
    ), "DOCX 泄漏了原始 citation marker"
    assert all(
        entry.text in paragraph_texts for entry in bibliography_nodes[0].entries
    ), "DOCX 缺少编译后的参考文献条目"
    assert footer_parts, "缺少页脚部件"
    footer_instructions = tuple(
        field
        for part in footer_parts
        for field in _field_instructions(_xml_part(output, part))
    )
    assert "PAGE" in footer_instructions, "页脚缺少 PAGE 字段"

    settings_xml = _xml_part(output, "word/settings.xml")
    assert settings_xml.xpath("./w:updateFields/@w:val", namespaces=NS) == ["true"], (
        "settings.xml 缺少 updateFields"
    )


def test_full_syntax_parser_fixture_parses_all_block_kinds():
    document = PARSER.parse_text(
        FULL_SYNTAX_SOURCE,
        source_path=Path("in-memory/full-syntax.md"),
    )
    block_kinds = {block.__class__.__name__ for block in document.blocks}
    assert {
        "Heading",
        "Paragraph",
        "ListBlock",
        "Figure",
        "Table",
        "Equation",
        "Algorithm",
        "Listing",
        "FootnoteDefinition",
    } <= block_kinds

    block_ids = {block.id for block in document.blocks if getattr(block, "id", None)}
    assert {
        "chap:introduction",
        "fig:model",
        "tbl:results",
        "eq:loss",
        "alg:train",
        "lst:predict",
    } <= block_ids

    assert {
        "fig:model",
        "tbl:results",
        "eq:loss",
        "alg:train",
        "lst:predict",
        "sec:background",
        "chap:introduction",
    } <= {
        reference.target
        for reference in DocumentIndex.from_document(document).cross_references
    }
    assert {"smith2025", "wang2024"} <= {
        key
        for citation in DocumentIndex.from_document(document).citations
        for key in citation.keys
    }
    assert {
        reference.label
        for reference in DocumentIndex.from_document(document).footnote_references
    } == {
        "note",
        "long",
    }
    assert document.metadata == {}


# ---------------------------------------------------------------------------
# D2 P0 负例（TF-D2-ID-001 / TF-D2-REF-004）：结构化诊断而非崩溃
# ---------------------------------------------------------------------------


def _validate_fixture(source: str, source_path: Path):
    document = PARSER.parse_text(source, source_path=source_path)
    context = ValidationContext.from_document(
        document,
        template_roots=(ROOT / "templates",),
        required_metadata=(),
    )
    issues = validate_document(document, context)
    return document, issues


def test_duplicate_id_fixture_reports_structured_diagnostic():
    document, issues = _validate_fixture(
        DUPLICATE_ID_SOURCE,
        Path("in-memory/duplicate-id.md"),
    )

    duplicates = [i for i in issues if i.code == "duplicate-id"]
    assert duplicates, "应报告 duplicate-id"
    assert all(i.severity == "error" for i in duplicates)
    assert {i.target for i in duplicates} == {"fig:dup"}
    # 两处容器都进入文档（重复的是第二处声明，line 指向后者）
    figure_ids = [b.id for b in document.blocks if b.__class__.__name__ == "Figure"]
    assert figure_ids == ["fig:dup", "fig:dup"]


def test_missing_reference_fixture_reports_structured_diagnostic():
    document, issues = _validate_fixture(
        MISSING_REFERENCE_SOURCE,
        Path("in-memory/missing-reference.md"),
    )

    missing = [i for i in issues if i.code == "missing-reference"]
    assert missing, "应报告 missing-reference"
    assert all(i.severity == "error" for i in missing)
    assert {i.target for i in missing} == {"fig:ghost"}
    # 唯一真实的 @fig:real 引用不被误报
    assert not [
        i for i in missing if i.target == "fig:real"
    ]
    assert "fig:real" in {b.id for b in document.blocks}
