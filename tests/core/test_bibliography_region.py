from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from docforge.application.contracts import PreviewResult
from docforge.bibliography import resolve_citation_provider
from docforge.core.compiler import compile_document
from docforge.core.parser_backend import create_parser_backend
from docforge.core.render_plan import BibliographyInstruction, HeadingInstruction
from docforge.core.validator import ValidationContext, validate_document
from docforge.presentation.review import (
    ReviewBibliographyContent,
    ReviewHeadingContent,
    map_review_result,
)
from docforge.renderers.docx.package import validate_docx_package
from docforge.renderers.docx.renderer import DocxRenderer

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = ROOT / "templates"
TEMPLATE_PATH = TEMPLATE_ROOT / "schools" / "example-university" / "2026.yaml"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

MANIFEST = """\
schema: docforge.project.v1
project:
  id: bibliography-region-evidence
  language: zh-CN
document:
  source: document.md
  type: academic
metadata:
  title:
    zh: 参考文献区域验证
  authors:
    - name: 测试作者
academic:
  student:
    name: 测试作者
    id: "20260001"
  institution:
    name: 示例大学
    department: 计算机学院
  degree:
    name: 工学学士
    major: 文档工程
  advisor:
    name: 示例导师
  completion:
    date: "2026-08"
resources:
  root: .
  assets: assets
  bibliography: refs/references.bib
render:
  template_id: example-university-2026
  citation_style: gbt7714-2025-numeric
"""

SOURCE = """\
# 绪论 {#chap:intro}

已有研究支持该方案 [@smith2025]，后续研究进一步验证了该方法 [@doe2024]。

# 参考文献 {#chap:bibliography}
"""

BIBLIOGRAPHY = """\
@article{smith2025,
  author  = {Smith, Jane and Zhang, Wei},
  title   = {Typed Document Pipelines for Academic Publishing},
  journal = {Journal of Document Engineering},
  year    = {2025},
  volume  = {12},
  number  = {3},
  pages   = {101--120}
}

@article{doe2024,
  author  = {Doe, John},
  title   = {Structured Academic Documents},
  journal = {Document Systems Review},
  year    = {2024},
  volume  = {8},
  number  = {2},
  pages   = {10--18}
}
"""


def _compile_manifest_project(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "assets").mkdir()
    (project / "refs").mkdir()
    (project / "docforge.yaml").write_text(MANIFEST, encoding="utf-8")
    bibliography_path = project / "refs" / "references.bib"
    bibliography_path.write_text(BIBLIOGRAPHY, encoding="utf-8")
    source_path = project / "document.md"
    source_path.write_text(SOURCE, encoding="utf-8")

    document = create_parser_backend().parse_file(source_path)
    context = ValidationContext.from_document(
        document,
        template_roots=(TEMPLATE_ROOT,),
        required_metadata=(),
    )
    assert context.project_error is None
    assert context.template_error is None
    assert context.template_path == TEMPLATE_PATH
    assert context.manifest_bibliography_reference == "refs/references.bib"
    assert context.manifest_bibliography_path == bibliography_path.resolve()

    issues = validate_document(document, context)
    assert issues == []
    assert context.bibliography_database is not None
    assert context.bibliography_database.source_path == bibliography_path.resolve()
    assert tuple(context.bibliography_database.records) == ("smith2025", "doe2024")
    assert context.manifest_citation_style == "gbt7714-2025-numeric"
    citation_provider = resolve_citation_provider(context.manifest_citation_style)
    assert citation_provider.info().styles == ("GB-T-7714-2025",)

    plan = compile_document(
        document,
        template=context.template,
        template_path=context.template_path,
        bibliography_database=context.bibliography_database,
        citation_formatter=citation_provider,
    )
    return document, context, plan


