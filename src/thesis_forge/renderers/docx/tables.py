from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table

from thesis_forge.core.render_plan import TableInstruction
from thesis_forge.templates.model import LengthSpec, TableSpec, ThesisTemplate

from .captions import add_caption
from .styles import ALIGNMENTS
from .units import to_points

TABLE_EDGES = ("top", "left", "bottom", "right", "insideH", "insideV")


def _border_size(width: LengthSpec | None) -> int:
    width_points = to_points(width) if width is not None else 1
    size = round(width_points * 8)
    if not 2 <= size <= 96:
        raise ValueError("Word table border width must be between 0.25pt and 12pt")
    return size


def _replace_border(
    parent,
    edge: str,
    value: str,
    *,
    width: LengthSpec | None = None,
) -> None:
    existing = parent.find(qn(f"w:{edge}"))
    if existing is not None:
        parent.remove(existing)
    border = OxmlElement(f"w:{edge}")
    border.set(qn("w:val"), value)
    if value == "single":
        border.set(qn("w:sz"), str(_border_size(width)))
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "auto")
    parent.append(border)


def _table_borders(table: Table):
    table_properties = table._tbl.tblPr
    borders = table_properties.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        table_properties.append(borders)
    return borders


def _set_header_bottom_border(
    table: Table,
    value: str,
    *,
    width: LengthSpec | None = None,
) -> None:
    if not table.rows:
        return
    for cell in table.rows[0].cells:
        cell_properties = cell._tc.get_or_add_tcPr()
        borders = cell_properties.find(qn("w:tcBorders"))
        if borders is None:
            borders = OxmlElement("w:tcBorders")
            cell_properties.append(borders)
        _replace_border(borders, "bottom", value, width=width)


def _apply_border_policy(table: Table, table_spec: TableSpec | None) -> None:
    borders = _table_borders(table)
    style = table_spec.style if table_spec is not None else "plain"
    if style == "grid":
        for edge in TABLE_EDGES:
            _replace_border(borders, edge, "single")
        return

    for edge in TABLE_EDGES:
        _replace_border(borders, edge, "nil")
    if style == "three_line":
        assert table_spec is not None
        policy = table_spec.three_line
        _replace_border(borders, "top", "single", width=policy.top_width)
        _replace_border(borders, "bottom", "single", width=policy.bottom_width)
        _set_header_bottom_border(
            table,
            "single",
            width=policy.header_width,
        )


def render_table(
    document: DocumentObject,
    instruction: TableInstruction,
    template: ThesisTemplate | None,
) -> None:
    table_spec = template.table if template is not None else None
    caption_spec = table_spec.caption if table_spec is not None else None
    position = caption_spec.position if caption_spec is not None else "top"

    def render_caption() -> None:
        add_caption(
            document,
            label=instruction.label,
            caption=instruction.caption,
            bookmark=instruction.bookmark,
            spec=caption_spec,
            template=template,
            fallback_alignment="center",
            sequence=instruction.sequence,
        )

    if position == "top":
        render_caption()
    if not instruction.rows:
        if position == "bottom":
            render_caption()
        return

    table = document.add_table(rows=0, cols=len(instruction.rows[0].cells))
    for row_instruction in instruction.rows:
        row = table.add_row()
        for cell, cell_instruction in zip(
            row.cells,
            row_instruction.cells,
            strict=True,
        ):
            cell.text = cell_instruction.text
            if cell_instruction.alignment is not None:
                cell.paragraphs[0].alignment = ALIGNMENTS[cell_instruction.alignment]

    _apply_border_policy(table, table_spec)
    if position == "bottom":
        render_caption()
