"""Focused tests for node identity (NodeId) and complete SourceSpan on the typed model."""

from __future__ import annotations

from thesis_forge.core.model import (
    Algorithm,
    BibliographyBlock,
    Block,
    Citation,
    CrossReference,
    Equation,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    GeneratedOrigin,
    Heading,
    Inline,
    ListBlock,
    Listing,
    ListItem,
    Paragraph,
    SourceLocation,
    Strong,
    Table,
    Text,
)

INLINE_CLASSES = [Text, Strong, CrossReference, Citation, FootnoteReference]
BLOCK_CLASSES = [
    Heading,
    Paragraph,
    ListBlock,
    Figure,
    Table,
    Equation,
    Listing,
    Algorithm,
    FootnoteDefinition,
    BibliographyBlock,
]


def _all_semantic_nodes() -> list[Inline | Block | ListItem]:
    return [cls() for cls in INLINE_CLASSES] + [cls() for cls in BLOCK_CLASSES] + [ListItem()]


def test_every_semantic_node_gets_non_empty_unique_node_id() -> None:
    nodes = _all_semantic_nodes()
    ids = [node.node_id for node in nodes]
    assert all(isinstance(node_id, str) and node_id for node_id in ids)
    assert len(set(ids)) == len(ids)


def test_same_content_nodes_have_different_node_ids_but_compare_equal() -> None:
    for cls in INLINE_CLASSES + BLOCK_CLASSES + [ListItem]:
        first = cls()
        second = cls()
        assert first.node_id != second.node_id
        assert first == second


def test_node_id_is_stable_across_repeated_reads() -> None:
    node = Paragraph(text="hello")
    first_read = node.node_id
    assert node.node_id == first_read
    assert node.node_id == first_read


def test_source_location_defaults_are_all_none() -> None:
    location = SourceLocation()
    assert location.line is None
    assert location.column is None
    assert location.end_line is None
    assert location.end_column is None
    assert location.source_file is None


def test_source_location_positional_line_column_unchanged() -> None:
    location = SourceLocation(3, 5)
    assert location.line == 3
    assert location.column == 5
    assert location.end_line is None
    assert location.end_column is None
    assert location.source_file is None


def test_source_location_multi_line_span_round_trips() -> None:
    location = SourceLocation(line=3, column=5, end_line=7, end_column=12, source_file="thesis.md")
    assert location.line == 3
    assert location.column == 5
    assert location.end_line == 7
    assert location.end_column == 12
    assert location.source_file == "thesis.md"


def test_generated_origin_empty_defaults() -> None:
    origin = GeneratedOrigin()
    assert origin.generator == ""
    assert origin.source_node_ids == ()


def test_parsed_nodes_default_origin_is_none() -> None:
    for node in _all_semantic_nodes():
        assert node.origin is None


def test_generated_node_refers_back_to_source_node() -> None:
    source = Heading(level=1, text="Chapter")
    generated = Paragraph(
        text="Chapter .... 1",
        origin=GeneratedOrigin(generator="toc", source_node_ids=(source.node_id,)),
    )
    assert generated.origin is not None
    assert generated.origin.generator == "toc"
    assert generated.origin.source_node_ids == (source.node_id,)


def test_generated_node_with_empty_source_location_is_representable() -> None:
    generated = Paragraph(
        text="generated",
        location=SourceLocation(),
        origin=GeneratedOrigin(generator="toc"),
    )
    assert generated.location == SourceLocation()
    assert generated.location.line is None
    assert generated.origin is not None


def test_multi_line_paragraph_with_span_and_default_origin() -> None:
    span = SourceLocation(line=3, column=1, end_line=5, end_column=20, source_file="thesis.md")
    paragraph = Paragraph(text="multi\nline\nparagraph", location=span)
    assert paragraph.location.end_line == 5
    assert paragraph.location.source_file == "thesis.md"
    assert paragraph.origin is None
    assert paragraph.node_id
