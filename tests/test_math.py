import pytest

from docforge.core.math import (
    LatexMathConverter,
    MathAccent,
    MathBinomial,
    MathDelimiter,
    MathEquationArray,
    MathFraction,
    MathFunction,
    MathLimitFunction,
    MathLiteral,
    MathMatrix,
    MathNary,
    MathScript,
    MathSequence,
    MathSyntaxError,
    MathTextRun,
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
    elif isinstance(node, MathNary | MathLimitFunction):
        if node.lower is not None:
            yield from _walk(node.lower)
        if node.upper is not None:
            yield from _walk(node.upper)
    elif isinstance(node, MathFunction):
        yield from _walk(node.argument)
    elif isinstance(node, MathAccent):
        yield from _walk(node.base)
    elif isinstance(node, MathDelimiter):
        yield from _walk(node.body)
    elif isinstance(node, MathMatrix | MathEquationArray):
        for row in node.rows:
            for cell in row:
                yield from _walk(cell)
    elif isinstance(node, MathBinomial):
        yield from _walk(node.top)
        yield from _walk(node.bottom)


def _convert(latex: str):
    return LatexMathConverter().convert(latex)


def test_latex_math_converter_supports_v1_editable_subset():
    expression = _convert(
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
    with pytest.raises(UnsupportedMathError, match=r"\\begin\{array\}"):
        _convert(r"\begin{array}{cc} 1 & 2 \end{array}")


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
        _convert(latex)


# ---------- ADR-0003 子集扩展：环境 ----------


@pytest.mark.parametrize(
    ("environment", "left", "right"),
    [
        ("matrix", None, None),
        ("pmatrix", "(", ")"),
        ("bmatrix", "[", "]"),
        ("vmatrix", "|", "|"),
    ],
)
def test_matrix_environments_parse_rows_and_delimiters(environment, left, right):
    expression = _convert(
        rf"A = \begin{{{environment}}} a & b \\ c & d \end{{{environment}}}"
    )

    matrices = [
        node for node in _walk(expression.root) if isinstance(node, MathMatrix)
    ]
    assert len(matrices) == 1
    matrix = matrices[0]
    assert matrix.left == left
    assert matrix.right == right
    assert matrix.column_alignment == "center"
    assert len(matrix.rows) == 2
    assert all(len(row) == 2 for row in matrix.rows)
    texts = [
        node.value
        for node in _walk(matrix)
        if isinstance(node, MathLiteral)
    ]
    assert texts == ["a", "b", "c", "d"]


def test_cases_environment_uses_left_brace_and_left_alignment():
    expression = _convert(
        r"f(x) = \begin{cases} x^2, & x \geq 0 \\ -x, & x < 0 \end{cases}"
    )

    matrix = next(
        node for node in _walk(expression.root) if isinstance(node, MathMatrix)
    )
    assert matrix.left == "{"
    assert matrix.right is None
    assert matrix.column_alignment == "left"
    assert [len(row) for row in matrix.rows] == [2, 2]


def test_aligned_environment_parses_alignment_cells():
    expression = _convert(r"\begin{aligned} y &= ax + b \\ &= c \end{aligned}")

    array = next(
        node for node in _walk(expression.root) if isinstance(node, MathEquationArray)
    )
    assert len(array.rows) == 2
    assert all(len(row) == 2 for row in array.rows)


def test_environment_name_must_match_at_end():
    with pytest.raises(MathSyntaxError, match="does not match"):
        _convert(r"\begin{pmatrix} a \end{cases}")


def test_environment_requires_end_marker():
    with pytest.raises(MathSyntaxError, match=r"Missing \\end"):
        _convert(r"\begin{pmatrix} a & b")


# ---------- ADR-0003 子集扩展：\left \right 自适应括号 ----------


def test_left_right_delimiters_with_scripts():
    expression = _convert(r"\left\| x \right\|_2")

    script = expression.root.items[0]
    assert isinstance(script, MathScript)
    assert isinstance(script.base, MathDelimiter)
    assert script.base.left == "‖"
    assert script.base.right == "‖"
    assert script.subscript is not None


def test_left_right_supports_invisible_delimiter():
    expression = _convert(r"\left. x \right)")

    delimiter = next(
        node for node in _walk(expression.root) if isinstance(node, MathDelimiter)
    )
    assert delimiter.left is None
    assert delimiter.right == ")"


def test_left_without_right_is_rejected():
    with pytest.raises(MathSyntaxError, match=r"Missing \\right"):
        _convert(r"\left( x")


def test_right_without_left_is_rejected():
    with pytest.raises(MathSyntaxError, match=r"\\right without matching \\left"):
        _convert(r"x \right)")


# ---------- ADR-0003 子集扩展：nary / 极限 ----------


def test_integral_parses_limits_as_nary():
    expression = _convert(r"\int_{a}^{b} f(x) dx = F(b) - F(a)")

    nary = next(node for node in _walk(expression.root) if isinstance(node, MathNary))
    assert nary.operator == "∫"
    assert nary.lower is not None
    assert nary.upper is not None


def test_product_parses_limits_as_nary():
    expression = _convert(r"\prod_{i=1}^{n} f(x_i; \theta)")

    nary = next(node for node in _walk(expression.root) if isinstance(node, MathNary))
    assert nary.operator == "∏"
    assert nary.lower is not None
    assert nary.upper is not None


def test_limit_operator_parses_lower_limit():
    expression = _convert(r"\lim_{n \to \infty} (1 + \frac{1}{n})^n = e")

    limit = next(
        node for node in _walk(expression.root) if isinstance(node, MathLimitFunction)
    )
    assert limit.name == "lim"
    assert limit.lower is not None
    assert limit.upper is None
    lower_values = {
        node.value for node in _walk(limit.lower) if isinstance(node, MathLiteral)
    }
    assert lower_values == {"n", "→", "∞"}


# ---------- ADR-0003 子集扩展：函数名上下标与参数保真 ----------


def test_function_name_carries_scripts():
    expression = _convert(r"\sin^2 \theta + \cos^2 \theta = 1")

    scripted_functions = [
        node
        for node in _walk(expression.root)
        if isinstance(node, MathScript) and isinstance(node.base, MathFunction)
    ]
    assert {node.base.name for node in scripted_functions} == {"sin", "cos"}
    assert all(node.superscript is not None for node in scripted_functions)


def test_function_subscript_before_argument():
    expression = _convert(r"T(n) = O(n \log_2 n)")

    scripted = next(
        node
        for node in _walk(expression.root)
        if isinstance(node, MathScript) and isinstance(node.base, MathFunction)
    )
    assert scripted.base.name == "log"
    assert scripted.subscript is not None


def test_function_argument_keeps_parenthesized_group_inside():
    expression = _convert(r"\log p(x_i)")

    function = next(
        node for node in _walk(expression.root) if isinstance(node, MathFunction)
    )
    texts = [
        node.value
        for node in _walk(function.argument)
        if isinstance(node, MathLiteral)
    ]
    assert texts == ["p", "(", "x", "i", ")"]


def test_function_argument_stops_at_binary_operator():
    expression = _convert(r"\ln \frac{N}{N_0} = -kt")

    function = next(
        node for node in _walk(expression.root) if isinstance(node, MathFunction)
    )
    assert function.name == "ln"
    assert isinstance(function.argument, MathFraction)


# ---------- ADR-0003 子集扩展：\text / \mathrm / \binom / accent ----------


def test_mathrm_and_text_parse_raw_content():
    expression = _convert(r"\frac{\mathrm{d} y}{\mathrm{d} x} = \mathrm{MSE}")

    runs = [
        node for node in _walk(expression.root) if isinstance(node, MathTextRun)
    ]
    assert [run.text for run in runs] == ["d", "d", "MSE"]
    assert all(run.style == "mathrm" for run in runs)


def test_text_command_preserves_cjk_and_spaces():
    expression = _convert(r"F = ma, \text{其中 } m \text{ 为质量}")

    runs = [
        node
        for node in _walk(expression.root)
        if isinstance(node, MathTextRun) and node.style == "text"
    ]
    assert [run.text for run in runs] == ["其中 ", " 为质量"]


def test_binom_parses_two_groups():
    expression = _convert(r"\binom{n}{k} = \frac{n!}{k!(n-k)!}")

    binomial = next(
        node for node in _walk(expression.root) if isinstance(node, MathBinomial)
    )
    top_values = [
        node.value for node in _walk(binomial.top) if isinstance(node, MathLiteral)
    ]
    bottom_values = [
        node.value for node in _walk(binomial.bottom) if isinstance(node, MathLiteral)
    ]
    assert top_values == ["n"]
    assert bottom_values == ["k"]


def test_extended_accent_commands():
    expression = _convert(r"\vec F = m \ddot a + c \dot x + \tilde y")

    kinds = [
        node.kind for node in _walk(expression.root) if isinstance(node, MathAccent)
    ]
    assert kinds == ["vec", "ddot", "dot", "tilde"]


# ---------- ADR-0003 子集扩展：希腊字母与单发命令 ----------


def test_eta_and_extended_greek_letters():
    expression = _convert(r"\eta \nu \tau \chi \psi \varepsilon \varphi")

    values = [
        node.value for node in _walk(expression.root) if isinstance(node, MathLiteral)
    ]
    assert values == ["η", "ν", "τ", "χ", "ψ", "ε", "φ"]


@pytest.mark.parametrize(
    ("command", "symbol"),
    [
        ("approx", "≈"),
        ("sim", "∼"),
        ("subset", "⊂"),
        ("in", "∈"),
        ("Rightarrow", "⇒"),
        ("propto", "∝"),
        ("nabla", "∇"),
        ("partial", "∂"),
        ("forall", "∀"),
        ("exists", "∃"),
    ],
)
def test_single_shot_operator_commands(command, symbol):
    expression = _convert(rf"x \{command} y")

    values = {
        node.value for node in _walk(expression.root) if isinstance(node, MathLiteral)
    }
    assert symbol in values


def test_det_is_a_function_name():
    expression = _convert(r"\det A = ad - bc")

    function = next(
        node for node in _walk(expression.root) if isinstance(node, MathFunction)
    )
    assert function.name == "det"


# ---------- ADR-0003 保真度修复：裸 \\ 显式报错 ----------


def test_bare_line_break_is_rejected_explicitly():
    with pytest.raises(MathSyntaxError, match=r"Bare \\\\ line break"):
        _convert(r"y = a + b \\ z = c + d")
