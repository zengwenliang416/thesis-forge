from __future__ import annotations

import inspect

from thesis_forge.core.model import Heading
from thesis_forge.core.parser_backend import (
    ParserBackend,
    create_parser_backend,
)
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend


def test_create_parser_backend_returns_the_canonical_v2_type() -> None:
    backend = create_parser_backend()

    assert type(backend) is MarkdownItParserBackend
    assert isinstance(backend, ParserBackend)
    assert backend.name == "markdown-it"


def test_create_parser_backend_has_no_backend_selector() -> None:
    assert tuple(inspect.signature(create_parser_backend).parameters) == ()


def test_canonical_backend_parses_v2_source() -> None:
    document = create_parser_backend().parse_text(
        "# 绪论 {#chap:intro}\n",
        source_path="thesis.md",
    )

    assert len(document.blocks) == 1
    assert isinstance(document.blocks[0], Heading)
    assert document.blocks[0].id == "chap:intro"
