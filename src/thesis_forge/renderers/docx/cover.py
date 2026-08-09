from __future__ import annotations

from docx.document import Document as DocumentObject

from thesis_forge.core.render_plan import CoverInstruction
from thesis_forge.templates.model import ThesisTemplate

from .styles import apply_paragraph_style


def render_cover(
    document: DocumentObject,
    instruction: CoverInstruction,
    template: ThesisTemplate,
) -> None:
    for item in template.cover.items:
        value = (
            item.text
            if item.text is not None
            else instruction.value_for(item.field or "")
        )
        if not value and item.skip_if_empty:
            continue

        paragraph = document.add_paragraph()
        paragraph.add_run(f"{item.prefix}{value}{item.suffix}")
        apply_paragraph_style(
            paragraph,
            item.style,
            fallback_font=template.body.font,
            fallback_size=template.body.size,
        )
