"""Focused tests for typed table cell and row model primitives."""

from __future__ import annotations

import dataclasses

from thesis_forge.core.model import (
    GeneratedOrigin,
    SourceLocation,
    TableCell,
    TableRow,
    Text,
)


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
