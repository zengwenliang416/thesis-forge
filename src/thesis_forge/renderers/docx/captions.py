from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.text.paragraph import Paragraph

from thesis_forge.core.render_plan import SequenceInstruction
from thesis_forge.templates.model import CaptionSpec, ThesisTemplate

from .bookmarks import end_bookmark, start_bookmark
from .fields import add_complex_field
from .fonts import apply_font
from .styles import ALIGNMENTS


def caption_text(label: str, caption: str) -> str:
    if label == caption:
        return caption
    return " ".join(part for part in (label, caption) if part)


def add_caption(
    document: DocumentObject,
    *,
    label: str,
    caption: str,
    bookmark: str | None,
    spec: CaptionSpec | None,
    template: ThesisTemplate | None,
    fallback_alignment: str,
    sequence: SequenceInstruction | None = None,
) -> Paragraph:
    paragraph = document.add_paragraph()
    paragraph.alignment = ALIGNMENTS[spec.alignment if spec else fallback_alignment]
    bookmark_id = start_bookmark(paragraph, bookmark)
    if sequence is not None:
        add_complex_field(
            paragraph,
            sequence.field_code,
            result=str(sequence.value),
            prefix=sequence.prefix,
            suffix=sequence.suffix,
        )
    else:
        paragraph.add_run(label)
    end_bookmark(paragraph, bookmark_id)
    if caption and (sequence is not None or (label and label != caption)):
        paragraph.add_run(f" {caption}")
    elif caption and not label:
        paragraph.add_run(caption)

    if template is not None:
        font_spec = spec.font if spec and spec.font is not None else template.body.font
        size = spec.size if spec and spec.size is not None else template.body.size
        for run in paragraph.runs:
            apply_font(run.font, font_spec, size=size)

    return paragraph
