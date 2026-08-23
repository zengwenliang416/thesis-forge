from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar, Literal, Protocol, Self, TypeAlias

from thesis_forge.templates.model import SectionsSpec, ThesisTemplate


@dataclass(slots=True)
class RenderNode:
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)


class TypedInstruction(Protocol):
    kind: ClassVar[str]

    @property
    def payload(self) -> dict[str, Any]: ...

    def to_render_node(self) -> RenderNode: ...


class _Instruction:
    kind: ClassVar[str]

    @property
    def payload(self) -> dict[str, Any]:
        raise NotImplementedError

    def to_render_node(self) -> RenderNode:
        return RenderNode(kind=self.kind, payload=self.payload)


@dataclass(frozen=True, slots=True)
class TextRun:
    text: str
    bold: bool = False
    code: bool = False


@dataclass(frozen=True, slots=True)
class ReferenceRun:
    target_id: str
    bookmark: str
    display_text: str


@dataclass(frozen=True, slots=True)
class CitationRun:
    keys: tuple[str, ...]
    ordinals: tuple[int, ...]
    locator: str | None = None
    raw: str = ""
    text: str = ""


@dataclass(frozen=True, slots=True)
class FootnoteReferenceRun:
    label: str
    footnote_id: int


@dataclass(frozen=True, slots=True)
class SoftBreakRun:
    pass


@dataclass(frozen=True, slots=True)
class HardBreakRun:
    pass


@dataclass(frozen=True, slots=True)
class HyperlinkRun:
    text: str
    destination: str


@dataclass(frozen=True, slots=True)
class MathRun:
    latex: str


InlineRun: TypeAlias = (
    TextRun
    | ReferenceRun
    | CitationRun
    | FootnoteReferenceRun
    | SoftBreakRun
    | HardBreakRun
    | HyperlinkRun
    | MathRun
)


def ensure_inline_run(value: object) -> InlineRun:
    if isinstance(
        value,
        (
            TextRun,
            ReferenceRun,
            CitationRun,
            FootnoteReferenceRun,
            SoftBreakRun,
            HardBreakRun,
            HyperlinkRun,
            MathRun,
        ),
    ):
        return value
    raise TypeError(f"unsupported InlineRun: {type(value).__name__}")


def _inline_run_text(runs: tuple[InlineRun, ...]) -> str:
    parts: list[str] = []
    for run in runs:
        if isinstance(run, TextRun):
            parts.append(run.text)
        elif isinstance(run, ReferenceRun):
            parts.append(run.display_text)
        elif isinstance(run, CitationRun):
            parts.append(run.text)
        elif isinstance(run, FootnoteReferenceRun):
            parts.append("")
        elif isinstance(run, HyperlinkRun):
            parts.append(run.text)
        elif isinstance(run, MathRun):
            parts.append(run.latex)
        elif isinstance(run, SoftBreakRun):
            parts.append(" ")
        elif isinstance(run, HardBreakRun):
            parts.append("\n")
        else:
            raise TypeError(f"unsupported InlineRun: {type(run).__name__}")
    return "".join(parts)


class CaptionRuns(str):
    """One validated typed caption value with a readable string projection."""

    _runs: tuple[InlineRun, ...]

    def __new__(cls, runs: tuple[InlineRun, ...]) -> Self:
        if type(runs) is not tuple:
            raise TypeError("CaptionRuns requires tuple[InlineRun, ...]")
        normalized = tuple(ensure_inline_run(run) for run in runs)
        value = str.__new__(cls, _inline_run_text(normalized))
        value._runs = normalized
        return value

    @property
    def runs(self) -> tuple[InlineRun, ...]:
        return self._runs


ParagraphRole: TypeAlias = Literal[
    "body",
    "abstract.zh.title",
    "abstract.zh.body",
    "keywords.zh",
    "abstract.en.title",
    "abstract.en.body",
    "keywords.en",
    "toc.title",
    "bibliography.title",
    "bibliography.entry",
    "special.acknowledgements",
    "special.achievements",
]


@dataclass(frozen=True, slots=True)
class HeadingInstruction(_Instruction):
    kind: ClassVar[str] = "heading"
    source_id: str | None
    level: int
    text: str
    inlines: tuple[InlineRun, ...] = ()
    bookmark: str | None = None
    role: ParagraphRole | None = None

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "level": self.level,
            "text": self.text,
            "bookmark": self.bookmark,
            "role": self.role,
        }


@dataclass(frozen=True, slots=True)
class ParagraphInstruction(_Instruction):
    kind: ClassVar[str] = "paragraph"
    text: str
    inlines: tuple[InlineRun, ...] = ()
    role: ParagraphRole = "body"

    @property
    def payload(self) -> dict[str, Any]:
        return {"text": self.text, "role": self.role}


