import base64
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from docforge.core.render_plan import (
    CaptionRuns,
    CitationRun,
    FigureInstruction,
    FootnoteDefinitionInstruction,
    FootnoteReferenceRun,
    HardBreakRun,
    HyperlinkRun,
    MathRun,
    ReferenceRun,
    RenderPlan,
    SequenceInstruction,
    SoftBreakRun,
    TextRun,
)
from docforge.renderers.docx import DocxRenderer
from docforge.templates import load_template
from docforge.templates.model import FontSpec, LengthSpec

NS = {
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _xml_part(path: Path, name: str):
    with ZipFile(path) as package:
        return etree.fromstring(package.read(name))


def test_docx_renders_rich_figure_caption_runs(tmp_path: Path) -> None:
    image = tmp_path / "figure.png"
    image.write_bytes(PNG_1X1)
    template = load_template("templates/base/bachelor.yaml")
    template.figure.caption.alignment = "left"
    template.figure.caption.font = FontSpec(east_asia="黑体", latin="Arial")
    template.figure.caption.size = LengthSpec.model_validate("10pt")

    output = tmp_path / "rich-caption.docx"
    DocxRenderer().render(
        RenderPlan(
            nodes=[
                FigureInstruction(
                    source_id="fig:main",
                    src="figure.png",
                    asset_path=image,
                    caption=CaptionRuns(
                        (
                            TextRun("图题 "),
                            TextRun("粗体", bold=True),
                            TextRun("代码", code=True),
                            HyperlinkRun("链接", "https://example.test/caption"),
                            MathRun("x^2"),
                            SoftBreakRun(),
                            HardBreakRun(),
                            ReferenceRun("fig:main", "tf_fig_main", "图1-1"),
                            CitationRun(
                                keys=("smith2025",),
                                ordinals=(1,),
                                raw="[@smith2025]",
                                text="[1]",
                            ),
                            FootnoteReferenceRun("note", 1),
                        )
                    ),
                    width=None,
                    resolved_width=None,
                    chapter=1,
                    number="1-1",
                    label="图1-1",
                    bookmark="tf_fig_main",
                    sequence=SequenceInstruction(
                        name="TF_Figure_1",
                        value=1,
                        prefix="图1-",
                        suffix="",
                        result="1",
                    ),
                ),
                FootnoteDefinitionInstruction(
                    label="note",
                    footnote_id=1,
                    text="脚注",
                    inlines=(TextRun("脚注"),),
                ),
            ],
            template=template,
        ),
        output,
    )

    document_xml = _xml_part(output, "word/document.xml")
    relationships_xml = _xml_part(output, "word/_rels/document.xml.rels")
    caption = document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_fig_main']]",
        namespaces=NS,
    )[0]

    assert caption.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == ["left"]
    assert caption.xpath(
        ".//w:instrText[text()='SEQ TF_Figure_1 \\r 1 \\* ARABIC']",
        namespaces=NS,
    )
    assert caption.xpath(
        ".//w:instrText[text()='REF tf_fig_main \\h']",
        namespaces=NS,
    )
    assert caption.xpath(
        ".//w:fldChar/@w:fldCharType",
        namespaces=NS,
    ) == ["begin", "separate", "end", "begin", "separate", "end"]
    assert caption.xpath(".//w:hyperlink", namespaces=NS)
    assert caption.xpath(".//m:oMath", namespaces=NS)
    assert len(caption.xpath(".//w:br", namespaces=NS)) == 1
    assert caption.xpath(
        ".//w:footnoteReference[@w:id='1']",
        namespaces=NS,
    )

    visible_text = "".join(caption.xpath(".//w:t/text()", namespaces=NS))
    assert "图题" in visible_text
    assert "粗体" in visible_text
    assert "代码" in visible_text
    assert "链接" in visible_text
    assert "[1]" in visible_text
    assert "[@smith2025]" not in visible_text
    assert "fig:main" not in visible_text
    assert "tf_fig_main" not in visible_text

    bookmark_start = caption.xpath(
        "./w:bookmarkStart[@w:name='tf_fig_main']",
        namespaces=NS,
    )[0]
    bookmark_end = caption.xpath(
        "./w:bookmarkEnd[@w:id=$bookmark_id]",
        namespaces=NS,
        bookmark_id=bookmark_start.get(f"{{{NS['w']}}}id"),
    )[0]
    children = list(caption)
    start_index = children.index(bookmark_start)
    end_index = children.index(bookmark_end)
    bookmarked_text = "".join(
        text
        for child in children[start_index + 1 : end_index]
        for text in child.xpath(".//w:t/text()", namespaces=NS)
    )
    assert bookmarked_text == "图1-1"

    assert {"黑体", "Courier New"} <= set(
        caption.xpath(".//w:rFonts/@w:eastAsia", namespaces=NS)
    )
    assert "Arial" in set(caption.xpath(".//w:rFonts/@w:ascii", namespaces=NS))
    assert "Courier New" in set(
        caption.xpath(".//w:rFonts/@w:ascii", namespaces=NS)
    )
    assert set(caption.xpath(".//w:sz/@w:val", namespaces=NS)) == {"20"}

    hyperlink_relationships = relationships_xml.xpath(
        "./pr:Relationship[contains(@Type, '/hyperlink')]",
        namespaces=NS,
    )
    assert len(hyperlink_relationships) == 1
    assert hyperlink_relationships[0].get("Target") == "https://example.test/caption"
    assert hyperlink_relationships[0].get("TargetMode") == "External"

    footnotes_xml = _xml_part(output, "word/footnotes.xml")
    assert footnotes_xml.xpath(
        "./w:footnote[@w:id='1']//w:t[text()='脚注']",
        namespaces=NS,
    )
