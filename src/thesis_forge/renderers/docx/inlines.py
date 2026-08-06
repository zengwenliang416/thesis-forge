from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.xmlchemy import BaseOxmlElement

from thesis_forge.core.render_plan import (
    CitationRun,
    FootnoteReferenceRun,
    InlineRun,
    ReferenceRun,
    TextRun,
)

from .errors import DocxRenderError


@dataclass(frozen=True, slots=True)
class InlineHandlers:
    text: Callable[[TextRun], None]
    reference: Callable[[ReferenceRun], None]
    citation: Callable[[CitationRun], None]
    footnote_reference: Callable[[FootnoteReferenceRun], None]


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
        else:
            raise DocxRenderError(
                capability,
                f"unsupported inline run {type(item).__name__}",
            )
