from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest
from lxml import etree

from thesis_forge.application.contracts import PreviewResult
from thesis_forge.core.compiler import compile_document
from thesis_forge.core.parser_backend import create_parser_backend
from thesis_forge.core.render_plan import EquationInstruction
from thesis_forge.core.validator import ValidationContext, validate_document
from thesis_forge.presentation.review import ReviewEquationContent, map_review_result
from thesis_forge.renderers.docx.package import validate_docx_package
from thesis_forge.renderers.docx.renderer import DocxRenderer
from thesis_forge.templates import load_template

ROOT = Path(__file__).resolve().parents[3]
TEMPLATE = ROOT / "templates" / "base" / "bachelor.yaml"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NS = {"w": W_NS, "m": M_NS}

CORPUS_SOURCE = r"""# 数学模型 {#chap:math}

$$
E = mc^2
$$
{#eq:energy}

$$
\frac{a}{b} + \sum_{i=1}^{n} x_i
$$
{#eq:sum}

$$
\begin{pmatrix} a & b \\ c & d \end{pmatrix}
$$
{#eq:matrix}
"""


def _compile_corpus(tmp_path: Path):
    source_path = tmp_path / "thesis.md"
    document = create_parser_backend().parse_text(
        CORPUS_SOURCE,
        source_path=source_path,
    )
    template = load_template(TEMPLATE)
    plan = compile_document(document, template=template)
    return document, plan


def _document_xml(path: Path):
    with ZipFile(path) as package:
        return etree.fromstring(package.read("word/document.xml"))


def test_math_corpus_reaches_typed_review_and_editable_docx(
    tmp_path: Path,
) -> None:
    document, plan = _compile_corpus(tmp_path)

    equations = [
        node for node in plan.nodes if isinstance(node, EquationInstruction)
    ]
    assert [node.source_id for node in equations] == [
        "eq:energy",
        "eq:sum",
        "eq:matrix",
    ]
    assert [node.number for node in equations] == ["1-1", "1-2", "1-3"]
    assert [node.bookmark for node in equations] == [
        "tf_eq_energy",
        "tf_eq_sum",
        "tf_eq_matrix",
    ]

    issues = validate_document(
        document,
        ValidationContext.from_document(
            document,
            template_path=TEMPLATE,
            required_metadata=(),
        ),
    )
    assert issues == []

    review = map_review_result(
        PreviewResult(
            document=document,
            context=ValidationContext(),
            issues=(),
            plan=plan,
        )
    )
    review_equations = [
        block.content
        for block in review.blocks
        if block.kind == "equation"
    ]
    assert all(isinstance(content, ReviewEquationContent) for content in review_equations)
    assert [content.label for content in review_equations] == ["(1-1)", "(1-2)", "(1-3)"]
    assert [content.latex for content in review_equations] == [
        "E = mc^2",
        r"\frac{a}{b} + \sum_{i=1}^{n} x_i",
        r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
    ]

    output = tmp_path / "math-corpus.docx"
    DocxRenderer().render(plan, output)
    validate_docx_package(output)

    document_xml = _document_xml(output)
    assert len(document_xml.xpath(".//m:oMath", namespaces=NS)) == 3

    field_codes = document_xml.xpath(".//w:instrText/text()", namespaces=NS)
    assert field_codes == [
        "SEQ TF_Equation_1 \\r 1 \\* ARABIC",
        "SEQ TF_Equation_1 \\r 2 \\* ARABIC",
        "SEQ TF_Equation_1 \\r 3 \\* ARABIC",
    ]

    bookmark_starts = {
        node.get(f"{{{W_NS}}}name"): node.get(f"{{{W_NS}}}id")
        for node in document_xml.xpath(".//w:bookmarkStart", namespaces=NS)
    }
    bookmark_ends = set(
        document_xml.xpath(".//w:bookmarkEnd/@w:id", namespaces=NS)
    )
    assert set(bookmark_starts) >= {
        "tf_eq_energy",
        "tf_eq_sum",
        "tf_eq_matrix",
    }
    assert set(bookmark_starts.values()) <= bookmark_ends


@pytest.mark.parametrize(
    ("source", "expected_code"),
    [
        (
            r"Unsupported $\begin{array}{cc} 1 & 2 \end{array}$.",
            "unsupported-math",
        ),
        ("$$\n\\frac{a}{b\n$$\n", "invalid-math"),
    ],
)
def test_math_corpus_validation_rejects_unsupported_or_malformed_formula(
    tmp_path: Path,
    source: str,
    expected_code: str,
) -> None:
    document = create_parser_backend().parse_text(
        source,
        source_path=tmp_path / "invalid-math.md",
    )
    issues = validate_document(
        document,
        ValidationContext.from_document(
            document,
            template_path=TEMPLATE,
            required_metadata=(),
        ),
    )

    math_issues = [
        issue
        for issue in issues
        if issue.code in {"unsupported-math", "invalid-math"}
    ]
    assert len(math_issues) == 1
    assert math_issues[0].code == expected_code
    assert math_issues[0].line == 1
    assert math_issues[0].target.startswith(("inline:", "equation:"))
