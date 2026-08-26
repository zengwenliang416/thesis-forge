from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from docforge.application.services import preview_service
from docforge.core.render_plan import (
    FigureInstruction,
    FigureWidthInstruction,
    RenderPlan,
)
from docforge.renderers.docx.renderer import DocxRenderer

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "tests" / "fixtures" / "v2-project"
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}


def _manifest_figure() -> tuple[FigureInstruction, RenderPlan]:
    result = preview_service(PROJECT / "thesis.md")

    assert result.plan is not None
    figure = next(
        node for node in result.plan.nodes if isinstance(node, FigureInstruction)
    )
    return figure, result.plan


def test_manifest_figure_width_reaches_render_plan_by_semantic_id() -> None:
    figure, _plan = _manifest_figure()

    assert figure.source_id == "fig:model"
    assert figure.width == "85%"
    assert figure.resolved_width == FigureWidthInstruction(
        value=Decimal(85),
        unit="percent",
        origin="manifest",
    )


def test_manifest_figure_width_reaches_docx_drawing_extent(tmp_path: Path) -> None:
    _figure, plan = _manifest_figure()
    output = tmp_path / "manifest-width.docx"

    DocxRenderer().render(plan, output)

    with ZipFile(output) as package:
        document_xml = etree.fromstring(package.read("word/document.xml"))
    section = document_xml.xpath("(.//w:sectPr)[last()]", namespaces=NS)[0]
    page_width = int(section.xpath("string(./w:pgSz/@w:w)", namespaces=NS))
    left = int(section.xpath("string(./w:pgMar/@w:left)", namespaces=NS))
    right = int(section.xpath("string(./w:pgMar/@w:right)", namespaces=NS))
    expected_width = round((page_width - left - right) * 635 * 85 / 100)

    assert document_xml.xpath(".//wp:extent/@cx", namespaces=NS) == [
        str(expected_width)
    ]
