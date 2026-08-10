from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from thesis_forge.templates.model import (
    OrderedListLevelSpec,
    OrderedListSpec,
    UnorderedListLevelSpec,
    UnorderedListSpec,
)

from .units import to_docx_length

WORD_NUMBER_FORMATS = {
    "decimal": "decimal",
    "lower_letter": "lowerLetter",
    "upper_letter": "upperLetter",
    "lower_roman": "lowerRoman",
    "upper_roman": "upperRoman",
}

ListPolicy = OrderedListSpec | UnorderedListSpec
ListLevelSpec = OrderedListLevelSpec | UnorderedListLevelSpec


def _next_abstract_id(parent) -> int:
    values = [
        int(element.get(qn("w:abstractNumId")))
        for element in parent.findall(qn("w:abstractNum"))
        if element.get(qn("w:abstractNumId")) is not None
    ]
    return max(values, default=0) + 1


def resolve_list_level(
    policy: ListPolicy,
    level: int,
) -> tuple[int, ListLevelSpec]:
    word_level = max(0, min(level, 8))
    return word_level, policy.for_level(word_level)


def _level_element(
    level: int,
    *,
    spec: ListLevelSpec,
    start: int,
) -> OxmlElement:
    level_element = OxmlElement("w:lvl")
    level_element.set(qn("w:ilvl"), str(level))

    start_element = OxmlElement("w:start")
    start_element.set(qn("w:val"), str(start))
    level_element.append(start_element)

    format_element = OxmlElement("w:numFmt")
    format_element.set(
        qn("w:val"),
        WORD_NUMBER_FORMATS[spec.format]
        if isinstance(spec, OrderedListLevelSpec)
        else "bullet",
    )
    level_element.append(format_element)

    text_element = OxmlElement("w:lvlText")
    text_element.set(
        qn("w:val"),
        (
            f"{spec.prefix}%{level + 1}{spec.suffix}"
            if isinstance(spec, OrderedListLevelSpec)
            else spec.marker
        ),
    )
    level_element.append(text_element)

    justification = OxmlElement("w:lvlJc")
    justification.set(qn("w:val"), spec.alignment)
    level_element.append(justification)

    paragraph_properties = OxmlElement("w:pPr")
    indentation = OxmlElement("w:ind")
    indentation.set(qn("w:left"), str(to_docx_length(spec.left_indent).twips))
    indentation.set(
        qn("w:hanging"),
        str(to_docx_length(spec.hanging_indent).twips),
    )
    paragraph_properties.append(indentation)
    level_element.append(paragraph_properties)
    return level_element


def create_list_numbering(
    document: DocumentObject,
    *,
    policy: ListPolicy,
    start: int = 1,
) -> int:
    numbering = document.part.numbering_part.element
    abstract_id = _next_abstract_id(numbering)

    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    multi_level_type = OxmlElement("w:multiLevelType")
    multi_level_type.set(qn("w:val"), "multilevel")
    abstract.append(multi_level_type)
    for level in range(9):
        _, level_spec = resolve_list_level(policy, level)
        abstract.append(
            _level_element(
                level,
                spec=level_spec,
                start=(
                    start
                    if isinstance(policy, OrderedListSpec) and level == 0
                    else 1
                ),
            )
        )
    first_number = numbering.find(qn("w:num"))
    if first_number is None:
        numbering.append(abstract)
    else:
        first_number.addprevious(abstract)

    number = numbering.add_num(abstract_id)
    return number.numId


def apply_list_numbering(paragraph: Paragraph, *, number_id: int, level: int) -> None:
    paragraph_properties = paragraph._p.get_or_add_pPr()
    number_properties = paragraph_properties.get_or_add_numPr()
    level_element = number_properties.get_or_add_ilvl()
    level_element.set(qn("w:val"), str(max(0, min(level, 8))))
    number_element = number_properties.get_or_add_numId()
    number_element.set(qn("w:val"), str(number_id))
