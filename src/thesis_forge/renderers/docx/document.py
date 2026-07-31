from __future__ import annotations

from docx import Document
from docx.document import Document as DocumentObject
from docx.enum.section import WD_ORIENT
from docx.shared import Mm

from thesis_forge.templates.model import ThesisTemplate

from .styles import configure_styles
from .units import to_docx_length

PAGE_SIZES_MM = {
    "A3": (297, 420),
    "A4": (210, 297),
    "A5": (148, 210),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
}


def create_document(template: ThesisTemplate | None) -> DocumentObject:
    document = Document()
    if template is None:
        return document

    section = document.sections[0]
    width_mm, height_mm = PAGE_SIZES_MM[template.page.size]
    if template.page.orientation == "landscape":
        section.orientation = WD_ORIENT.LANDSCAPE
        width_mm, height_mm = height_mm, width_mm
    else:
        section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Mm(width_mm)
    section.page_height = Mm(height_mm)
    section.top_margin = to_docx_length(template.page.margin.top)
    section.bottom_margin = to_docx_length(template.page.margin.bottom)
    section.left_margin = to_docx_length(template.page.margin.left)
    section.right_margin = to_docx_length(template.page.margin.right)
    configure_styles(document, template)
    return document

