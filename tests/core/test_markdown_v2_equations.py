from __future__ import annotations

import pytest

from thesis_forge.core.model import Equation, Heading
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend
from thesis_forge.core.parser_support import ParseError

BACKEND = MarkdownItParserBackend()


def _parse(source: str):
    return BACKEND.parse_text(source, source_path="equations.md")


def test_display_math_with_equation_id_becomes_typed_equation() -> None:
    document = _parse(
        "$$\n"
        "L=-\\sum_{i=1}^{N} y_i \\log \\hat y_i\n"
        "$$\n"
        "{#eq:loss}\n"
        "# 结论 {#chap:conclusion}\n"
    )

    equation, heading = document.blocks
    assert isinstance(equation, Equation)
    assert equation.id == "eq:loss"
    assert equation.latex == r"L=-\sum_{i=1}^{N} y_i \log \hat y_i"
    assert equation.display is True
    assert equation.location.line == 1
    assert isinstance(heading, Heading)


def test_unnumbered_display_math_has_no_id() -> None:
    document = _parse("$$\nx^2 + y^2\n$$\n")

    equation = document.blocks[0]
    assert isinstance(equation, Equation)
    assert equation.id is None
    assert equation.latex == "x^2 + y^2"
    assert equation.display is True


def test_single_line_display_math_is_supported() -> None:
    document = _parse("$$E=mc^2$$\n{#eq:energy}\n")

    equation = document.blocks[0]
    assert isinstance(equation, Equation)
    assert equation.id == "eq:energy"
    assert equation.latex == "E=mc^2"


@pytest.mark.parametrize(
    "source",
    [
        "$$\nx\n$$\n\n{#eq:detached}\n",
        "{#eq:before}\n$$\nx\n$$\n",
    ],
    ids=["id-after-blank-line", "id-before-equation"],
)
def test_detached_equation_id_is_rejected(source: str) -> None:
    with pytest.raises(ParseError, match="公式 ID"):
        _parse(source)


def test_duplicate_equation_id_is_rejected() -> None:
    with pytest.raises(ParseError, match="重复.*equation ID"):
        _parse(
            "$$\nx\n$$\n{#eq:same}\n\n"
            "$$\ny\n$$\n{#eq:same}\n"
        )


@pytest.mark.parametrize(
    "source",
    [
        "$$\nx\n",
        "$$\n\n$$\n",
        "$$\nx\n$$\n{#tbl:wrong}\n",
    ],
    ids=["missing-closing", "empty-body", "wrong-id-prefix"],
)
def test_malformed_display_math_is_rejected(source: str) -> None:
    with pytest.raises(ParseError, match="display math"):
        _parse(source)
