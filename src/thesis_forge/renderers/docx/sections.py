from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from thesis_forge.templates.model import SectionSpec, SectionsSpec, ThesisTemplate

from .fields import add_complex_field

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


def _section_spec(
    policy: SectionsSpec | None,
    role: str | None,
) -> SectionSpec | None:
    if policy is None or role is None:
        return None
    return getattr(policy, role)


def _clear_paragraph(paragraph) -> None:
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def _apply_page_number(section, spec: SectionSpec) -> None:
    section_properties = section._sectPr
    existing = section_properties.find(qn("w:pgNumType"))
    if spec.page_number.format == "none":
        if existing is not None:
            section_properties.remove(existing)
        return
    if existing is None:
        existing = OxmlElement("w:pgNumType")
        section_properties.append(existing)
    existing.set(qn("w:fmt"), PAGE_NUMBER_FORMATS[spec.page_number.format])
    if spec.page_number.restart is not None:
        existing.set(qn("w:start"), str(spec.page_number.restart))
    elif existing.get(qn("w:start")) is not None:
        del existing.attrib[qn("w:start")]


def _configure_header(
    section,
    spec: SectionSpec,
    *,
    unlink_disabled: bool,
) -> None:
    if not spec.header.enabled and not unlink_disabled:
        return
    header = section.header
    header.is_linked_to_previous = False
    paragraph = header.paragraphs[0]
    _clear_paragraph(paragraph)
    if spec.header.enabled and spec.header.text:
        paragraph.add_run(spec.header.text)


def _configure_footer(
    section,
    spec: SectionSpec,
    *,
    unlink_disabled: bool,
) -> None:
    if not spec.footer.enabled and not unlink_disabled:
        return
    footer = section.footer
    footer.is_linked_to_previous = False
    paragraph = footer.paragraphs[0]
    _clear_paragraph(paragraph)
    if spec.footer.enabled and spec.footer.text:
        paragraph.add_run(spec.footer.text)
    if spec.page_number.format != "none":
        if spec.footer.enabled and spec.footer.text:
            paragraph.add_run(" ")
        add_complex_field(paragraph, "PAGE", result="1", prefix="第 ", suffix=" 页")
        paragraph.add_run(" / ")
        add_complex_field(paragraph, "NUMPAGES", result="1", prefix="共 ", suffix=" 页")


def _apply_section_policy(
    section,
    spec: SectionSpec,
    *,
    unlink_disabled: bool,
) -> None:
    section.start_type = SECTION_STARTS[spec.start]
    section.different_first_page_header_footer = (
        spec.header.different_first_page or spec.footer.different_first_page
    )
    _apply_page_number(section, spec)
    _configure_header(section, spec, unlink_disabled=unlink_disabled)
    _configure_footer(section, spec, unlink_disabled=unlink_disabled)


def configure_initial_section(
    document: DocumentObject,
    template: ThesisTemplate | None,
    policy: SectionsSpec | None,
    role: str | None,
) -> None:
    spec = _section_spec(policy, role)
    if spec is not None:
        _apply_section_policy(
            document.sections[0],
            spec,
            unlink_disabled=False,
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
        previous = document.sections[-2]
        section.orientation = previous.orientation
        section.page_width = previous.page_width
        section.page_height = previous.page_height
        section.top_margin = previous.top_margin
        section.bottom_margin = previous.bottom_margin
        section.left_margin = previous.left_margin
        section.right_margin = previous.right_margin
    _apply_section_policy(section, spec, unlink_disabled=True)
