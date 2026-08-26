from dataclasses import fields
from typing import get_args, get_type_hints

import pytest

from docforge.core import render_plan
from docforge.core.render_plan import (
    CitationRun,
    FigureInstruction,
    FootnoteReferenceRun,
    HardBreakRun,
    HyperlinkRun,
    InlineRun,
    MathRun,
    ReferenceRun,
    SoftBreakRun,
    TextRun,
    ensure_inline_run,
)


def test_inline_run_contains_exact_canonical_variants():
    assert get_args(InlineRun) == (
        TextRun,
        ReferenceRun,
        CitationRun,
        FootnoteReferenceRun,
        SoftBreakRun,
        HardBreakRun,
        HyperlinkRun,
        MathRun,
    )


def test_rich_runs_retain_renderer_neutral_semantic_fields():
    assert get_type_hints(HyperlinkRun) == {
        "text": str,
        "destination": str,
    }
    assert get_type_hints(MathRun) == {"latex": str}

    hyperlink = HyperlinkRun(text="ThesisForge", destination="https://example.test")
    math = MathRun(latex=r"x^2 + y^2")

    assert hyperlink.text == "ThesisForge"
    assert hyperlink.destination == "https://example.test"
    assert math.latex == r"x^2 + y^2"


def test_break_runs_are_distinct_nominal_types_without_compatibility_flags():
    soft = SoftBreakRun()
    hard = HardBreakRun()

    assert type(soft) is SoftBreakRun
    assert type(hard) is HardBreakRun
    assert type(soft) is not type(hard)
    assert fields(SoftBreakRun) == ()
    assert fields(HardBreakRun) == ()
    assert "hard" not in SoftBreakRun.__dataclass_fields__
    assert "soft" not in HardBreakRun.__dataclass_fields__


def test_unknown_inline_values_fail_at_the_explicit_typed_boundary():
    class ForeignInline:
        pass

    known = HyperlinkRun(text="label", destination="/target")
    assert ensure_inline_run(known) is known

    with pytest.raises(TypeError, match=r"unsupported InlineRun: ForeignInline"):
        ensure_inline_run(ForeignInline())


def test_a1m_does_not_add_aliases_or_a_second_figure_caption_source():
    assert not hasattr(render_plan, "BreakRun")
    assert not hasattr(render_plan, "LinkRun")
    assert "caption_inlines" not in {field.name for field in fields(FigureInstruction)}