@dataclass(frozen=True, slots=True)
class ListItemInstruction:
    text: str
    level: int
    ordinal: int | None
    inlines: tuple[InlineRun, ...] = ()


@dataclass(frozen=True, slots=True)
class ListInstruction(_Instruction):
    kind: ClassVar[str] = "list"
    ordered: bool
    start: int | None
    items: tuple[ListItemInstruction, ...]

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "ordered": self.ordered,
            "start": self.start,
            "items": [
                {"text": item.text, "level": item.level, "ordinal": item.ordinal}
                for item in self.items
            ],
        }


@dataclass(frozen=True, slots=True)
class FigureWidthInstruction:
    value: Decimal
    unit: Literal["percent", "mm", "cm", "pt", "em"]
    origin: Literal["source", "template"]

    @property
    def payload(self) -> dict[str, str]:
        return {
            "value": str(self.value),
            "unit": self.unit,
            "origin": self.origin,
        }


@dataclass(frozen=True, slots=True)
class SequenceInstruction:
    name: str
    value: int
    prefix: str
    suffix: str
    result: str

    @property
    def field_code(self) -> str:
        return f"SEQ {self.name} \\r {self.value} \\* ARABIC"

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "result": self.result,
            "field_code": self.field_code,
        }


@dataclass(frozen=True, slots=True)
class FigureInstruction(_Instruction):
    kind: ClassVar[str] = "figure"
    source_id: str | None
    src: str
    asset_path: Path
    caption: CaptionRuns
    width: str | None
    resolved_width: FigureWidthInstruction | None
    chapter: int
    number: str | None
    label: str
    bookmark: str | None
    sequence: SequenceInstruction | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.caption, CaptionRuns):
            raise TypeError("FigureInstruction caption must be CaptionRuns")

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "src": self.src,
            "asset_path": str(self.asset_path),
            "caption": self.caption,
            "width": self.width,
            "resolved_width": (
                self.resolved_width.payload if self.resolved_width is not None else None
            ),
            "number": self.number,
            "label": self.label,
            "bookmark": self.bookmark,
            "sequence": self.sequence.payload if self.sequence is not None else None,
        }


@dataclass(frozen=True, slots=True)
class TableCellInstruction:
    inlines: tuple[InlineRun, ...]
    alignment: Literal["left", "center", "right"] | None = None

    def __post_init__(self) -> None:
        if type(self.inlines) is not tuple:
            raise TypeError("TableCellInstruction requires tuple[InlineRun, ...]")
        for inline in self.inlines:
            ensure_inline_run(inline)

    @classmethod
    def from_inlines(
        cls,
        inlines: tuple[InlineRun, ...],
        alignment: Literal["left", "center", "right"] | None = None,
    ) -> Self:
        return cls(inlines=inlines, alignment=alignment)

    @property
    def text(self) -> str:
        return _inline_run_text(self.inlines)


@dataclass(frozen=True, slots=True)
class TableRowInstruction:
    header: bool
    cells: tuple[TableCellInstruction, ...]


@dataclass(frozen=True, slots=True)
class TableInstruction(_Instruction):
    kind: ClassVar[str] = "table"
    source_id: str | None
    caption: str
    rows: tuple[TableRowInstruction, ...]
    chapter: int
    number: str | None
    label: str
    bookmark: str | None
    sequence: SequenceInstruction | None = None

    @classmethod
    def from_typed_rows(
        cls,
        *,
        source_id: str | None,
        caption: str,
        rows: tuple[TableRowInstruction, ...],
        chapter: int,
        number: str | None,
        label: str,
        bookmark: str | None,
        sequence: SequenceInstruction | None = None,
    ) -> Self:
        return cls(
            source_id=source_id,
            caption=caption,
            rows=rows,
            chapter=chapter,
            number=number,
            label=label,
            bookmark=bookmark,
            sequence=sequence,
        )

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "caption": self.caption,
            "rows": [
                {
                    "header": row.header,
                    "cells": [
                        {"text": cell.text, "alignment": cell.alignment}
                        for cell in row.cells
                    ],
                }
                for row in self.rows
            ],
            "number": self.number,
            "label": self.label,
            "bookmark": self.bookmark,
            "sequence": self.sequence.payload if self.sequence is not None else None,
        }


@dataclass(frozen=True, slots=True)
class EquationInstruction(_Instruction):
    kind: ClassVar[str] = "equation"
    source_id: str | None
    latex: str
    alignment: str
    chapter: int
    number: str | None
    label: str
    bookmark: str | None
    sequence: SequenceInstruction | None = None
    display: bool = True

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "latex": self.latex,
            "number": self.number,
            "label": self.label,
            "bookmark": self.bookmark,
            "sequence": self.sequence.payload if self.sequence is not None else None,
        }


@dataclass(frozen=True, slots=True)
class ListingInstruction(_Instruction):
    kind: ClassVar[str] = "listing"
    source_id: str | None
    caption: str
    language: str | None
    code: str
    bookmark: str | None

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "caption": self.caption,
            "language": self.language,
            "code": self.code,
            "bookmark": self.bookmark,
        }


