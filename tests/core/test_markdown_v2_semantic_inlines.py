from __future__ import annotations

from pathlib import Path

from docforge.core.model import (
    Citation,
    CrossReference,
    FootnoteDefinition,
    FootnoteReference,
    Link,
    Paragraph,
)
from docforge.core.parser_markdown_it import MarkdownItParserBackend


def _document(source: str):
    return MarkdownItParserBackend().parse_text(
        source,
        source_path=Path("semantic.md"),
    )


def test_citation_cluster_is_typed_and_source_mapped() -> None:
    document = _document("相关研究[@smith2025; @lee2024, p. 7]。\n")

    paragraph = document.blocks[0]
    assert isinstance(paragraph, Paragraph)
    citation = paragraph.inlines[1]
    assert isinstance(citation, Citation)
    assert citation.keys == ["smith2025", "lee2024"]
    assert citation.locator == "p. 7"
    assert citation.raw == "[@smith2025; @lee2024, p. 7]"
    assert citation.location.line == 1
    assert citation.location.column == 5


def test_semantic_internal_link_becomes_cross_reference_with_fallback() -> None:
    document = _document("[系统架构](#fig:architecture)\n")

    paragraph = document.blocks[0]
    assert isinstance(paragraph, Paragraph)
    reference = paragraph.inlines[0]
    assert isinstance(reference, CrossReference)
    assert reference.target == "fig:architecture"
    assert reference.fallback == "系统架构"
    assert reference.location.line == 1
    assert reference.location.column == 1


def test_normal_links_remain_typed_links() -> None:
    document = _document("[项目主页](https://example.com/project)\n")

    paragraph = document.blocks[0]
    assert isinstance(paragraph, Paragraph)
    link = paragraph.inlines[0]
    assert isinstance(link, Link)
    assert link.label == "项目主页"
    assert link.destination == "https://example.com/project"


def test_footnote_reference_and_definition_are_typed() -> None:
    document = _document(
        "这是说明[^scope]。\n\n"
        "[^scope]: 该说明保留为脚注定义。\n"
    )

    paragraph, definition = document.blocks
    assert isinstance(paragraph, Paragraph)
    assert isinstance(paragraph.inlines[1], FootnoteReference)
    assert paragraph.inlines[1].label == "scope"
    assert isinstance(definition, FootnoteDefinition)
    assert definition.label == "scope"
    assert definition.inlines[0].value == "该说明保留为脚注定义。"
