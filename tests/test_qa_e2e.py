"""QA E2E 结构门禁测试（对应用例 TF-D4-REF-001 / TF-D1-SYN-001 /
TF-D2-ID-001 / TF-D2-REF-004）。

对 qa/fixtures/e2e/figure-reference 走完整编译管线
（parse → validate → compile → render，不走 finalizer），
随后运行 qa/tools/openxml_validate.py 全部检查，并用 zipfile + lxml
做 XPath/field 语义断言。证据 JSON 落在 pytest tmp_path，不写入 qa/results/。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from thesis_forge.core.compiler import compile_document
from thesis_forge.core.parser import parse_markdown
from thesis_forge.core.validator import ValidationContext, validate_document
from thesis_forge.renderers.docx import DocxRenderer

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "qa" / "fixtures" / "e2e" / "figure-reference"
SOURCE = FIXTURE_DIR / "thesis.md"
TEMPLATE = ROOT / "templates" / "schools" / "example-university" / "2026.yaml"
OPENXML_VALIDATE = ROOT / "qa" / "tools" / "openxml_validate.py"
PARSER_FIXTURE = ROOT / "qa" / "fixtures" / "parser" / "full-syntax.md"

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


def _build_fixture_docx(output: Path) -> None:
    """parse → validate → compile → render（不走 finalizer / 办公软件刷新）。"""
    document = parse_markdown(SOURCE)
    context = ValidationContext.from_document(document, template_path=TEMPLATE)
    issues = validate_document(document, context)
    errors = [issue for issue in issues if issue.severity == "error"]
    assert not errors, f"夹具校验存在错误: {[(i.code, i.target) for i in errors]}"
    assert context.template is not None, "模板未成功解析"
    plan = compile_document(
        document,
        template=context.template,
        template_path=context.template_path,
        bibliography_database=context.bibliography_database,
    )
    DocxRenderer().render(plan, output)


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
    _build_fixture_docx(output)
    assert output.is_file()

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
        footer_parts = sorted(
            name
            for name in package.namelist()
            if name.startswith("word/footer") and name.endswith(".xml")
        )
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
    document = parse_markdown(PARSER_FIXTURE)
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
        "BibliographyBlock",
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
    } <= {reference.target for reference in document.cross_references}
    assert {"smith2025", "wang2024"} <= {
        key for citation in document.citations for key in citation.keys
    }
    assert {reference.label for reference in document.footnote_references} == {
        "note",
        "long",
    }
    assert document.metadata["document"]["type"] == "master_thesis"


# ---------------------------------------------------------------------------
# D2 P0 负例（TF-D2-ID-001 / TF-D2-REF-004）：结构化诊断而非崩溃
# ---------------------------------------------------------------------------


def _validate_fixture(source: Path):
    document = parse_markdown(source)
    context = ValidationContext.from_document(document, template_path=TEMPLATE)
    issues = validate_document(document, context)
    return document, issues


def test_duplicate_id_fixture_reports_structured_diagnostic():
    document, issues = _validate_fixture(ROOT / "qa/fixtures/parser/duplicate-id.md")

    duplicates = [i for i in issues if i.code == "duplicate-id"]
    assert duplicates, "应报告 duplicate-id"
    assert all(i.severity == "error" for i in duplicates)
    assert {i.target for i in duplicates} == {"fig:dup"}
    # 两处容器都进入文档（重复的是第二处声明，line 指向后者）
    figure_ids = [b.id for b in document.blocks if b.__class__.__name__ == "Figure"]
    assert figure_ids == ["fig:dup", "fig:dup"]


def test_missing_reference_fixture_reports_structured_diagnostic():
    document, issues = _validate_fixture(
        ROOT / "qa/fixtures/parser/missing-reference.md"
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
