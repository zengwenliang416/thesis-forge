from __future__ import annotations

from typing import TypeAlias

from docx.document import Document as DocumentObject
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu
from docx.styles.style import ParagraphStyle
from docx.text.paragraph import Paragraph

from thesis_forge.core.render_plan import ParagraphRole
from thesis_forge.templates.model import (
    FontSpec,
    LengthSpec,
    ParagraphStyleSpec,
    ThesisTemplate,
    TocLevelSpec,
)

from .fonts import apply_font
from .units import to_docx_length, to_points

ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

PARAGRAPH_STYLE_NAMES = {
    "abstract.zh.title": "TF Abstract ZH Title",
    "abstract.zh.body": "TF Abstract ZH Body",
    "keywords.zh": "TF Keywords ZH",
    "abstract.en.title": "TF Abstract EN Title",
    "abstract.en.body": "TF Abstract EN Body",
    "keywords.en": "TF Keywords EN",
    "toc.title": "TF TOC Title",
    "bibliography.title": "TF Bibliography Title",
    "bibliography.entry": "TF Bibliography Entry",
    "special.acknowledgements": "TF Acknowledgements",
    "special.achievements": "TF Achievements",
}

HEADING_BASE_ROLES = frozenset(
    {
        "abstract.zh.title",
        "abstract.en.title",
        "toc.title",
        "bibliography.title",
        "special.acknowledgements",
        "special.achievements",
    }
)

TOC_STYLE_NAMES = {
    1: "TOC 1",
    2: "TOC 2",
    3: "TOC 3",
}

TOC_LEADERS = {
    "none": "none",
    "dots": "dot",
    "dashes": "hyphen",
    "line": "underscore",
    "heavy": "heavy",
    "middle_dot": "middleDot",
}


ParagraphTarget: TypeAlias = ParagraphStyle | Paragraph


def resolve_paragraph_style(
    template: ThesisTemplate | None,
    role: ParagraphRole,
    *,
    heading_level: int | None = None,
) -> ParagraphStyleSpec | None:
    if template is None:
        return None
    if role == "body":
        return template.body

    heading_fallback = (
        template.heading.for_level(heading_level or 1) or template.heading.level1
    )
    semantic = template.semantic_styles
    if role == "abstract.zh.title":
        return (
            semantic.abstract_zh.title
            if semantic.abstract_zh is not None and semantic.abstract_zh.title is not None
            else heading_fallback
        )
    if role == "abstract.zh.body":
        return (
            semantic.abstract_zh.body
            if semantic.abstract_zh is not None and semantic.abstract_zh.body is not None
            else template.body
        )
    if role == "keywords.zh":
        return (
            semantic.abstract_zh.keywords
            if semantic.abstract_zh is not None
            and semantic.abstract_zh.keywords is not None
            else template.body
        )
    if role == "abstract.en.title":
        return (
            semantic.abstract_en.title
            if semantic.abstract_en is not None and semantic.abstract_en.title is not None
            else heading_fallback
        )
    if role == "abstract.en.body":
        return (
            semantic.abstract_en.body
            if semantic.abstract_en is not None and semantic.abstract_en.body is not None
            else template.body
        )
    if role == "keywords.en":
        return (
            semantic.abstract_en.keywords
            if semantic.abstract_en is not None
            and semantic.abstract_en.keywords is not None
            else template.body
        )
    if role == "toc.title":
        return (
            template.toc.title
            if template.toc is not None and template.toc.title is not None
            else heading_fallback
        )
    if role == "bibliography.title":
        return (
            template.bibliography.title
            if template.bibliography is not None
            and template.bibliography.title is not None
            else heading_fallback
        )
    if role == "bibliography.entry":
        return (
            template.bibliography.entry
            if template.bibliography is not None
            and template.bibliography.entry is not None
            else template.body
        )
    if role == "special.acknowledgements":
        return semantic.acknowledgements or heading_fallback
    if role == "special.achievements":
        return semantic.achievements or heading_fallback
    raise ValueError(f"unsupported paragraph role: {role}")


def resolve_role_em_size_points(
    template: ThesisTemplate,
    role: ParagraphRole,
    *,
    heading_level: int | None = None,
) -> float:
    if role in HEADING_BASE_ROLES:
        heading = (
            template.heading.for_level(heading_level or 1)
            or template.heading.level1
        )
        resolved = _resolved_size_points(heading.size, template.body.size)
    else:
        resolved = _resolved_size_points(template.body.size, None)
    if resolved is None:
        raise ValueError(f"paragraph role has no effective font size: {role}")
    return resolved


