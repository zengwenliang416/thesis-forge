import inspect

import pytest

from thesis_forge.core.render_plan import (
    CitationRun,
    FootnoteReferenceRun,
    HardBreakRun,
    HyperlinkRun,
    MathRun,
    ReferenceRun,
    SoftBreakRun,
    TableCellInstruction,
    TableCellRuns,
    TableInstruction,
    TableRowInstruction,
    TextRun,
)


def test_table_cell_runs_validate_all_declared_inline_runs_and_project_text() -> None:
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

    cell_runs = TableCellRuns(runs)

    assert isinstance(cell_runs, str)
    assert cell_runs.runs == runs
    assert str(cell_runs) == "beforeFigure 1-1[1]linkx^2 \n"


def test_table_cell_runs_reject_unknown_values_at_the_typed_boundary() -> None:
    with pytest.raises(TypeError, match=r"unsupported InlineRun: object"):
        TableCellRuns((object(),))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        [TextRun("list")],
        iter((TextRun("iterator"),)),
    ],
)
def test_table_cell_runs_reject_non_tuple_containers(value: object) -> None:
    with pytest.raises(TypeError, match=r"TableCellRuns requires tuple"):
        TableCellRuns(value)  # type: ignore[arg-type]


def test_table_cell_runs_reject_tuple_subclasses() -> None:
    class TupleSubclass(tuple[TextRun, ...]):
        pass

    with pytest.raises(TypeError, match=r"TableCellRuns requires tuple"):
        TableCellRuns(TupleSubclass((TextRun("subclass"),)))


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

    assert isinstance(cell.text, TableCellRuns)
    assert cell.text.runs == runs
    assert str(cell.text) == "header"
    assert table.rows == (row,)
    assert "text" not in inspect.signature(TableCellInstruction.from_inlines).parameters
    assert "markdown" not in inspect.signature(
        TableInstruction.from_typed_rows
    ).parameters
