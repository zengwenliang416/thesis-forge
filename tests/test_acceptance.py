from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from thesis_forge.renderers.docx.package import validate_docx_package

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples" / "bachelor-thesis"
SOURCE = EXAMPLE_DIR / "thesis.md"
BIBLIOGRAPHY = EXAMPLE_DIR / "references.bib"
FIGURE = EXAMPLE_DIR / "images" / "acceptance-architecture.png"
CLI = ROOT / ".venv" / "bin" / "thesisforge"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _offline_environment(tmp_path: Path) -> dict[str, str]:
    blocker = tmp_path / "offline"
    blocker.mkdir(exist_ok=True)
    (blocker / "sitecustomize.py").write_text(
        """import socket
def blocked(*args, **kwargs):
    raise RuntimeError("network access is forbidden in acceptance tests")
socket.create_connection = blocked
socket.socket.connect = blocked
""",
        encoding="utf-8",
    )
    environment = {
        key: value
        for key, value in os.environ.items()
        if not any(
            marker in key.upper()
            for marker in (
                "OPENAI",
                "ANTHROPIC",
                "GEMINI",
                "GOOGLE_API_KEY",
                "AZURE",
                "DEEPSEEK",
            )
        )
    }
    existing_python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(blocker), existing_python_path) if value
    )
    environment["NO_PROXY"] = "*"
    environment["no_proxy"] = "*"
    return environment


def _run_cli(tmp_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CLI), *arguments],
        cwd=tmp_path,
        env=_offline_environment(tmp_path),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _xml_part(path: Path, part: str):
    with ZipFile(path) as package:
        return etree.fromstring(package.read(part))


def _field_instructions(document_xml) -> tuple[str, ...]:
    return tuple(
        " ".join(text.split())
        for text in document_xml.xpath(".//w:instrText/text()", namespaces=NS)
    )


def _normalized_ooxml(path: Path) -> dict[str, object]:
    document_xml = _xml_part(path, "word/document.xml")
    return {
        "fields": _field_instructions(document_xml),
        "bookmarks": tuple(
            document_xml.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
        ),
        "section_count": len(document_xml.xpath(".//w:sectPr", namespaces=NS)),
        "drawing_count": len(document_xml.xpath(".//w:drawing", namespaces=NS)),
        "table_count": len(document_xml.xpath(".//w:tbl", namespaces=NS)),
        "math_count": len(document_xml.xpath(".//m:oMath", namespaces=NS)),
    }


def test_complete_example_inventory_and_offline_inspect_are_read_only(tmp_path: Path):
    input_paths = (SOURCE, BIBLIOGRAPHY, FIGURE)
    before = {path: _digest(path) for path in input_paths}

    result = _run_cli(tmp_path, "inspect", str(SOURCE))

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    block_kinds = {block["kind"] for block in payload["blocks"]}
    assert {
        "Heading",
        "Paragraph",
        "ListBlock",
        "Figure",
        "Table",
        "Equation",
        "Listing",
        "Algorithm",
        "FootnoteDefinition",
        "BibliographyBlock",
    } <= block_kinds
    block_ids = {block["id"] for block in payload["blocks"] if block.get("id")}
    assert {
        "chap:abstract-zh",
        "chap:abstract-en",
        "chap:introduction",
        "fig:architecture",
        "tbl:capabilities",
        "eq:pipeline",
        "alg:build",
        "lst:service",
        "chap:acknowledgements",
        "chap:appendix-a",
    } <= block_ids
    assert {"fig:architecture", "tbl:capabilities", "eq:pipeline"} <= {
        reference["target"] for reference in payload["cross_references"]
    }
    assert {"ref-example-1", "ref-example-2"} <= {
        key for citation in payload["citations"] for key in citation["keys"]
    }
    assert {reference["label"] for reference in payload["footnote_references"]} == {
        "determinism"
    }
    assert {path: _digest(path) for path in input_paths} == before
    assert list(tmp_path.iterdir()) == [tmp_path / "offline"]


def test_complete_example_validates_and_builds_offline_without_mutating_inputs(
    tmp_path: Path,
):
    input_paths = (SOURCE, BIBLIOGRAPHY, FIGURE)
    before = {path: _digest(path) for path in input_paths}

    validation = _run_cli(tmp_path, "validate", str(SOURCE))
    assert validation.returncode == 0, validation.stderr or validation.stdout
    assert "未发现结构性问题" in validation.stdout

    output = tmp_path / "acceptance.docx"
    build = _run_cli(tmp_path, "build", str(SOURCE), "-o", str(output))
    assert build.returncode == 0, build.stderr or build.stdout
    assert output.is_file()
    validate_docx_package(output)
    assert {path: _digest(path) for path in input_paths} == before
    assert sorted(path.name for path in tmp_path.iterdir()) == ["acceptance.docx", "offline"]


