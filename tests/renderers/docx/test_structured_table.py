from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import (
    Citation,
    CrossReference,
    Emphasis,
    FootnoteDefinition,
    FootnoteReference,
    ForgeDocument,
    HardBreak,
    Heading,
    InlineCode,
    InlineMath,
    Link,
    SoftBreak,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
)
from thesis_forge.renderers.docx import DocxRenderer
from thesis_forge.templates import load_template

NS = {
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}


def _xml_part(path: Path, name: str):
    with ZipFile(path) as package:
        return etree.fromstring(package.read(name))


def test_docx_structured_table_renders_typed_cells_and_capability_evidence(
    tmp_path: Path,
) -> None:
    template = load_template("templates/base/bachelor.yaml")
    template.table.caption.alignment = "right"
    document = ForgeDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Heading(id="sec:target", level=1, inlines=[Text(value="Target")]),
            FootnoteDefinition(label="note", inlines=[Text(value="Footnote")]),
            Table(
                id="tbl:rich",
                caption_inlines=(Text(value="Rich table"),),
                rows=(
                    TableRow(
                        header=True,
                        cells=(
                            TableCell(
                                inlines=(Text(value="Content"),),
                                alignment="left",
                            ),
                            TableCell(
                                inlines=(Text(value="Value"),),
                                alignment="right",
                            ),
                        ),
                    ),
                    TableRow(
                        cells=(
                            TableCell(
                                inlines=(
                                    Text(value="text"),
                                    Strong(children=(Text(value="strong"),)),
                                    Emphasis(children=(Text(value="emphasis"),)),
                                    InlineCode(value="code"),
                                    Link(
                                        label="link",
                                        destination="https://example.test/table",
                                    ),
                                    InlineMath(latex="x^2"),
                                    SoftBreak(),
                                    HardBreak(),
                                    CrossReference(target="sec:target"),
                                    Citation(keys=["smith2025"], raw="[@smith2025]"),
                                    FootnoteReference(label="note"),
                                )
                            ),
                            TableCell(
                                inlines=(Text(value="0.94"),),
                                alignment="right",
                            ),
                        ),
                    ),
                ),
            ),
        ],
    )
    output = tmp_path / "structured-table.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    document_xml = _xml_part(output, "word/document.xml")
    relationships_xml = _xml_part(output, "word/_rels/document.xml.rels")
    footnotes_xml = _xml_part(output, "word/footnotes.xml")

    table = document_xml.xpath(".//w:tbl", namespaces=NS)[0]
    assert table.xpath(".//w:tr[1]/w:tc//w:t/text()", namespaces=NS) == [
        "Content",
        "Value",
    ]
    assert table.xpath(".//w:tr[2]/w:tc[2]//w:t/text()", namespaces=NS) == [
        "0.94"
    ]
    assert table.xpath(
        ".//w:tr[1]/w:tc[1]/w:p/w:pPr/w:jc/@w:val",
        namespaces=NS,
    ) == ["left"]
    assert table.xpath(
        ".//w:tr[1]/w:tc[2]/w:p/w:pPr/w:jc/@w:val",
        namespaces=NS,
    ) == ["right"]

    caption = document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_tbl_rich']]",
        namespaces=NS,
    )[0]
    assert caption.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == ["right"]
    assert "".join(caption.xpath(".//w:t/text()", namespaces=NS)) == "表1-1 Rich table"
    assert caption.xpath(".//w:instrText/text()", namespaces=NS) == [
        "SEQ TF_Table_1 \\r 1 \\* ARABIC"
    ]

    assert table.xpath(".//w:r/w:rPr/w:b", namespaces=NS)
    assert table.xpath(".//w:rFonts[@w:ascii='Courier New']", namespaces=NS)
    assert table.xpath(".//w:hyperlink", namespaces=NS)
    assert table.xpath(".//m:oMath", namespaces=NS)
    assert table.xpath(".//w:t[text()=' ']", namespaces=NS)
    assert table.xpath(".//w:br", namespaces=NS)
    assert table.xpath(
        ".//w:instrText[text()='REF tf_sec_target \\h']",
        namespaces=NS,
    )
    assert table.xpath(".//w:t[text()='[1]']", namespaces=NS)
    assert table.xpath(".//w:footnoteReference[@w:id='1']", namespaces=NS)
    visible_text = "".join(table.xpath(".//w:t/text()", namespaces=NS))
    assert "[@smith2025]" not in visible_text
    assert "sec:target" not in visible_text

    hyperlink_relationships = relationships_xml.xpath(
        "./pr:Relationship[contains(@Type, '/hyperlink')]",
        namespaces=NS,
    )
    assert len(hyperlink_relationships) == 1
    assert hyperlink_relationships[0].get("Target") == "https://example.test/table"
    assert hyperlink_relationships[0].get("TargetMode") == "External"
    assert footnotes_xml.xpath("./w:footnote[@w:id='1']", namespaces=NS)

    borders = table.xpath("./w:tblPr/w:tblBorders", namespaces=NS)[0]
    assert borders.xpath("./w:top/@w:val", namespaces=NS) == ["single"]
    assert borders.xpath("./w:bottom/@w:val", namespaces=NS) == ["single"]
