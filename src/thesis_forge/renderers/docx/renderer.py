from __future__ import annotations

from pathlib import Path

from docx.document import Document as DocumentObject
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from thesis_forge.core.math import MathConversionError
from thesis_forge.core.render_plan import (
    AlgorithmInstruction,
    BibliographyInstruction,
    BlockQuoteInstruction,
    CodeBlockInstruction,
    CoverInstruction,
    EquationInstruction,
    FigureInstruction,
    FootnoteDefinitionInstruction,
    HeadingInstruction,
    InlineRun,
    ListingInstruction,
    ListInstruction,
    PageBreakInstruction,
    ParagraphInstruction,
    ParagraphRole,
    RenderPlan,
    SectionBreakInstruction,
    TableInstruction,
    TextRun,
    TocInstruction,
)
from thesis_forge.templates.model import ListSpec, ThesisTemplate

from .bookmarks import wrap_paragraph_in_bookmark
from .captions import add_caption
from .cover import render_cover
from .document import create_document
from .equations import render_equation
from .errors import DocxRenderError
from .fields import add_reference_field, set_update_fields
from .figures import render_figure
from .footnotes import FootnoteManager
from .inlines import (
    InlineHandlers,
    citation_run_element,
    hyperlink_run_element,
    math_run_element,
    render_inline_runs,
)
from .lists import apply_list_numbering, create_list_numbering, resolve_list_level
from .sections import add_section, configure_initial_section
from .styles import (
    HEADING_BASE_ROLES,
    apply_paragraph_style,
    ensure_paragraph_style,
    resolve_paragraph_style,
    resolve_role_em_size_points,
)
from .tables import render_table
from .toc import add_toc_field


def _citation_superscript(template: ThesisTemplate | None) -> bool:
    return (
        template is not None
        and template.citation is not None
        and template.citation.presentation == "superscript"
    )


def _add_runs(
    paragraph,
    runs: tuple[InlineRun, ...],
    footnotes: FootnoteManager,
    template: ThesisTemplate | None,
) -> None:
    render_inline_runs(
        runs,
        InlineHandlers(
            text=lambda item: _add_text_run(paragraph, item),
            reference=lambda item: add_reference_field(paragraph, item),
            citation=lambda item: paragraph._p.append(
                citation_run_element(
                    item,
                    superscript=_citation_superscript(template),
                )
            ),
            footnote_reference=lambda item: footnotes.add_reference(paragraph, item),
            hyperlink=lambda item: _add_hyperlink_run(paragraph, item),
            math=lambda item: paragraph._p.append(math_run_element(item)),
            soft_break=lambda item: paragraph.add_run(" "),
            hard_break=lambda item: paragraph.add_run().add_break(),
        ),
        capability="paragraph",
    )


def _add_hyperlink_run(paragraph, item) -> None:
    relationship_id = paragraph.part.relate_to(
        item.destination,
        RT.HYPERLINK,
        is_external=True,
    )
    paragraph._p.append(hyperlink_run_element(item, relationship_id))


def _add_text_run(paragraph, item: TextRun) -> None:
    run = paragraph.add_run(item.text)
    if item.bold:
        run.bold = True
    if item.italic:
        run.italic = True
    if item.code:
        properties = run._r.get_or_add_rPr()
        fonts = properties.get_or_add_rFonts()
        for theme_name in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
            fonts.attrib.pop(qn(f"w:{theme_name}"), None)
        fonts.set(qn("w:ascii"), "Courier New")
        fonts.set(qn("w:hAnsi"), "Courier New")
        fonts.set(qn("w:eastAsia"), "Courier New")
        properties.append(OxmlElement("w:noProof"))


def _add_preformatted_paragraph(
    document: DocumentObject,
    text: str,
    template: ThesisTemplate | None = None,
):
    paragraph = document.add_paragraph()
    if template is not None:
        apply_paragraph_style(
            paragraph,
            template.body,
            fallback_font=template.body.font,
            fallback_size=template.body.size,
        )
    _add_text_run(paragraph, TextRun(text=text, code=True))
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    properties = paragraph._p.get_or_add_pPr()
    indentation = properties.find(qn("w:ind"))
    if indentation is None:
        indentation = OxmlElement("w:ind")
        properties.append(indentation)
    indentation.set(qn("w:firstLine"), "0")
    return paragraph


