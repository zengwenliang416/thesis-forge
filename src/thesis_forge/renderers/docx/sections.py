from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from thesis_forge.templates.model import (
    HeaderFooterSpec,
    HeaderFooterVariantSpec,
    PageNumberDisplaySpec,
    ParagraphBorderSpec,
    SectionSpec,
    SectionsSpec,
    ThesisTemplate,
)

from .document import configure_section_geometry
from .fields import add_complex_field
from .styles import apply_paragraph_style
from .units import to_points

SECTION_STARTS = {
    "continuous": WD_SECTION_START.CONTINUOUS,
    "new_page": WD_SECTION_START.NEW_PAGE,
    "odd_page": WD_SECTION_START.ODD_PAGE,
    "even_page": WD_SECTION_START.EVEN_PAGE,
}
PAGE_NUMBER_FORMATS = {
    "decimal": "decimal",
    "roman-lower": "lowerRoman",
    "roman-upper": "upperRoman",
}
PAGE_NUMBER_ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
}
VARIANT_ACCESSORS = {
    ("header", "default"): "header",
    ("header", "first"): "first_page_header",
    ("header", "even"): "even_page_header",
    ("footer", "default"): "footer",
    ("footer", "first"): "first_page_footer",
    ("footer", "even"): "even_page_footer",
}


def _section_spec(
    policy: SectionsSpec | None,
    role: str | None,
) -> SectionSpec | None:
    if policy is None or role is None:
        return None
    return getattr(policy, role)


def _clear_part(part) -> None:
    for child in list(part._element):
        part._element.remove(child)
    for relationship_id in tuple(part.part.rels):
        part.part.drop_rel(relationship_id)
    part.add_paragraph()


