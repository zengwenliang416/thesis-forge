"""Document-wide semantic symbols used by compilation and cross-reference resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from thesis_forge.templates.model import NumberingSpec, ThesisTemplate

from .model import (
    Algorithm,
    BibliographyBlock,
    Block,
    Equation,
    Figure,
    Heading,
    Listing,
    Table,
    ThesisDocument,
    inline_plain_text,
)

BOOKMARK_MAX_LENGTH = 40
BOOKMARK_INVALID_RE = re.compile(r"[^A-Za-z0-9_]")

NumberingKind = Literal["figure", "table", "equation"]
NumberingMode = Literal["chapter", "continuous", "none"]


class SymbolTableError(ValueError):
    """Base error for invalid document-wide symbol identity."""


class DuplicateSymbolError(SymbolTableError):
    def __init__(self, public_id: str):
        self.public_id = public_id
        super().__init__(f"Duplicate public symbol ID: {public_id}")


class BookmarkCollisionError(SymbolTableError):
    def __init__(self, bookmark: str, source_ids: tuple[str, str]):
        self.bookmark = bookmark
        self.source_ids = source_ids
        super().__init__(
            f"Bookmark name collision: {bookmark}: {source_ids[0]}, {source_ids[1]}"
        )


@dataclass(frozen=True, slots=True)
class NumberingInputs:
    """Resolved inputs that a later field/numbering pass consumes."""

    kind: NumberingKind
    chapter: int
    mode: NumberingMode
    separator: str
    sequence_value: int | None
    number: str | None
    caption_prefix: str


@dataclass(frozen=True, slots=True)
class SymbolEntry:
    public_id: str
    target_type: str
    display_label: str
    numbering_inputs: NumberingInputs | None
    bookmark: str


@dataclass(frozen=True, slots=True)
class SymbolTable:
    entries: dict[str, SymbolEntry]
    bookmarks: dict[str, str]

    @classmethod
    def from_document(
        cls,
        document: ThesisDocument,
        template: ThesisTemplate | None = None,
    ) -> SymbolTable:
        entries: dict[str, SymbolEntry] = {}
        bookmarks: dict[str, str] = {}
        bookmark_sources: dict[str, str] = {}
        chapter = 0
        chapter_counters: dict[tuple[NumberingKind, int], int] = {}
        continuous_counters: dict[NumberingKind, int] = {}
        has_front_matter = (
            template is not None and template.sections.front_matter is not None
        )

        for block in document.blocks:
            if (
                isinstance(block, Heading)
                and block.level == 1
                and (not has_front_matter or not is_front_matter_heading(block))
            ):
                chapter += 1

            if not block.id:
                continue
            if block.id in entries:
                raise DuplicateSymbolError(block.id)

            bookmark = bookmark_name(block.id)
            previous = bookmark_sources.get(bookmark)
            if previous is not None:
                raise BookmarkCollisionError(bookmark, (previous, block.id))

            numbering_inputs = _numbering_inputs(
                block,
                template,
                chapter or 1,
                chapter_counters,
                continuous_counters,
            )
            entries[block.id] = SymbolEntry(
                public_id=block.id,
                target_type=_target_type(block),
                display_label=_display_label(block, numbering_inputs),
                numbering_inputs=numbering_inputs,
                bookmark=bookmark,
            )
            bookmarks[block.id] = bookmark
            bookmark_sources[bookmark] = block.id

        return cls(entries=entries, bookmarks=bookmarks)


def bookmark_name(public_id: str) -> str:
    normalized = BOOKMARK_INVALID_RE.sub("_", public_id)
    return f"tf_{normalized}"[:BOOKMARK_MAX_LENGTH]


def is_front_matter_heading(block: Heading) -> bool:
    source_id = block.id or ""
    normalized_text = inline_plain_text(block.inlines).strip().lower()
    return source_id.startswith(("chap:abstract", "chap:toc", "chap:contents")) or (
        normalized_text in {"摘要", "abstract", "目录", "contents"}
    )


def _target_type(block: Block) -> str:
    if isinstance(block, Heading):
        return "chap" if block.level == 1 else "sec"
    if isinstance(block, Figure):
        return "fig"
    if isinstance(block, Table):
        return "tbl"
    if isinstance(block, Equation):
        return "eq"
    if isinstance(block, Listing):
        return "lst"
    if isinstance(block, Algorithm):
        return "alg"
    if isinstance(block, BibliographyBlock):
        return "bibliography"
    return type(block).__name__.lower()


def _numbering_spec(
    template: ThesisTemplate | None,
    kind: NumberingKind,
) -> NumberingSpec | None:
    style = getattr(template, kind, None) if template is not None else None
    return getattr(style, "numbering", None)


def _caption_prefix(template: ThesisTemplate | None, kind: NumberingKind) -> str:
    style = getattr(template, kind, None) if template is not None else None
    caption = getattr(style, "caption", None)
    return getattr(caption, "prefix", "")


def _numbering_inputs(
    block: Block,
    template: ThesisTemplate | None,
    chapter: int,
    chapter_counters: dict[tuple[NumberingKind, int], int],
    continuous_counters: dict[NumberingKind, int],
) -> NumberingInputs | None:
    kind: NumberingKind | None = None
    if isinstance(block, Figure):
        kind = "figure"
    elif isinstance(block, Table):
        kind = "table"
    elif isinstance(block, Equation):
        kind = "equation"
    if kind is None:
        return None

    numbering = _numbering_spec(template, kind)
    caption_prefix = _caption_prefix(template, kind)
    if numbering is None:
        return NumberingInputs(
            kind=kind,
            chapter=chapter,
            mode="none",
            separator="-",
            sequence_value=None,
            number=None,
            caption_prefix=caption_prefix,
        )

    mode: NumberingMode = numbering.mode
    if mode == "none":
        return NumberingInputs(
            kind=kind,
            chapter=chapter,
            mode=mode,
            separator=numbering.separator,
            sequence_value=None,
            number=None,
            caption_prefix=caption_prefix,
        )

    active_chapter = chapter or 1
    if mode == "chapter":
        key = (kind, active_chapter)
        sequence_value = chapter_counters.get(key, 0) + 1
        chapter_counters[key] = sequence_value
        number = f"{active_chapter}{numbering.separator}{sequence_value}"
    else:
        sequence_value = continuous_counters.get(kind, 0) + 1
        continuous_counters[kind] = sequence_value
        number = str(sequence_value)

    return NumberingInputs(
        kind=kind,
        chapter=active_chapter,
        mode=mode,
        separator=numbering.separator,
        sequence_value=sequence_value,
        number=number,
        caption_prefix=caption_prefix,
    )


def _display_label(
    block: Block,
    numbering_inputs: NumberingInputs | None,
) -> str:
    if isinstance(block, (Figure, Table, Equation)):
        number = numbering_inputs.number if numbering_inputs is not None else None
        if isinstance(block, Equation):
            return f"({number})" if number else block.id or ""
        caption = inline_plain_text(block.caption_inlines)
        if number and numbering_inputs is not None:
            return f"{numbering_inputs.caption_prefix}{number}"
        return caption
    if isinstance(block, Heading):
        return inline_plain_text(block.inlines)
    if isinstance(block, (Listing, Algorithm)):
        return inline_plain_text(block.caption_inlines)
    return block.id or ""
