import base64
from pathlib import Path

import pytest
from lxml import etree

import thesis_forge.renderers.docx.fields as fields_module
import thesis_forge.renderers.docx.renderer as renderer_module
from thesis_forge.bibliography import Gbt7714Formatter, LocalBibTeXLoader
from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import (
    Algorithm,
    BibliographyBlock,
    Citation,
    CrossReference,
    Equation,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    Heading,
    ListBlock,
    Listing,
    ListItem,
    Paragraph,
    Table,
    Text,
    ThesisDocument,
)
from thesis_forge.core.render_plan import ReferenceRun
from thesis_forge.renderers.docx import DocxRenderer
from thesis_forge.renderers.docx.errors import DocxRenderError
from thesis_forge.renderers.docx.package import list_package_parts, read_package_part
from thesis_forge.templates import FontSpec, LengthSpec, SectionsSpec, load_template

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
REL_NS = {"pr": "http://schemas.openxmlformats.org/package/2006/relationships"}
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _xml_part(path: Path, name: str):
    return etree.fromstring(read_package_part(path, name))


def test_docx_renderer_applies_template_page_body_and_heading_xml(tmp_path: Path):
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Heading(id="chap:intro", level=1, text="绪论", inlines=[Text(value="绪论")]),
            Paragraph(text="正文段落", inlines=[Text(value="正文段落")]),
        ],
    )
    template = load_template("templates/schools/example-university/2026.yaml")
    plan = compile_document(document, template=template)
    output = tmp_path / "thesis.docx"

    DocxRenderer().render(plan, output)

    document_xml = _xml_part(output, "word/document.xml")
    styles_xml = _xml_part(output, "word/styles.xml")
    section = document_xml.find(".//w:sectPr", NS)
    assert section is not None
    page_size = section.find("w:pgSz", NS)
    margins = section.find("w:pgMar", NS)
    assert page_size is not None
    assert page_size.get(f"{{{NS['w']}}}w") == "11906"
    assert page_size.get(f"{{{NS['w']}}}h") == "16838"
    assert margins is not None
    assert margins.get(f"{{{NS['w']}}}left") == "1701"
    assert margins.get(f"{{{NS['w']}}}right") == "1417"

    normal = styles_xml.xpath(".//w:style[@w:styleId='Normal']", namespaces=NS)[0]
    assert normal.xpath("./w:rPr/w:rFonts/@w:eastAsia", namespaces=NS) == ["宋体"]
    assert normal.xpath("./w:rPr/w:rFonts/@w:ascii", namespaces=NS) == ["Times New Roman"]
    assert normal.xpath("./w:rPr/w:sz/@w:val", namespaces=NS) == ["24"]
    assert normal.xpath("./w:pPr/w:ind/@w:firstLine", namespaces=NS) == ["480"]
    assert normal.xpath("./w:pPr/w:spacing/@w:line", namespaces=NS) == ["400"]
    assert normal.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == ["both"]

    heading = styles_xml.xpath(".//w:style[@w:styleId='Heading1']", namespaces=NS)[0]
    assert heading.xpath("./w:rPr/w:rFonts/@w:eastAsia", namespaces=NS) == ["黑体"]
    assert heading.xpath("./w:rPr/w:b", namespaces=NS)
    assert heading.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == ["center"]
    assert "[TODO:" not in etree.tostring(document_xml, encoding="unicode")
    assert "word/document.xml" in list_package_parts(output)


def test_docx_renderer_applies_landscape_orientation(tmp_path: Path):
    template = load_template("templates/base/bachelor.yaml")
    template.page.orientation = "landscape"
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[Paragraph(text="正文", inlines=[Text(value="正文")])],
    )
    output = tmp_path / "landscape.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    document_xml = _xml_part(output, "word/document.xml")
    page_size = document_xml.find(".//w:sectPr/w:pgSz", NS)
    assert page_size is not None
    assert page_size.get(f"{{{NS['w']}}}orient") == "landscape"
    assert page_size.get(f"{{{NS['w']}}}w") == "16838"
    assert page_size.get(f"{{{NS['w']}}}h") == "11906"


