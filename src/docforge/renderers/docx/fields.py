from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from docforge.core.render_plan import ReferenceRun

XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def _text_run(text: str):
    run = OxmlElement("w:r")
    value = OxmlElement("w:t")
    if text.startswith(" ") or text.endswith(" "):
        value.set(XML_SPACE, "preserve")
    value.text = text
    run.append(value)
    return run


def _field_char_run(field_type: str, *, dirty: bool = False):
    run = OxmlElement("w:r")
    field_char = OxmlElement("w:fldChar")
    field_char.set(qn("w:fldCharType"), field_type)
    if dirty:
        field_char.set(qn("w:dirty"), "true")
    run.append(field_char)
    return run


def complex_field_runs(
    instruction: str,
    *,
    result: str = "",
    prefix: str = "",
    suffix: str = "",
) -> tuple:
    runs = []
    if prefix:
        runs.append(_text_run(prefix))
    runs.append(_field_char_run("begin", dirty=True))

    instruction_run = OxmlElement("w:r")
    instruction_text = OxmlElement("w:instrText")
    instruction_text.set(XML_SPACE, "preserve")
    instruction_text.text = instruction
    instruction_run.append(instruction_text)
    runs.append(instruction_run)
    runs.append(_field_char_run("separate"))

    if result:
        runs.append(_text_run(result))
    runs.append(_field_char_run("end"))

    if suffix:
        runs.append(_text_run(suffix))
    return tuple(runs)


def add_complex_field(
    paragraph: Paragraph,
    instruction: str,
    *,
    result: str = "",
    prefix: str = "",
    suffix: str = "",
) -> None:
    paragraph._p.extend(
        complex_field_runs(
            instruction,
            result=result,
            prefix=prefix,
            suffix=suffix,
        )
    )


def reference_field_runs(reference: ReferenceRun) -> tuple:
    return complex_field_runs(
        f"REF {reference.bookmark} \\h",
        result=reference.display_text,
    )


def add_reference_field(paragraph: Paragraph, reference: ReferenceRun) -> None:
    paragraph._p.extend(reference_field_runs(reference))


def set_update_fields(document: DocumentObject) -> None:
    settings = document.settings.element
    existing = settings.find(qn("w:updateFields"))
    if existing is None:
        existing = OxmlElement("w:updateFields")
        settings.insert_element_before(
            existing,
            "w:hdrShapeDefaults",
            "w:footnotePr",
            "w:endnotePr",
            "w:compat",
            "w:docVars",
            "w:rsids",
            "m:mathPr",
            "w:attachedSchema",
            "w:themeFontLang",
            "w:clrSchemeMapping",
            "w:doNotIncludeSubdocsInStats",
            "w:doNotAutoCompressPictures",
            "w:forceUpgrade",
            "w:captions",
            "w:readModeInkLockDown",
            "w:smartTagType",
            "sl:schemaLibrary",
            "w:shapeDefaults",
            "w:doNotEmbedSmartTags",
            "w:decimalSymbol",
            "w:listSeparator",
        )
    existing.set(qn("w:val"), "true")
