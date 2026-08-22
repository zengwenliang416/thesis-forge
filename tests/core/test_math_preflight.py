from __future__ import annotations

from pathlib import Path

from thesis_forge.core.math import preflight_latex
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend
from thesis_forge.core.validator import ValidationContext, validate_document

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "templates" / "base" / "bachelor.yaml"


def _math_issues(source: str):
    document = MarkdownItParserBackend().parse_text(
        source,
        source_path=Path("math.md"),
    )
    context = ValidationContext.from_document(
        document,
        template_path=TEMPLATE,
        required_metadata=(),
    )
    return [
        issue
        for issue in validate_document(document, context)
        if issue.code in {"invalid-math", "unsupported-math"}
    ]


def test_supported_inline_and_display_math_pass_preflight() -> None:
    preflight_latex(r"x_i^2 + \frac{a}{b}")
    assert _math_issues(
        "Inline $x_i^2 + \\frac{a}{b}$.\n\n$$\n\\sum_{i=1}^n x_i\n$$\n"
    ) == []


def test_unsupported_inline_math_returns_source_linked_diagnostic() -> None:
    issues = _math_issues(r"Unsupported $\begin{array}{cc} 1 & 2 \end{array}$.\n")

    assert len(issues) == 1
    issue = issues[0]
    assert issue.code == "unsupported-math"
    assert issue.line == 1
    assert issue.target.startswith("inline:")
    assert issue.details["command"] == r"\begin{array}"
    assert issue.details["source_line"] == 1
    assert issue.details["formula"] == r"\begin{array}{cc} 1 & 2 \end{array}"


def test_malformed_display_math_returns_structured_diagnostic() -> None:
    issues = _math_issues("$$\n\\frac{a}{b\n$$\n")

    assert len(issues) == 1
    issue = issues[0]
    assert issue.code == "invalid-math"
    assert issue.line == 1
    assert issue.target.startswith("equation:")
    assert issue.details["error_type"] == "MathSyntaxError"
    assert issue.details["source_line"] == 1