def test_docx_renderer_writes_metadata_cover_before_front_matter(tmp_path: Path):
    template = load_template("templates/schools/example-university/2026.yaml")
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        metadata={
            "university": {"name": "XX大学", "college": "计算机学院"},
            "thesis": {
                "title": "结构化论文编译",
                "title_en": "Structured Thesis Compilation",
                "major": "计算机科学与技术",
                "degree": "工学学士",
            },
            "author": {"name": "张三", "student_id": "2022000001"},
            "advisor": {"name": "李老师", "title": "副教授"},
            "dates": {"completed": "2026-06"},
        },
        blocks=[
            Heading(id="chap:abstract-zh", level=1, text="摘要"),
            Heading(id="chap:introduction", level=1, text="绪论"),
        ],
    )
    output = tmp_path / "cover.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    document_xml = _xml_part(output, "word/document.xml")
    body_text = "".join(document_xml.xpath(".//w:body//w:t/text()", namespaces=NS))
    assert body_text.startswith(
        "XX大学计算机学院结构化论文编译Structured Thesis Compilation"
    )
    for value in (
        "计算机科学与技术",
        "工学学士",
        "张三",
        "2022000001",
        "李老师",
        "副教授",
        "2026-06",
        "摘要",
        "目录",
        "绪论",
    ):
        assert value in body_text
    assert len(document_xml.xpath(".//w:sectPr", namespaces=NS)) == 3
    assert document_xml.xpath(".//w:headerReference", namespaces=NS)
    assert document_xml.xpath(".//w:footerReference", namespaces=NS)


def test_docx_renderer_bookmarks_listing_and_algorithm_objects(tmp_path: Path):
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Listing(
                id="lst:service",
                caption="构建服务",
                language="python",
                code="build_service(source, output)",
            ),
            Algorithm(
                id="alg:build",
                caption="安全构建",
                body="1. validate\n2. render\n3. replace",
            ),
        ],
    )
    output = tmp_path / "listing-algorithm.docx"

    DocxRenderer().render(
        compile_document(
            document,
            template=load_template("templates/base/bachelor.yaml"),
        ),
        output,
    )

    document_xml = _xml_part(output, "word/document.xml")
    bookmark_starts = {
        node.get(f"{{{NS['w']}}}id"): node.get(f"{{{NS['w']}}}name")
        for node in document_xml.xpath(".//w:bookmarkStart", namespaces=NS)
    }
    bookmark_ends = set(
        document_xml.xpath(".//w:bookmarkEnd/@w:id", namespaces=NS)
    )
    assert {"tf_lst_service", "tf_alg_build"} <= set(bookmark_starts.values())
    assert set(bookmark_starts) <= bookmark_ends
    assert document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_lst_service']]//w:t[text()='构建服务']",
        namespaces=NS,
    )
    assert document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_alg_build']]//w:t[text()='安全构建']",
        namespaces=NS,
    )
    for body_text in ("build_service(source, output)", "1. validate"):
        body_paragraph = document_xml.xpath(
            f".//w:p[.//w:t[contains(., '{body_text}')]]",
            namespaces=NS,
        )[0]
        assert body_paragraph.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == ["left"]
        assert body_paragraph.xpath(
            "./w:pPr/w:spacing/@w:lineRule",
            namespaces=NS,
        ) == ["auto"]
        assert body_paragraph.xpath(
            "./w:pPr/w:spacing/@w:line",
            namespaces=NS,
        ) == ["240"]


def test_docx_renderer_preserves_list_start_and_nesting_xml(tmp_path: Path):
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            ListBlock(
                ordered=True,
                start=3,
                items=[
                    ListItem(text="第三项", level=0, ordinal=3, inlines=[Text(value="第三项")]),
                    ListItem(text="子项", level=1, ordinal=1, inlines=[Text(value="子项")]),
                    ListItem(text="第四项", level=0, ordinal=4, inlines=[Text(value="第四项")]),
                ],
            )
        ],
    )
    output = tmp_path / "list.docx"

    DocxRenderer().render(
        compile_document(document, template=load_template("templates/base/bachelor.yaml")),
        output,
    )

    document_xml = _xml_part(output, "word/document.xml")
    numbering_xml = _xml_part(output, "word/numbering.xml")
    assert document_xml.xpath(".//w:p/w:pPr/w:numPr/w:ilvl/@w:val", namespaces=NS) == [
        "0",
        "1",
        "0",
    ]
    assert len(document_xml.xpath(".//w:p/w:pPr/w:numPr/w:numId", namespaces=NS)) == 3
    assert "3" in numbering_xml.xpath(
        ".//w:abstractNum/w:lvl[@w:ilvl='0']/w:start/@w:val",
        namespaces=NS,
    )
    assert numbering_xml.xpath(
        ".//w:abstractNum/w:lvl/w:numFmt/@w:val",
        namespaces=NS,
    )
    children = [etree.QName(child).localname for child in numbering_xml]
    assert max(index for index, name in enumerate(children) if name == "abstractNum") < min(
        index for index, name in enumerate(children) if name == "num"
    )
    abstract_ids = set(
        numbering_xml.xpath("./w:abstractNum/@w:abstractNumId", namespaces=NS)
    )
    referenced_ids = set(
        numbering_xml.xpath("./w:num/w:abstractNumId/@w:val", namespaces=NS)
    )
    assert referenced_ids <= abstract_ids


