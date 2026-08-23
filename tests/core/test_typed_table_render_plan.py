import inspect
from pathlib import Path

import pytest

from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import (
    Citation,
    CrossReference,
    Emphasis,
    FootnoteDefinition,
    FootnoteReference,
    HardBreak,
    Heading,
    InlineCode,
    InlineMath,
    Link,
    SoftBreak,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
    ThesisDocument,
)
from thesis_forge.core.render_plan import (
    CitationRun,
    FootnoteReferenceRun,
    HardBreakRun,
    HyperlinkRun,
    MathRun,
    ReferenceRun,
    SoftBreakRun,
    TableCellInstruction,
    TableInstruction,
    TableRowInstruction,
    TextRun,
)


def test_table_cell_inlines_validate_all_declared_inline_runs_and_project_text() -> None:
    runs = (
        TextRun("before"),
        ReferenceRun("fig:model", "tf_fig_model", "Figure 1-1"),
        CitationRun(("smith2025",), (1,), raw="[@smith2025]", text="[1]"),
        FootnoteReferenceRun("note", 1),
        HyperlinkRun("link", "https://example.test"),
        MathRun("x^2"),
        SoftBreakRun(),
        HardBreakRun(),
    )

    cell = TableCellInstruction.from_inlines(runs)

    assert cell.inlines == runs
    assert cell.text == "beforeFigure 1-1[1]linkx^2 \n"


def test_table_cell_inlines_reject_unknown_values_at_the_typed_boundary() -> None:
    with pytest.raises(TypeError, match=r"unsupported InlineRun: object"):
        TableCellInstruction.from_inlines((object(),))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        [TextRun("list")],
        iter((TextRun("iterator"),)),
    ],
)
def test_table_cell_inlines_reject_non_tuple_containers(value: object) -> None:
    with pytest.raises(TypeError, match=r"TableCellInstruction requires tuple"):
        TableCellInstruction.from_inlines(value)  # type: ignore[arg-type]


def test_table_cell_inlines_reject_tuple_subclasses() -> None:
    class TupleSubclass(tuple[TextRun, ...]):
        pass

    with pytest.raises(TypeError, match=r"TableCellInstruction requires tuple"):
        TableCellInstruction.from_inlines(TupleSubclass((TextRun("subclass"),)))


def test_table_constructors_use_typed_runs_without_raw_fixture_arguments() -> None:
    runs = (TextRun("header"),)
    cell = TableCellInstruction.from_inlines(runs, alignment="center")
    row = TableRowInstruction(header=True, cells=(cell,))
    table = TableInstruction.from_typed_rows(
        source_id="tbl:results",
        caption="Results",
        rows=(row,),
        chapter=1,
        number="1-1",
        label="Table 1-1",
        bookmark="tf_tbl_results",
    )

    assert cell.inlines == runs
    assert cell.text == "header"
    assert table.rows == (row,)
    assert "inlines" in inspect.signature(TableCellInstruction).parameters
    assert "text" not in inspect.signature(TableCellInstruction.from_inlines).parameters
    assert "markdown" not in inspect.signature(
        TableInstruction.from_typed_rows
    ).parameters
    assert "markdown" not in table.payload
    assert table.payload["rows"] == [
        {"header": True, "cells": [{"text": "header", "alignment": "center"}]}
    ]


def test_compiler_builds_table_cells_from_authoritative_inline_runs() -> None:
    document = ThesisDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(id="sec:target", level=1, inlines=[Text(value="Target")]),
            FootnoteDefinition(label="note", inlines=[Text(value="Footnote")]),
            Table(
                id="tbl:rich",
                caption_inlines=(Text(value="Rich table"),),
                rows=(
                    TableRow(
                        header=True,
                        cells=(TableCell(inlines=(Text(value="Header"),)),),
                    ),
                    TableRow(
                        cells=(
                            TableCell(
                                inlines=(
                                    Text(value="text"),
                                    Strong(children=(Text(value="strong"),)),
                                    Emphasis(children=(Text(value="emphasis"),)),
                                    InlineCode(value="code"),
                                    Link(label="link", destination="https://example.test"),
                                    InlineMath(latex="x^2"),
                                    SoftBreak(),
                                    HardBreak(),
                                    CrossReference(target="sec:target"),
                                    Citation(keys=["smith2025"], raw="[@smith2025]"),
                                    FootnoteReference(label="note"),
                                )
                            ),
                        ),
                    ),
                ),
            ),
        ],
    )

    plan = compile_document(document)
    table = next(node for node in plan.nodes if isinstance(node, TableInstruction))
    cell = table.rows[1].cells[0]

    assert [type(run) for run in cell.inlines] == [
        TextRun,
        TextRun,
        TextRun,
        TextRun,
        HyperlinkRun,
        MathRun,
        SoftBreakRun,
        HardBreakRun,
        ReferenceRun,
        CitationRun,
        FootnoteReferenceRun,
    ]
    assert cell.inlines[1] == TextRun("strong", bold=True)
    assert cell.inlines[2] == TextRun("emphasis")
    assert cell.inlines[3] == TextRun("code", code=True)
    assert cell.inlines[4] == HyperlinkRun("link", "https://example.test")
    assert cell.inlines[8].target_id == "sec:target"
    assert cell.inlines[8].display_text == "Target"
    assert cell.inlines[9].raw == ""
    assert cell.inlines[9].text == "[1]"
    assert cell.inlines[10] == FootnoteReferenceRun("note", 1)
    assert "markdown" not in table.payload
    assert "[@smith2025]" not in cell.text
    assert "sec:target" not in cell.text