@dataclass(frozen=True, slots=True)
class AlgorithmInstruction(_Instruction):
    kind: ClassVar[str] = "algorithm"
    source_id: str | None
    caption: str
    body: str
    bookmark: str | None

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "id": self.source_id,
            "caption": self.caption,
            "body": self.body,
            "bookmark": self.bookmark,
        }


@dataclass(frozen=True, slots=True)
class FootnoteDefinitionInstruction(_Instruction):
    kind: ClassVar[str] = "footnote_definition"
    label: str
    footnote_id: int
    text: str
    inlines: tuple[InlineRun, ...] = ()

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "footnote_id": self.footnote_id,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class BibliographyEntryInstruction:
    key: str
    ordinal: int
    text: str


@dataclass(frozen=True, slots=True)
class BibliographyInstruction(_Instruction):
    kind: ClassVar[str] = "bibliography"
    entries: tuple[BibliographyEntryInstruction, ...] = ()

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "entries": [
                {
                    "key": entry.key,
                    "ordinal": entry.ordinal,
                    "text": entry.text,
                }
                for entry in self.entries
            ]
        }


@dataclass(frozen=True, slots=True)
class CoverInstruction(_Instruction):
    kind: ClassVar[str] = "cover"
    university: str = ""
    college: str = ""
    title: str = ""
    title_en: str = ""
    major: str = ""
    degree: str = ""
    author: str = ""
    student_id: str = ""
    advisor: str = ""
    advisor_title: str = ""
    completed: str = ""

    def value_for(self, field: str) -> str:
        values = {
            "university.name": self.university,
            "university.college": self.college,
            "thesis.title": self.title,
            "thesis.title_en": self.title_en,
            "thesis.major": self.major,
            "thesis.degree": self.degree,
            "author.name": self.author,
            "author.student_id": self.student_id,
            "advisor.name": self.advisor,
            "advisor.title": self.advisor_title,
            "dates.completed": self.completed,
        }
        try:
            return values[field]
        except KeyError as error:
            raise ValueError(f"unsupported cover field: {field}") from error

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "university": self.university,
            "college": self.college,
            "title": self.title,
            "title_en": self.title_en,
            "major": self.major,
            "degree": self.degree,
            "author": self.author,
            "student_id": self.student_id,
            "advisor": self.advisor,
            "advisor_title": self.advisor_title,
            "completed": self.completed,
        }


@dataclass(frozen=True, slots=True)
class TocEntryInstruction:
    """One cached table-of-contents entry resolved at compile time.

    Page numbers are unknown without a layout engine; renderers emit a
    reference field (e.g. PAGEREF) per entry with a placeholder cached value.
    """

    text: str
    level: int
    bookmark: str | None = None

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "level": self.level,
            "bookmark": self.bookmark,
        }


@dataclass(frozen=True, slots=True)
class TocInstruction(_Instruction):
    kind: ClassVar[str] = "toc"
    min_level: int = 1
    max_level: int = 3
    entries: tuple[TocEntryInstruction, ...] = ()

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "min_level": self.min_level,
            "max_level": self.max_level,
            "entries": [entry.payload for entry in self.entries],
        }


@dataclass(frozen=True, slots=True)
class PageBreakInstruction(_Instruction):
    kind: ClassVar[str] = "page_break"

    @property
    def payload(self) -> dict[str, Any]:
        return {}


@dataclass(frozen=True, slots=True)
class SectionBreakInstruction(_Instruction):
    kind: ClassVar[str] = "section_break"
    role: Literal["cover", "front_matter", "main"]

    @property
    def payload(self) -> dict[str, Any]:
        return {"role": self.role}


RenderInstruction: TypeAlias = (
    HeadingInstruction
    | ParagraphInstruction
    | ListInstruction
    | FigureInstruction
    | TableInstruction
    | EquationInstruction
    | ListingInstruction
    | AlgorithmInstruction
    | FootnoteDefinitionInstruction
    | BibliographyInstruction
    | CoverInstruction
    | TocInstruction
    | PageBreakInstruction
    | SectionBreakInstruction
)


@dataclass(frozen=True, slots=True)
class ResolvedReference:
    target_id: str
    bookmark: str
    display_text: str


@dataclass(slots=True)
class RenderPlan:
    nodes: list[RenderInstruction | RenderNode] = field(default_factory=list)
    template: ThesisTemplate | None = None
    template_path: Path | None = None
    bookmarks: dict[str, str] = field(default_factory=dict)
    references: dict[str, ResolvedReference] = field(default_factory=dict)
    citation_order: tuple[str, ...] = ()
    section_policy: SectionsSpec | None = None
    initial_section_role: Literal["cover", "front_matter", "main"] | None = None