def _indent_blockquote_paragraph(paragraph) -> None:
    properties = paragraph._p.get_or_add_pPr()
    indentation = properties.find(qn("w:ind"))
    if indentation is None:
        indentation = OxmlElement("w:ind")
        properties.append(indentation)
    for side in ("left", "right"):
        attribute = qn(f"w:{side}")
        current = int(indentation.get(attribute, "0"))
        indentation.set(attribute, str(current + 360))
    indentation.set(qn("w:firstLine"), "0")


def _render_captioned_preformatted(
    document: DocumentObject,
    *,
    text: str,
    label: str,
    caption: str,
    bookmark: str | None,
    sequence,
    caption_spec,
    template: ThesisTemplate | None,
) -> None:
    def render_caption() -> None:
        add_caption(
            document,
            label=label,
            caption=caption,
            bookmark=bookmark,
            spec=caption_spec,
            template=template,
            fallback_alignment="center",
            sequence=sequence,
        )

    if caption_spec is not None and caption_spec.position == "bottom":
        _add_preformatted_paragraph(document, text, template)
        render_caption()
    else:
        render_caption()
        _add_preformatted_paragraph(document, text, template)


def _exclude_from_outline(paragraph) -> None:
    properties = paragraph._p.get_or_add_pPr()
    outline_level = properties.find(qn("w:outlineLvl"))
    if outline_level is None:
        outline_level = OxmlElement("w:outlineLvl")
        properties.append(outline_level)
    outline_level.set(qn("w:val"), "9")


def _semantic_word_style(
    document: DocumentObject,
    template: ThesisTemplate | None,
    role: ParagraphRole,
    *,
    heading_level: int | None = None,
):
    if template is None or role == "body":
        return None
    spec = resolve_paragraph_style(
        template,
        role,
        heading_level=heading_level,
    )
    if spec is None:
        return None
    base_style = None
    if role in HEADING_BASE_ROLES:
        base_style = document.styles[f"Heading {min(heading_level or 1, 9)}"]
    em_fallback_size = (
        template.body.size
        if spec.size is not None and spec.size.unit == "em"
        else None
    )
    return ensure_paragraph_style(
        document,
        role,
        spec,
        fallback_size=em_fallback_size,
        base_style=base_style,
        em_size_pt=resolve_role_em_size_points(
            template,
            role,
            heading_level=heading_level,
        ),
    )


