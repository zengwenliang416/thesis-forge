from decimal import Decimal
from typing import get_args

import pytest

from docforge.core.render_plan import (
    BibliographyEntryInstruction,
    BibliographyInstruction,
    CaptionRuns,
    CoverInstruction,
    FigureInstruction,
    FigureWidthInstruction,
    HeadingInstruction,
    ParagraphInstruction,
    ParagraphRole,
    RenderPlan,
    SectionBreakInstruction,
    SequenceInstruction,
    TableCellInstruction,
    TableInstruction,
    TableRowInstruction,
    TextRun,
)


def test_cover_instruction_resolves_closed_renderer_neutral_fields():
    instruction = CoverInstruction(
        university="湖南工业大学",
        title="确定性论文编译",
        author="曾文亮",
    )

    assert instruction.value_for("university.name") == "湖南工业大学"
    assert instruction.value_for("thesis.title") == "确定性论文编译"
    assert instruction.value_for("author.name") == "曾文亮"
    assert instruction.value_for("advisor.title") == ""
    with pytest.raises(ValueError, match="unsupported cover field"):
        instruction.value_for("word.style")


def test_typed_instruction_preserves_renderer_neutral_fields():
    instruction = HeadingInstruction(
        source_id="chap:intro",
        level=1,
        text="绪论",
        inlines=(TextRun("绪论"),),
        bookmark="tf_chap_intro",
        role="abstract.zh.title",
    )
    plan = RenderPlan(nodes=[instruction])

    assert plan.nodes[0].kind == "heading"
    assert plan.nodes[0].payload == {
        "id": "chap:intro",
        "level": 1,
        "text": "绪论",
        "bookmark": "tf_chap_intro",
        "role": "abstract.zh.title",
    }


def test_paragraph_roles_are_closed_renderer_neutral_values_with_compatible_defaults():
    assert set(get_args(ParagraphRole)) == {
        "body",
        "abstract.zh.title",
        "abstract.zh.body",
        "keywords.zh",
        "abstract.en.title",
        "abstract.en.body",
        "keywords.en",
        "toc.title",
        "bibliography.title",
        "bibliography.entry",
        "special.acknowledgements",
        "special.achievements",
    }

    heading = HeadingInstruction(source_id=None, level=2, text="普通标题")
    paragraph = ParagraphInstruction(text="普通正文")

    assert heading.role is None
    assert paragraph.role == "body"
    assert heading.payload["role"] is None
    assert paragraph.payload == {"text": "普通正文", "role": "body"}


def test_figure_and_table_instructions_keep_renderer_neutral_compatibility_payloads():
    figure = FigureInstruction(
        source_id="fig:model",
        src="./images/model.png",
        asset_path="/tmp/thesis/images/model.png",
        caption=CaptionRuns((TextRun("模型"),)),
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
    table = TableInstruction.from_typed_rows(
        source_id="tbl:results",
        caption="结果",
        rows=(
            TableRowInstruction(
                header=True,
                cells=(
                    TableCellInstruction.from_inlines(
                        (TextRun("A"),),
                        alignment=None,
                    ),
                ),
            ),
            TableRowInstruction(
                header=False,
                cells=(
                    TableCellInstruction.from_inlines(
                        (TextRun("1"),),
                        alignment=None,
                    ),
                ),
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
    assert section.kind == "section_break"
    assert section.payload == {"role": "main"}


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