def test_docx_renderer_creates_real_figures_captions_bookmarks_and_three_line_table(
    tmp_path: Path,
):
    images = tmp_path / "images"
    images.mkdir()
    (images / "model.png").write_bytes(PNG_1X1)
    template = load_template("templates/base/bachelor.yaml")
    template.figure.default_width = LengthSpec.model_validate("40mm")
    template.figure.caption.alignment = "left"
    template.figure.caption.font = FontSpec(east_asia="黑体", latin="Arial")
    template.figure.caption.size = LengthSpec.model_validate("10pt")
    template.table.caption.alignment = "right"
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Heading(id="chap:intro", level=1, text="绪论", inlines=[Text(value="绪论")]),
            Figure(
                id="fig:model",
                src="./images/model.png",
                caption="系统模型",
                width="50%",
            ),
            Figure(
                id="fig:default",
                src="./images/model.png",
                caption="默认宽度",
            ),
            Table(
                id="tbl:results",
                caption="实验结果",
                markdown="| 模型 | AUROC |\n| --- | ---: |\n| A | 0.91 |\n| B | 0.94 |",
            ),
        ],
    )
    output = tmp_path / "figures-tables.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    document_xml = _xml_part(output, "word/document.xml")
    relationships_xml = _xml_part(output, "word/_rels/document.xml.rels")
    package_parts = list_package_parts(output)
    image_relationships = relationships_xml.xpath(
        "./pr:Relationship[contains(@Type, '/image')]",
        namespaces=REL_NS,
    )
    assert image_relationships
    assert any(part.startswith("word/media/") for part in package_parts)
    assert len(document_xml.xpath(".//w:drawing", namespaces=NS)) == 2
    assert document_xml.xpath(".//wp:extent/@cx", namespaces=NS) == [
        "2790190",
        "1440000",
    ]
    for drawing_paragraph in document_xml.xpath(".//w:p[.//w:drawing]", namespaces=NS):
        assert drawing_paragraph.xpath(
            "./w:pPr/w:spacing/@w:lineRule",
            namespaces=NS,
        ) == ["auto"]
        assert drawing_paragraph.xpath(
            "./w:pPr/w:spacing/@w:line",
            namespaces=NS,
        ) == ["240"]
    assert document_xml.xpath(".//a:blip/@r:embed", namespaces=NS)

    bookmark_names = document_xml.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
    assert {"tf_fig_model", "tf_fig_default", "tf_tbl_results"} <= set(bookmark_names)
    bookmark_starts = {
        node.get(f"{{{NS['w']}}}id"): node.get(f"{{{NS['w']}}}name")
        for node in document_xml.xpath(".//w:bookmarkStart", namespaces=NS)
    }
    bookmark_ends = set(document_xml.xpath(".//w:bookmarkEnd/@w:id", namespaces=NS))
    assert set(bookmark_starts) <= bookmark_ends

    body = document_xml.find(".//w:body", namespaces=NS)
    assert body is not None
    body_children = list(body)
    drawing_indices = [
        index
        for index, child in enumerate(body_children)
        if child.xpath(".//w:drawing", namespaces=NS)
    ]
    paragraph_text = {
        index: "".join(child.xpath(".//w:t/text()", namespaces=NS))
        for index, child in enumerate(body_children)
        if etree.QName(child).localname == "p"
    }
    assert paragraph_text[drawing_indices[0] + 1] == "图1-1 系统模型"
    assert paragraph_text[drawing_indices[1] + 1] == "图1-2 默认宽度"
    table_index = next(
        index
        for index, child in enumerate(body_children)
        if etree.QName(child).localname == "tbl"
    )
    assert paragraph_text[table_index - 1] == "表1-1 实验结果"

    figure_caption = document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_fig_model']]",
        namespaces=NS,
    )[0]
    assert figure_caption.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == ["left"]
    assert set(
        figure_caption.xpath(".//w:rFonts/@w:eastAsia", namespaces=NS)
    ) == {"黑体"}
    assert set(figure_caption.xpath(".//w:rFonts/@w:ascii", namespaces=NS)) == {
        "Arial"
    }
    assert set(figure_caption.xpath(".//w:sz/@w:val", namespaces=NS)) == {"20"}
    table_caption = document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_tbl_results']]",
        namespaces=NS,
    )[0]
    assert table_caption.xpath("./w:pPr/w:jc/@w:val", namespaces=NS) == ["right"]

    table = document_xml.xpath(".//w:tbl", namespaces=NS)[0]
    assert table.xpath(".//w:tr[1]/w:tc//w:t/text()", namespaces=NS) == ["模型", "AUROC"]
    assert table.xpath(".//w:tr[2]/w:tc//w:t/text()", namespaces=NS) == ["A", "0.91"]
    borders = table.xpath("./w:tblPr/w:tblBorders", namespaces=NS)[0]
    assert borders.xpath("./w:top/@w:val", namespaces=NS) == ["single"]
    assert borders.xpath("./w:bottom/@w:val", namespaces=NS) == ["single"]
    for edge in ("left", "right", "insideH", "insideV"):
        assert borders.xpath(f"./w:{edge}/@w:val", namespaces=NS) == ["nil"]
    assert table.xpath(
        ".//w:tr[1]/w:tc/w:tcPr/w:tcBorders/w:bottom/@w:val",
        namespaces=NS,
    ) == ["single", "single"]


