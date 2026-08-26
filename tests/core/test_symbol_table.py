from pathlib import Path

import pytest

from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import (
    Algorithm,
    CrossReference,
    Equation,
    Figure,
    ForgeDocument,
    Heading,
    Listing,
    Paragraph,
    Table,
    Text,
)
from thesis_forge.core.render_plan import ParagraphInstruction, ReferenceRun
from thesis_forge.core.symbols import (
    BookmarkCollisionError,
    DuplicateSymbolError,
    NumberingInputs,
    SymbolTable,
)
from thesis_forge.templates import load_template


def _text(value: str) -> list[Text]:
    return [Text(value=value)]


def test_symbol_table_centralizes_identity_labels_numbering_and_bookmarks() -> None:
    document = ForgeDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Heading(id="chap:intro", level=1, inlines=_text("绪论")),
            Figure(
                id="fig:model",
                src="model.png",
                caption_inlines=_text("系统模型"),
            ),
            Table(id="tbl:data", caption_inlines=_text("实验数据")),
            Equation(id="eq:loss", latex="E=mc^2"),
            Listing(
                id="lst:demo",
                caption_inlines=_text("示例代码"),
                language="python",
                code="print(1)",
            ),
            Algorithm(
                id="alg:sort",
                caption_inlines=_text("排序算法"),
                body="1. 输入",
            ),
        ],
    )

    table = SymbolTable.from_document(
        document,
        load_template("templates/base/bachelor.yaml"),
    )

    figure = table.entries["fig:model"]
    assert figure.target_type == "fig"
    assert figure.display_label == "图1-1"
    assert figure.bookmark == "tf_fig_model"
    assert figure.numbering_inputs == NumberingInputs(
        kind="figure",
        chapter=1,
        mode="chapter",
        separator="-",
        sequence_value=1,
        number="1-1",
        caption_prefix="图",
    )
    assert table.entries["tbl:data"].display_label == "表1-1"
    assert table.entries["eq:loss"].display_label == "(1-1)"
    assert table.entries["lst:demo"].target_type == "lst"
    assert table.entries["alg:sort"].target_type == "alg"
    assert table.bookmarks == {
        "chap:intro": "tf_chap_intro",
        "fig:model": "tf_fig_model",
        "tbl:data": "tf_tbl_data",
        "eq:loss": "tf_eq_loss",
        "lst:demo": "tf_lst_demo",
        "alg:sort": "tf_alg_sort",
    }


def test_compile_document_consumes_symbol_table_for_cross_references() -> None:
    document = ForgeDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Paragraph(inlines=[CrossReference(target="fig:model")]),
            Figure(
                id="fig:model",
                src="model.png",
                caption_inlines=_text("系统模型"),
            ),
        ],
    )

    plan = compile_document(
        document,
        template=load_template("templates/base/bachelor.yaml"),
    )
    paragraph = next(
        node for node in plan.nodes if isinstance(node, ParagraphInstruction)
    )
    reference = next(
        run for run in paragraph.inlines if isinstance(run, ReferenceRun)
    )

    assert reference.bookmark == "tf_fig_model"
    assert reference.display_text == "图1-1"
    assert plan.references["fig:model"].display_text == "图1-1"


@pytest.mark.parametrize(
    ("blocks", "error_type"),
    [
        (
            [
                Heading(id="sec:duplicate", level=2),
                Figure(id="sec:duplicate", src="model.png"),
            ],
            DuplicateSymbolError,
        ),
        (
            [
                Figure(id="fig:a-b", src="a.png"),
                Figure(id="fig:a_b", src="b.png"),
            ],
            BookmarkCollisionError,
        ),
    ],
)
def test_symbol_table_rejects_identity_collisions(
    blocks: list[object],
    error_type: type[ValueError],
) -> None:
    document = ForgeDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=blocks,  # type: ignore[arg-type]
    )

    with pytest.raises(error_type):
        SymbolTable.from_document(document)


def test_compile_document_rejects_collisions_before_rendering() -> None:
    document = ForgeDocument(
        source_path=Path("/tmp/thesis.md"),
        blocks=[
            Figure(id="fig:a-b", src="a.png"),
            Figure(id="fig:a_b", src="b.png"),
        ],
    )

    with pytest.raises(BookmarkCollisionError):
        compile_document(document)
