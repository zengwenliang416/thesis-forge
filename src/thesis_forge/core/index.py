"""Derived semantic indexes over the immutable ThesisDocument.

The parser never maintains synchronized duplicate caches; ID, citation,
cross-reference and footnote indexes are derived by traversal
(docs/THESISFORGE_V2_PRODUCT_SPEC.md §7.4). Duplicate public IDs surface
every conflicting node instead of being overwritten by dictionary
construction.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .model import (
    Algorithm,
    BibliographyBlock,
    Block,
    BlockQuote,
    BulletList,
    Citation,
    CodeBlock,
    CrossReference,
    Emphasis,
    Equation,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    HardBreak,
    Heading,
    Inline,
    InlineCode,
    InlineMath,
    Link,
    ListBlock,
    Listing,
    ListItem,
    OrderedList,
    Paragraph,
    SoftBreak,
    Strong,
    Table,
    Text,
    ThesisDocument,
)

__all__ = [
    "DocumentIndex",
    "DuplicateIdConflict",
]

_INDEXED_INLINES = (Citation, CrossReference, FootnoteReference)
_CONTAINER_INLINES = (Strong, Emphasis)
_PLAIN_INLINES = (Text, SoftBreak, HardBreak, InlineCode, Link, InlineMath)
_KNOWN_INLINES = _INDEXED_INLINES + _CONTAINER_INLINES + _PLAIN_INLINES

_CAPTIONED_BLOCKS = (Figure, Table, Listing, Algorithm)
_ITEM_BLOCKS = (ListBlock, OrderedList, BulletList)
_OPAQUE_BLOCKS = (CodeBlock, Equation, BibliographyBlock)


@dataclass(frozen=True, slots=True)
class DuplicateIdConflict:
    """One public-ID collision: the first claimant and one later duplicate."""

    object_id: str
    first: Block
    duplicate: Block


@dataclass(frozen=True, slots=True)
class DocumentIndex:
    """Traversal-derived ID/citation/reference/footnote indexes.

    ``by_id`` keeps the first node that claimed a public ID; every later
    claimant is recorded in ``id_conflicts`` with both nodes, so duplicate
    IDs are reported instead of silently overwriting dictionary entries.
    """

    by_id: Mapping[str, Block]
    id_conflicts: tuple[DuplicateIdConflict, ...]
    citations: tuple[Citation, ...]
    cross_references: tuple[CrossReference, ...]
    footnote_references: tuple[FootnoteReference, ...]
    footnote_definitions: Mapping[str, FootnoteDefinition]

    @classmethod
    def from_document(cls, document: ThesisDocument) -> DocumentIndex:
        by_id: dict[str, Block] = {}
        conflicts: list[DuplicateIdConflict] = []
        citations: list[Citation] = []
        cross_references: list[CrossReference] = []
        footnote_references: list[FootnoteReference] = []
        footnote_definitions: dict[str, FootnoteDefinition] = {}

        def visit_inlines(inlines: Iterable[Inline]) -> None:
            for inline in inlines:
                if isinstance(inline, Citation):
                    citations.append(inline)
                elif isinstance(inline, CrossReference):
                    cross_references.append(inline)
                elif isinstance(inline, FootnoteReference):
                    footnote_references.append(inline)
                if isinstance(inline, _CONTAINER_INLINES):
                    visit_inlines(inline.children)
                elif not isinstance(inline, _KNOWN_INLINES):
                    raise TypeError(f"unknown Inline subclass: {type(inline).__name__}")

        def visit_item(item: ListItem) -> None:
            visit_inlines(item.inlines)
            for child in item.children:
                visit_block(child)

        def visit_block(block: Block) -> None:
            if block.id:
                existing = by_id.get(block.id)
                if existing is None:
                    by_id[block.id] = block
                else:
                    conflicts.append(
                        DuplicateIdConflict(block.id, existing, block)
                    )
            if isinstance(block, (Heading, Paragraph, FootnoteDefinition)):
                if isinstance(block, FootnoteDefinition) and block.label:
                    footnote_definitions.setdefault(block.label, block)
                visit_inlines(block.inlines)
            elif isinstance(block, _ITEM_BLOCKS):
                for item in block.items:
                    visit_item(item)
            elif isinstance(block, BlockQuote):
                for child in block.children:
                    visit_block(child)
            elif isinstance(block, _CAPTIONED_BLOCKS):
                visit_inlines(block.caption_inlines)
                if isinstance(block, Table):
                    for row in block.rows:
                        for cell in row.cells:
                            visit_inlines(cell.inlines)
            elif isinstance(block, _OPAQUE_BLOCKS):
                pass
            else:
                raise TypeError(f"unknown Block subclass: {type(block).__name__}")

        for block in document.blocks:
            visit_block(block)

        return cls(
            by_id=by_id,
            id_conflicts=tuple(conflicts),
            citations=tuple(citations),
            cross_references=tuple(cross_references),
            footnote_references=tuple(footnote_references),
            footnote_definitions=footnote_definitions,
        )