def _resolved_size_points(
    size: LengthSpec | None,
    fallback_size: LengthSpec | None,
) -> float | None:
    selected = size or fallback_size
    if selected is None:
        return None
    if selected.unit != "em":
        return to_points(selected)
    if fallback_size is None or fallback_size.unit == "em":
        raise ValueError("em font size requires a non-em fallback size")
    return to_points(selected, em_size_pt=to_points(fallback_size))


def _font_size_em_base_points(
    size: LengthSpec | None,
    fallback_size: LengthSpec | None,
) -> float | None:
    if size is None or size.unit != "em":
        return None
    if fallback_size is None or fallback_size.unit == "em":
        raise ValueError("em font size requires a non-em fallback size")
    return to_points(fallback_size)


def _set_on_off_property(paragraph, tag: str, value: bool | None) -> None:
    if value is None:
        return
    p_pr = paragraph._element.get_or_add_pPr()
    element = p_pr.find(qn(tag))
    if element is None:
        element = OxmlElement(tag)
        p_pr.append(element)
    if value:
        element.attrib.pop(qn("w:val"), None)
    else:
        element.set(qn("w:val"), "0")


def _set_outline_level(paragraph, value: int | None) -> None:
    if value is None:
        return
    p_pr = paragraph._element.get_or_add_pPr()
    outline = p_pr.find(qn("w:outlineLvl"))
    if outline is None:
        outline = OxmlElement("w:outlineLvl")
        p_pr.append(outline)
    outline.set(qn("w:val"), str(value))


def apply_paragraph_style(
    target: ParagraphTarget,
    spec: ParagraphStyleSpec,
    *,
    fallback_font: FontSpec | None = None,
    fallback_size: LengthSpec | None = None,
    em_size_pt: float | None = None,
) -> None:
    font_spec = spec.font or fallback_font
    size = spec.size or fallback_size
    size_pt = _resolved_size_points(spec.size, fallback_size)
    if size_pt is None:
        size_pt = em_size_pt
    font_em_base_pt = _font_size_em_base_points(spec.size, fallback_size)

    if isinstance(target, Paragraph):
        for run in target.runs:
            apply_font(
                run.font,
                font_spec,
                size=size,
                bold=spec.bold,
                italic=spec.italic,
                em_size_pt=font_em_base_pt,
            )
    else:
        apply_font(
            target.font,
            font_spec,
            size=size,
            bold=spec.bold,
            italic=spec.italic,
            em_size_pt=font_em_base_pt,
        )

    paragraph = target.paragraph_format
    if spec.alignment is not None:
        paragraph.alignment = ALIGNMENTS[spec.alignment]
    if spec.left_indent is not None:
        paragraph.left_indent = to_docx_length(
            spec.left_indent,
            em_size_pt=size_pt,
        )
    if spec.right_indent is not None:
        paragraph.right_indent = to_docx_length(
            spec.right_indent,
            em_size_pt=size_pt,
        )
    if spec.hanging_indent is not None and spec.hanging_indent.value > 0:
        paragraph.first_line_indent = -to_docx_length(
            spec.hanging_indent,
            em_size_pt=size_pt,
        )
    elif spec.first_line_indent is not None:
        paragraph.first_line_indent = to_docx_length(
            spec.first_line_indent,
            em_size_pt=size_pt,
        )
    elif spec.hanging_indent is not None:
        paragraph.first_line_indent = to_docx_length(
            spec.hanging_indent,
            em_size_pt=size_pt,
        )
    if spec.space_before is not None:
        paragraph.space_before = to_docx_length(
            spec.space_before,
            em_size_pt=size_pt,
        )
    if spec.space_after is not None:
        paragraph.space_after = to_docx_length(
            spec.space_after,
            em_size_pt=size_pt,
        )

    spacing = spec.line_spacing
    if spacing is not None:
        if spacing.type == "fixed":
            paragraph.line_spacing = to_docx_length(
                spacing.value,
                em_size_pt=size_pt,
            )
            paragraph.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        elif spacing.type == "multiple":
            paragraph.line_spacing = float(spacing.value)
            paragraph.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        else:
            paragraph.line_spacing_rule = WD_LINE_SPACING.SINGLE

    if spec.widow_control is not None:
        paragraph.widow_control = spec.widow_control
    if spec.keep_together is not None:
        paragraph.keep_together = spec.keep_together
    if spec.keep_with_next is not None:
        paragraph.keep_with_next = spec.keep_with_next
    if spec.page_break_before is not None:
        paragraph.page_break_before = spec.page_break_before
    _set_outline_level(paragraph, spec.outline_level)
    _set_on_off_property(paragraph, "w:snapToGrid", spec.snap_to_grid)


