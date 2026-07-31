from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.enum.text import WD_ALIGN_PARAGRAPH

from thesis_forge.core.render_plan import CoverInstruction


def _centered_paragraph(
    document: DocumentObject,
    text: str,
) -> None:
    if not text:
        return
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run(text)


def render_cover(document: DocumentObject, instruction: CoverInstruction) -> None:
    _centered_paragraph(document, instruction.university)
    _centered_paragraph(document, instruction.college)
    document.add_paragraph()
    _centered_paragraph(document, instruction.title)
    _centered_paragraph(document, instruction.title_en)
    document.add_paragraph()
    for value in (
        instruction.major,
        instruction.degree,
        instruction.author,
        instruction.student_id,
        instruction.advisor,
        instruction.advisor_title,
        instruction.completed,
    ):
        _centered_paragraph(document, value)
