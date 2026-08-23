from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from docx.enum.section import WD_SECTION
from lxml import etree

from thesis_forge.core.render_plan import (
    CaptionRuns,
    FootnoteDefinitionInstruction,
    FootnoteReferenceRun,
    ReferenceRun,
    SequenceInstruction,
    TextRun,
    TocEntryInstruction,
    TocInstruction,
)
from thesis_forge.renderers.docx.bookmarks import wrap_paragraph_in_bookmark
from thesis_forge.renderers.docx.captions import add_caption
from thesis_forge.renderers.docx.document import create_document
from thesis_forge.renderers.docx.fields import (
    add_complex_field,
    add_reference_field,
    set_update_fields,
)
from thesis_forge.renderers.docx.footnotes import FootnoteManager
from thesis_forge.renderers.docx.lists import apply_list_numbering, create_list_numbering
from thesis_forge.renderers.docx.package import (
    DocxPackageValidationError,
    validate_docx_package,
)
from thesis_forge.renderers.docx.toc import add_toc_field
from thesis_forge.templates import load_template

ROOT = Path(__file__).resolve().parents[3]
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W_NS, "r": R_NS, "pr": PR_NS}
W = lambda name: f"{{{W_NS}}}{name}"
R_TYPE = "Type"
IMAGE_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "image"
)
HYPERLINK_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "hyperlink"
)
HEADER_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "header"
)


def _semantic_package(tmp_path: Path) -> Path:
    template = load_template(ROOT / "templates/base/bachelor.yaml")
    document = create_document(template)
    set_update_fields(document)

    section = document.sections[0]
    section.header.paragraphs[0].text = "Header"
    section.footer.paragraphs[0].text = "Footer"

    heading = document.add_paragraph("Introduction", style="Heading 1")
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
        template,
    )

    add_caption(
        document,
        label="Figure 1-1",
        caption=CaptionRuns((TextRun("Model"),)),
        bookmark="tf_fig_model",
        spec=None,
        template=None,
        fallback_alignment="center",
        sequence=SequenceInstruction(
            name="TF_Figure_1",
            value=1,
            prefix="Figure 1-",
            suffix="",
            result="1",
        ),
    )
    reference_paragraph = document.add_paragraph()
    add_reference_field(
        reference_paragraph,
        ReferenceRun(
            target_id="fig:model",
            bookmark="tf_fig_model",
            display_text="Figure 1-1",
        ),
    )
    add_complex_field(document.add_paragraph(), "PAGE", result="1")
    add_complex_field(document.add_paragraph(), "NUMPAGES", result="1")

    number_id = create_list_numbering(
        document,
        policy=template.list.ordered,
    )
    list_paragraph = document.add_paragraph("Numbered item")
    apply_list_numbering(list_paragraph, number_id=number_id, level=0)

    footnotes = FootnoteManager(document)
    footnote_paragraph = document.add_paragraph("Footnote")
    footnotes.add_reference(
        footnote_paragraph,
        FootnoteReferenceRun(label="note", footnote_id=1),
    )
    footnotes.add_definition(
        FootnoteDefinitionInstruction(
            label="note",
            footnote_id=1,
            text="Footnote text",
            inlines=(TextRun("Footnote text"),),
        )
    )

    image_path = ROOT / "tests/fixtures/v2-project/assets/model.png"
    document.add_picture(str(image_path))

    second_section = document.add_section(WD_SECTION.NEW_PAGE)
    second_section.header.is_linked_to_previous = False
    second_section.footer.is_linked_to_previous = False
    second_section.header.paragraphs[0].text = "Second header"
    second_section.footer.paragraphs[0].text = "Second footer"

    footnotes.attach()
    output = tmp_path / "semantic.docx"
    document.save(output)
    return output


def _rewrite_package(
    source: Path,
    destination: Path,
    mutate,
) -> None:
    with ZipFile(source) as package:
        entries = {
            name: package.read(name)
            for name in package.namelist()
        }
    mutate(entries)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as package:
        for name, content in entries.items():
            package.writestr(name, content)


def _xml(entries: dict[str, bytes], part: str):
    return etree.fromstring(entries[part])


def _store_xml(entries: dict[str, bytes], part: str, root) -> None:
    entries[part] = etree.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True,
    )


