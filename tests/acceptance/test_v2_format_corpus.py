from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Iterable
from dataclasses import fields, is_dataclass
from pathlib import Path
from zipfile import ZipFile

from docx.shared import Mm
from lxml import etree

from docforge.application import preview_service, validation_service
from docforge.core.render_plan import (
    CitationRun,
    FigureInstruction,
    FootnoteReferenceRun,
    HardBreakRun,
    HeadingInstruction,
    HyperlinkRun,
    ListInstruction,
    MathRun,
    ParagraphInstruction,
    ReferenceRun,
    SectionBreakInstruction,
    SoftBreakRun,
    TextRun,
    TocInstruction,
)
from docforge.presentation.review import (
    ReviewTextRun,
    map_review_result,
)
from docforge.presentation.review_markdown import render_review_markdown
from docforge.renderers.docx import DocxRenderer
from docforge.renderers.docx.package import validate_docx_package

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "examples" / "v2-format-corpus"
SOURCE = CORPUS / "thesis.md"
CLI = ROOT / ".venv" / "bin" / "thesisforge"

NS = {
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}

TECHNICAL_MARKER_RE = re.compile(
    r"\[@[^\]]+\]|\{#[A-Za-z0-9_.:-]+\}|"
    r"(?<![\w-])@?(?:fig|tbl|eq|sec|chap|lst|alg|bib|ref|fn):[A-Za-z0-9_.-]+"
)


def _xml_part(path: Path, name: str):
    with ZipFile(path) as package:
        return etree.fromstring(package.read(name))


def _review_visible_text(value: object) -> Iterable[str]:
    if isinstance(value, ReviewTextRun) and value.code:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (tuple, list)):
        return tuple(
            text
            for item in value
            for text in _review_visible_text(item)
        )
    if not is_dataclass(value):
        return ()

    ignored_fields = {"asset_handle", "code", "destination"}
    return tuple(
        text
        for field in fields(value)
        if field.name not in ignored_fields
        for text in _review_visible_text(getattr(value, field.name))
    )


def _review_markdown(result) -> str:
    review = map_review_result(result)
    rendered = render_review_markdown(review, source_name="thesis.md")
    visible = "\n".join(
        text
        for block in review.blocks
        for text in _review_visible_text(block.content)
    )
    assert review.status == "ready"
    assert TECHNICAL_MARKER_RE.search(visible) is None

    markdown_without_fences = re.sub(
        r"```.*?```",
        "",
        rendered.markdown,
        flags=re.DOTALL,
    )
    assert TECHNICAL_MARKER_RE.search(markdown_without_fences) is None
    assert "{#literal}" in rendered.markdown
    assert "[@literal]" in rendered.markdown
    assert "@fig:literal" in rendered.markdown
    return rendered.markdown


