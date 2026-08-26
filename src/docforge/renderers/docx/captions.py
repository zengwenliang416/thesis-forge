from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from docforge.core.render_plan import (
    CaptionRuns,
    FootnoteReferenceRun,
    InlineRun,
    SequenceInstruction,
    TextRun,
)
from docforge.templates.model import CaptionSpec, ThesisTemplate

from .bookmarks import end_bookmark, start_bookmark
from .fields import add_complex_field, reference_field_runs
from .fonts import apply_font
from .inlines import (
    InlineHandlers,
    citation_run_element,
    hyperlink_run_element,
    math_run_element,
    render_inline_runs,
)
from .styles import ALIGNMENTS


def caption_text(label: str, caption: str | CaptionRuns) -> str:
    value = str(caption)
    if label == value:
        return value
    return " ".join(part for part in (label, value) if part)


def _code_font(run: Run) -> None:
    properties = run._r.get_or_add_rPr()
    fonts = properties.get_or_add_rFonts()
    for theme_name in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        fonts.attrib.pop(qn(f"w:{theme_name}"), None)
    fonts.set(qn("w:ascii"), "Courier New")
    fonts.set(qn("w:hAnsi"), "Courier New")
    fonts.set(qn("w:eastAsia"), "Courier New")
    if properties.find(qn("w:noProof")) is None:
        properties.append(OxmlElement("w:noProof"))


def _append_text_run(paragraph: Paragraph, item: TextRun) -> Run:
    run = paragraph.add_run(item.text)
    if item.bold:
        run.bold = True
    if item.italic:
        run.italic = True
    return run


def _footnote_reference_element(item: FootnoteReferenceRun):
    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    style = OxmlElement("w:rStyle")
    style.set(qn("w:val"), "FootnoteReference")
    properties.append(style)
    run.append(properties)
    reference = OxmlElement("w:footnoteReference")
    reference.set(qn("w:id"), str(item.footnote_id))
    run.append(reference)
    return run


def _citation_superscript(template: ThesisTemplate | None) -> bool:
    return (
        template is not None
        and template.citation is not None
        and template.citation.presentation == "superscript"
    )


def _append_caption_runs(
    paragraph: Paragraph,
    runs: tuple[InlineRun, ...],
    template: ThesisTemplate | None,
) -> tuple[Run, ...]:
    code_runs: list[Run] = []

    def append_text(item: TextRun) -> None:
        run = _append_text_run(paragraph, item)
        if item.code:
            code_runs.append(run)

    render_inline_runs(
        runs,
        InlineHandlers(
            text=append_text,
            reference=lambda item: paragraph._p.extend(reference_field_runs(item)),
            citation=lambda item: paragraph._p.append(
                citation_run_element(
                    item,
                    superscript=_citation_superscript(template),
                )
            ),
            footnote_reference=lambda item: paragraph._p.append(
                _footnote_reference_element(item)
            ),
            hyperlink=lambda item: paragraph._p.append(
                hyperlink_run_element(
                    item,
                    paragraph.part.relate_to(
                        item.destination,
                        RT.HYPERLINK,
                        is_external=True,
                    ),
                )
            ),
            math=lambda item: paragraph._p.append(math_run_element(item)),
            soft_break=lambda _item: paragraph.add_run(" "),
            hard_break=lambda _item: paragraph.add_run().add_break(),
        ),
        capability="figure-caption",
    )
    return tuple(code_runs)


def _style_caption_runs(
    paragraph: Paragraph,
    *,
    spec: CaptionSpec | None,
    template: ThesisTemplate | None,
    code_runs: tuple[Run, ...],
) -> None:
    font_spec = spec.font if spec and spec.font is not None else (
        template.body.font if template is not None else None
    )
    size = spec.size if spec and spec.size is not None else (
        template.body.size if template is not None else None
    )
    for element in paragraph._p.iter(qn("w:r")):
        apply_font(Run(element, paragraph).font, font_spec, size=size)
    for run in code_runs:
        _code_font(run)


def add_caption(
    document: DocumentObject,
    *,
    label: str,
    caption: str | CaptionRuns,
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
    code_runs: tuple[Run, ...] = ()
    if caption and (sequence is not None or (label and label != caption)):
        paragraph.add_run(" ")
        if isinstance(caption, CaptionRuns):
            code_runs = _append_caption_runs(paragraph, caption.runs, template)
        else:
            paragraph.add_run(caption)
    elif caption and not label:
        if isinstance(caption, CaptionRuns):
            code_runs = _append_caption_runs(paragraph, caption.runs, template)
        else:
            paragraph.add_run(caption)

    _style_caption_runs(
        paragraph,
        spec=spec,
        template=template,
        code_runs=code_runs,
    )

    return paragraph
