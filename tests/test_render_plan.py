from decimal import Decimal

from thesis_forge.core.render_plan import (
    BibliographyEntryInstruction,
    BibliographyInstruction,
    FigureInstruction,
    FigureWidthInstruction,
    HeadingInstruction,
    RenderNode,
    RenderPlan,
    SectionBreakInstruction,
    SequenceInstruction,
    TableCellInstruction,
    TableInstruction,
    TableRowInstruction,
    TextRun,
)


def test_typed_instruction_preserves_generic_render_node_contract():
    instruction = HeadingInstruction(
        source_id="chap:intro",
        level=1,
        text="绪论",
        inlines=(TextRun("绪论"),),
        bookmark="tf_chap_intro",
    )
    plan = RenderPlan(nodes=[instruction])

    assert plan.nodes[0].kind == "heading"
    assert plan.nodes[0].payload == {
        "id": "chap:intro",
        "level": 1,
        "text": "绪论",
        "bookmark": "tf_chap_intro",
    }
    assert instruction.to_render_node() == RenderNode(
        kind="heading",
        payload={
            "id": "chap:intro",
            "level": 1,
            "text": "绪论",
            "bookmark": "tf_chap_intro",
        },
    )


def test_figure_and_table_instructions_keep_renderer_neutral_compatibility_payloads():
    figure = FigureInstruction(
        source_id="fig:model",
        src="./images/model.png",
        asset_path="/tmp/thesis/images/model.png",
        caption="模型",
        width="80%",
        resolved_width=FigureWidthInstruction(
            value=Decimal(80),
            unit="percent",
            origin="source",
        ),
        chapter=1,
        number="1-1",
        label="图1-1",
        bookmark="tf_fig_model",
    )
    table = TableInstruction(
        source_id="tbl:results",
        caption="结果",
        markdown="| A |\n| --- |\n| 1 |",
        rows=(
            TableRowInstruction(
                header=True,
                cells=(TableCellInstruction(text="A", alignment=None),),
            ),
            TableRowInstruction(
                header=False,
                cells=(TableCellInstruction(text="1", alignment=None),),
            ),
        ),
        chapter=1,
        number="1-1",
        label="表1-1",
        bookmark="tf_tbl_results",
    )

    assert figure.payload["src"] == "./images/model.png"
    assert figure.payload["asset_path"] == "/tmp/thesis/images/model.png"
    assert figure.payload["resolved_width"] == {
        "value": "80",
        "unit": "percent",
        "origin": "source",
    }
    assert table.payload["rows"] == [
        {"header": True, "cells": [{"text": "A", "alignment": None}]},
        {"header": False, "cells": [{"text": "1", "alignment": None}]},
    ]


def test_sequence_and_section_instructions_remain_renderer_neutral():
    sequence = SequenceInstruction(
        name="TF_Figure_1",
        value=2,
        prefix="图1-",
        suffix="",
        result="图1-2",
    )
    section = SectionBreakInstruction(role="main")

    assert sequence.field_code == "SEQ TF_Figure_1 \\r 2 \\* ARABIC"
    assert section.payload == {"role": "main"}
    assert section.to_render_node() == RenderNode(
        kind="section_break",
        payload={"role": "main"},
    )


def test_bibliography_instruction_has_renderer_neutral_ordered_payload():
    instruction = BibliographyInstruction(
        entries=(
            BibliographyEntryInstruction(
                key="doe2024",
                ordinal=1,
                text="[1] DOE J. Structured Academic Documents[M].",
            ),
            BibliographyEntryInstruction(
                key="smith2025",
                ordinal=2,
                text="[2] SMITH J. Deterministic Thesis Compilation[J].",
            ),
        )
    )

    assert instruction.payload == {
        "entries": [
            {
                "key": "doe2024",
                "ordinal": 1,
                "text": "[1] DOE J. Structured Academic Documents[M].",
            },
            {
                "key": "smith2025",
                "ordinal": 2,
                "text": "[2] SMITH J. Deterministic Thesis Compilation[J].",
            },
        ]
    }
    assert instruction.to_render_node() == RenderNode(
        kind="bibliography",
        payload=instruction.payload,
    )