def _render_typed(
    document: DocumentObject,
    instruction,
    template: ThesisTemplate | None,
    plan: RenderPlan,
    footnotes: FootnoteManager,
) -> None:
    if isinstance(instruction, CoverInstruction):
        if template is None:
            raise DocxRenderError("cover", "cover rendering requires a template")
        render_cover(document, instruction, template)
    elif isinstance(instruction, HeadingInstruction):
        style = f"Heading {min(instruction.level, 9)}"
        if instruction.role is not None:
            style = _semantic_word_style(
                document,
                template,
                instruction.role,
                heading_level=instruction.level,
            ) or style
        paragraph = document.add_paragraph(style=style)
        _add_runs(paragraph, instruction.inlines, footnotes, template)
        wrap_paragraph_in_bookmark(paragraph, instruction.bookmark)
    elif isinstance(instruction, ParagraphInstruction):
        style = _semantic_word_style(document, template, instruction.role)
        paragraph = document.add_paragraph(style=style)
        _add_runs(paragraph, instruction.inlines, footnotes, template)
    elif isinstance(instruction, CodeBlockInstruction):
        _add_preformatted_paragraph(document, instruction.code, template)
    elif isinstance(instruction, BlockQuoteInstruction):
        paragraph_count = len(document.paragraphs)
        for child in instruction.children:
            _render_typed(document, child, template, plan, footnotes)
        for paragraph in document.paragraphs[paragraph_count:]:
            _indent_blockquote_paragraph(paragraph)
    elif isinstance(instruction, ListInstruction):
        list_spec = template.list if template is not None else ListSpec()
        policy = (
            list_spec.ordered
            if instruction.ordered
            else list_spec.unordered
        )
        first_ordinal = next(
            (item.ordinal for item in instruction.items if item.ordinal is not None),
            None,
        )
        number_id = create_list_numbering(
            document,
            policy=policy,
            start=instruction.start or first_ordinal or 1,
        )
        for item in instruction.items:
            word_level, level_spec = resolve_list_level(policy, item.level)
            paragraph = document.add_paragraph()
            _add_runs(paragraph, item.inlines, footnotes, template)
            apply_paragraph_style(
                paragraph,
                level_spec.style,
                fallback_font=template.body.font if template is not None else None,
                fallback_size=template.body.size if template is not None else None,
            )
            apply_list_numbering(
                paragraph,
                number_id=number_id,
                level=word_level,
            )
    elif isinstance(instruction, FigureInstruction):
        render_figure(document, instruction, template)
    elif isinstance(instruction, TableInstruction):
        render_table(document, instruction, template)
    elif isinstance(instruction, EquationInstruction):
        render_equation(document, instruction)
    elif isinstance(instruction, ListingInstruction):
        listing_spec = template.listing if template is not None else None
        caption_spec = listing_spec.caption if listing_spec is not None else None
        _render_captioned_preformatted(
            document,
            text=instruction.code,
            label=instruction.label,
            caption=instruction.caption,
            bookmark=instruction.bookmark,
            sequence=instruction.sequence,
            caption_spec=caption_spec,
            template=template,
        )
    elif isinstance(instruction, AlgorithmInstruction):
        algorithm_spec = template.algorithm if template is not None else None
        caption_spec = algorithm_spec.caption if algorithm_spec is not None else None
        _render_captioned_preformatted(
            document,
            text=instruction.body,
            label=instruction.label,
            caption=instruction.caption,
            bookmark=instruction.bookmark,
            sequence=instruction.sequence,
            caption_spec=caption_spec,
            template=template,
        )
    elif isinstance(instruction, FootnoteDefinitionInstruction):
        footnotes.add_definition(instruction)
    elif isinstance(instruction, BibliographyInstruction):
        style = _semantic_word_style(document, template, "bibliography.entry")
        for entry in instruction.entries:
            document.add_paragraph(entry.text, style=style)
    elif isinstance(instruction, PageBreakInstruction):
        document.add_page_break()
    elif isinstance(instruction, TocInstruction):
        style = _semantic_word_style(
            document,
            template,
            "toc.title",
            heading_level=1,
        )
        title = document.add_paragraph("目录", style=style)
        _exclude_from_outline(title)
        paragraph = document.add_paragraph()
        add_toc_field(document, paragraph, instruction, template)
        wrap_paragraph_in_bookmark(paragraph, "tf_toc_index")
    elif isinstance(instruction, SectionBreakInstruction):
        add_section(
            document,
            template,
            plan.section_policy,
            instruction.role,
        )
    else:
        raise DocxRenderError(
            "instruction",
            f"unsupported instruction {type(instruction).__name__}",
        )


class DocxRenderer:
    """Render a renderer-neutral plan into an editable DOCX."""

    def render(self, plan: RenderPlan, output: str | Path) -> Path:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            document = create_document(plan.template)
            set_update_fields(document)
            configure_initial_section(
                document,
                plan.template,
                plan.section_policy,
                plan.initial_section_role,
            )
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            raise DocxRenderError("document", str(error)) from error
        footnotes = FootnoteManager(
            document,
            citation_superscript=_citation_superscript(plan.template),
        )

        for node in plan.nodes:
            try:
                _render_typed(document, node, plan.template, plan, footnotes)
            except DocxRenderError:
                raise
            except MathConversionError:
                raise
            except (AttributeError, KeyError, TypeError, ValueError) as error:
                capability = getattr(node, "kind", type(node).__name__)
                raise DocxRenderError(capability, str(error)) from error

        try:
            footnotes.attach()
            document.save(output_path)
        except DocxRenderError:
            raise
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            raise DocxRenderError("package", str(error)) from error
        return output_path
