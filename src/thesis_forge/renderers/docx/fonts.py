from __future__ import annotations

from docx.oxml.ns import qn
from docx.text.run import Font

from thesis_forge.templates.model import FontSpec, LengthSpec

from .units import to_docx_length


def apply_font(
    font: Font,
    spec: FontSpec,
    *,
    size: LengthSpec | None = None,
    bold: bool | None = None,
    italic: bool | None = None,
) -> None:
    font.name = spec.latin
    if size is not None:
        font.size = to_docx_length(size, em_size_pt=12)
    if bold is not None:
        font.bold = bold
    if italic is not None:
        font.italic = italic

    r_pr = font._element.get_or_add_rPr()
    r_fonts = r_pr.get_or_add_rFonts()
    r_fonts.set(qn("w:ascii"), spec.latin)
    r_fonts.set(qn("w:hAnsi"), spec.latin)
    r_fonts.set(qn("w:eastAsia"), spec.east_asia)