def test_docx_renderer_honors_non_default_caption_positions(tmp_path: Path):
    images = tmp_path / "images"
    images.mkdir()
    (images / "model.png").write_bytes(PNG_1X1)
    template = load_template("templates/base/bachelor.yaml")
    template.figure.caption.position = "top"
    template.table.caption.position = "bottom"
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Figure(id="fig:model", src="./images/model.png", caption="系统模型"),
            Table(
                id="tbl:results",
                caption="实验结果",
                markdown="| 模型 | AUROC |\n| --- | ---: |\n| A | 0.91 |",
            ),
        ],
    )
    output = tmp_path / "caption-positions.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    document_xml = _xml_part(output, "word/document.xml")
    body = document_xml.find(".//w:body", namespaces=NS)
    assert body is not None
    children = [
        (
            etree.QName(child).localname,
            "".join(child.xpath(".//w:t/text()", namespaces=NS)),
            bool(child.xpath(".//w:drawing", namespaces=NS)),
        )
        for child in body
        if etree.QName(child).localname != "sectPr"
    ]
    assert children == [
        ("p", "图1-1 系统模型", False),
        ("p", "", True),
        ("tbl", "模型AUROCA0.91", False),
        ("p", "表1-1 实验结果", False),
    ]


def test_docx_renderer_preserves_intrinsic_image_size_without_width_policy(
    tmp_path: Path,
):
    image = tmp_path / "model.png"
    image.write_bytes(PNG_1X1)
    template = load_template("templates/base/bachelor.yaml")
    template.figure.default_width = None
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[Figure(id="fig:model", src="./model.png", caption="系统模型")],
    )
    output = tmp_path / "intrinsic-width.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    document_xml = _xml_part(output, "word/document.xml")
    assert document_xml.xpath(".//wp:extent/@cx", namespaces=NS) == ["12700"]


@pytest.mark.parametrize(
    ("style", "expected"),
    [
        ("grid", "single"),
        ("plain", "nil"),
    ],
)
def test_docx_renderer_applies_non_three_line_table_border_policies(
    tmp_path: Path,
    style: str,
    expected: str,
):
    template = load_template("templates/base/bachelor.yaml")
    template.table.style = style
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Table(
                id="tbl:results",
                caption="实验结果",
                markdown="| 模型 | AUROC |\n| --- | ---: |\n| A | 0.91 |",
            )
        ],
    )
    output = tmp_path / f"{style}.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    document_xml = _xml_part(output, "word/document.xml")
    table = document_xml.xpath(".//w:tbl", namespaces=NS)[0]
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        assert table.xpath(
            f"./w:tblPr/w:tblBorders/w:{edge}/@w:val",
            namespaces=NS,
        ) == [expected]
    assert not table.xpath(".//w:tcBorders", namespaces=NS)


