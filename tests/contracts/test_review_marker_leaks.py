from __future__ import annotations

import re
from dataclasses import fields, is_dataclass
from pathlib import Path

import pytest

from thesis_forge.application.contracts import PreviewResult
from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import (
    Citation,
    CrossReference,
    Figure,
    Listing,
    Paragraph,
    SourceLocation,
    ThesisDocument,
)
from thesis_forge.core.parser_backend import create_parser_backend
from thesis_forge.core.parser_support import ParseError
from thesis_forge.core.render_plan import (
    CitationRun,
    FigureInstruction,
    ListingInstruction,
    ParagraphInstruction,
    ReferenceRun,
    RenderPlan,
)
from thesis_forge.core.validator import ValidationContext
from thesis_forge.presentation.review import (
    ReviewAlgorithmContent,
    ReviewListingContent,
    ReviewParagraphContent,
    ReviewTextRun,
    map_review_result,
    project_instruction,
)

ROOT = Path(__file__).resolve().parents[2]
V2_PROJECT = ROOT / "tests" / "fixtures" / "v2-project"
CANONICAL_SOURCE = V2_PROJECT / "thesis.md"
TEMPLATE_ROOT = ROOT / "templates"

_MARKER_LABELS = frozenset(
    {
        "front_matter",
        "legacy_container",
        "stable_id",
        "raw_citation",
        "legacy_reference",
        "absolute_path",
    }
)
_MARKER_PATTERNS = {
    "front_matter": re.compile(r"(?m)^\s*---\s*$"),
    "legacy_container": re.compile(r"(?m)^\s*:::"),
    "stable_id": re.compile(r"\{#[A-Za-z0-9_.:-]+\}"),
    "raw_citation": re.compile(r"\[@[^\]]+\]"),
    "legacy_reference": re.compile(
        r"(?<![\w-])@?(?:fig|tbl|eq|sec|chap|lst|alg):[A-Za-z0-9_.-]+"
    ),
    "absolute_path": re.compile(
        r"(?<![\w:])/(?:Users|Volumes|private|tmp|var|home|opt|etc|"
        r"Applications|System|Library)(?:/[^\s]*)?"
    ),
}
_MARKER_SAMPLES = {
    "front_matter": "---\nkey: value\n---",
    "legacy_container": "::: figure {#fig:model}\n:::",
    "stable_id": "{#fig:model}",
    "raw_citation": "[@smith2025]",
    "legacy_reference": "@fig:model",
    "absolute_path": "/Volumes/secret/thesis.md",
}


def _iter_visible_text(value: object) -> list[str]:
    if isinstance(value, ReviewTextRun) and value.code:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (tuple, list)):
        result: list[str] = []
        for item in value:
            result.extend(_iter_visible_text(item))
        return result
    if not is_dataclass(value):
        return []

    result = []
    for field in fields(value):
        if field.name in {"asset_handle", "code", "destination"}:
            continue
        result.extend(_iter_visible_text(getattr(value, field.name)))
    return result


def _review_visible_text(review) -> str:
    return "\n".join(
        text
        for block in review.blocks
        for text in _iter_visible_text(block.content)
    )


def _canonical_review():
    parser = create_parser_backend()
    document = parser.parse_file(CANONICAL_SOURCE)
    context = ValidationContext.from_document(
        document,
        template_roots=(TEMPLATE_ROOT,),
        required_metadata=(),
    )
    assert context.project_error is None
    assert context.template_error is None
    assert context.template is not None

    plan = compile_document(
        document,
        template=context.template,
        template_path=context.template_path,
    )
    review = map_review_result(
        PreviewResult(
            document=document,
            context=context,
            issues=(),
            plan=plan,
        )
    )
    return document, plan, review