def test_complete_example_docx_contains_required_visible_content_and_word_objects(
    tmp_path: Path,
):
    output = tmp_path / "complete-thesis.docx"
    build = _run_cli(tmp_path, "build", str(SOURCE), "-o", str(output))
    assert build.returncode == 0, build.stderr or build.stdout

    with ZipFile(output) as package:
        assert package.testzip() is None
        parts = set(package.namelist())
    assert {
        "word/document.xml",
        "word/styles.xml",
        "word/settings.xml",
        "word/numbering.xml",
        "word/footnotes.xml",
    } <= parts
    assert any(part.startswith("word/media/") for part in parts)
    assert any(part.startswith("word/header") for part in parts)
    assert any(part.startswith("word/footer") for part in parts)

    document_xml = _xml_part(output, "word/document.xml")
    document_text = "".join(document_xml.xpath(".//w:body//w:t/text()", namespaces=NS))
    for expected in (
        "XX大学",
        "基于结构化 Markdown 的本科论文编译系统设计",
        "张三",
        "2022000001",
        "李老师",
        "摘要",
        "Abstract",
        "绪论",
        "系统设计",
        "参考文献",
        "致谢",
        "附录 A",
    ):
        assert expected in document_text
    heading_texts = {
        "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
        for paragraph in document_xml.xpath(
            (
                ".//w:p[w:pPr/w:pStyle["
                "starts-with(@w:val, 'Heading') "
                "or @w:val='TFAbstractZHTitle' "
                "or @w:val='TFAbstractENTitle'"
                "]]"
            ),
            namespaces=NS,
        )
    }
    assert {"摘要", "Abstract", "绪论", "系统设计"} <= heading_texts
    assert document_xml.xpath(
        ".//w:p[.//w:t[text()='摘要']]/w:pPr/w:pStyle/@w:val",
        namespaces=NS,
    ) == ["TFAbstractZHTitle"]
    assert document_xml.xpath(
        ".//w:p[.//w:t[text()='Abstract']]/w:pPr/w:pStyle/@w:val",
        namespaces=NS,
    ) == ["TFAbstractENTitle"]
    assert {
        "XX大学",
        "基于结构化 Markdown 的本科论文编译系统设计",
    }.isdisjoint(heading_texts)

    fields = _field_instructions(document_xml)
    assert any(field.startswith("TOC ") for field in fields)
    assert sum(field.startswith("SEQ ") for field in fields) >= 3
    assert any(field == "REF tf_fig_architecture \\h" for field in fields)
    assert any(field == "REF tf_tbl_capabilities \\h" for field in fields)
    assert any(field == "REF tf_eq_pipeline \\h" for field in fields)
    footer_fields = tuple(
        field
        for part in sorted(parts)
        if part.startswith("word/footer") and part.endswith(".xml")
        for field in _field_instructions(_xml_part(output, part))
    )
    assert "PAGE" in footer_fields
    assert "NUMPAGES" in footer_fields

    bookmark_names = set(
        document_xml.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
    )
    assert {
        "tf_fig_architecture",
        "tf_tbl_capabilities",
        "tf_eq_pipeline",
        "tf_alg_build",
        "tf_lst_service",
    } <= bookmark_names
    assert document_xml.xpath(".//m:oMath", namespaces=NS)
    assert document_xml.xpath(".//w:footnoteReference", namespaces=NS)
    assert len(document_xml.xpath(".//w:sectPr", namespaces=NS)) >= 3
    assert document_xml.xpath(".//w:headerReference", namespaces=NS)
    assert document_xml.xpath(".//w:footerReference", namespaces=NS)
    assert document_xml.xpath(".//w:drawing", namespaces=NS)

    tables = document_xml.xpath(".//w:tbl", namespaces=NS)
    assert tables
    borders = tables[0].xpath("./w:tblPr/w:tblBorders", namespaces=NS)
    assert borders
    assert borders[0].xpath("./w:top/@w:val", namespaces=NS) == ["single"]
    assert borders[0].xpath("./w:bottom/@w:val", namespaces=NS) == ["single"]
    assert "[1]" in document_text
    assert "[2]" in document_text
    assert "Deterministic Thesis Compilation" in document_text

    footnotes_xml = _xml_part(output, "word/footnotes.xml")
    footnote_text = "".join(
        footnotes_xml.xpath("./w:footnote[@w:id='1']//w:t/text()", namespaces=NS)
    )
    assert "确定性构建" in footnote_text


def test_complete_example_repeated_builds_are_semantically_equivalent(tmp_path: Path):
    first = tmp_path / "first.docx"
    second = tmp_path / "second.docx"

    first_result = _run_cli(tmp_path, "build", str(SOURCE), "-o", str(first))
    second_result = _run_cli(tmp_path, "build", str(SOURCE), "-o", str(second))

    assert first_result.returncode == 0, first_result.stderr or first_result.stdout
    assert second_result.returncode == 0, second_result.stderr or second_result.stdout
    assert _normalized_ooxml(first) == _normalized_ooxml(second)
