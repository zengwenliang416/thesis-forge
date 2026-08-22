"""Focused tests for the recursive inline type set (SoftBreak/HardBreak/Strong/Emphasis/Link/InlineMath/InlineCode)."""

from __future__ import annotations

import dataclasses

from thesis_forge.core.model import (
    CrossReference,
    Emphasis,
    HardBreak,
    Inline,
    InlineCode,
    InlineMath,
    Link,
    SoftBreak,
    Strong,
    Text,
)

NEW_INLINE_CLASSES = [SoftBreak, HardBreak, Emphasis, Link, InlineMath, InlineCode]


def test_new_inline_types_construct_with_defaults() -> None:
    for cls in NEW_INLINE_CLASSES:
        node = cls()
        assert isinstance(node, Inline)
        assert node.node_id
        assert node.origin is None
    node_ids = [cls().node_id for cls in NEW_INLINE_CLASSES]
    assert len(set(node_ids)) == len(node_ids)


def test_soft_break_and_hard_break_are_marker_nodes() -> None:
    for cls in (SoftBreak, HardBreak):
        field_names = {f.name for f in dataclasses.fields(cls)}
        assert field_names == {"location", "node_id", "origin"}


def test_emphasis_children_are_inline_tuple() -> None:
    children = (Text(value="x"), InlineCode(value="y"))
    node = Emphasis(children=children)
    assert isinstance(node.children, tuple)
    assert node.children == children
    assert all(isinstance(child, Inline) for child in node.children)


def test_emphasis_has_no_plain_text_field() -> None:
    field_names = {f.name for f in dataclasses.fields(Emphasis)}
    assert "value" not in field_names
    assert "text" not in field_names
    assert field_names == {"location", "node_id", "origin", "children"}


def test_emphasis_defaults_to_empty_children() -> None:
    assert Emphasis().children == ()


def test_strong_children_are_inline_tuple() -> None:
    children = (Text(value="x"),)
    node = Strong(children=children)
    assert isinstance(node.children, tuple)
    assert node.children == children
    assert all(isinstance(child, Inline) for child in node.children)


def test_strong_defaults_to_empty_children() -> None:
    assert Strong().children == ()


def test_strong_has_no_plain_text_field() -> None:
    field_names = {f.name for f in dataclasses.fields(Strong)}
    assert "value" not in field_names
    assert "text" not in field_names
    assert field_names == {"location", "node_id", "origin", "children"}


def test_nested_strong_emphasis_is_representable() -> None:
    node = Strong(children=(Emphasis(children=(Text(value="deep"),)),))
    inner = node.children[0]
    assert isinstance(inner, Emphasis)
    leaf = inner.children[0]
    assert isinstance(leaf, Text)
    assert leaf.value == "deep"


def test_strong_inherits_inline_node_identity() -> None:
    node = Strong(children=(Text(value="x"),))
    assert node.node_id
    assert node.origin is None
    other = Strong(children=(Text(value="x"),))
    assert other.node_id != node.node_id
    # node_id is excluded from equality (compare=False), so two Strong nodes
    # with equal children compare equal despite distinct node_ids.
    assert node == other


def test_link_round_trip_and_defaults() -> None:
    node = Link(label="see", destination="https://example.com")
    assert node.label == "see"
    assert node.destination == "https://example.com"
    default = Link()
    assert default.label == ""
    assert default.destination == ""


def test_inline_math_round_trip() -> None:
    node = InlineMath(latex="e^{i\\pi}+1=0")
    assert node.latex == "e^{i\\pi}+1=0"
    assert InlineMath().latex == ""


def test_inline_code_round_trip() -> None:
    node = InlineCode(value="x = 1")
    assert node.value == "x = 1"
    assert InlineCode().value == ""


def test_cross_reference_defaults_keep_fallback_fields_none() -> None:
    node = CrossReference(target="fig:a")
    assert node.target == "fig:a"
    assert node.fallback is None
    assert node.display_mode is None


def test_cross_reference_positional_construction_unchanged() -> None:
    field_names = [f.name for f in dataclasses.fields(CrossReference)]
    assert field_names[:4] == ["location", "node_id", "origin", "target"]
    assert field_names[4:] == ["fallback", "display_mode"]
    # First positional arg binds to the inherited `location`, exactly as before
    # the fallback/display_mode fields were appended after `target`.
    node = CrossReference("fig:a")
    assert node.location == "fig:a"
    assert node.target == ""
    assert node.fallback is None
    assert node.display_mode is None


def test_cross_reference_fallback_round_trip() -> None:
    node = CrossReference(target="fig:a", fallback="图", display_mode="label")
    assert node.target == "fig:a"
    assert node.fallback == "图"
    assert node.display_mode == "label"


def test_nested_emphasis_is_representable() -> None:
    node = Emphasis(children=(Emphasis(children=(Text(value="deep"),)),))
    inner = node.children[0]
    assert isinstance(inner, Emphasis)
    leaf = inner.children[0]
    assert isinstance(leaf, Text)
    assert leaf.value == "deep"