def test_v2_format_corpus_covers_render_plan_review_and_inline_semantics() -> None:
    validation = validation_service(SOURCE)
    assert validation.errors == ()

    preview = preview_service(SOURCE)
    assert preview.errors == ()
    assert preview.plan is not None
    plan = preview.plan

    expected_kinds = {
        "cover",
        "section_break",
        "heading",
        "paragraph",
        "code_block",
        "blockquote",
        "list",
        "figure",
        "table",
        "equation",
        "listing",
        "algorithm",
        "footnote_definition",
        "bibliography",
        "page_break",
        "toc",
    }
    assert expected_kinds <= {node.kind for node in plan.nodes}
    assert plan.initial_section_role == "cover"
    assert {
        node.role
        for node in plan.nodes
        if isinstance(node, SectionBreakInstruction)
    } == {"front_matter", "main"}
    semantic_headings = {
        node.source_id: node
        for node in plan.nodes
        if isinstance(node, HeadingInstruction)
        and node.source_id in {
            "sec:semantic-types",
            "chap:acknowledgements",
            "chap:achievements",
        }
    }
    assert semantic_headings["sec:semantic-types"].level == 3
    assert semantic_headings["chap:acknowledgements"].role == (
        "special.acknowledgements"
    )
    assert semantic_headings["chap:achievements"].role == "special.achievements"

    toc = next(node for node in plan.nodes if isinstance(node, TocInstruction))
    assert len(toc.entries) >= 5
    assert any(
        entry.level == 3 and entry.bookmark == "tf_sec_semantic_types"
        for entry in toc.entries
    )
    assert any(
        isinstance(node, HeadingInstruction) and node.source_id == "chap:introduction"
        for node in plan.nodes
    )
    figures = [
        node for node in plan.nodes if isinstance(node, FigureInstruction)
    ]
    assert [node.source_id for node in figures] == [
        "fig:architecture",
        "fig:model",
    ]
    assert [node.width for node in figures] == ["75%", "90mm"]
    assert [
        (node.resolved_width.value, node.resolved_width.unit)
        for node in figures
        if node.resolved_width is not None
    ] == [(75, "percent"), (90, "mm")]

    lists = [node for node in plan.nodes if isinstance(node, ListInstruction)]
    ordered = next(node for node in lists if node.ordered)
    unordered = next(node for node in lists if not node.ordered)
    assert ordered.start == 3
    assert [item.ordinal for item in ordered.items] == [3, 4]
    assert [item.level for item in unordered.items] == [0, 1, 2, 0]

    equations = [node for node in plan.nodes if node.kind == "equation"]
    assert [node.source_id for node in equations] == [
        "eq:loss",
        "eq:energy",
        "eq:frac-sum",
        "eq:matrix",
    ]
    assert [node.latex for node in equations] == [
        r"L(\theta) = -\sum_{i=1}^{N} y_i \log \hat{y}_i",
        "E = mc^2",
        r"\frac{a}{b} + \sum_{i=1}^{n} x_i",
        r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
    ]
    bibliography = next(node for node in plan.nodes if node.kind == "bibliography")
    assert [entry.key for entry in bibliography.entries] == [
        "smith2025",
        "doe2024",
        "chen2023",
    ]
    assert "[J]" in bibliography.entries[0].text
    assert "[M]" in bibliography.entries[1].text
    assert "[C]" in bibliography.entries[2].text

    rich_paragraph = next(
        node
        for node in plan.nodes
        if isinstance(node, ParagraphInstruction) and node.text.startswith("这里有")
    )
    runs = rich_paragraph.inlines
    assert TextRun("粗体", bold=True) in runs
    assert TextRun("斜体", italic=True) in runs
    assert TextRun("粗斜体", bold=True, italic=True) in runs
    assert TextRun("inline-code", code=True) in runs
    assert HyperlinkRun("普通链接", "https://example.com/spec") in runs
    assert sum(
        isinstance(run, HyperlinkRun) and run.destination.startswith("mailto:")
        for run in runs
    ) == 2
    assert any(isinstance(run, MathRun) and run.latex == "E = mc^2" for run in runs)
    assert any(
        isinstance(run, CitationRun)
        and run.keys == ("smith2025",)
        and run.locator == "p. 12"
        for run in runs
    )
    assert {
        run.target_id
        for run in runs
        if isinstance(run, ReferenceRun)
    } >= {
        "chap:introduction",
        "sec:inlines",
        "fig:architecture",
        "tbl:results",
        "eq:loss",
        "lst:training",
        "alg:compile",
    }
    assert any(isinstance(run, SoftBreakRun) for run in runs)
    assert any(isinstance(run, HardBreakRun) for run in runs)
    assert any(
        isinstance(run, FootnoteReferenceRun)
        and run.label == "scope"
        and run.footnote_id == 1
        for run in runs
    )

    review_markdown = _review_markdown(preview)
    assert "# Review" in review_markdown
    assert "编译流水线" in review_markdown
    assert "训练代码清单" in review_markdown
    assert "脚注 1" in review_markdown
    assert "致谢" in review_markdown
    assert "攻读学位期间的成果" in review_markdown
    assert "三级标题用于验证 H3" in review_markdown


