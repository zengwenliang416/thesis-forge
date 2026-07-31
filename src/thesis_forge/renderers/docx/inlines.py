from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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
