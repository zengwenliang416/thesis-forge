from __future__ import annotations

import pytest

from docforge.core.model import (
    Algorithm,
    Citation,
    CodeBlock,
    Listing,
    Strong,
    inline_plain_text,
)
from docforge.core.parser_markdown_it import MarkdownItParserBackend
from docforge.core.parser_support import ParseError

BACKEND = MarkdownItParserBackend()


def _parse(source: str):
    return BACKEND.parse_text(source, source_path="fences.md")


def test_listing_fence_becomes_typed_listing_with_literal_code() -> None:
    document = _parse(
        '```python {#lst:training title="训练 **代码**"}\n'
        "**literal** [@not-a-citation]\n"
        "```\n"
    )

    listing = document.blocks[0]
    assert isinstance(listing, Listing)
    assert listing.id == "lst:training"
    assert listing.language == "python"
    assert listing.code == "**literal** [@not-a-citation]"
    assert inline_plain_text(listing.caption_inlines) == "训练 代码"
    assert isinstance(listing.caption_inlines[1], Strong)
    assert listing.location.line == 1


def test_algorithm_fence_preserves_typed_body_lines_and_title() -> None:
    document = _parse(
        '```algorithm {#alg:training title="训练流程"}\n'
        "输入：训练集 D\n"
        "2. 迭代优化 [@algorithm-source]\n"
        "```\n"
    )

    algorithm = document.blocks[0]
    assert isinstance(algorithm, Algorithm)
    assert algorithm.id == "alg:training"
    assert algorithm.body == "输入：训练集 D\n2. 迭代优化 [@algorithm-source]"
    assert inline_plain_text(algorithm.caption_inlines) == "训练流程"
    assert len(algorithm.body_lines) == 2
    assert inline_plain_text(algorithm.body_lines[1]) == "2. 迭代优化 [@algorithm-source]"
    assert isinstance(algorithm.body_lines[1][-1], Citation)
    assert algorithm.body_lines[0][0].location.line == 2
    assert algorithm.body_lines[1][0].location.line == 3


def test_plain_fence_remains_literal_code_block() -> None:
    document = _parse("```python\n**literal** [@not-a-citation]\n```\n")

    code = document.blocks[0]
    assert isinstance(code, CodeBlock)
    assert code.language == "python"
    assert code.code == "**literal** [@not-a-citation]\n"


@pytest.mark.parametrize(
    "source",
    [
        '```python title="缺少 ID"\nx\n```\n',
        "```python {#lst:missing-title}\nx\n```\n",
        '```python {#alg:wrong-prefix title="标题"}\nx\n```\n',
        '```algorithm {#lst:wrong-prefix title="标题"}\nx\n```\n',
        "```algorithm\nx\n```\n",
        '```python {#lst:id title="标题" extra="属性"}\nx\n```\n',
    ],
    ids=[
        "missing-id",
        "missing-title",
        "listing-wrong-id-prefix",
        "algorithm-wrong-id-prefix",
        "algorithm-missing-attributes",
        "unknown-attribute",
    ],
)
def test_listing_and_algorithm_fences_require_valid_id_and_title(source: str) -> None:
    with pytest.raises(ParseError, match="围栏"):
        _parse(source)
