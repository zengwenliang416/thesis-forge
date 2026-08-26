from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from docforge.core.compiler import compile_document
from docforge.core.parser_markdown_it import MarkdownItParserBackend
from docforge.core.render_plan import (
    BlockQuoteInstruction,
    CodeBlockInstruction,
    ParagraphInstruction,
    TextRun,
)
from docforge.renderers.docx import DocxRenderer

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def _xml_part(path: Path, name: str):
    with ZipFile(path) as package:
        return etree.fromstring(package.read(name))


def test_compiler_preserves_code_block_blockquote_and_nested_emphasis() -> None:
    document = MarkdownItParserBackend().parse_text(
        "**粗体 *粗斜体*** 与 *斜体*。\n\n"
        "> 引用段落\n"
        ">\n"
        "> ```python\n"
        "> print('quoted')\n"
        "> ```\n\n"
        "```text\n"
        "literal\n"
        "```\n",
        source_path="format.md",
    )

    plan = compile_document(document)

    paragraph = plan.nodes[0]
    assert isinstance(paragraph, ParagraphInstruction)
    assert paragraph.inlines == (
        TextRun("粗体 ", bold=True),
        TextRun("粗斜体", bold=True, italic=True),
        TextRun(" 与 "),
        TextRun("斜体", italic=True),
        TextRun("。"),
    )

    quote = plan.nodes[1]
    assert isinstance(quote, BlockQuoteInstruction)
    assert [type(child) for child in quote.children] == [
        ParagraphInstruction,
        CodeBlockInstruction,
    ]
    assert quote.children[1] == CodeBlockInstruction(
        language="python",
        code="print('quoted')\n",
    )

    assert plan.nodes[2] == CodeBlockInstruction(language="text", code="literal\n")


def test_docx_renders_italic_code_and_indented_blockquote(tmp_path: Path) -> None:
    document = MarkdownItParserBackend().parse_text(
        "*斜体* 与 **粗体**。\n\n"
        "> 引用 *内容*\n\n"
        "```python\n"
        "print(1)\n"
        "```\n",
        source_path="format.md",
    )
    output = tmp_path / "format.docx"

    DocxRenderer().render(compile_document(document), output)

    root = _xml_part(output, "word/document.xml")
    paragraphs = root.xpath(".//w:body/w:p", namespaces=NS)

    italic_runs = root.xpath(".//w:r[w:rPr/w:i]/w:t/text()", namespaces=NS)
    assert "斜体" in italic_runs
    assert "内容" in italic_runs
    assert root.xpath(".//w:r[w:rPr/w:b]/w:t[text()='粗体']", namespaces=NS)

    quote = next(
        paragraph
        for paragraph in paragraphs
        if "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)) == "引用 内容"
    )
    assert quote.xpath("./w:pPr/w:ind/@w:left", namespaces=NS) == ["360"]
    assert quote.xpath("./w:pPr/w:ind/@w:right", namespaces=NS) == ["360"]
    assert quote.xpath("./w:pPr/w:ind/@w:firstLine", namespaces=NS) == ["0"]

    code = next(
        paragraph
        for paragraph in paragraphs
        if "print(1)" in "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
    )
    assert code.xpath(".//w:rPr/w:rFonts/@w:ascii", namespaces=NS) == ["Courier New"]
    assert code.xpath(".//w:rPr/w:noProof", namespaces=NS)
