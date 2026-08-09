from __future__ import annotations

from decimal import Decimal

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.run import Font

from thesis_forge.templates.model import FontSpec, LengthSpec

from .units import to_docx_length


def _apply_color(font: Font, color: str | None) -> None:
    if color is None:
        return

    r_pr = font._element.get_or_add_rPr()
    color_element = r_pr.find(qn("w:color"))
    if color_element is None:
        color_element = OxmlElement("w:color")
        r_pr.append(color_element)
    color_element.set(qn("w:val"), color if color == "auto" else color.upper())
    for attribute in ("w:themeColor", "w:themeTint", "w:themeShade"):
        color_element.attrib.pop(qn(attribute), None)


def apply_font(
    font: Font,
    spec: FontSpec | None,
    *,
    size: LengthSpec | None = None,
    color: str | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
    em_size_pt: Decimal | float | None = 12,
) -> None:
    if spec is not None:
        font.name = spec.latin
    if size is not None:
        font.size = to_docx_length(size, em_size_pt=em_size_pt)
    if bold is not None:
        font.bold = bold
    if italic is not None:
        font.italic = italic
    _apply_color(font, color)

    if spec is None:
        return
    r_pr = font._element.get_or_add_rPr()
    r_fonts = r_pr.get_or_add_rFonts()
    r_fonts.set(qn("w:ascii"), spec.latin)
    r_fonts.set(qn("w:hAnsi"), spec.latin)
    r_fonts.set(qn("w:eastAsia"), spec.east_asia)