def test_canonical_fixture_review_hides_markers_and_keeps_code_literal() -> None:
    document, plan, review = _canonical_review()

    assert document.source_path == CANONICAL_SOURCE.resolve()
    assert any(isinstance(block, Figure) for block in document.blocks)
    assert any(isinstance(block, Listing) for block in document.blocks)
    parsed_inlines = [
        inline
        for block in document.blocks
        if isinstance(block, Paragraph)
        for inline in block.inlines
    ]
    assert any(isinstance(inline, Citation) for inline in parsed_inlines)
    assert any(isinstance(inline, CrossReference) for inline in parsed_inlines)
    assert any(isinstance(node, FigureInstruction) for node in plan.nodes)
    assert any(isinstance(node, ListingInstruction) for node in plan.nodes)

    assert set(_MARKER_PATTERNS) == _MARKER_LABELS
    for label, sample in _MARKER_SAMPLES.items():
        assert _MARKER_PATTERNS[label].search(sample), label

    assert review.status == "ready"
    visible = _review_visible_text(review)
    for label, pattern in _MARKER_PATTERNS.items():
        assert pattern.search(visible) is None, label
    assert str(CANONICAL_SOURCE) not in visible
    assert str(V2_PROJECT) not in visible

    listing_block = next(
        block
        for block in review.blocks
        if isinstance(block.content, ReviewListingContent)
    )
    assert listing_block.content.code == (
        "# 代码中的 {#literal}、[@literal] 与 @fig:literal 必须保持字面量\n"
        "for epoch in range(epochs):\n"
        "    train_one_epoch()"
    )
    assert "{#literal}" in listing_block.content.code
    assert "[@literal]" in listing_block.content.code
    assert "@fig:literal" in listing_block.content.code

    heading_block = next(
        block
        for block in review.blocks
        if isinstance(block.content, ReviewParagraphContent)
        and block.source is not None
    )
    assert heading_block.source is not None
    assert heading_block.source.node_id.startswith("n")
    assert heading_block.source.node_id not in _review_visible_text(review)


@pytest.mark.parametrize(
    ("source", "code"),
    [
        (
            "---\ntitle: Legacy\n---\n# Thesis\n",
            "TF-SOURCE-LEGACY-001",
        ),
        (
            (
                "::: figure {#fig:model}\n"
                'src: "assets/model.png"\n'
                'caption: "Model"\n'
                ":::\n"
            ),
            "TF-SOURCE-LEGACY-002",
        ),
    ],
    ids=("front-matter", "legacy-container"),
)
def test_canonical_parser_rejects_non_review_source_markers(
    source: str,
    code: str,
) -> None:
    with pytest.raises(ParseError, match=code):
        create_parser_backend().parse_text(source, source_path=Path("boundary.md"))


def test_review_sanitizes_dirty_reference_display_and_citation_text() -> None:
    document = ThesisDocument(
        source_path=Path("thesis.md"),
        blocks=[Paragraph(location=SourceLocation(line=1))],
    )
    review = map_review_result(
        PreviewResult(
            document=document,
            context=ValidationContext(),
            issues=(),
            plan=RenderPlan(
                nodes=(
                    ParagraphInstruction(
                        text="",
                        inlines=(
                            ReferenceRun(
                                target_id="fig:model",
                                bookmark="tf_fig_model",
                                display_text=(
                                    "图 1-1 {#fig:model} /Volumes/secret/thesis.md"
                                ),
                            ),
                            CitationRun(
                                keys=("secret-key",),
                                ordinals=(2,),
                                raw="[@secret-key]",
                                text="[@secret-key]",
                            ),
                        ),
                    ),
                )
            ),
        )
    )

    paragraph = review.blocks[0].content
    assert isinstance(paragraph, ReviewParagraphContent)
    assert "图 1-1" in paragraph.text
    assert "[2]" in paragraph.text
    assert "fig:model" not in paragraph.text
    assert "secret-key" not in paragraph.text
    assert "{#" not in paragraph.text
    assert "/Volumes" not in paragraph.text


def test_review_rejects_unknown_instruction_and_inline_boundaries() -> None:
    with pytest.raises(TypeError, match="unsupported RenderInstruction"):
        project_instruction(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="unsupported InlineRun"):
        project_instruction(
            ParagraphInstruction(text="", inlines=(object(),))  # type: ignore[arg-type]
        )


def test_review_code_is_not_confused_with_normal_marker_leaks() -> None:
    document, _plan, review = _canonical_review()
    listing = next(
        block.content
        for block in review.blocks
        if isinstance(block.content, ReviewListingContent)
    )
    algorithm = next(
        block.content
        for block in review.blocks
        if isinstance(block.content, ReviewAlgorithmContent)
    )

    assert isinstance(listing, ReviewListingContent)
    assert isinstance(algorithm, ReviewAlgorithmContent)
    assert "{#literal}" not in _review_visible_text(review)
    assert "[@literal]" not in _review_visible_text(review)
    assert "@fig:literal" not in _review_visible_text(review)
    assert "{#literal}" in listing.code
    assert "[@literal]" in listing.code
    assert "@fig:literal" in listing.code
    assert "训练流程" in algorithm.caption
    assert document.source_path == CANONICAL_SOURCE.resolve()
