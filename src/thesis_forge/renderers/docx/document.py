from __future__ import annotations

from docx import Document
from docx.document import Document as DocumentObject
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm

from thesis_forge.templates.model import PageSpec, ThesisTemplate

from .styles import configure_styles
from .units import to_docx_length

PAGE_SIZES_MM = {
    "A3": (297, 420),
    "A4": (210, 297),
    "A5": (148, 210),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
}
DOCUMENT_GRID_TYPES = {
    "default": "default",
    "lines": "lines",
    "lines_and_chars": "linesAndChars",
    "snap_to_chars": "snapToChars",
}


def _apply_document_grid(section, page: PageSpec) -> None:
    if page.document_grid is None:
        return

    section_properties = section._sectPr
    existing = section_properties.find(qn("w:docGrid"))
    if existing is not None:
        section_properties.remove(existing)

    grid = OxmlElement("w:docGrid")
    grid.set(qn("w:type"), DOCUMENT_GRID_TYPES[page.document_grid.type])
    if page.document_grid.line_pitch is not None:
        grid.set(
            qn("w:linePitch"),
            str(to_docx_length(page.document_grid.line_pitch).twips),
        )
    if page.document_grid.char_space is not None:
        grid.set(qn("w:charSpace"), str(page.document_grid.char_space))
    section_properties.insert_element_before(
        grid,
        "w:printerSettings",
        "w:sectPrChange",
    )


def configure_section_geometry(section, page: PageSpec) -> None:
    width_mm, height_mm = PAGE_SIZES_MM[page.size]
    if page.orientation == "landscape":
        section.orientation = WD_ORIENT.LANDSCAPE
        width_mm, height_mm = height_mm, width_mm
    else:
        section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Mm(width_mm)
    section.page_height = Mm(height_mm)
    section.top_margin = to_docx_length(page.margin.top)
    section.bottom_margin = to_docx_length(page.margin.bottom)
    section.left_margin = to_docx_length(page.margin.left)
    section.right_margin = to_docx_length(page.margin.right)
    if page.header_distance is not None:
        section.header_distance = to_docx_length(page.header_distance)
    if page.footer_distance is not None:
        section.footer_distance = to_docx_length(page.footer_distance)
    _apply_document_grid(section, page)


def create_document(template: ThesisTemplate | None) -> DocumentObject:
    document = Document()
    if template is None:
        return document

    configure_section_geometry(document.sections[0], template.page)
    configure_styles(document, template)
    return document