def _apply_paragraph_border(
    paragraph,
    spec: ParagraphBorderSpec,
) -> None:
    paragraph_properties = paragraph._p.get_or_add_pPr()
    borders = paragraph_properties.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        paragraph_properties.insert_element_before(
            borders,
            "w:shd",
            "w:tabs",
            "w:snapToGrid",
            "w:spacing",
            "w:ind",
            "w:contextualSpacing",
            "w:mirrorIndents",
            "w:suppressOverlap",
            "w:jc",
        )

    bottom = borders.find(qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        borders.append(bottom)
    bottom.set(qn("w:val"), "nil" if spec.style == "none" else spec.style)
    bottom.set(qn("w:color"), spec.color)
    if spec.width is not None:
        bottom.set(qn("w:sz"), str(round(to_points(spec.width) * 8)))
    if spec.space is not None:
        bottom.set(qn("w:space"), str(round(to_points(spec.space))))


def _add_page_number(
    paragraph,
    display: PageNumberDisplaySpec,
) -> None:
    add_complex_field(
        paragraph,
        "PAGE",
        result="1",
        prefix=display.page_prefix,
        suffix=display.page_suffix,
    )
    if display.include_total:
        paragraph.add_run(display.separator)
        add_complex_field(
            paragraph,
            "NUMPAGES",
            result="1",
            prefix=display.total_prefix,
            suffix=display.total_suffix,
        )
    paragraph.alignment = PAGE_NUMBER_ALIGNMENTS[display.alignment]


def _page_number_display(
    part_name: str,
    part_spec: HeaderFooterSpec,
    variant: HeaderFooterVariantSpec,
    section_spec: SectionSpec,
    *,
    uses_default_policy: bool,
) -> PageNumberDisplaySpec | None:
    if section_spec.page_number.format == "none":
        return None
    if variant.page_number is not None:
        return variant.page_number
    if (
        part_name == "footer"
        and uses_default_policy
        and part_spec.enabled
    ):
        return section_spec.page_number.display
    return None


def _should_configure_variant(
    variant_name: str,
    variant: HeaderFooterVariantSpec,
    *,
    unlink_disabled: bool,
) -> bool:
    if variant_name != "default":
        return True
    if unlink_disabled:
        return True
    return (
        variant.enabled
        or variant.text is not None
        or variant.style is not None
        or variant.bottom_border is not None
        or variant.page_number is not None
    )


def _configure_variant(
    section,
    template: ThesisTemplate | None,
    section_spec: SectionSpec,
    part_name: str,
    variant_name: str,
    part_spec: HeaderFooterSpec,
    variant: HeaderFooterVariantSpec,
    *,
    unlink_disabled: bool,
    uses_default_policy: bool,
) -> None:
    if not _should_configure_variant(
        variant_name,
        variant,
        unlink_disabled=unlink_disabled,
    ):
        return

    part = getattr(section, VARIANT_ACCESSORS[(part_name, variant_name)])
    part.is_linked_to_previous = False
    _clear_part(part)
    paragraph = part.paragraphs[0]
    if not variant.enabled:
        return

    if variant.text:
        paragraph.add_run(variant.text)
    display = _page_number_display(
        part_name,
        part_spec,
        variant,
        section_spec,
        uses_default_policy=uses_default_policy,
    )
    if display is not None:
        if variant.text:
            paragraph.add_run(" ")
        _add_page_number(paragraph, display)
    if variant.style is not None:
        apply_paragraph_style(
            paragraph,
            variant.style,
            fallback_font=template.body.font if template is not None else None,
            fallback_size=template.body.size if template is not None else None,
        )
        if display is not None:
            paragraph.alignment = PAGE_NUMBER_ALIGNMENTS[display.alignment]
    if variant.bottom_border is not None:
        _apply_paragraph_border(paragraph, variant.bottom_border)


def _apply_page_number(section, spec: SectionSpec) -> None:
    section_properties = section._sectPr
    existing = section_properties.find(qn("w:pgNumType"))
    if spec.page_number.format == "none":
        if existing is not None:
            section_properties.remove(existing)
        return
    if existing is None:
        existing = OxmlElement("w:pgNumType")
        section_properties.insert_element_before(
            existing,
            "w:formProt",
            "w:cols",
            "w:vAlign",
            "w:noEndnote",
            "w:titlePg",
            "w:textDirection",
            "w:bidi",
            "w:rtlGutter",
            "w:docGrid",
            "w:printerSettings",
            "w:sectPrChange",
        )
    existing.set(qn("w:fmt"), PAGE_NUMBER_FORMATS[spec.page_number.format])
    if spec.page_number.restart is not None:
        existing.set(qn("w:start"), str(spec.page_number.restart))
    elif existing.get(qn("w:start")) is not None:
        del existing.attrib[qn("w:start")]


def _enable_even_and_odd_headers(document: DocumentObject) -> None:
    document.settings.odd_and_even_pages_header_footer = True


def _uses_even_variants(policy: SectionsSpec | None) -> bool:
    if policy is None:
        return False
    return any(
        spec is not None
        and (spec.header.even is not None or spec.footer.even is not None)
        for spec in (policy.cover, policy.front_matter, policy.main)
    )


def _configure_header_footer_variants(
    document: DocumentObject,
    section,
    template: ThesisTemplate | None,
    spec: SectionSpec,
    *,
    unlink_disabled: bool,
    use_even_variants: bool,
) -> None:
    use_first_variants = (
        spec.header.first is not None or spec.footer.first is not None
    )
    section.different_first_page_header_footer = use_first_variants
    if use_even_variants:
        _enable_even_and_odd_headers(document)

    for part_name, part_spec in (("header", spec.header), ("footer", spec.footer)):
        for variant_name in ("default", "first", "even"):
            variant = getattr(part_spec, variant_name)
            uses_default_policy = variant_name == "default"
            needs_default_fallback = (
                variant_name == "first" and use_first_variants
            ) or (
                variant_name == "even" and use_even_variants
            )
            if needs_default_fallback and variant is None:
                variant = part_spec.default
                uses_default_policy = True
            if variant is None:
                continue
            _configure_variant(
                section,
                template,
                spec,
                part_name,
                variant_name,
                part_spec,
                variant,
                unlink_disabled=unlink_disabled,
                uses_default_policy=uses_default_policy,
            )


def _apply_section_policy(
    document: DocumentObject,
    section,
    template: ThesisTemplate | None,
    spec: SectionSpec,
    *,
    unlink_disabled: bool,
    use_even_variants: bool,
) -> None:
    section.start_type = SECTION_STARTS[spec.start]
    _apply_page_number(section, spec)
    _configure_header_footer_variants(
        document,
        section,
        template,
        spec,
        unlink_disabled=unlink_disabled,
        use_even_variants=use_even_variants,
    )


def configure_initial_section(
    document: DocumentObject,
    template: ThesisTemplate | None,
    policy: SectionsSpec | None,
    role: str | None,
) -> None:
    spec = _section_spec(policy, role)
    if spec is not None:
        _apply_section_policy(
            document,
            document.sections[0],
            template,
            spec,
            unlink_disabled=False,
            use_even_variants=_uses_even_variants(policy),
        )


def add_section(
    document: DocumentObject,
    template: ThesisTemplate | None,
    policy: SectionsSpec | None,
    role: str,
) -> None:
    spec = _section_spec(policy, role)
    if spec is None:
        return
    section = document.add_section(SECTION_STARTS[spec.start])
    if template is not None:
        configure_section_geometry(section, template.page)
    _apply_section_policy(
        document,
        section,
        template,
        spec,
        unlink_disabled=True,
        use_even_variants=_uses_even_variants(policy),
    )
