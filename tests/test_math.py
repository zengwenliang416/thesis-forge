import pytest

from thesis_forge.core.math import (
    LatexMathConverter,
    MathAccent,
    MathFraction,
    MathFunction,
    MathNary,
    MathScript,
    MathSequence,
    MathSyntaxError,
    UnsupportedMathError,
)


def _walk(node):
    yield node
    if isinstance(node, MathSequence):
        for item in node.items:
            yield from _walk(item)
    elif isinstance(node, MathFraction):
        yield from _walk(node.numerator)
        yield from _walk(node.denominator)
    elif isinstance(node, MathScript):
        yield from _walk(node.base)
        if node.subscript is not None:
            yield from _walk(node.subscript)
        if node.superscript is not None:
            yield from _walk(node.superscript)
    elif isinstance(node, MathNary):
        if node.lower is not None:
            yield from _walk(node.lower)
        if node.upper is not None:
            yield from _walk(node.upper)
    elif isinstance(node, MathFunction):
        yield from _walk(node.argument)
    elif isinstance(node, MathAccent):
        yield from _walk(node.base)


def test_latex_math_converter_supports_v1_editable_subset():
    expression = LatexMathConverter().convert(
        r"x_i^2 + \frac{a}{b} + \sum_{i=1}^n x_i + \alpha + \log \hat{y}_i"
    )

    nodes = tuple(_walk(expression.root))
    assert any(isinstance(node, MathFraction) for node in nodes)
    assert any(isinstance(node, MathNary) and node.operator == "∑" for node in nodes)
    assert any(isinstance(node, MathFunction) and node.name == "log" for node in nodes)
    assert any(isinstance(node, MathAccent) and node.kind == "hat" for node in nodes)
    assert any(
        isinstance(node, MathScript)
        and node.subscript is not None
        and node.superscript is not None
        for node in nodes
    )


def test_latex_math_converter_rejects_unsupported_commands_explicitly():
    with pytest.raises(UnsupportedMathError, match=r"\\begin"):
        LatexMathConverter().convert(r"\begin{matrix}1&2\end{matrix}")


@pytest.mark.parametrize(
    ("latex", "message"),
    [
        ("", "empty"),
        (r"\frac{a}", "requires a braced argument"),
        ("x_i_j", "Duplicate subscript"),
        ("x^{2", "Missing closing"),
        (r"\log", "Expected math atom"),
    ],
)
def test_latex_math_converter_rejects_malformed_supported_syntax(
    latex: str,
    message: str,
):
    with pytest.raises(MathSyntaxError, match=message):
        LatexMathConverter().convert(latex)