def ensure_paragraph_style(
    document: DocumentObject,
    role: str,
    spec: ParagraphStyleSpec,
    *,
    fallback_font: FontSpec | None = None,
    fallback_size: LengthSpec | None = None,
    base_style: ParagraphStyle | None = None,
    em_size_pt: float | None = None,
) -> ParagraphStyle:
    try:
        style_name = PARAGRAPH_STYLE_NAMES[role]
    except KeyError as error:
        raise ValueError(f"unsupported paragraph role: {role}") from error

    style_id = style_name.replace(" ", "")
    style = next(
        (
            candidate
            for candidate in document.styles
            if candidate.type == WD_STYLE_TYPE.PARAGRAPH
            and candidate.style_id == style_id
        ),
        None,
    )
    if style is None:
        style = document.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
    style.base_style = base_style or document.styles["Normal"]
    apply_paragraph_style(
        style,
        spec,
        fallback_font=fallback_font,
        fallback_size=fallback_size,
        em_size_pt=em_size_pt,
    )
    return style


def _set_right_tab(
    style: ParagraphStyle,
    *,
    position_twips: int,
    leader: str,
) -> None:
    p_pr = style._element.get_or_add_pPr()
    tabs = p_pr.find(qn("w:tabs"))
    if tabs is None:
        tabs = OxmlElement("w:tabs")
        p_pr.insert_element_before(
            tabs,
            "w:spacing",
            "w:ind",
            "w:jc",
            "w:outlineLvl",
            "w:rPr",
        )
    for tab in tuple(tabs.findall(qn("w:tab"))):
        if tab.get(qn("w:val")) == "right":
            tabs.remove(tab)

    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "right")
    tab.set(qn("w:pos"), str(position_twips))
    tab.set(qn("w:leader"), TOC_LEADERS[leader])
    tabs.append(tab)


def _toc_content_width_twips(document: DocumentObject) -> int:
    section = document.sections[0]
    content_width = (
        int(section.page_width)
        - int(section.left_margin)
        - int(section.right_margin)
    )
    if content_width <= 0:
        raise ValueError("TOC page-number tab requires positive content width")
    return Emu(content_width).twips


def configure_toc_styles(
    document: DocumentObject,
    template: ThesisTemplate,
) -> None:
    if template.toc is None:
        return

    normal = document.styles["Normal"]
    default_tab_position = _toc_content_width_twips(document)
    for level, style_name in TOC_STYLE_NAMES.items():
        spec = template.toc.for_level(level) or TocLevelSpec()
        style_id = style_name.replace(" ", "")
        style = next(
            (
                candidate
                for candidate in document.styles
                if candidate.type == WD_STYLE_TYPE.PARAGRAPH
                and candidate.style_id == style_id
            ),
            None,
        )
        if style is None:
            style = document.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = normal

        em_size_pt = _resolved_size_points(spec.size, template.body.size)
        em_fallback_size = (
            template.body.size
            if spec.size is not None and spec.size.unit == "em"
            else None
        )
        apply_paragraph_style(
            style,
            spec,
            fallback_size=em_fallback_size,
            em_size_pt=em_size_pt,
        )
        position_twips = default_tab_position
        if spec.page_number_tab is not None:
            position_twips = to_docx_length(
                spec.page_number_tab,
                em_size_pt=em_size_pt,
            ).twips
        _set_right_tab(
            style,
            position_twips=position_twips,
            leader=spec.leader,
        )


def configure_styles(document: DocumentObject, template: ThesisTemplate) -> None:
    normal = document.styles["Normal"]
    apply_paragraph_style(normal, template.body)

    for level in range(1, 4):
        heading = template.heading.for_level(level)
        if heading is not None:
            apply_paragraph_style(
                document.styles[f"Heading {level}"],
                heading,
                fallback_font=template.body.font,
                fallback_size=template.body.size,
            )
    configure_toc_styles(document, template)
