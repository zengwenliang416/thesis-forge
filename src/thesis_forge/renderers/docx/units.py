from __future__ import annotations

from decimal import Decimal

from docx.shared import Cm, Emu, Mm, Pt

from thesis_forge.templates.model import LengthSpec


def to_docx_length(length: LengthSpec, *, em_size_pt: Decimal | float | None = None) -> Emu:
    value = float(length.value)
    if length.unit == "mm":
        return Mm(value)
    if length.unit == "cm":
        return Cm(value)
    if length.unit == "pt":
        return Pt(value)
    if em_size_pt is None:
        raise ValueError("em length requires em_size_pt")
    return Pt(value * float(em_size_pt))


def to_points(length: LengthSpec, *, em_size_pt: Decimal | float | None = None) -> float:
    return to_docx_length(length, em_size_pt=em_size_pt).pt

