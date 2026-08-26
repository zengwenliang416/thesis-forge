"""Focused tests for the traversal-derived DocumentIndex."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from thesis_forge.core.index import DocumentIndex, DuplicateIdConflict
from thesis_forge.core.model import (
    Algorithm,
    Block,
    BlockQuote,
    BulletList,
    Citation,
    CodeBlock,
    CrossReference,
    Emphasis,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    ForgeDocument,
    Heading,
    Inline,
    ListBlock,
    Listing,
    ListItem,
    OrderedList,
    Paragraph,
    SourceLocation,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
)


def _document(*blocks: Block) -> ForgeDocument:
    return ForgeDocument(source_path=Path("thesis.md"), blocks=list(blocks))


def test_empty_document_yields_empty_index() -> None:
    index = DocumentIndex.from_document(_document())
    assert index.by_id == {}
    assert index.id_conflicts == ()
    assert index.citations == ()
    assert index.cross_references == ()
    assert index.footnote_references == ()
    assert index.footnote_definitions == {}


def test_public_ids_of_all_referencable_blocks_are_indexed() -> None:
    heading = Heading(id="chap:intro", level=1, inlines=[Text(value="绪论")])
    figure = Figure(id="fig:model", src="assets/model.png")
    table = Table(id="tbl:experiment")
    listing = Listing(id="lst:training", language="python", code="x = 1")
    index = DocumentIndex.from_document(_document(heading, figure, table, listing))
    assert index.by_id == {
        "chap:intro": heading,
        "fig:model": figure,
        "tbl:experiment": table,
        "lst:training": listing,
    }
    assert index.id_conflicts == ()


def test_duplicate_ids_report_every_conflict_without_overwrite() -> None:
    first = Heading(
        id="sec:dup",
        level=2,
        inlines=[Text(value="第一处")],
        location=SourceLocation(line=3),
    )
    duplicate = Heading(
        id="sec:dup",
        level=2,
        inlines=[Text(value="第二处")],
        location=SourceLocation(line=9),
    )
    third = Figure(id="sec:dup", src="assets/other.png")
    index = DocumentIndex.from_document(_document(first, duplicate, third))
    assert index.by_id["sec:dup"] is first
    assert index.id_conflicts == (
        DuplicateIdConflict(object_id="sec:dup", first=first, duplicate=duplicate),
        DuplicateIdConflict(object_id="sec:dup", first=first, duplicate=third),
    )
    conflict = index.id_conflicts[0]
    assert conflict.first.location.line == 3
    assert conflict.duplicate.location.line == 9


def test_nested_ids_from_quote_children_and_list_items_are_indexed() -> None:
    nested_heading = Heading(id="sec:nested", level=3, inlines=[])
    quote = BlockQuote(children=(nested_heading,))
    item = ListItem(children=(Figure(id="fig:in-item", src="a.png"),))
    listing_block = ListBlock(items=[item])
    index = DocumentIndex.from_document(_document(quote, listing_block))
    assert index.by_id == {"sec:nested": nested_heading, "fig:in-item": item.children[0]}


def test_semantic_inlines_in_captions_cells_and_children_are_indexed() -> None:
    caption_citation = Citation(keys=["smith2025"], raw="[@smith2025]")
    figure = Figure(id="fig:model", caption_inlines=(caption_citation,))
    cell_reference = CrossReference(target="fig:model")
    table = Table(
        id="tbl:experiment",
        caption_inlines=(Text(value="结果"),),
        rows=(TableRow(cells=(TableCell(inlines=(cell_reference,)),)),),
    )
    nested_citation = Citation(keys=["jones2024"], raw="[@jones2024]")
    deep = Strong(children=(Emphasis(children=(nested_citation,)),))
    item = ListItem(inlines=[deep])
    typed_list = OrderedList(items=(item,))
    footnote_ref = FootnoteReference(label="scope")
    quote = BlockQuote(children=(Paragraph(inlines=[footnote_ref]),))
    index = DocumentIndex.from_document(_document(figure, table, typed_list, quote))
    assert index.citations == (caption_citation, nested_citation)
    assert index.cross_references == (cell_reference,)
    assert index.footnote_references == (footnote_ref,)


def test_bullet_list_items_are_traversed() -> None:
    citation = Citation(keys=["a"], raw="[@a]")
    index = DocumentIndex.from_document(
        _document(BulletList(items=(ListItem(inlines=[citation]),)))
    )
    assert index.citations == (citation,)


def test_semantic_collections_preserve_document_order() -> None:
    first = Citation(keys=["one"], raw="[@one]")
    second = CrossReference(target="tbl:experiment")
    third = Citation(keys=["two"], raw="[@two]")
    document = _document(
        Paragraph(inlines=[first]),
        Table(id="tbl:experiment", caption_inlines=(second,)),
        Paragraph(inlines=[third]),
    )
    index = DocumentIndex.from_document(document)
    assert index.citations == (first, third)
    assert index.cross_references == (second,)


def test_footnote_definitions_are_indexed_by_label() -> None:
    definition = FootnoteDefinition(
        label="scope", inlines=[Text(value="说明性脚注。")]
    )
    index = DocumentIndex.from_document(_document(definition))
    assert index.footnote_definitions == {"scope": definition}


def test_algorithm_body_lines_are_indexed_with_locations() -> None:
    body_citation = Citation(
        keys=["alg-src"], raw="[@alg-src]", location=SourceLocation(line=5, column=9)
    )
    algorithm = Algorithm(
        id="alg:train",
        caption_inlines=(Text(value="训练流程"),),
        body_lines=(
            (Text(value="1. 初始化参数；", location=SourceLocation(line=4)),),
            (Text(value="2. 读取数据 "), body_citation),
        ),
    )
    index = DocumentIndex.from_document(_document(algorithm))
    assert index.citations == (body_citation,)
    assert index.inlines[-1] is body_citation


def test_code_blocks_and_equations_are_traversed_without_inline_content() -> None:
    index = DocumentIndex.from_document(
        _document(
            CodeBlock(language="python", code="x = 1"),
        )
    )
    assert index.citations == ()
    assert index.by_id == {}


def test_unknown_block_subclass_raises_type_error() -> None:
    class Foreign(Block):
        pass

    with pytest.raises(TypeError, match="unknown Block subclass: Foreign"):
        DocumentIndex.from_document(_document(Foreign()))


def test_unknown_inline_subclass_raises_type_error() -> None:
    class ForeignInline(Inline):
        pass

    with pytest.raises(TypeError, match="unknown Inline subclass: ForeignInline"):
        DocumentIndex.from_document(
            _document(Paragraph(inlines=[ForeignInline()]))
        )


def test_traversal_does_not_mutate_the_document() -> None:
    document = _document(
        Heading(id="chap:intro", level=1, inlines=[Text(value="绪论")]),
        Table(
            id="tbl:experiment",
            rows=(TableRow(cells=(TableCell(inlines=(Citation(keys=["a"], raw="[@a]"),)),)),),
        ),
        BlockQuote(children=(Paragraph(inlines=[FootnoteReference(label="scope")]),)),
    )
    before = dataclasses.asdict(document)
    DocumentIndex.from_document(document)
    assert dataclasses.asdict(document) == before
