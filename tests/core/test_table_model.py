"""Focused tests for typed table cell and row model primitives."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from thesis_forge.core.model import (
    GeneratedOrigin,
    SourceLocation,
    Table,
    TableCell,
    TableRow,
    Text,
    inline_plain_text,
)
from thesis_forge.core.parser import parse_markdown_text


def test_table_cell_defaults_and_identity() -> None:
    first = TableCell()
    second = TableCell()

    assert first.inlines == ()
    assert first.alignment is None
    assert first.location == SourceLocation()
    assert first.origin is None
    assert first.node_id != second.node_id
    assert first == second


def test_table_cell_preserves_typed_inline_content_and_alignment() -> None:
    cell = TableCell(
        inlines=(Text(value="A"),),
        alignment="right",
        location=SourceLocation(line=4, column=2),
        origin=GeneratedOrigin(generator="table-normalize"),
    )

    assert cell.inlines == (Text(value="A"),)
    assert cell.alignment == "right"
    assert cell.location == SourceLocation(line=4, column=2)
    assert cell.origin == GeneratedOrigin(generator="table-normalize")


def test_table_row_preserves_header_state_and_cells() -> None:
    cells = (
        TableCell(inlines=(Text(value="A"),), alignment="left"),
        TableCell(inlines=(Text(value="B"),), alignment="center"),
    )
    row = TableRow(header=True, cells=cells)

    assert row.header is True
    assert isinstance(row.cells, tuple)
    assert row.cells == cells
    assert all(isinstance(cell, TableCell) for cell in row.cells)


def test_table_primitives_have_stable_structural_fields() -> None:
    assert [field.name for field in dataclasses.fields(TableCell)] == [
        "inlines",
        "alignment",
        "location",
        "node_id",
        "origin",
    ]
    assert [field.name for field in dataclasses.fields(TableRow)] == [
        "header",
        "cells",
        "location",
        "node_id",
        "origin",
    ]


def test_parser_populates_structured_table_caption_rows_and_cells() -> None:
    source = """::: table {#tbl:results}
caption: "结果 [@table-source]"

| 模型 | AUROC |
| :--- | ---: |
| A [@cell-source] | 0.91 |
:::
"""
    document = parse_markdown_text(source, source_path=Path("table.md"))

    table = document.blocks[0]
    assert isinstance(table, Table)
    assert inline_plain_text(table.caption_inlines) == "结果 [@table-source]"
    assert len(table.rows) == 2
    assert table.rows[0].header is True
    assert table.rows[1].header is False
    assert [cell.alignment for cell in table.rows[0].cells] == ["left", "right"]
    assert inline_plain_text(table.rows[1].cells[0].inlines) == "A [@cell-source]"
    assert inline_plain_text(table.rows[1].cells[1].inlines) == "0.91"


def test_table_has_no_raw_caption_or_markdown_fields() -> None:
    field_names = {field.name for field in dataclasses.fields(Table)}

    assert "caption" not in field_names
    assert "markdown" not in field_names
    assert {"caption_inlines", "rows"} <= field_names
