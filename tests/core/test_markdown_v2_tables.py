from __future__ import annotations

import pytest

from thesis_forge.core.model import Emphasis, Heading, Strong, Table, inline_plain_text
from thesis_forge.core.parser import ParseError
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend

BACKEND = MarkdownItParserBackend()


def _parse(source: str):
    return BACKEND.parse_text(source, source_path="tables.md")


def test_standard_table_parses_rows_alignment_and_typed_caption() -> None:
    document = _parse(
        "| 模型 | 指标 |\n"
        "| :--- | ---: |\n"
        "| A [@cell-source] | **0.91** |\n"
        ": 结果 *说明* {#tbl:results}\n"
    )

    table = document.blocks[0]
    assert isinstance(table, Table)
    assert table.id == "tbl:results"
    assert inline_plain_text(table.caption_inlines) == "结果 说明"
    assert isinstance(table.caption_inlines[1], Emphasis)
    assert len(table.rows) == 2
    assert table.rows[0].header is True
    assert table.rows[1].header is False
    assert [cell.alignment for cell in table.rows[0].cells] == ["left", "right"]
    assert inline_plain_text(table.rows[1].cells[0].inlines) == "A [@cell-source]"
    assert any(isinstance(inline, Strong) for inline in table.rows[1].cells[1].inlines)


def test_standard_gfm_table_allows_optional_outer_pipes_and_escaped_pipes() -> None:
    document = _parse("模型 | 备注\n--- | ---\nA \\| B | 可用\n")

    table = document.blocks[0]
    assert isinstance(table, Table)
    assert table.id is None
    assert table.caption_inlines == ()
    assert len(table.rows) == 2
    assert inline_plain_text(table.rows[1].cells[0].inlines) == "A | B"
    assert inline_plain_text(table.rows[1].cells[1].inlines) == "可用"


def test_standard_table_caption_is_consumed_before_following_heading() -> None:
    document = _parse(
        "| A |\n"
        "| --- |\n"
        "| 1 |\n"
        ": 数据 {#tbl:data}\n"
        "# 结论 {#chap:conclusion}\n"
    )

    assert [type(block) for block in document.blocks] == [Table, Heading]
    assert document.blocks[0].id == "tbl:data"
    assert document.blocks[1].id == "chap:conclusion"


@pytest.mark.parametrize(
    "source",
    [
        "| A | B |\n| --- | --- |\n| 1 |\n",
        "| A | B |\n| --- | --- |\n| 1 | 2 | 3 |\n",
    ],
    ids=["missing-cell", "extra-cell"],
)
def test_standard_table_rejects_malformed_column_counts(source: str) -> None:
    with pytest.raises(ParseError, match="列数"):
        _parse(source)


def test_standard_table_rejects_malformed_caption() -> None:
    with pytest.raises(ParseError, match="caption"):
        _parse("| A |\n| --- |\n| 1 |\n: 数据\n")