def test_docx_renderer_does_not_create_fake_table_for_empty_rows(tmp_path: Path):
    template = load_template("templates/base/bachelor.yaml")
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[Table(id="tbl:empty", caption="空表", markdown="")],
    )
    output = tmp_path / "empty-table.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    document_xml = _xml_part(output, "word/document.xml")
    assert not document_xml.xpath(".//w:tbl", namespaces=NS)
    assert "".join(
        document_xml.xpath(
            ".//w:p[.//w:bookmarkStart[@w:name='tf_tbl_empty']]//w:t/text()",
            namespaces=NS,
        )
    ) == "表1-1 空表"


def test_docx_renderer_creates_real_math_fields_footnotes_and_page_structures(
    tmp_path: Path,
):
    image = tmp_path / "model.png"
    image.write_bytes(PNG_1X1)
    template = load_template("templates/base/bachelor.yaml")
    template.sections = SectionsSpec.model_validate(
        {
            "cover": {
                "start": "new_page",
                "page_number": {"format": "none"},
            },
            "front_matter": {
                "start": "new_page",
                "footer": {"enabled": True},
                "page_number": {"format": "roman-lower"},
            },
            "main": {
                "start": "odd_page",
                "header": {
                    "enabled": True,
                    "text": "基于结构化 Markdown 的论文",
                    "different_first_page": True,
                },
                "footer": {"enabled": True},
                "page_number": {"format": "decimal", "restart": 1},
            },
        }
    )
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Heading(id="chap:abstract-zh", level=1, text="摘要"),
            Paragraph(text="摘要正文", inlines=[Text(value="摘要正文")]),
            Heading(id="chap:introduction", level=1, text="绪论"),
            Figure(id="fig:model", src="./model.png", caption="系统模型"),
            Table(
                id="tbl:data",
                caption="实验数据",
                markdown="| 模型 | 值 |\n| --- | ---: |\n| A | 1 |",
            ),
            Equation(
                id="eq:loss",
                latex=r"L=-\sum_{i=1}^n y_i \log \hat{y}_i+x_i^2",
            ),
            Paragraph(
                text="参见图和公式并带脚注",
                inlines=[
                    Text(value="参见"),
                    CrossReference(target="fig:model"),
                    Text(value="与"),
                    CrossReference(target="eq:loss"),
                    FootnoteReference(label="note"),
                ],
            ),
            FootnoteDefinition(
                label="note",
                text="真实脚注正文，参见图",
                inlines=[
                    Text(value="真实脚注正文，参见"),
                    CrossReference(target="fig:model"),
                ],
            ),
        ],
    )
    output = tmp_path / "advanced.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    package_parts = list_package_parts(output)
    document_xml = _xml_part(output, "word/document.xml")
    settings_xml = _xml_part(output, "word/settings.xml")
    relationships_xml = _xml_part(output, "word/_rels/document.xml.rels")
    content_types_xml = _xml_part(output, "[Content_Types].xml")

    assert document_xml.xpath(".//m:oMath", namespaces=NS)
    assert document_xml.xpath(".//m:nary", namespaces=NS)
    assert document_xml.xpath(".//m:func", namespaces=NS)
    assert document_xml.xpath(".//m:acc", namespaces=NS)
    assert document_xml.xpath(".//m:sSubSup", namespaces=NS)
    assert document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_eq_loss']]//m:oMath",
        namespaces=NS,
    )
    equation_paragraph = document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_eq_loss']]",
        namespaces=NS,
    )[0]
    equation_children = list(equation_paragraph)
    equation_math = next(
        index
        for index, child in enumerate(equation_children)
        if etree.QName(child).localname == "oMath"
    )
    equation_start = next(
        index
        for index, child in enumerate(equation_children)
        if etree.QName(child).localname == "bookmarkStart"
    )
    equation_end = next(
        index
        for index, child in enumerate(equation_children)
        if etree.QName(child).localname == "bookmarkEnd"
    )
    assert equation_math < equation_start < equation_end
    assert "".join(
        text
        for child in equation_children[equation_start + 1 : equation_end]
        for text in child.xpath(".//w:t/text()", namespaces=NS)
    ) == "(1-1)"
    equation_bookmark_id = equation_children[equation_start].get(f"{{{NS['w']}}}id")
    assert equation_children[equation_end].get(f"{{{NS['w']}}}id") == equation_bookmark_id
    field_codes = [
        "".join(node.itertext()).strip()
        for node in document_xml.xpath(".//w:instrText", namespaces=NS)
    ]
    assert any(code.startswith("SEQ TF_Figure_1") for code in field_codes)
    assert any(code.startswith("SEQ TF_Table_1") for code in field_codes)
    assert any(code.startswith("SEQ TF_Equation_1") for code in field_codes)
    assert "REF tf_fig_model \\h" in field_codes
    assert "REF tf_eq_loss \\h" in field_codes
    assert 'TOC \\o "1-3" \\h \\z \\u' in field_codes
    field_types = document_xml.xpath(".//w:fldChar/@w:fldCharType", namespaces=NS)
    assert field_types.count("begin") == field_types.count("separate")
    assert field_types.count("begin") == field_types.count("end")
    assert settings_xml.xpath("./w:updateFields/@w:val", namespaces=NS) == ["true"]
    for instruction_text in document_xml.xpath(".//w:instrText", namespaces=NS):
        run = instruction_text.getparent()
        paragraph = run.getparent()
        runs = list(paragraph)
        instruction_index = runs.index(run)
        begin = runs[instruction_index - 1].find("w:fldChar", namespaces=NS)
        separate = runs[instruction_index + 1].find("w:fldChar", namespaces=NS)
        assert begin is not None
        assert begin.get(f"{{{NS['w']}}}fldCharType") == "begin"
        assert begin.get(f"{{{NS['w']}}}dirty") == "true"
        assert separate is not None
        assert separate.get(f"{{{NS['w']}}}fldCharType") == "separate"
        assert any(
            candidate.get(f"{{{NS['w']}}}fldCharType") == "end"
            for later_run in runs[instruction_index + 2 :]
            for candidate in later_run.findall("w:fldChar", namespaces=NS)
        )

    figure_caption = document_xml.xpath(
        ".//w:p[.//w:bookmarkStart[@w:name='tf_fig_model']]",
        namespaces=NS,
    )[0]
    children = list(figure_caption)
    bookmark_start = next(
        index
        for index, child in enumerate(children)
        if etree.QName(child).localname == "bookmarkStart"
    )
    bookmark_end = next(
        index
        for index, child in enumerate(children)
        if etree.QName(child).localname == "bookmarkEnd"
    )
    bookmarked_text = "".join(
        text
        for child in children[bookmark_start + 1 : bookmark_end]
        for text in child.xpath(".//w:t/text()", namespaces=NS)
    )
    following_text = "".join(
        text
        for child in children[bookmark_end + 1 :]
        for text in child.xpath(".//w:t/text()", namespaces=NS)
    )
    assert bookmarked_text == "图1-1"
    assert following_text == " 系统模型"

    assert "word/footnotes.xml" in package_parts
    footnotes_xml = _xml_part(output, "word/footnotes.xml")
    assert footnotes_xml.xpath("./w:footnote[@w:id='-1']", namespaces=NS)
    assert footnotes_xml.xpath("./w:footnote[@w:id='0']", namespaces=NS)
    assert footnotes_xml.xpath(
        "./w:footnote[@w:id='1']//w:t[text()='真实脚注正文，参见']",
        namespaces=NS,
    )
    assert footnotes_xml.xpath(
        "./w:footnote[@w:id='1']//w:instrText[text()='REF tf_fig_model \\h']",
        namespaces=NS,
    )
    assert footnotes_xml.xpath(
        "./w:footnote[@w:id='1']//w:fldChar/@w:fldCharType",
        namespaces=NS,
    ) == ["begin", "separate", "end"]
    assert document_xml.xpath(".//w:footnoteReference/@w:id", namespaces=NS) == ["1"]
    assert relationships_xml.xpath(
        "./pr:Relationship[contains(@Type, '/footnotes')]",
        namespaces=REL_NS,
    )
    assert content_types_xml.xpath(
        "./*[local-name()='Override'][@PartName='/word/footnotes.xml']"
    )

    sections = document_xml.xpath(".//w:sectPr", namespaces=NS)
    assert len(sections) == 3
    assert sections[1].xpath("./w:pgNumType/@w:fmt", namespaces=NS) == ["lowerRoman"]
    assert sections[2].xpath("./w:type/@w:val", namespaces=NS) == ["oddPage"]
    assert sections[2].xpath("./w:pgNumType/@w:fmt", namespaces=NS) == ["decimal"]
    assert sections[2].xpath("./w:pgNumType/@w:start", namespaces=NS) == ["1"]
    assert sections[2].xpath("./w:titlePg", namespaces=NS)
    assert sections[1].xpath("./w:footerReference/@r:id", namespaces=NS)
    assert sections[2].xpath("./w:headerReference/@r:id", namespaces=NS)
    assert sections[2].xpath("./w:footerReference/@r:id", namespaces=NS)
    assert relationships_xml.xpath(
        "./pr:Relationship[contains(@Type, '/header')]",
        namespaces=REL_NS,
    )
    assert relationships_xml.xpath(
        "./pr:Relationship[contains(@Type, '/footer')]",
        namespaces=REL_NS,
    )
    header_text = "".join(
        text
        for part in package_parts
        if part.startswith("word/header") and part.endswith(".xml")
        for text in _xml_part(output, part).xpath(".//w:t/text()", namespaces=NS)
    )
    assert "基于结构化 Markdown 的论文" in header_text
    footer_field_codes = [
        "".join(node.itertext()).strip()
        for part in package_parts
        if part.startswith("word/footer") and part.endswith(".xml")
        for node in _xml_part(output, part).xpath(".//w:instrText", namespaces=NS)
    ]
    assert "PAGE" in footer_field_codes
    assert "NUMPAGES" in footer_field_codes


