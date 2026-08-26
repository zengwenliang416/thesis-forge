import pytest

from docforge.core.render_plan import (
    CaptionRuns,
    CitationRun,
    FootnoteReferenceRun,
    HardBreakRun,
    HyperlinkRun,
    MathRun,
    ReferenceRun,
    SoftBreakRun,
    TextRun,
)


def test_caption_runs_validate_all_declared_inline_runs_and_project_readable_text() -> None:
    runs = (
        TextRun("前"),
        ReferenceRun("fig:model", "tf_fig_model", "图1-1"),
        CitationRun(("smith2025",), (1,), raw="[@smith2025]", text="[1]"),
        FootnoteReferenceRun("note", 1),
        HyperlinkRun("链接", "https://example.test"),
        MathRun("x^2"),
        SoftBreakRun(),
        HardBreakRun(),
    )

    caption = CaptionRuns(runs)

    assert isinstance(caption, str)
    assert caption.runs == runs
    assert str(caption) == "前图1-1[1]链接x^2 \n"


def test_caption_runs_reject_unknown_values_at_the_typed_boundary() -> None:
    with pytest.raises(TypeError, match=r"unsupported InlineRun: object"):
        CaptionRuns((object(),))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        [TextRun("list")],
        iter((TextRun("iterator"),)),
    ],
)
def test_caption_runs_reject_non_tuple_containers(value: object) -> None:
    with pytest.raises(TypeError, match=r"CaptionRuns requires tuple"):
        CaptionRuns(value)  # type: ignore[arg-type]


def test_caption_runs_reject_tuple_subclasses() -> None:
    class TupleSubclass(tuple[TextRun, ...]):
        pass

    with pytest.raises(TypeError, match=r"CaptionRuns requires tuple"):
        CaptionRuns(TupleSubclass((TextRun("subclass"),)))