def test_manifest_bibliography_region_resolves_once_through_review_and_docx(
    tmp_path: Path,
) -> None:
    document, context, plan = _compile_manifest_project(tmp_path)

    titles = [
        (index, node)
        for index, node in enumerate(plan.nodes)
        if isinstance(node, HeadingInstruction)
        and node.role == "bibliography.title"
    ]
    bibliographies = [
        (index, node)
        for index, node in enumerate(plan.nodes)
        if isinstance(node, BibliographyInstruction)
    ]

    assert len(titles) == 1
    title_index, title = titles[0]
    assert title.source_id == "chap:bibliography"
    assert title.text == "参考文献"

    assert len(bibliographies) == 1
    bibliography_index, bibliography = bibliographies[0]
    assert title_index < bibliography_index
    assert [(entry.key, entry.ordinal) for entry in bibliography.entries] == [
        ("smith2025", 1),
        ("doe2024", 2),
    ]
    assert bibliography.entries[0].text.startswith(
        "[1] SMITH J, ZHANG W. Typed Document Pipelines for Academic Publishing[J]."
    )
    assert bibliography.entries[1].text.startswith(
        "[2] DOE J. Structured Academic Documents[J]."
    )
    assert plan.citation_order == ("smith2025", "doe2024")

    review = map_review_result(
        PreviewResult(
            document=document,
            context=context,
            issues=(),
            plan=plan,
        )
    )
    review_titles = [
        block.content
        for block in review.blocks
        if block.kind == "heading"
        and isinstance(block.content, ReviewHeadingContent)
        and block.content.text == "参考文献"
    ]
    review_bibliographies = [
        block.content
        for block in review.blocks
        if block.kind == "bibliography"
    ]
    assert len(review_titles) == 1
    assert len(review_bibliographies) == 1
    review_bibliography = review_bibliographies[0]
    assert isinstance(review_bibliography, ReviewBibliographyContent)
    assert [(entry.ordinal, entry.text) for entry in review_bibliography.entries] == [
        (1, bibliography.entries[0].text),
        (2, bibliography.entries[1].text),
    ]
    assert all(
        key not in entry.text
        for key in ("smith2025", "doe2024")
        for entry in review_bibliography.entries
    )
    assert all("[@" not in entry.text for entry in review_bibliography.entries)

    output = tmp_path / "build" / "bibliography.docx"
    DocxRenderer().render(plan, output)
    validate_docx_package(output)

    with ZipFile(output) as package:
        document_xml = etree.fromstring(package.read("word/document.xml"))
        styles_xml = etree.fromstring(package.read("word/styles.xml"))

    paragraphs = document_xml.xpath(".//w:body/w:p", namespaces=NS)
    paragraph_texts = [
        "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
        for paragraph in paragraphs
    ]
    assert paragraph_texts.count("参考文献") == 1
    assert paragraph_texts.count(bibliography.entries[0].text) == 1
    assert paragraph_texts.count(bibliography.entries[1].text) == 1
    assert paragraph_texts.index("参考文献") < paragraph_texts.index(
        bibliography.entries[0].text
    )
    assert paragraph_texts.index(bibliography.entries[0].text) < paragraph_texts.index(
        bibliography.entries[1].text
    )
    assert "[@smith2025]" not in "\n".join(paragraph_texts)
    assert "[@doe2024]" not in "\n".join(paragraph_texts)

    title_paragraph = next(
        paragraph
        for paragraph, text in zip(paragraphs, paragraph_texts, strict=True)
        if text == "参考文献"
    )
    entry_paragraph = next(
        paragraph
        for paragraph, text in zip(paragraphs, paragraph_texts, strict=True)
        if text == bibliography.entries[0].text
    )
    assert title_paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS) == [
        "TFBibliographyTitle"
    ]
    assert entry_paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS) == [
        "TFBibliographyEntry"
    ]
    assert styles_xml.xpath(
        ".//w:style[@w:styleId='TFBibliographyTitle']",
        namespaces=NS,
    )
    assert styles_xml.xpath(
        ".//w:style[@w:styleId='TFBibliographyEntry']",
        namespaces=NS,
    )
