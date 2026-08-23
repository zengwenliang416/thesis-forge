from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.xmlchemy import BaseOxmlElement

from thesis_forge.core.math import LatexMathConverter
from thesis_forge.core.render_plan import (
    CitationRun,
    FootnoteReferenceRun,
    HardBreakRun,
    HyperlinkRun,
    InlineRun,
    MathRun,
    ReferenceRun,
    SoftBreakRun,
    TextRun,
)

from .equations import _append_math
from .errors import DocxRenderError


@dataclass(frozen=True, slots=True)
class InlineHandlers:
    text: Callable[[TextRun], None]
    reference: Callable[[ReferenceRun], None]
    citation: Callable[[CitationRun], None]
    footnote_reference: Callable[[FootnoteReferenceRun], None]
    hyperlink: Callable[[HyperlinkRun], None] | None = None
    math: Callable[[MathRun], None] | None = None
    soft_break: Callable[[SoftBreakRun], None] | None = None
    hard_break: Callable[[HardBreakRun], None] | None = None


def citation_run_element(
    citation: CitationRun,
    *,
    superscript: bool,
) -> BaseOxmlElement:
    run = OxmlElement("w:r")
    if superscript:
        properties = OxmlElement("w:rPr")
        vertical_alignment = OxmlElement("w:vertAlign")
        vertical_alignment.set(qn("w:val"), "superscript")
        properties.append(vertical_alignment)
        run.append(properties)
    value = OxmlElement("w:t")
    if citation.text.startswith(" ") or citation.text.endswith(" "):
        value.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    value.text = citation.text
    run.append(value)
    return run


def hyperlink_run_element(
    hyperlink: HyperlinkRun,
    relationship_id: str,
) -> BaseOxmlElement:
    element = OxmlElement("w:hyperlink")
    element.set(qn("r:id"), relationship_id)
    run = OxmlElement("w:r")
    value = OxmlElement("w:t")
    if hyperlink.text.startswith(" ") or hyperlink.text.endswith(" "):
        value.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    value.text = hyperlink.text
    run.append(value)
    element.append(run)
    return element


def math_run_element(math: MathRun) -> BaseOxmlElement:
    expression = LatexMathConverter().convert(math.latex)
    element = OxmlElement("m:oMath")
    _append_math(element, expression.root)
    return element


def render_inline_runs(
    runs: tuple[InlineRun, ...],
    handlers: InlineHandlers,
    *,
    capability: str,
) -> None:
    for item in runs:
        if isinstance(item, TextRun):
            handlers.text(item)
        elif isinstance(item, ReferenceRun):
            handlers.reference(item)
        elif isinstance(item, CitationRun):
            handlers.citation(item)
        elif isinstance(item, FootnoteReferenceRun):
            handlers.footnote_reference(item)
        elif isinstance(item, HyperlinkRun):
            if handlers.hyperlink is None:
                raise DocxRenderError(
                    capability,
                    "inline run hyperlink handler is not configured",
                )
            handlers.hyperlink(item)
        elif isinstance(item, MathRun):
            if handlers.math is None:
                raise DocxRenderError(
                    capability,
                    "inline run math handler is not configured",
                )
            handlers.math(item)
        elif isinstance(item, SoftBreakRun):
            if handlers.soft_break is None:
                raise DocxRenderError(
                    capability,
                    "inline run soft-break handler is not configured",
                )
            handlers.soft_break(item)
        elif isinstance(item, HardBreakRun):
            if handlers.hard_break is None:
                raise DocxRenderError(
                    capability,
                    "inline run hard-break handler is not configured",
                )
            handlers.hard_break(item)
        else:
            raise DocxRenderError(
                capability,
                f"unsupported inline run {type(item).__name__}",
            )
