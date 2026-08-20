from __future__ import annotations

from docx.document import Document as DocumentObject
from docx.opc.constants import CONTENT_TYPE as CT
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import XmlPart
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.text.paragraph import Paragraph

from thesis_forge.core.render_plan import FootnoteDefinitionInstruction, FootnoteReferenceRun

from .errors import DocxRenderError
from .fields import reference_field_runs
from .inlines import InlineHandlers, citation_run_element, render_inline_runs


def _text_run(text: str, *, bold: bool = False, code: bool = False):
    run = OxmlElement("w:r")
    if bold or code:
        properties = OxmlElement("w:rPr")
        if bold:
            properties.append(OxmlElement("w:b"))
        if code:
            fonts = OxmlElement("w:rFonts")
            fonts.set(qn("w:ascii"), "Courier New")
            fonts.set(qn("w:hAnsi"), "Courier New")
            fonts.set(qn("w:eastAsia"), "Courier New")
            properties.append(fonts)
            properties.append(OxmlElement("w:noProof"))
        run.append(properties)
    value = OxmlElement("w:t")
    if text.startswith(" ") or text.endswith(" "):
        value.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    value.text = text
    run.append(value)
    return run


def _reserved_footnote(footnote_id: int, kind: str):
    footnote = OxmlElement("w:footnote")
    footnote.set(qn("w:id"), str(footnote_id))
    footnote.set(qn("w:type"), kind)
    paragraph = OxmlElement("w:p")
    run = OxmlElement("w:r")
    run.append(OxmlElement(f"w:{kind}"))
    paragraph.append(run)
    footnote.append(paragraph)
    return footnote


class FootnoteManager:
    def __init__(
        self,
        document: DocumentObject,
        *,
        citation_superscript: bool = False,
    ):
        self.document = document
        self.citation_superscript = citation_superscript
        self.definitions: dict[int, FootnoteDefinitionInstruction] = {}

    def add_reference(self, paragraph: Paragraph, reference: FootnoteReferenceRun) -> None:
        run = paragraph.add_run()
        properties = run._r.get_or_add_rPr()
        style = OxmlElement("w:rStyle")
        style.set(qn("w:val"), "FootnoteReference")
        properties.append(style)
        element = OxmlElement("w:footnoteReference")
        element.set(qn("w:id"), str(reference.footnote_id))
        run._r.append(element)

    def add_definition(self, definition: FootnoteDefinitionInstruction) -> None:
        self.definitions[definition.footnote_id] = definition

    def attach(self) -> None:
        if not self.definitions:
            return

        root = parse_xml(f"<w:footnotes {nsdecls('w')}/>")
        root.append(_reserved_footnote(-1, "separator"))
        root.append(_reserved_footnote(0, "continuationSeparator"))
        for footnote_id in sorted(self.definitions):
            root.append(self._definition_element(self.definitions[footnote_id]))

        part = XmlPart(
            PackURI("/word/footnotes.xml"),
            CT.WML_FOOTNOTES,
            root,
            self.document.part.package,
        )
        self.document.part.relate_to(part, RT.FOOTNOTES)

    def _definition_element(self, definition: FootnoteDefinitionInstruction):
        footnote = OxmlElement("w:footnote")
        footnote.set(qn("w:id"), str(definition.footnote_id))
        paragraph = OxmlElement("w:p")
        marker_run = OxmlElement("w:r")
        marker_run.append(OxmlElement("w:footnoteRef"))
        paragraph.append(marker_run)
        paragraph.append(_text_run(" "))
        render_inline_runs(
            definition.inlines,
            InlineHandlers(
                text=lambda item: paragraph.append(
                    _text_run(item.text, bold=item.bold, code=item.code)
                ),
                reference=lambda item: paragraph.extend(reference_field_runs(item)),
                citation=lambda item: paragraph.append(
                    citation_run_element(
                        item,
                        superscript=self.citation_superscript,
                    )
                ),
                footnote_reference=lambda item: self._reject_nested_reference(
                    item.label
                ),
            ),
            capability="footnote",
        )
        footnote.append(paragraph)
        return footnote

    @staticmethod
    def _reject_nested_reference(label: str) -> None:
        raise DocxRenderError(
            "footnote",
            f"nested footnote reference is unsupported: {label}",
        )
