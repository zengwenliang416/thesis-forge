from __future__ import annotations

import pytest

from docforge.core.model import Figure, Strong, inline_plain_text
from docforge.core.parser_markdown_it import MarkdownItParserBackend
from docforge.core.parser_support import ParseError

BACKEND = MarkdownItParserBackend()


def _parse(source: str):
    return BACKEND.parse_text(source, source_path="figures.md")


def test_standard_image_becomes_figure_with_typed_caption() -> None:
    document = _parse("![模型 **结构**](assets/model.png){#fig:model}\n")

    assert len(document.blocks) == 1
    figure = document.blocks[0]
    assert isinstance(figure, Figure)
    assert figure.id == "fig:model"
    assert figure.src == "assets/model.png"
    assert figure.location.line == 1
    assert figure.width is None
    assert inline_plain_text(figure.caption_inlines) == "模型 结构"
    assert any(isinstance(inline, Strong) for inline in figure.caption_inlines)
    strong = next(
        inline for inline in figure.caption_inlines if isinstance(inline, Strong)
    )
    assert strong.location.line == 1
    assert strong.location.column == 6


@pytest.mark.parametrize(
    "source",
    [
        "![caption](assets/model.png)\n",
        "![caption](assets/model.png){#tbl:model}\n",
        "![caption](assets/model.png){#fig:}\n",
    ],
    ids=["missing-id", "wrong-prefix", "empty-id"],
)
def test_standard_image_requires_a_valid_figure_id(source: str) -> None:
    with pytest.raises(ParseError, match="fig ID"):
        _parse(source)


def test_standard_image_does_not_parse_markdown_width() -> None:
    document = _parse("![模型](assets/model.png){#fig:model}\n")

    figure = document.blocks[0]
    assert isinstance(figure, Figure)
    assert figure.width is None
