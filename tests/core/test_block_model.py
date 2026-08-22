"""Focused tests for typed block structures (BlockQuote/CodeBlock/OrderedList/BulletList) and inline_plain_text."""

from __future__ import annotations

import dataclasses

import pytest

from thesis_forge.core.model import (
    Block,
    BlockQuote,
    BulletList,
    Citation,
    CodeBlock,
    CrossReference,
    Emphasis,
    FootnoteReference,
    HardBreak,
    Heading,
    Inline,
    InlineCode,
    InlineMath,
    Link,
    ListItem,
    OrderedList,
    Paragraph,
    SoftBreak,
    Strong,
    Text,
    inline_plain_text,
)

NEW_BLOCK_CLASSES = [BlockQuote, CodeBlock, OrderedList, BulletList]


def test_new_block_types_construct_with_defaults() -> None:
    for cls in NEW_BLOCK_CLASSES:
        node = cls()
        assert isinstance(node, Block)
        assert node.id is None
        assert node.node_id
        assert node.origin is None
    node_ids = [cls().node_id for cls in NEW_BLOCK_CLASSES]
    assert len(set(node_ids)) == len(node_ids)


def test_block_quote_children_default_to_empty_tuple() -> None:
    quote = BlockQuote()
    assert quote.children == ()
    children = (Paragraph(text="quoted"),)
    node = BlockQuote(children=children)
    assert isinstance(node.children, tuple)
    assert node.children == children
    assert all(isinstance(child, Block) for child in node.children)


def test_code_block_round_trip_and_defaults() -> None:
    node = CodeBlock(language="python", code="x = 1")
    assert node.language == "python"
    assert node.code == "x = 1"
    default = CodeBlock()
    assert default.language is None
    assert default.code == ""


def test_ordered_list_round_trip_and_defaults() -> None:
    items = (ListItem(text="first"), ListItem(text="second"))
    node = OrderedList(start=3, items=items)
    assert node.start == 3
    assert node.items == items
    default = OrderedList()
    assert default.start is None
    assert default.items == ()
    assert isinstance(default.items, tuple)


def test_bullet_list_round_trip_and_defaults() -> None:
    items = (ListItem(text="one"),)
    node = BulletList(items=items)
    assert node.items == items
    default = BulletList()
    assert default.items == ()
    assert isinstance(default.items, tuple)


def test_list_item_children_default_to_empty_tuple() -> None:
    item = ListItem()
    assert item.children == ()
    field_names = [f.name for f in dataclasses.fields(ListItem)]
    assert field_names[-1] == "children"


def test_recursive_nested_list_is_representable() -> None:
    nested = OrderedList(
        start=1,
        items=(ListItem(text="nested-a"), ListItem(text="nested-b")),
    )
    outer_item = ListItem(text="outer", children=(nested,))
    root = BulletList(items=(outer_item, ListItem(text="sibling")))
    assert len(root.items) == 2
    first = root.items[0]
    assert first.text == "outer"
    assert len(first.children) == 1
    inner = first.children[0]
    assert isinstance(inner, OrderedList)
    assert inner.start == 1
    assert [item.text for item in inner.items] == ["nested-a", "nested-b"]
    assert root.items[1].text == "sibling"
    assert root.items[1].children == ()


def test_block_quote_with_heading_and_paragraph_children() -> None:
    heading = Heading(level=2, text="quoted title")
    paragraph = Paragraph(text="quoted body")
    quote = BlockQuote(children=(heading, paragraph))
    assert quote.children == (heading, paragraph)
    assert isinstance(quote.children[0], Heading)
    assert quote.children[0].level == 2
    assert quote.children[0].text == "quoted title"
    assert isinstance(quote.children[1], Paragraph)
    assert quote.children[1].text == "quoted body"


def test_new_block_types_get_distinct_node_ids() -> None:
    nodes = [cls() for cls in NEW_BLOCK_CLASSES]
    ids = [node.node_id for node in nodes]
    assert all(isinstance(node_id, str) and node_id.startswith("n") for node_id in ids)
    assert len(set(ids)) == len(ids)


def test_node_id_excluded_from_equality_for_new_block_types() -> None:
    pairs = [
        (BlockQuote(children=(Paragraph(text="q"),)), BlockQuote(children=(Paragraph(text="q"),))),
        (CodeBlock(language="python", code="x = 1"), CodeBlock(language="python", code="x = 1")),
        (OrderedList(start=2, items=(ListItem(text="a"),)), OrderedList(start=2, items=(ListItem(text="a"),))),
        (BulletList(items=(ListItem(text="a"),)), BulletList(items=(ListItem(text="a"),))),
    ]
    for first, second in pairs:
        assert first.node_id != second.node_id
        assert first == second


def test_inline_plain_text_text_and_inline_code() -> None:
    assert inline_plain_text([Text(value="plain")]) == "plain"
    assert inline_plain_text([InlineCode(value="x = 1")]) == "x = 1"
    assert inline_plain_text((Text(value="a"), InlineCode(value="b"))) == "ab"


def test_inline_plain_text_strong_emphasis_recursion() -> None:
    node = Strong(children=(Text(value="a"), Emphasis(children=(Text(value="b"),))))
    assert inline_plain_text([node]) == "ab"
    nested = Emphasis(children=(Strong(children=(Text(value="x"),)), Text(value="y")))
    assert inline_plain_text([nested]) == "xy"


def test_inline_plain_text_link_uses_label_not_destination() -> None:
    node = Link(label="see here", destination="https://example.com")
    assert inline_plain_text([node]) == "see here"


def test_inline_plain_text_inline_math_uses_latex() -> None:
    assert inline_plain_text([InlineMath(latex="e^{i\\pi}+1=0")]) == "e^{i\\pi}+1=0"


def test_inline_plain_text_breaks_produce_newlines() -> None:
    assert inline_plain_text([SoftBreak()]) == "\n"
    assert inline_plain_text([HardBreak()]) == "\n"
    assert inline_plain_text([Text(value="a"), SoftBreak(), Text(value="b")]) == "a\nb"
    assert inline_plain_text([Text(value="a"), HardBreak(), Text(value="b")]) == "a\nb"


def test_inline_plain_text_citation_uses_raw() -> None:
    node = Citation(keys=["doe2020"], raw="[@doe2020]")
    assert inline_plain_text([node]) == "[@doe2020]"


def test_inline_plain_text_cross_reference_fallback_and_target() -> None:
    with_fallback = CrossReference(target="fig:a", fallback="图 3-2")
    assert inline_plain_text([with_fallback]) == "图 3-2"
    without_fallback = CrossReference(target="fig:a")
    assert inline_plain_text([without_fallback]) == "fig:a"


def test_inline_plain_text_footnote_reference_is_empty() -> None:
    assert inline_plain_text([FootnoteReference(label="note1")]) == ""


def test_inline_plain_text_unknown_inline_subclass_raises_type_error() -> None:
    class DummyInline(Inline):
        pass

    with pytest.raises(TypeError, match="DummyInline"):
        inline_plain_text([DummyInline()])


def test_inline_plain_text_does_not_mutate_input() -> None:
    inlines = [Text(value="a"), Strong(children=(Text(value="b"),))]
    snapshot = list(inlines)
    assert inline_plain_text(inlines) == "ab"
    assert inlines == snapshot
    assert inline_plain_text([]) == ""
