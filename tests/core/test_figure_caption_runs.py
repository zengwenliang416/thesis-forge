from pathlib import Path

import pytest

from thesis_forge.core.compiler import _compile_inlines, compile_document
from thesis_forge.core.model import (
    Citation,
    CrossReference,
    Emphasis,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    HardBreak,
    Heading,
    Inline,
    InlineCode,
    InlineMath,
    Link,
    Paragraph,
    SoftBreak,
    Strong,
    Text,
    ThesisDocument,
)
from thesis_forge.core.render_plan import (
    CaptionRuns,
    CitationRun,
    FigureInstruction,
    FootnoteReferenceRun,
    HardBreakRun,
    HyperlinkRun,
    MathRun,
    ParagraphInstruction,
    ReferenceRun,
    SoftBreakRun,
    TextRun,
)
from thesis_forge.templates import load_template


class UnknownInline(Inline):
    pass


def _rich_document() -> ThesisDocument:
    return ThesisDocument(
        source_path=Path("/tmp/thesis/thesis.md"),
        blocks=[
            Heading(id="chap:intro", level=1, inlines=[Text(value="绪论")]),
            Figure(
                id="fig:main",
                src="main.png",
                caption_inlines=(
                    Text(value="图题 "),
                    InlineCode(value="code"),
                    Strong(children=(Text(value="粗体"),)),
                    Emphasis(children=(Text(value="强调"),)),
                    Link(label="链接", destination="https://example.com"),
                    InlineMath(latex="x^2"),
                    SoftBreak(),
                    HardBreak(),
                    CrossReference(target="sec:target"),
                    Citation(keys=["caption"], raw="[@caption]"),
                    FootnoteReference(label="note"),
                ),
            ),
            Paragraph(
                inlines=[
                    Text(value="正文"),
                    Citation(keys=["body"], raw="[@body]"),
                ]
            ),
            Heading(
                id="sec:target",
                level=2,
                inlines=[
                    Text(value="目标 fig:heading"),
                    Citation(keys=["target"], raw="[@target]"),
                ],
            ),
            FootnoteDefinition(label="note", inlines=[Text(value="脚注")]),
        ],
    )


def _marker_document() -> ThesisDocument:
    return ThesisDocument(
        source_path=Path("/tmp/thesis/thesis.md"),
        blocks=[
            Figure(
                id="fig:main",
                src="main.png",
                caption_inlines=(
                    Text(value="主图 "),
                    CrossReference(target="fig:target"),
                    Citation(keys=["main"], raw="[@main]"),
                ),
            ),
            Paragraph(inlines=[Citation(keys=["body"], raw="[@body]")]),
            Figure(
                id="fig:target",
                src="target.png",
                caption_inlines=(
                    Text(value="目标图题 fig:other"),
                    Citation(keys=["targetfig"], raw="[@targetfig]"),
                ),
            ),
        ],
    )


def test_figure_caption_uses_one_typed_value_for_all_inline_variants() -> None:
    plan = compile_document(
        _rich_document(),
        template=load_template("templates/base/bachelor.yaml"),
    )

    figure = next(node for node in plan.nodes if isinstance(node, FigureInstruction))
    assert isinstance(figure.caption, CaptionRuns)
    assert "caption_inlines" not in {field.name for field in figure.__dataclass_fields__.values()}
    assert "caption_inlines" not in figure.payload

    runs = figure.caption.runs
    assert [type(run) for run in runs] == [
        TextRun,
        TextRun,
        TextRun,
        TextRun,
        HyperlinkRun,
        MathRun,
        SoftBreakRun,
        HardBreakRun,
        ReferenceRun,
        CitationRun,
        FootnoteReferenceRun,
    ]
    assert runs[1] == TextRun("code", code=True)
    assert runs[2] == TextRun("粗体", bold=True)
    assert runs[3] == TextRun("强调")
    assert runs[4] == HyperlinkRun("链接", "https://example.com")
    assert runs[5] == MathRun("x^2")
    assert isinstance(runs[8], ReferenceRun)
    assert runs[8].display_text == "目标"
    assert isinstance(runs[9], CitationRun)
    assert runs[9].raw == ""
    assert runs[9].ordinals == (1,)
    assert isinstance(runs[10], FootnoteReferenceRun)
    assert figure.label == "图1-1"
    assert figure.number == "1-1"
    assert figure.bookmark == "tf_fig_main"
    assert figure.sequence is not None

    paragraph = next(
        node for node in plan.nodes if isinstance(node, ParagraphInstruction)
    )
    body_citation = next(
        run for run in paragraph.inlines if isinstance(run, CitationRun)
    )
    assert body_citation.raw == "[@body]"


def test_figure_caption_citations_follow_document_order() -> None:
    plan = compile_document(_marker_document())

    assert plan.citation_order == ("main", "body", "targetfig")
    figures = [
        node for node in plan.nodes if isinstance(node, FigureInstruction)
    ]
    main_citation = next(
        run for run in figures[0].caption.runs if isinstance(run, CitationRun)
    )
    body = next(node for node in plan.nodes if isinstance(node, ParagraphInstruction))
    body_citation = next(
        run for run in body.inlines if isinstance(run, CitationRun)
    )
    assert main_citation.ordinals == (1,)
    assert body_citation.ordinals == (2,)


def test_figure_caption_and_references_remove_raw_markers_and_stable_ids() -> None:
    plan = compile_document(_marker_document())
    figures = [
        node for node in plan.nodes if isinstance(node, FigureInstruction)
    ]
    main, target = figures
    reference = next(run for run in main.caption.runs if isinstance(run, ReferenceRun))

    assert reference.display_text == "目标图题"
    assert target.label == "目标图题"
    assert plan.references["fig:target"].display_text == "目标图题"
    assert "[@main]" not in str(main.caption)
    assert "[@targetfig]" not in str(target.caption)
    assert "fig:target" not in str(main.caption)
    assert "fig:other" not in str(target.payload["label"])
    assert "[@targetfig]" not in str(target.payload["label"])


def test_figure_instruction_rejects_raw_caption_values() -> None:
    with pytest.raises(TypeError, match="caption must be CaptionRuns"):
        FigureInstruction(
            source_id="fig:raw",
            src="raw.png",
            asset_path=Path("/tmp/thesis/raw.png"),
            caption="raw caption",  # type: ignore[arg-type]
            width=None,
            resolved_width=None,
            chapter=1,
            number=None,
            label="",
            bookmark=None,
        )


def test_unknown_inline_fails_at_the_typed_compilation_seam() -> None:
    with pytest.raises(TypeError, match="unknown Inline subclass: UnknownInline"):
        _compile_inlines(
            [UnknownInline()],
            resolved={},
            citation_numbers={},
            footnote_ids={},
            bibliography_database=None,
            citation_formatter=None,
        )
