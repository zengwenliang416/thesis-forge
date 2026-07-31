from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

from thesis_forge.templates.model import HeadingLevelSpec, ThesisTemplate

from .fonts import apply_font
from .units import to_docx_length, to_points

ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _configure_heading(
    document: DocumentObject,
    template: ThesisTemplate,
    level: int,
    spec: HeadingLevelSpec,
) -> None:
    style = document.styles[f"Heading {level}"]
    apply_font(
        style.font,
        spec.font or template.body.font,
        size=spec.size,
        bold=spec.bold,
        italic=spec.italic,
    )
    paragraph = style.paragraph_format
    paragraph.alignment = ALIGNMENTS[spec.alignment]
    paragraph.page_break_before = spec.page_break_before
    if spec.space_before is not None:
        paragraph.space_before = to_docx_length(
            spec.space_before,
            em_size_pt=to_points(spec.size, em_size_pt=12),
        )
    if spec.space_after is not None:
        paragraph.space_after = to_docx_length(
            spec.space_after,
            em_size_pt=to_points(spec.size, em_size_pt=12),
        )


def configure_styles(document: DocumentObject, template: ThesisTemplate) -> None:
    normal = document.styles["Normal"]
    body_size_pt = to_points(template.body.size, em_size_pt=12)
    apply_font(normal.font, template.body.font, size=template.body.size)
    paragraph = normal.paragraph_format
    paragraph.alignment = ALIGNMENTS[template.body.alignment]
    paragraph.first_line_indent = to_docx_length(
        template.body.first_line_indent,
        em_size_pt=body_size_pt,
    )

    spacing = template.body.line_spacing
    if spacing.type == "fixed":
        paragraph.line_spacing = to_docx_length(spacing.value, em_size_pt=body_size_pt)
        paragraph.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    elif spacing.type == "multiple":
        paragraph.line_spacing = float(spacing.value)
        paragraph.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    else:
        paragraph.line_spacing_rule = WD_LINE_SPACING.SINGLE

    for level in range(1, 4):
        heading = template.heading.for_level(level)
        if heading is not None:
            _configure_heading(document, template, level, heading)

