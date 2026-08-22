from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Severity = Literal["info", "warning", "error"]

NodeId = str

_node_id_counter = itertools.count(1)


def _next_node_id() -> NodeId:
    return f"n{next(_node_id_counter)}"


@dataclass(slots=True)
class SourceLocation:
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None
    source_file: str | None = None


@dataclass(frozen=True, slots=True)
class GeneratedOrigin:
    generator: str = ""
    source_node_ids: tuple[NodeId, ...] = ()


@dataclass(slots=True)
class Inline:
    location: SourceLocation = field(default_factory=SourceLocation)
    node_id: NodeId = field(default_factory=_next_node_id, compare=False)
    origin: GeneratedOrigin | None = None


@dataclass(slots=True)
class Text(Inline):
    value: str = ""


@dataclass(slots=True)
class Strong(Inline):
    children: tuple[Inline, ...] = ()


@dataclass(slots=True)
class SoftBreak(Inline):
    pass


@dataclass(slots=True)
class HardBreak(Inline):
    pass


@dataclass(slots=True)
class Emphasis(Inline):
    children: tuple[Inline, ...] = ()


@dataclass(slots=True)
class Link(Inline):
    label: str = ""
    destination: str = ""


@dataclass(slots=True)
class InlineMath(Inline):
    latex: str = ""


@dataclass(slots=True)
class InlineCode(Inline):
    value: str = ""


@dataclass(slots=True)
class CrossReference(Inline):
    target: str = ""
    fallback: str | None = None
    display_mode: str | None = None


@dataclass(slots=True)
class Citation(Inline):
    keys: list[str] = field(default_factory=list)
    locator: str | None = None
    raw: str = ""


@dataclass(slots=True)
class FootnoteReference(Inline):
    label: str = ""


def inline_plain_text(inlines: list[Inline] | tuple[Inline, ...]) -> str:
    """Derive the canonical plain-text form of an inline sequence.

    Pure derivation: the input is never mutated, and every known Inline
    subclass maps to a deterministic text fragment. Unknown subclasses raise
    TypeError instead of being silently skipped.
    """
    parts: list[str] = []
    for inline in inlines:
        if isinstance(inline, (Text, InlineCode)):
            parts.append(inline.value)
        elif isinstance(inline, (Strong, Emphasis)):
            parts.append(inline_plain_text(list(inline.children)))
        elif isinstance(inline, Link):
            parts.append(inline.label)
        elif isinstance(inline, InlineMath):
            parts.append(inline.latex)
        elif isinstance(inline, (SoftBreak, HardBreak)):
            parts.append("\n")
        elif isinstance(inline, Citation):
            parts.append(inline.raw)
        elif isinstance(inline, CrossReference):
            parts.append(inline.fallback if inline.fallback is not None else inline.target)
        elif isinstance(inline, FootnoteReference):
            parts.append("")
        else:
            raise TypeError(f"unknown Inline subclass: {type(inline).__name__}")
    return "".join(parts)


@dataclass(slots=True)
class Block:
    id: str | None = None
    location: SourceLocation = field(default_factory=SourceLocation)
    node_id: NodeId = field(default_factory=_next_node_id, compare=False)
    origin: GeneratedOrigin | None = None


@dataclass(slots=True)
class Heading(Block):
    level: int = 1
    inlines: list[Inline] = field(default_factory=list)


@dataclass(slots=True)
class Paragraph(Block):
    inlines: list[Inline] = field(default_factory=list)


@dataclass(slots=True)
class ListItem:
    level: int = 0
    marker: str = ""
    ordinal: int | None = None
    location: SourceLocation = field(default_factory=SourceLocation)
    inlines: list[Inline] = field(default_factory=list)
    node_id: NodeId = field(default_factory=_next_node_id, compare=False)
    origin: GeneratedOrigin | None = None
    children: tuple[Block, ...] = ()


@dataclass(slots=True)
class TableCell:
    inlines: tuple[Inline, ...] = ()
    alignment: Literal["left", "center", "right"] | None = None
    location: SourceLocation = field(default_factory=SourceLocation)
    node_id: NodeId = field(default_factory=_next_node_id, compare=False)
    origin: GeneratedOrigin | None = None


@dataclass(slots=True)
class TableRow:
    header: bool = False
    cells: tuple[TableCell, ...] = ()
    location: SourceLocation = field(default_factory=SourceLocation)
    node_id: NodeId = field(default_factory=_next_node_id, compare=False)
    origin: GeneratedOrigin | None = None


@dataclass(slots=True)
class ListBlock(Block):
    ordered: bool = False
    start: int | None = None
    items: list[ListItem] = field(default_factory=list)


@dataclass(slots=True)
class BlockQuote(Block):
    children: tuple[Block, ...] = ()


@dataclass(slots=True)
class CodeBlock(Block):
    language: str | None = None
    code: str = ""


@dataclass(slots=True)
class OrderedList(Block):
    start: int | None = None
    items: tuple[ListItem, ...] = ()


@dataclass(slots=True)
class BulletList(Block):
    items: tuple[ListItem, ...] = ()


@dataclass(slots=True)
class Figure(Block):
    src: str = ""
    caption: str = ""
    width: str | None = None


@dataclass(slots=True)
class Table(Block):
    caption_inlines: tuple[Inline, ...] = ()
    rows: tuple[TableRow, ...] = ()


@dataclass(slots=True)
class Equation(Block):
    latex: str = ""


@dataclass(slots=True)
class Listing(Block):
    caption: str = ""
    language: str | None = None
    code: str = ""


@dataclass(slots=True)
class Algorithm(Block):
    caption: str = ""
    body: str = ""


@dataclass(slots=True)
class FootnoteDefinition(Block):
    label: str = ""
    text: str = ""
    inlines: list[Inline] = field(default_factory=list)


@dataclass(slots=True)
class BibliographyBlock(Block):
    pass


@dataclass(slots=True)
class BibliographyConfig:
    path: str | None = None
    citation_style: str | None = None


@dataclass(slots=True)
class ThesisDocument:
    source_path: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)
    bibliography: BibliographyConfig | None = None
    inline_content: list[Inline] = field(default_factory=list)
    cross_references: list[CrossReference] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    footnote_references: list[FootnoteReference] = field(default_factory=list)

    def index_by_id(self) -> dict[str, Block]:
        return {block.id: block for block in self.blocks if block.id}

    def register_inlines(self, inlines: list[Inline]) -> None:
        for inline in inlines:
            self.inline_content.append(inline)
            if isinstance(inline, CrossReference):
                self.cross_references.append(inline)
            elif isinstance(inline, Citation):
                self.citations.append(inline)
            elif isinstance(inline, FootnoteReference):
                self.footnote_references.append(inline)
            if isinstance(inline, (Strong, Emphasis)):
                self.register_inlines(list(inline.children))


@dataclass(slots=True)
class ValidationIssue:
    code: str
    severity: Severity
    message: str
    line: int | None = None
    target: str | None = None
    details: dict[str, str | int] = field(default_factory=dict)
