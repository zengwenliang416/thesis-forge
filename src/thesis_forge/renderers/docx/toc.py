"""TOC field rendering with cached entries (ADR-0005 §2.1, debt D-11).

The generated TOC field keeps the dirty/updateFields semantics unchanged,
but its cached result now contains one paragraph per heading so that any
consumer that never evaluates fields (Word "don't update", previewers,
direct PDF export) still shows a non-empty table of contents.

Entry structure mimics a real Word TOC cache: ``w:hyperlink`` anchored at
the heading bookmark, entry text, a right-aligned tab (from the TOC level
style), and a nested ``PAGEREF`` field whose cached value is a placeholder.
Page numbers are unknowable at compile time (no layout engine), so the
placeholder is ``1`` — consistent with the PAGE/NUMPAGES cached-value
convention (spikes/phase0/fields REPORT §2). Any field-evaluating consumer
replaces it with the real page number on update.
"""

from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from thesis_forge.core.render_plan import TocEntryInstruction, TocInstruction
from thesis_forge.templates.model import ThesisTemplate

from .fields import XML_SPACE, _field_char_run, _text_run
from .styles import TOC_STYLE_NAMES, ensure_toc_level_style

CACHED_PAGE_NUMBER = "1"


def _instruction_run(instruction: str):
    run = OxmlElement("w:r")
    instruction_text = OxmlElement("w:instrText")
    instruction_text.set(XML_SPACE, "preserve")
    instruction_text.text = instruction
    run.append(instruction_text)
    return run


def _tab_run():
    run = OxmlElement("w:r")
    run.append(OxmlElement("w:tab"))
    return run


def _pageref_runs(bookmark: str) -> list:
    return [
        _field_char_run("begin", dirty=True),
        _instruction_run(f"PAGEREF {bookmark} \\h"),
        _field_char_run("separate"),
        _text_run(CACHED_PAGE_NUMBER),
        _field_char_run("end"),
    ]


def _entry_paragraph(
    document: DocumentObject,
    template: ThesisTemplate | None,
    entry: TocEntryInstruction,
) -> Paragraph:
    level = min(max(entry.level, 1), max(TOC_STYLE_NAMES))
    style = ensure_toc_level_style(document, template, level)
    paragraph = document.add_paragraph(style=style)

    content = [_text_run(entry.text), _tab_run()]
    if entry.bookmark is None:
        # Without a heading bookmark there is no anchor to reference;
        # degrade to a plain-text page-number placeholder.
        content.append(_text_run(CACHED_PAGE_NUMBER))
        paragraph._p.extend(content)
        return paragraph

    content.extend(_pageref_runs(entry.bookmark))
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("w:anchor"), entry.bookmark)
    for run in content:
        hyperlink.append(run)
    paragraph._p.append(hyperlink)
    return paragraph


def add_toc_field(
    document: DocumentObject,
    paragraph: Paragraph,
    instruction: TocInstruction,
    template: ThesisTemplate | None,
) -> None:
    """Write the TOC field into ``paragraph`` plus cached entry paragraphs.

    The field instruction stays ``TOC \\o "min-max" \\h \\z \\u`` with a dirty
    begin; cached entries live between separate and end, and the field end is
    appended to the last entry paragraph (the structure Word itself produces).
    """
    toc_instruction = (
        f'TOC \\o "{instruction.min_level}-{instruction.max_level}" \\h \\z \\u'
    )
    paragraph._p.append(_field_char_run("begin", dirty=True))
    paragraph._p.append(_instruction_run(toc_instruction))
    paragraph._p.append(_field_char_run("separate"))

    field_end_parent = paragraph._p
    for entry in instruction.entries:
        entry_paragraph = _entry_paragraph(document, template, entry)
        field_end_parent = entry_paragraph._p
    field_end_parent.append(_field_char_run("end"))