def test_docx_renderer_omits_page_fields_when_page_number_format_is_none(
    tmp_path: Path,
):
    template = load_template("templates/base/bachelor.yaml")
    template.sections = SectionsSpec.model_validate(
        {
            "main": {
                "footer": {"enabled": True, "text": "保密文档"},
                "page_number": {"format": "none"},
            }
        }
    )
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[Heading(id="chap:intro", level=1, text="绪论")],
    )
    output = tmp_path / "no-page-number.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    footer_parts = [
        part
        for part in list_package_parts(output)
        if part.startswith("word/footer") and part.endswith(".xml")
    ]
    assert len(footer_parts) == 1
    footer_xml = _xml_part(output, footer_parts[0])
    assert footer_xml.xpath(".//w:t/text()", namespaces=NS) == ["保密文档"]
    assert not footer_xml.xpath(".//w:instrText", namespaces=NS)


def test_docx_renderer_prevents_disabled_section_header_footer_inheritance(
    tmp_path: Path,
):
    template = load_template("templates/base/bachelor.yaml")
    template.sections = SectionsSpec.model_validate(
        {
            "front_matter": {
                "header": {"enabled": True, "text": "FRONT HEADER"},
                "footer": {"enabled": True, "text": "FRONT FOOTER"},
                "page_number": {"format": "roman-lower"},
            },
            "main": {
                "header": {"enabled": False, "text": "DISABLED HEADER TEXT"},
                "footer": {"enabled": False, "text": "DISABLED FOOTER TEXT"},
                "page_number": {"format": "none"},
            },
        }
    )
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Heading(id="chap:abstract-zh", level=1, text="摘要"),
            Heading(id="chap:intro", level=1, text="绪论"),
        ],
    )
    output = tmp_path / "disabled-header-footer.docx"

    DocxRenderer().render(compile_document(document, template=template), output)

    reloaded = __import__("docx").Document(output)
    assert len(reloaded.sections) == 2
    assert reloaded.sections[1].header.is_linked_to_previous is False
    assert reloaded.sections[1].footer.is_linked_to_previous is False
    assert not any(
        paragraph.text for paragraph in reloaded.sections[1].header.paragraphs
    )
    assert not any(
        paragraph.text for paragraph in reloaded.sections[1].footer.paragraphs
    )

    document_xml = _xml_part(output, "word/document.xml")
    sections = document_xml.xpath(".//w:sectPr", namespaces=NS)
    main_header_id = sections[1].xpath("./w:headerReference/@r:id", namespaces=NS)
    main_footer_id = sections[1].xpath("./w:footerReference/@r:id", namespaces=NS)
    assert main_header_id
    assert main_footer_id
    relationships = _xml_part(output, "word/_rels/document.xml.rels")
    targets = {
        node.get("Id"): node.get("Target")
        for node in relationships.xpath("./pr:Relationship", namespaces=REL_NS)
    }
    main_header = _xml_part(output, f"word/{targets[main_header_id[0]]}")
    main_footer = _xml_part(output, f"word/{targets[main_footer_id[0]]}")
    assert not main_header.xpath(".//w:t[text()='FRONT HEADER']", namespaces=NS)
    assert not main_footer.xpath(".//w:t[text()='FRONT FOOTER']", namespaces=NS)
    assert not main_header.xpath(
        ".//w:t[text()='DISABLED HEADER TEXT']",
        namespaces=NS,
    )
    assert not main_footer.xpath(
        ".//w:t[text()='DISABLED FOOTER TEXT']",
        namespaces=NS,
    )
    assert not main_footer.xpath(".//w:instrText", namespaces=NS)


