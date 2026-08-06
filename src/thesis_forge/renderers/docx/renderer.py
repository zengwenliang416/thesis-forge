from __future__ import annotations

from pathlib import Path

from docx.document import Document as DocumentObject
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

from thesis_forge.core.math import MathConversionError
from thesis_forge.core.render_plan import (
    AlgorithmInstruction,
    BibliographyInstruction,
    CoverInstruction,
    EquationInstruction,
    FigureInstruction,
    FootnoteDefinitionInstruction,
    HeadingInstruction,
    InlineRun,
    ListingInstruction,
    ListInstruction,
    ParagraphInstruction,
    ParagraphRole,
    RenderNode,
    RenderPlan,
    SectionBreakInstruction,
    TableInstruction,
    TocInstruction,
)
from thesis_forge.templates.model import ThesisTemplate

from .bookmarks import wrap_paragraph_in_bookmark
from .cover import render_cover
from .document import create_document
from .equations import render_equation
from .errors import DocxRenderError
from .fields import add_complex_field, add_reference_field, set_update_fields
from .figures import render_figure
from .footnotes import FootnoteManager
from .inlines import InlineHandlers, citation_run_element, render_inline_runs
from .lists import apply_list_numbering, create_list_numbering
from .sections import add_section, configure_initial_section
from .styles import (
    HEADING_BASE_ROLES,
    ensure_paragraph_style,
    resolve_paragraph_style,
    resolve_role_em_size_points,
)
from .tables import render_table


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
            text=lambda item: paragraph.add_run(item.text),
            reference=lambda item: add_reference_field(paragraph, item),
            citation=lambda item: paragraph._p.append(
                citation_run_element(
                    item,
                    superscript=_citation_superscript(template),
                )
            ),
            footnote_reference=lambda item: footnotes.add_reference(paragraph, item),
        ),
        capability="paragraph",
    )


def _add_preformatted_paragraph(document: DocumentObject, text: str):
    paragraph = document.add_paragraph(text)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    return paragraph


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
        render_cover(document, instruction)
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
    elif isinstance(instruction, ListInstruction):
        first_ordinal = next(
            (item.ordinal for item in instruction.items if item.ordinal is not None),
            None,
        )
        number_id = create_list_numbering(
            document,
            ordered=instruction.ordered,
            start=instruction.start or first_ordinal or 1,
        )
        for item in instruction.items:
            paragraph = document.add_paragraph()
            apply_list_numbering(
                paragraph,
                number_id=number_id,
                level=item.level,
            )
            _add_runs(paragraph, item.inlines, footnotes, template)
    elif isinstance(instruction, FigureInstruction):
        render_figure(document, instruction, template)
    elif isinstance(instruction, TableInstruction):
        render_table(document, instruction, template)
    elif isinstance(instruction, EquationInstruction):
        render_equation(document, instruction)
    elif isinstance(instruction, ListingInstruction):
        anchor = None
        if instruction.caption:
            anchor = document.add_paragraph(instruction.caption)
        code = _add_preformatted_paragraph(document, instruction.code)
        wrap_paragraph_in_bookmark(anchor or code, instruction.bookmark)
    elif isinstance(instruction, AlgorithmInstruction):
        anchor = None
        if instruction.caption:
            anchor = document.add_paragraph(instruction.caption)
        body = _add_preformatted_paragraph(document, instruction.body)
        wrap_paragraph_in_bookmark(anchor or body, instruction.bookmark)
    elif isinstance(instruction, FootnoteDefinitionInstruction):
        footnotes.add_definition(instruction)
    elif isinstance(instruction, BibliographyInstruction):
        style = _semantic_word_style(document, template, "bibliography.entry")
        for entry in instruction.entries:
            document.add_paragraph(entry.text, style=style)
    elif isinstance(instruction, TocInstruction):
        style = _semantic_word_style(
            document,
            template,
            "toc.title",
            heading_level=1,
        )
        paragraph = document.add_paragraph(style=style)
        add_complex_field(
            paragraph,
            f'TOC \\o "{instruction.min_level}-{instruction.max_level}" \\h \\z \\u',
            result="目录",
        )
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


def _render_legacy(document: DocumentObject, node: RenderNode) -> None:
    if node.kind == "heading":
        document.add_heading(
            node.payload.get("text", ""),
            level=min(int(node.payload.get("level", 1)), 9),
        )
    elif node.kind == "paragraph":
        document.add_paragraph(node.payload.get("text", ""))
    else:
        document.add_paragraph(f"[{node.kind}] {node.payload}")


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
                if isinstance(node, RenderNode):
                    _render_legacy(document, node)
                else:
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
