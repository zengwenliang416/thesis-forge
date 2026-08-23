from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from docx import Document
from lxml import etree

from thesis_forge.core.render_plan import (
    CaptionRuns,
    ReferenceRun,
    SequenceInstruction,
    TextRun,
    TocEntryInstruction,
    TocInstruction,
)
from thesis_forge.renderers.docx.bookmarks import wrap_paragraph_in_bookmark
from thesis_forge.renderers.docx.captions import add_caption
from thesis_forge.renderers.docx.fields import (
    add_complex_field,
    add_reference_field,
    set_update_fields,
)
from thesis_forge.renderers.docx.package import validate_docx_package
from thesis_forge.renderers.docx.toc import add_toc_field

ROOT = Path(__file__).resolve().parents[3]
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def _xml_part(path: Path, name: str):
    with ZipFile(path) as package:
        return etree.fromstring(package.read(name))


def _field_runs(container, instruction):
    instruction_run = instruction.getparent()
    runs = container.xpath("./w:r", namespaces=NS)
    index = runs.index(instruction_run)
    return runs, index


def _assert_local_field(container, instruction, cached_result: str) -> None:
    runs, index = _field_runs(container, instruction)
    field_types = [
        field.get(f"{{{W_NS}}}fldCharType")
        for run in runs
        for field in run.xpath("./w:fldChar", namespaces=NS)
    ]
    assert field_types == ["begin", "separate", "end"]
    begin = runs[index - 1].find("w:fldChar", namespaces=NS)
    assert begin is not None
    assert begin.get(f"{{{W_NS}}}dirty") == "true"
    cached = "".join(runs[index + 2].xpath(".//w:t/text()", namespaces=NS))
    assert cached == cached_result


def test_word_field_families_preserve_typed_inputs_and_docx_structure(
    tmp_path: Path,
) -> None:
    document = Document()
    set_update_fields(document)

    heading = document.add_paragraph("Introduction")
    wrap_paragraph_in_bookmark(heading, "tf_chap_intro")

    toc_paragraph = document.add_paragraph()
    add_toc_field(
        document,
        toc_paragraph,
        TocInstruction(
            entries=(
                TocEntryInstruction(
                    text="Introduction",
                    level=1,
                    bookmark="tf_chap_intro",
                ),
            ),
        ),
        template=None,
    )

    add_caption(
        document,
        label="Figure 3-2",
        caption=CaptionRuns((TextRun("Model caption"),)),
        bookmark="tf_fig_model",
        spec=None,
        template=None,
        fallback_alignment="center",
        sequence=SequenceInstruction(
            name="TF_Figure_3",
            value=2,
            prefix="Figure 3-",
            suffix="",
            result="2",
        ),
    )

    reference_paragraph = document.add_paragraph()
    add_reference_field(
        reference_paragraph,
        ReferenceRun(
            target_id="fig:model",
            bookmark="tf_fig_model",
            display_text="Figure 3-2",
        ),
    )

    page_paragraph = document.add_paragraph()
    add_complex_field(page_paragraph, "PAGE", result="7")
    total_pages_paragraph = document.add_paragraph()
    add_complex_field(total_pages_paragraph, "NUMPAGES", result="12")

    output = tmp_path / "fields-v2.docx"
    document.save(output)
    validate_docx_package(output)

    document_xml = _xml_part(output, "word/document.xml")
    settings_xml = _xml_part(output, "word/settings.xml")

    field_codes = [
        "".join(node.itertext()).strip()
        for node in document_xml.xpath(".//w:instrText", namespaces=NS)
    ]
    assert field_codes == [
        'TOC \\o "1-3" \\h \\z \\u',
        "PAGEREF tf_chap_intro \\h",
        "SEQ TF_Figure_3 \\r 2 \\* ARABIC",
        "REF tf_fig_model \\h",
        "PAGE",
        "NUMPAGES",
    ]

    field_types = document_xml.xpath(
        ".//w:fldChar/@w:fldCharType",
        namespaces=NS,
    )
    assert field_types.count("begin") == 6
    assert field_types.count("separate") == 6
    assert field_types.count("end") == 6
    assert all(
        node.get(f"{{{W_NS}}}dirty") == "true"
        for node in document_xml.xpath(
            ".//w:fldChar[@w:fldCharType='begin']",
            namespaces=NS,
        )
    )
    assert settings_xml.xpath("./w:updateFields/@w:val", namespaces=NS) == ["true"]

    body = document_xml.xpath("./w:body", namespaces=NS)[0]
    toc_index = next(
        index
        for index, paragraph in enumerate(body)
        if paragraph.xpath(
            ".//w:instrText[starts-with(., 'TOC ')]",
            namespaces=NS,
        )
    )
    toc_entry = body[toc_index + 1]
    assert toc_entry.xpath(
        ".//w:hyperlink/@w:anchor",
        namespaces=NS,
    ) == ["tf_chap_intro"]
    assert "".join(toc_entry.xpath(".//w:t/text()", namespaces=NS)) == "Introduction1"
    pageref = toc_entry.xpath(
        ".//w:instrText[starts-with(., 'PAGEREF ')]",
        namespaces=NS,
    )[0]
    _assert_local_field(pageref.getparent().getparent(), pageref, "1")
    assert toc_entry.xpath(
        "./w:r/w:fldChar/@w:fldCharType",
        namespaces=NS,
    )[-1] == "end"

    sequence = document_xml.xpath(
        ".//w:instrText[starts-with(., 'SEQ ')]",
        namespaces=NS,
    )[0]
    _assert_local_field(sequence.getparent().getparent(), sequence, "2")
    sequence_paragraph = sequence.getparent().getparent()
    assert "".join(sequence_paragraph.xpath(".//w:t/text()", namespaces=NS)) == (
        "Figure 3-2 Model caption"
    )

    reference = document_xml.xpath(
        ".//w:instrText[starts-with(., 'REF ')]",
        namespaces=NS,
    )[0]
    _assert_local_field(reference.getparent().getparent(), reference, "Figure 3-2")

    page = document_xml.xpath(".//w:instrText[.='PAGE']", namespaces=NS)[0]
    _assert_local_field(page.getparent().getparent(), page, "7")
    total_pages = document_xml.xpath(
        ".//w:instrText[.='NUMPAGES']",
        namespaces=NS,
    )[0]
    _assert_local_field(
        total_pages.getparent().getparent(),
        total_pages,
        "12",
    )

    render_plan_source = (
        ROOT / "src" / "thesis_forge" / "core" / "render_plan.py"
    ).read_text(encoding="utf-8")
    assert "from docx" not in render_plan_source
    assert "from lxml" not in render_plan_source
    assert "fldChar" not in render_plan_source
