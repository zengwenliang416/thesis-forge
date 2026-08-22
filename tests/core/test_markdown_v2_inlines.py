from __future__ import annotations

from pathlib import Path

import pytest

from thesis_forge.core.model import (
    Emphasis,
    HardBreak,
    InlineCode,
    InlineMath,
    Link,
    Paragraph,
    SoftBreak,
    Strong,
    Text,
)
from thesis_forge.core.parser import ParseError
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend


def _paragraph(source: str) -> Paragraph:
    document = MarkdownItParserBackend().parse_text(
        source,
        source_path=Path("inline.md"),
    )
    assert len(document.blocks) == 1
    assert isinstance(document.blocks[0], Paragraph)
    return document.blocks[0]


def test_standard_inline_tokens_become_typed_nodes_with_spans() -> None:
    paragraph = _paragraph(
        "a **bold _nested_** `code` [link](https://example.com) $x^2$.\n"
    )

    assert [type(inline) for inline in paragraph.inlines] == [
        Text,
        Strong,
        Text,
        InlineCode,
        Text,
        Link,
        Text,
        InlineMath,
        Text,
    ]
    assert paragraph.inlines[0].value == "a "

    strong = paragraph.inlines[1]
    assert isinstance(strong, Strong)
    assert [type(child) for child in strong.children] == [Text, Emphasis]
    assert strong.children[0].value == "bold "
    assert isinstance(strong.children[1], Emphasis)
    assert strong.children[1].children[0].value == "nested"

    code = paragraph.inlines[3]
    assert isinstance(code, InlineCode)
    assert code.value == "code"

    link = paragraph.inlines[5]
    assert isinstance(link, Link)
    assert link.label == "link"
    assert link.destination == "https://example.com"

    math = paragraph.inlines[7]
    assert isinstance(math, InlineMath)
    assert math.latex == "x^2"

    for inline in paragraph.inlines:
        assert inline.location.line == 1
        assert inline.location.column is not None
        assert inline.location.end_line == 1
        assert inline.location.end_column is not None


def test_nested_strong_and_emphasis_preserve_typed_children() -> None:
    paragraph = _paragraph("**outer *inner* text**\n")
    strong = paragraph.inlines[0]

    assert isinstance(strong, Strong)
    assert [type(child) for child in strong.children] == [Text, Emphasis, Text]
    assert isinstance(strong.children[1], Emphasis)
    assert strong.children[1].children[0].value == "inner"


def test_softbreak_and_hardbreak_are_distinct() -> None:
    soft = _paragraph("first\nsecond\n")
    hard = _paragraph("first  \nsecond\n")

    assert [type(inline) for inline in soft.inlines] == [Text, SoftBreak, Text]
    assert [type(inline) for inline in hard.inlines] == [Text, HardBreak, Text]
    assert soft.inlines[1].location.line == 1
    assert hard.inlines[1].location.line == 1


def test_inline_math_does_not_parse_inside_code() -> None:
    paragraph = _paragraph("`$not_math$` and $math$\n")

    assert isinstance(paragraph.inlines[0], InlineCode)
    assert paragraph.inlines[0].value == "$not_math$"
    assert isinstance(paragraph.inlines[2], InlineMath)
    assert paragraph.inlines[2].latex == "math"


def test_link_destination_allows_balanced_parentheses() -> None:
    paragraph = _paragraph("[link](https://example.com/a_(b))\n")
    link = paragraph.inlines[0]

    assert isinstance(link, Link)
    assert link.destination == "https://example.com/a_(b)"
    assert link.location.end_column == len("[link](https://example.com/a_(b))") + 1


def test_autolinks_become_typed_links_with_angle_bracket_spans() -> None:
    paragraph = _paragraph(
        "<https://example.com/path_(x)> and <user@example.com>\n"
    )

    url, separator, email = paragraph.inlines
    assert isinstance(url, Link)
    assert url.label == "https://example.com/path_(x)"
    assert url.destination == "https://example.com/path_(x)"
    assert url.location.column == 1
    assert url.location.end_column == len("<https://example.com/path_(x)>") + 1
    assert isinstance(separator, Text)
    assert isinstance(email, Link)
    assert email.label == "user@example.com"
    assert email.destination == "mailto:user@example.com"
    assert email.location.column == len("<https://example.com/path_(x)> and ") + 1


def test_escaped_text_maps_to_source_without_parsing_escaped_dollar() -> None:
    paragraph = _paragraph(r"cost \$5 and $x$" + "\n")

    assert [type(inline) for inline in paragraph.inlines] == [Text, InlineMath]
    assert paragraph.inlines[0].value == "cost $5 and "
    assert paragraph.inlines[1].latex == "x"
    assert paragraph.inlines[0].location.end_column == len(r"cost \$5 and ") + 1


def test_unsupported_inline_token_fails_explicitly() -> None:
    with pytest.raises(ParseError, match="行内 token: image"):
        _paragraph("![image](./image.png)\n")
