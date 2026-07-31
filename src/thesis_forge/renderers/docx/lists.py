from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

BULLETS = ("•", "◦", "▪")


def _next_id(parent, child_tag: str, attribute: str) -> int:
    values = [
        int(element.get(qn(attribute)))
        for element in parent.findall(qn(child_tag))
        if element.get(qn(attribute)) is not None
    ]
    return max(values, default=0) + 1


def _level_element(level: int, *, ordered: bool, start: int) -> OxmlElement:
    level_element = OxmlElement("w:lvl")
    level_element.set(qn("w:ilvl"), str(level))

    start_element = OxmlElement("w:start")
    start_element.set(qn("w:val"), str(start))
    level_element.append(start_element)

    format_element = OxmlElement("w:numFmt")
    format_element.set(qn("w:val"), "decimal" if ordered else "bullet")
    level_element.append(format_element)

    text_element = OxmlElement("w:lvlText")
    text_element.set(
        qn("w:val"),
        f"%{level + 1}." if ordered else BULLETS[level % len(BULLETS)],
    )
    level_element.append(text_element)

    justification = OxmlElement("w:lvlJc")
    justification.set(qn("w:val"), "left")
    level_element.append(justification)

    paragraph_properties = OxmlElement("w:pPr")
    indentation = OxmlElement("w:ind")
    indentation.set(qn("w:left"), str(720 * (level + 1)))
    indentation.set(qn("w:hanging"), "360")
    paragraph_properties.append(indentation)
    level_element.append(paragraph_properties)
    return level_element


def create_list_numbering(
    document: DocumentObject,
    *,
    ordered: bool,
    start: int = 1,
) -> int:
    numbering = document.part.numbering_part.element
    abstract_id = _next_id(numbering, "w:abstractNum", "w:abstractNumId")
    number_id = _next_id(numbering, "w:num", "w:numId")

    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    multi_level_type = OxmlElement("w:multiLevelType")
    multi_level_type.set(qn("w:val"), "multilevel")
    abstract.append(multi_level_type)
    for level in range(9):
        abstract.append(
            _level_element(
                level,
                ordered=ordered,
                start=start if ordered and level == 0 else 1,
            )
        )
    first_number = numbering.find(qn("w:num"))
    if first_number is None:
        numbering.append(abstract)
    else:
        first_number.addprevious(abstract)

    number = OxmlElement("w:num")
    number.set(qn("w:numId"), str(number_id))
    abstract_reference = OxmlElement("w:abstractNumId")
    abstract_reference.set(qn("w:val"), str(abstract_id))
    number.append(abstract_reference)
    numbering.append(number)
    return number_id


def apply_list_numbering(paragraph: Paragraph, *, number_id: int, level: int) -> None:
    paragraph_properties = paragraph._p.get_or_add_pPr()
    number_properties = paragraph_properties.get_or_add_numPr()
    level_element = number_properties.get_or_add_ilvl()
    level_element.set(qn("w:val"), str(max(0, min(level, 8))))
    number_element = number_properties.get_or_add_numId()
    number_element.set(qn("w:val"), str(number_id))
