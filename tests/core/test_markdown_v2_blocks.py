from __future__ import annotations

from thesis_forge.core.model import (
    BlockQuote,
    CodeBlock,
    Heading,
    ListBlock,
    Paragraph,
    inline_plain_text,
)
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend

BACKEND = MarkdownItParserBackend()


def _parse(source: str):
    return BACKEND.parse_text(source, source_path="blocks.md")


def test_heading_id_and_paragraph_inline_spans_are_preserved() -> None:
    document = _parse("# 引言 {#chap:intro}\n\n第一段\n第二行\n")

    heading, paragraph = document.blocks
    assert isinstance(heading, Heading)
    assert heading.id == "chap:intro"
    assert heading.level == 1
    assert heading.location.line == 1
    assert inline_plain_text(heading.inlines) == "引言"
    assert heading.inlines[0].location.line == 1
    assert heading.inlines[0].location.column == 3
    assert heading.inlines[0].location.end_column == 5

    assert isinstance(paragraph, Paragraph)
    assert paragraph.location.line == 3
    assert inline_plain_text(paragraph.inlines) == "第一段\n第二行"
    assert [type(inline).__name__ for inline in paragraph.inlines] == [
        "Text",
        "SoftBreak",
        "Text",
    ]
    assert paragraph.inlines[0].location.line == 3
    assert paragraph.inlines[0].location.column == 1
    assert paragraph.inlines[2].location.line == 4


def test_nested_lists_preserve_order_depth_and_source_locations() -> None:
    document = _parse(
        "3. 第三章\n"
        "4. 第四章\n"
        "\n"
        "- 一级\n"
        "  - 二级\n"
        "    - 三级\n"
    )

    ordered, nested = document.blocks
    assert isinstance(ordered, ListBlock)
    assert ordered.ordered is True
    assert ordered.start == 3
    assert [item.ordinal for item in ordered.items] == [3, 4]
    assert [item.location.line for item in ordered.items] == [1, 2]

    assert isinstance(nested, ListBlock)
    assert nested.ordered is False
    assert [item.level for item in nested.items] == [0, 1, 2]
    assert [inline_plain_text(item.inlines) for item in nested.items] == [
        "一级",
        "二级",
        "三级",
    ]
    assert [item.location.line for item in nested.items] == [4, 5, 6]
    assert [item.inlines[0].location.column for item in nested.items] == [3, 5, 7]


def test_blockquote_contains_typed_child_blocks() -> None:
    document = _parse("> 引用内容\n")

    assert len(document.blocks) == 1
    quote = document.blocks[0]
    assert isinstance(quote, BlockQuote)
    assert quote.location.line == 1
    assert len(quote.children) == 1
    assert isinstance(quote.children[0], Paragraph)
    assert quote.children[0].location.line == 1
    assert inline_plain_text(quote.children[0].inlines) == "引用内容"


def test_fenced_code_is_a_literal_typed_block() -> None:
    document = _parse("```python\nprint(1)\n```\n")

    assert len(document.blocks) == 1
    code = document.blocks[0]
    assert isinstance(code, CodeBlock)
    assert code.language == "python"
    assert code.code == "print(1)\n"
    assert code.location.line == 1