def _duplicate_bookmark_name(entries: dict[str, bytes]) -> None:
    root = _xml(entries, "word/document.xml")
    starts = root.xpath(".//w:bookmarkStart", namespaces=NS)
    starts[1].set(W("name"), starts[0].get(W("name")))
    _store_xml(entries, "word/document.xml", root)


def _remove_last_field_end(entries: dict[str, bytes]) -> None:
    root = _xml(entries, "word/document.xml")
    ends = root.xpath(".//w:fldChar[@w:fldCharType='end']", namespaces=NS)
    end = ends[-1]
    end.getparent().remove(end)
    _store_xml(entries, "word/document.xml", root)


def _use_missing_style(entries: dict[str, bytes]) -> None:
    root = _xml(entries, "word/document.xml")
    root.xpath(".//w:pStyle", namespaces=NS)[0].set(W("val"), "MissingStyle")
    _store_xml(entries, "word/document.xml", root)


def _use_missing_numbering_id(entries: dict[str, bytes]) -> None:
    root = _xml(entries, "word/document.xml")
    root.xpath(".//w:body//w:numId", namespaces=NS)[0].set(W("val"), "9999")
    _store_xml(entries, "word/document.xml", root)


def _use_missing_footnote(entries: dict[str, bytes]) -> None:
    root = _xml(entries, "word/document.xml")
    root.xpath(".//w:footnoteReference", namespaces=NS)[0].set(W("id"), "9999")
    _store_xml(entries, "word/document.xml", root)


def _remove_footnote_ref(entries: dict[str, bytes]) -> None:
    root = _xml(entries, "word/footnotes.xml")
    marker = root.xpath(
        ".//w:footnote[@w:id='1']//w:footnoteRef",
        namespaces=NS,
    )[0]
    marker.getparent().remove(marker)
    _store_xml(entries, "word/footnotes.xml", root)


def _change_header_relationship_type(entries: dict[str, bytes]) -> None:
    root = _xml(entries, "word/_rels/document.xml.rels")
    relation = root.xpath(
        ".//pr:Relationship[@Type=$relationship_type]",
        namespaces=NS,
        relationship_type=HEADER_RELATIONSHIP,
    )[0]
    relation.set(R_TYPE, IMAGE_RELATIONSHIP)
    _store_xml(entries, "word/_rels/document.xml.rels", root)


def _change_image_relationship_type(entries: dict[str, bytes]) -> None:
    root = _xml(entries, "word/_rels/document.xml.rels")
    relation = root.xpath(
        ".//pr:Relationship[@Type=$relationship_type]",
        namespaces=NS,
        relationship_type=IMAGE_RELATIONSHIP,
    )[0]
    relation.set(R_TYPE, HYPERLINK_RELATIONSHIP)
    _store_xml(entries, "word/_rels/document.xml.rels", root)


def test_valid_package_passes_semantic_postflight(tmp_path: Path) -> None:
    output = _semantic_package(tmp_path)

    validate_docx_package(output)

    with ZipFile(output) as package:
        assert "word/footnotes.xml" in package.namelist()
        assert "word/numbering.xml" in package.namelist()
        assert any(name.startswith("word/media/") for name in package.namelist())


@pytest.mark.parametrize(
    ("name", "mutator", "expected_code"),
    [
        ("bookmark", _duplicate_bookmark_name, "TF-DOCX-BOOKMARK-004"),
        ("field", _remove_last_field_end, "TF-DOCX-FIELD-009"),
        ("style", _use_missing_style, "TF-DOCX-STYLE-005"),
        ("numbering", _use_missing_numbering_id, "TF-DOCX-NUMBERING-007"),
        ("footnote", _use_missing_footnote, "TF-DOCX-FOOTNOTE-006"),
        (
            "footnote-marker",
            _remove_footnote_ref,
            "TF-DOCX-FOOTNOTE-005",
        ),
        ("section", _change_header_relationship_type, "TF-DOCX-SECTION-004"),
        ("media", _change_image_relationship_type, "TF-DOCX-MEDIA-003"),
    ],
)
def test_semantic_repair_risks_report_stable_docx_diagnostics(
    tmp_path: Path,
    name: str,
    mutator,
    expected_code: str,
) -> None:
    valid = _semantic_package(tmp_path)
    broken = tmp_path / f"broken-{name}.docx"
    _rewrite_package(valid, broken, mutator)

    with pytest.raises(DocxPackageValidationError) as captured:
        validate_docx_package(broken)

    assert captured.value.code == expected_code
    assert str(captured.value).startswith("TF-DOCX-")