def test_reference_field_runs_centralize_ref_instruction():
    reference = ReferenceRun(
        target_id="fig:model",
        bookmark="tf_fig_model",
        display_text="图1-1",
    )

    runs = fields_module.reference_field_runs(reference)

    instructions = [
        "".join(node.itertext())
        for run in runs
        for node in run.xpath("./w:instrText")
    ]
    assert instructions == ["REF tf_fig_model \\h"]


def test_docx_renderer_writes_resolved_body_footnote_and_bibliography_text(
    tmp_path: Path,
):
    fixture = Path(__file__).parent / "fixtures" / "bibliography" / "gbt7714-v1.bib"
    database = LocalBibTeXLoader().load(fixture)
    body_citation = Citation(
        keys=["doe2024", "smith2025"],
        raw="[@doe2024; @smith2025]",
    )
    footnote_citation = Citation(keys=["smith2025"], raw="[@smith2025]")
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Paragraph(
                text="正文引用",
                inlines=[
                    Text(value="正文引用"),
                    body_citation,
                    FootnoteReference(label="note"),
                ],
            ),
            FootnoteDefinition(
                label="note",
                text="脚注引用",
                inlines=[Text(value="脚注引用"), footnote_citation],
            ),
            BibliographyBlock(),
        ],
        citations=[body_citation, footnote_citation],
    )
    output = tmp_path / "bibliography.docx"

    plan = compile_document(
        document,
        template=load_template("templates/base/bachelor.yaml"),
        bibliography_database=database,
        citation_formatter=Gbt7714Formatter(),
    )
    DocxRenderer().render(plan, output)

    document_xml = _xml_part(output, "word/document.xml")
    footnotes_xml = _xml_part(output, "word/footnotes.xml")
    body_text = "".join(document_xml.xpath(".//w:body//w:t/text()", namespaces=NS))
    footnote_text = "".join(
        footnotes_xml.xpath("./w:footnote[@w:id='1']//w:t/text()", namespaces=NS)
    )
    paragraphs = [
        "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
        for paragraph in document_xml.xpath(".//w:body/w:p", namespaces=NS)
    ]

    assert "正文引用[1,2]" in body_text
    assert "[@doe2024" not in body_text
    assert "脚注引用[2]" in footnote_text
    assert "[@smith2025]" not in footnote_text
    assert paragraphs[-2:] == [
        "[1] DOE J. Structured Academic Documents[M]. Beijing: Example Press, 2024.",
        (
            "[2] SMITH J, WANG L. Deterministic Thesis Compilation[J]. "
            "Journal of Document Engineering, 2025, 12(3): 101-118. "
            "DOI:10.1000/tf.2025.001."
        ),
    ]


@pytest.mark.parametrize("error_type", [AttributeError, ValueError])
def test_docx_renderer_wraps_private_api_failures_with_capability_context(
    tmp_path: Path,
    monkeypatch,
    error_type,
):
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[Equation(id="eq:broken", latex="x")],
    )
    plan = compile_document(
        document,
        template=load_template("templates/base/bachelor.yaml"),
    )

    def fail_render(*args, **kwargs):
        raise error_type("missing private member")

    monkeypatch.setattr(renderer_module, "render_equation", fail_render)

    with pytest.raises(DocxRenderError, match="equation.*missing private member"):
        DocxRenderer().render(plan, tmp_path / "broken.docx")
