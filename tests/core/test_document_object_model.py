"""Focused tests for rich document-object model primitives."""

from __future__ import annotations

import dataclasses

from docforge.core.index import DocumentIndex
from docforge.core.model import (
    Algorithm,
    Citation,
    Equation,
    Figure,
    FootnoteDefinition,
    GeneratedOrigin,
    Listing,
    SourceLocation,
    Text,
    inline_plain_text,
)
from docforge.core.parser_backend import create_parser_backend

BACKEND = create_parser_backend()


def test_rich_object_defaults_preserve_source_identity() -> None:
    nodes = [Figure(), Equation(), Listing(), Algorithm()]
    ids = [node.node_id for node in nodes]

    assert len(set(ids)) == len(ids)
    assert all(node.origin is None for node in nodes)
    assert all(node.location == SourceLocation() for node in nodes)
    assert Figure().caption_inlines == ()
    assert Listing().caption_inlines == ()
    assert Algorithm().caption_inlines == ()
    assert Equation().display is True


def test_typed_caption_inlines_preserve_semantic_children() -> None:
    caption = (
        Text(value="系统"),
        Citation(keys=["caption-source"], raw="[@caption-source]"),
    )
    figure = Figure(
        id="fig:model",
        caption_inlines=caption,
        origin=GeneratedOrigin(generator="object-normalize"),
    )
    listing = Listing(caption_inlines=caption)
    algorithm = Algorithm(caption_inlines=caption)

    assert figure.caption_inlines == caption
    assert listing.caption_inlines == caption
    assert algorithm.caption_inlines == caption
    assert figure.origin == GeneratedOrigin(generator="object-normalize")


def test_equation_display_state_is_explicit_and_typed() -> None:
    displayed = Equation(latex="x^2", display=True)
    inline_reserved = Equation(latex="x^2", display=False)

    assert displayed.display is True
    assert inline_reserved.display is False


def test_rich_object_fields_are_structurally_pinned() -> None:
    figure_fields = {field.name for field in dataclasses.fields(Figure)}
    listing_fields = {field.name for field in dataclasses.fields(Listing)}
    algorithm_fields = {field.name for field in dataclasses.fields(Algorithm)}
    footnote_fields = {
        field.name for field in dataclasses.fields(FootnoteDefinition)
    }

    assert "caption" not in figure_fields
    assert "caption" not in listing_fields
    assert "caption" not in algorithm_fields
    assert "text" not in footnote_fields
    assert "caption_inlines" in {
        field.name for field in dataclasses.fields(Figure)
    }
    assert "caption_inlines" in {
        field.name for field in dataclasses.fields(Listing)
    }
    assert "caption_inlines" in {
        field.name for field in dataclasses.fields(Algorithm)
    }
    assert "display" in {field.name for field in dataclasses.fields(Equation)}


def test_parser_populates_typed_object_captions_and_equation_display() -> None:
    source = """![系统模型 [@figure-source]](model.png){#fig:model}

```python {#lst:demo title="示例代码 [@listing-source]"}
print(1)
```

```algorithm {#alg:demo title="构建流程 [@algorithm-source]"}
1. 校验
```

$$E = mc^2$$
{#eq:loss}
"""
    document = BACKEND.parse_text(source, source_path="objects.md")

    figure, listing, algorithm, equation = document.blocks
    assert isinstance(figure, Figure)
    assert isinstance(listing, Listing)
    assert isinstance(algorithm, Algorithm)
    assert isinstance(equation, Equation)
    assert inline_plain_text(figure.caption_inlines) == "系统模型 [@figure-source]"
    assert inline_plain_text(listing.caption_inlines) == "示例代码 [@listing-source]"
    assert inline_plain_text(algorithm.caption_inlines) == "构建流程 [@algorithm-source]"
    assert equation.display is True
    assert [
        citation.keys
        for citation in DocumentIndex.from_document(document).citations
    ] == [
        ["figure-source"],
        ["listing-source"],
        ["algorithm-source"],
    ]