def test_v2_format_corpus_renders_editable_docx_objects_and_manifest_widths(
    tmp_path: Path,
) -> None:
    preview = preview_service(SOURCE)
    assert preview.plan is not None
    output = tmp_path / "v2-format-corpus.docx"
    DocxRenderer().render(preview.plan, output)
    validate_docx_package(output)

    document_xml = _xml_part(output, "word/document.xml")
    settings_xml = _xml_part(output, "word/settings.xml")
    footnotes_xml = _xml_part(output, "word/footnotes.xml")

    with ZipFile(output) as package:
        word_parts = {
            name: etree.fromstring(package.read(name))
            for name in package.namelist()
            if name.startswith("word/") and name.endswith(".xml")
        }

    field_codes = tuple(
        " ".join(text.split())
        for root in word_parts.values()
        for text in root.xpath(".//w:instrText/text()", namespaces=NS)
    )
    assert any(code.startswith("TOC ") for code in field_codes)
    assert any(code.startswith("SEQ TF_Figure_1 ") for code in field_codes)
    assert any(code.startswith("SEQ TF_Table_1 ") for code in field_codes)
    assert any(code.startswith("SEQ TF_Equation_1 ") for code in field_codes)
    assert "REF tf_fig_architecture \\h" in field_codes
    assert "REF tf_tbl_results \\h" in field_codes
    assert "PAGE" in field_codes
    assert settings_xml.xpath("./w:updateFields/@w:val", namespaces=NS) == ["true"]

    section = document_xml.xpath("(.//w:sectPr)[last()]", namespaces=NS)[0]
    page_width = int(section.xpath("string(./w:pgSz/@w:w)", namespaces=NS))
    left_margin = int(section.xpath("string(./w:pgMar/@w:left)", namespaces=NS))
    right_margin = int(section.xpath("string(./w:pgMar/@w:right)", namespaces=NS))
    content_width = page_width - left_margin - right_margin
    expected_extents = [
        str(round(content_width * 635 * 75 / 100)),
        str(Mm(90)),
    ]
    assert document_xml.xpath(".//wp:extent/@cx", namespaces=NS) == expected_extents
    assert len(document_xml.xpath(".//w:drawing", namespaces=NS)) == 2

    assert document_xml.xpath(".//w:rPr/w:b", namespaces=NS)
    assert document_xml.xpath(".//w:rPr/w:i", namespaces=NS)
    assert document_xml.xpath(".//w:rFonts[@w:ascii='Courier New']", namespaces=NS)
    assert document_xml.xpath(".//w:noProof", namespaces=NS)
    assert document_xml.xpath(
        ".//w:p[w:pPr/w:ind[@w:left='360' and @w:right='360']]",
        namespaces=NS,
    )

    table = document_xml.xpath(".//w:tbl", namespaces=NS)[0]
    assert table.xpath(
        ".//w:tr[1]/w:tc[1]/w:p/w:pPr/w:jc/@w:val",
        namespaces=NS,
    ) == ["left"]
    assert table.xpath(
        ".//w:tr[1]/w:tc[2]/w:p/w:pPr/w:jc/@w:val",
        namespaces=NS,
    ) == ["center"]
    assert table.xpath(
        ".//w:tr[1]/w:tc[3]/w:p/w:pPr/w:jc/@w:val",
        namespaces=NS,
    ) == ["right"]
    assert table.xpath(
        "./w:tblPr/w:tblBorders/w:top/@w:val",
        namespaces=NS,
    ) == ["single"]
    assert table.xpath(
        "./w:tblPr/w:tblBorders/w:bottom/@w:val",
        namespaces=NS,
    ) == ["single"]

    assert len(document_xml.xpath(".//m:oMath", namespaces=NS)) == 5
    equation_paragraphs = document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[starts-with(@w:name, 'tf_eq_')]]",
        namespaces=NS,
    )
    assert len(equation_paragraphs) == 4
    for paragraph in equation_paragraphs:
        assert paragraph.xpath(
            "./w:pPr/w:jc/@w:val",
            namespaces=NS,
        ) == ["left"]
        assert paragraph.xpath(
            "./w:pPr/w:tabs/w:tab/@w:val",
            namespaces=NS,
        ) == ["center", "right"]
        assert paragraph.xpath(
            "./w:pPr/w:tabs/w:tab/@w:pos",
            namespaces=NS,
        ) == [str(content_width // 2), str(content_width)]
        children = list(paragraph)
        math_index = next(
            index
            for index, child in enumerate(children)
            if etree.QName(child).localname == "oMath"
        )
        tab_indexes = [
            index
            for index, child in enumerate(children)
            if child.xpath("./w:tab", namespaces=NS)
        ]
        bookmark_index = next(
            index
            for index, child in enumerate(children)
            if etree.QName(child).localname == "bookmarkStart"
        )
        assert tab_indexes[0] < math_index < tab_indexes[1] < bookmark_index

    assert document_xml.xpath(
        ".//w:footnoteReference[@w:id='1']",
        namespaces=NS,
    )
    assert footnotes_xml.xpath(".//w:footnote[@w:id='1']", namespaces=NS)
    assert footnotes_xml.xpath(".//w:footnoteRef", namespaces=NS)

    bookmark_starts = {
        node.get(f"{{{NS['w']}}}name"): node.get(f"{{{NS['w']}}}id")
        for node in document_xml.xpath(".//w:bookmarkStart", namespaces=NS)
    }
    bookmark_ends = set(
        document_xml.xpath(".//w:bookmarkEnd/@w:id", namespaces=NS)
    )
    expected_bookmarks = {
        "tf_fig_architecture",
        "tf_fig_model",
        "tf_tbl_results",
        "tf_eq_loss",
        "tf_lst_training",
        "tf_alg_compile",
        "tf_toc_index",
    }
    assert expected_bookmarks <= set(bookmark_starts)
    assert set(bookmark_starts.values()) <= bookmark_ends
    assert len(document_xml.xpath(".//w:sectPr", namespaces=NS)) >= 3
    assert document_xml.xpath(
        ".//w:p[w:pPr/w:numPr]/w:pPr/w:numPr/w:ilvl/@w:val",
        namespaces=NS,
    ) == ["0", "0", "0", "1", "2", "0"]
    assert document_xml.xpath(
        ".//w:p[w:pPr/w:numPr]/w:pPr/w:numPr/w:numId/@w:val",
        namespaces=NS,
    )

    header_text = "\n".join(
        text
        for root in word_parts.values()
        if etree.QName(root).localname == "hdr"
        for text in root.xpath(".//w:t/text()", namespaces=NS)
    )
    assert "XX大学本科毕业论文" in header_text
    assert sum(
        name.startswith("word/header") and name.endswith(".xml")
        for name in word_parts
    ) >= 2
    assert sum(
        name.startswith("word/footer") and name.endswith(".xml")
        for name in word_parts
    ) >= 2


def test_v2_format_corpus_cli_validate_is_clean() -> None:
    result = subprocess.run(
        [str(CLI), "validate", str(CORPUS), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout) == {"issues": []}
