from __future__ import annotations

from decimal import Decimal

from docx.document import Document as DocumentObject
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.image.exceptions import (
    InvalidImageStreamError,
    UnexpectedEndOfFileError,
    UnrecognizedImageError,
)
from docx.shared import Emu

from docforge.core.render_plan import FigureInstruction, FigureWidthInstruction
from docforge.templates.model import LengthSpec, ThesisTemplate

from .captions import add_caption
from .units import to_docx_length, to_points


class FigureRenderError(ValueError):
    def __init__(self, asset_path: str):
        self.asset_path = asset_path
        super().__init__(f"无法识别图片：{asset_path}")


def _docx_figure_width(
    document: DocumentObject,
    width: FigureWidthInstruction | None,
    template: ThesisTemplate | None,
) -> Emu | None:
    if width is None:
        return None
    if width.unit == "percent":
        section = document.sections[-1]
        content_width = int(section.page_width) - int(section.left_margin) - int(
            section.right_margin
        )
        return Emu(round(Decimal(content_width) * width.value / Decimal(100)))

    length = LengthSpec.model_validate(f"{width.value}{width.unit}")
    em_size_pt = (
        to_points(template.body.size, em_size_pt=12) if template is not None else 12
    )
    return to_docx_length(length, em_size_pt=em_size_pt)


def render_figure(
    document: DocumentObject,
    instruction: FigureInstruction,
    template: ThesisTemplate | None,
) -> None:
    figure_spec = template.figure if template is not None else None
    caption_spec = figure_spec.caption if figure_spec is not None else None
    position = caption_spec.position if caption_spec is not None else "bottom"

    def render_caption() -> None:
        add_caption(
            document,
            label=instruction.label,
            caption=instruction.caption,
            bookmark=instruction.bookmark,
            spec=caption_spec,
            template=template,
            fallback_alignment="center",
            sequence=instruction.sequence,
        )

    if position == "top":
        render_caption()

    width = _docx_figure_width(document, instruction.resolved_width, template)
    try:
        if width is None:
            document.add_picture(str(instruction.asset_path))
        else:
            document.add_picture(str(instruction.asset_path), width=width)
    except (
        InvalidImageStreamError,
        UnexpectedEndOfFileError,
        UnrecognizedImageError,
    ) as error:
        raise FigureRenderError(str(instruction.asset_path)) from error
    figure_paragraph = document.paragraphs[-1]
    figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    figure_paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

    if position == "bottom":
        render_caption()
