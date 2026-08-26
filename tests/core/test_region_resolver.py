from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest
from lxml import etree
from pydantic import ValidationError

from docforge.application.contracts import PreviewResult
from docforge.core.compiler import compile_document
from docforge.core.parser_backend import create_parser_backend
from docforge.core.render_plan import (
    PageBreakInstruction,
    SectionBreakInstruction,
    TocEntryInstruction,
    TocInstruction,
)
from docforge.core.validator import ValidationContext
from docforge.presentation.review import (
    ReviewSectionContent,
    ReviewTocContent,
    map_review_result,
)
from docforge.renderers.docx.package import validate_docx_package
from docforge.renderers.docx.renderer import DocxRenderer
from docforge.templates.v2.schema import RegionsSpec

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = ROOT / "templates"
TEMPLATE_PATH = TEMPLATE_ROOT / "schools" / "example-university" / "2026.yaml"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

MANIFEST = """\
schema: thesisforge.project.v2
project:
  id: region-evidence
  language: zh-CN
document:
  source: thesis.md
resources:
  root: .
  assets: assets
render:
  template_id: example-university-2026
"""

SOURCE = """\
# 摘要 {#chap:abstract-zh}

摘要正文。

# 绪论 {#chap:intro}

## 研究背景 {#sec:background}
"""


def _compile_manifest_project(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "assets").mkdir()
    (project / "thesisforge.yaml").write_text(MANIFEST, encoding="utf-8")
    source_path = project / "thesis.md"
    source_path.write_text(SOURCE, encoding="utf-8")

    document = create_parser_backend().parse_file(source_path)
    context = ValidationContext.from_document(
        document,
        template_roots=(TEMPLATE_ROOT,),
    )
    assert context.project_error is None
    assert context.template_error is None
    assert context.template_path == TEMPLATE_PATH
    assert context.template is not None

    plan = compile_document(
        document,
        template=context.template,
        template_path=context.template_path,
    )
    return document, context, plan


def test_manifest_regions_resolve_once_through_review_and_docx(tmp_path: Path) -> None:
    document, context, plan = _compile_manifest_project(tmp_path)

    sections = [
        node for node in plan.nodes if isinstance(node, SectionBreakInstruction)
    ]
    assert [node.role for node in sections] == ["front_matter", "main"]
    assert plan.section_policy is context.template.sections
    assert plan.initial_section_role == "cover"

    toc_nodes = [node for node in plan.nodes if isinstance(node, TocInstruction)]
    assert len(toc_nodes) == 1
    toc = toc_nodes[0]
    assert toc.entries == (
        TocEntryInstruction(
            text="摘要",
            level=1,
            bookmark="tf_chap_abstract_zh",
        ),
        TocEntryInstruction(
            text="绪论",
            level=1,
            bookmark="tf_chap_intro",
        ),
        TocEntryInstruction(
            text="研究背景",
            level=2,
            bookmark="tf_sec_background",
        ),
    )
    toc_index = plan.nodes.index(toc)
    assert isinstance(plan.nodes[toc_index - 1], PageBreakInstruction)
    assert plan.nodes[toc_index + 1] == SectionBreakInstruction(role="main")

    review = map_review_result(
        PreviewResult(
            document=document,
            context=context,
            issues=(),
            plan=plan,
        )
    )
    assert review.status == "ready"
    review_sections = [
        block.content
        for block in review.blocks
        if block.kind == "section_break"
    ]
    assert all(isinstance(content, ReviewSectionContent) for content in review_sections)
    assert [content.role for content in review_sections] == [
        "front_matter",
        "main",
    ]
    review_toc = next(
        block.content for block in review.blocks if block.kind == "toc"
    )
    assert isinstance(review_toc, ReviewTocContent)
    assert [(entry.text, entry.level) for entry in review_toc.entries] == [
        ("摘要", 1),
        ("绪论", 1),
        ("研究背景", 2),
    ]

    output = tmp_path / "build" / "regions.docx"
    DocxRenderer().render(plan, output)
    validate_docx_package(output)

    with ZipFile(output) as package:
        document_xml = etree.fromstring(package.read("word/document.xml"))

    section_properties = document_xml.xpath(".//w:sectPr", namespaces=NS)
    assert len(section_properties) == 3
    page_formats = {
        value
        for section in section_properties
        for value in section.xpath("./w:pgNumType/@w:fmt", namespaces=NS)
    }
    assert {"upperRoman", "decimal"} <= page_formats
    decimal_sections = [
        section
        for section in section_properties
        if section.xpath("./w:pgNumType/@w:fmt", namespaces=NS) == ["decimal"]
    ]
    assert len(decimal_sections) == 1
    assert decimal_sections[0].xpath(
        "./w:pgNumType/@w:start",
        namespaces=NS,
    ) == ["1"]

    toc_fields = document_xml.xpath(
        ".//w:p[.//w:instrText[contains(., 'TOC')]]",
        namespaces=NS,
    )
    assert len(toc_fields) == 1
    assert [
        "".join(field.xpath(".//w:instrText/text()", namespaces=NS)).strip()
        for field in toc_fields
    ] == ['TOC \\o "1-3" \\h \\z \\u']
    body = toc_fields[0].getparent()
    field_index = body.index(toc_fields[0])
    cached_entries = body[field_index + 1 : field_index + 4]
    assert [
        paragraph.xpath(".//w:t/text()", namespaces=NS)[0]
        for paragraph in cached_entries
    ] == ["摘要", "绪论", "研究背景"]


def test_region_order_contract_rejects_duplicate_and_invalid_placement() -> None:
    legal = RegionsSpec(order=["cover", "toc", "main"])
    assert legal.order == ["cover", "toc", "main"]

    with pytest.raises(ValidationError, match="regions.order 元素必须唯一"):
        RegionsSpec(order=["main", "main"])

    with pytest.raises(ValidationError, match="regions.order 必须含且仅含一个 main"):
        RegionsSpec(order=["toc"])
