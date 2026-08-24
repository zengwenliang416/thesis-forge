"""Typed reader-facing projection of a resolved RenderPlan."""

from __future__ import annotations

import re
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from typing import TYPE_CHECKING, Literal, TypeAlias

from thesis_forge.core.model import (
    Algorithm,
    BibliographyBlock,
    Block,
    BlockQuote,
    BulletList,
    CodeBlock,
    Equation,
    Figure,
    FootnoteDefinition,
    Heading,
    ListBlock,
    Listing,
    OrderedList,
    Paragraph,
    Table,
    ThesisDocument,
)
from thesis_forge.core.render_plan import (
    AlgorithmInstruction,
    BibliographyInstruction,
    BlockQuoteInstruction,
    CitationRun,
    CodeBlockInstruction,
    CoverInstruction,
    EquationInstruction,
    FigureInstruction,
    FootnoteDefinitionInstruction,
    FootnoteReferenceRun,
    HardBreakRun,
    HeadingInstruction,
    HyperlinkRun,
    InlineRun,
    ListingInstruction,
    ListInstruction,
    MathRun,
    PageBreakInstruction,
    ParagraphInstruction,
    ReferenceRun,
    RenderInstruction,
    SectionBreakInstruction,
    SoftBreakRun,
    TableInstruction,
    TextRun,
    TocInstruction,
)

if TYPE_CHECKING:
    from thesis_forge.application.contracts import PreviewResult
    from thesis_forge.core.model import ValidationIssue

__all__ = [
    "REVIEW_PROJECTION_REGISTRY",
    "ReviewAlgorithmContent",
    "ReviewBibliographyContent",
    "ReviewBibliographyEntry",
    "ReviewBlock",
    "ReviewBlockQuoteContent",
    "ReviewCitationRun",
    "ReviewCodeBlockContent",
    "ReviewContent",
    "ReviewCoverContent",
    "ReviewCoverField",
    "ReviewDocument",
    "ReviewEquationContent",
    "ReviewFigureContent",
    "ReviewFootnoteContent",
    "ReviewFootnoteReferenceRun",
    "ReviewHardBreakRun",
    "ReviewHeadingContent",
    "ReviewHyperlinkRun",
    "ReviewInline",
    "ReviewListContent",
    "ReviewListItem",
    "ReviewListingContent",
    "ReviewMathRun",
    "ReviewPageBreakContent",
    "ReviewParagraphContent",
    "ReviewReferenceRun",
    "ReviewSectionContent",
    "ReviewSoftBreakRun",
    "ReviewSource",
    "ReviewTableCell",
    "ReviewTableContent",
    "ReviewTableRow",
    "ReviewTextRun",
    "ReviewTocContent",
    "ReviewTocEntry",
    "map_review_result",
    "project_instruction",
    "project_review",
]

ReviewStatus: TypeAlias = Literal["ready", "partial", "blocked"]


@dataclass(frozen=True, slots=True)
class ReviewSource:
    """Source navigation data kept out of visible Review content."""

    node_id: str
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None


@dataclass(frozen=True, slots=True)
class ReviewTextRun:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


@dataclass(frozen=True, slots=True)
class ReviewReferenceRun:
    text: str


@dataclass(frozen=True, slots=True)
class ReviewCitationRun:
    text: str


@dataclass(frozen=True, slots=True)
class ReviewFootnoteReferenceRun:
    text: str
    footnote_id: int


@dataclass(frozen=True, slots=True)
class ReviewHyperlinkRun:
    text: str
    destination: str


@dataclass(frozen=True, slots=True)
class ReviewMathRun:
    text: str
    latex: str


@dataclass(frozen=True, slots=True)
class ReviewSoftBreakRun:
    text: str = " "


@dataclass(frozen=True, slots=True)
class ReviewHardBreakRun:
    text: str = "\n"


ReviewInline: TypeAlias = (
    ReviewTextRun
    | ReviewReferenceRun
    | ReviewCitationRun
    | ReviewFootnoteReferenceRun
    | ReviewHyperlinkRun
    | ReviewMathRun
    | ReviewSoftBreakRun
    | ReviewHardBreakRun
)


@dataclass(frozen=True, slots=True)
class ReviewHeadingContent:
    text: str
    level: int
    runs: tuple[ReviewInline, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewParagraphContent:
    text: str
    runs: tuple[ReviewInline, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewCodeBlockContent:
    language: str | None
    code: str


@dataclass(frozen=True, slots=True)
class ReviewBlockQuoteContent:
    children: tuple[ReviewContent, ...]


@dataclass(frozen=True, slots=True)
class ReviewListItem:
    text: str
    level: int
    ordinal: int | None
    runs: tuple[ReviewInline, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewListContent:
    ordered: bool
    start: int | None
    items: tuple[ReviewListItem, ...]


@dataclass(frozen=True, slots=True)
class ReviewFigureContent:
    label: str
    caption: str
    asset_handle: str
    available: bool
    width: str | None


@dataclass(frozen=True, slots=True)
class ReviewTableCell:
    text: str
    alignment: Literal["left", "center", "right"] | None = None


@dataclass(frozen=True, slots=True)
class ReviewTableRow:
    header: bool
    cells: tuple[ReviewTableCell, ...]


@dataclass(frozen=True, slots=True)
class ReviewTableContent:
    label: str
    caption: str
    rows: tuple[ReviewTableRow, ...]


@dataclass(frozen=True, slots=True)
class ReviewEquationContent:
    label: str
    latex: str
    alignment: str


@dataclass(frozen=True, slots=True)
class ReviewListingContent:
    caption: str
    language: str | None
    code: str


@dataclass(frozen=True, slots=True)
class ReviewAlgorithmContent:
    caption: str
    body: str


@dataclass(frozen=True, slots=True)
class ReviewFootnoteContent:
    footnote_id: int
    text: str
    runs: tuple[ReviewInline, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewBibliographyEntry:
    ordinal: int
    text: str


@dataclass(frozen=True, slots=True)
class ReviewBibliographyContent:
    entries: tuple[ReviewBibliographyEntry, ...]


@dataclass(frozen=True, slots=True)
class ReviewCoverField:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class ReviewCoverContent:
    fields: tuple[ReviewCoverField, ...]


@dataclass(frozen=True, slots=True)
class ReviewTocEntry:
    text: str
    level: int


@dataclass(frozen=True, slots=True)
class ReviewTocContent:
    entries: tuple[ReviewTocEntry, ...]
    min_level: int
    max_level: int


@dataclass(frozen=True, slots=True)
class ReviewSectionContent:
    role: Literal["cover", "front_matter", "main"]


@dataclass(frozen=True, slots=True)
class ReviewPageBreakContent:
    pass


ReviewContent: TypeAlias = (
    ReviewHeadingContent
    | ReviewParagraphContent
    | ReviewCodeBlockContent
    | ReviewBlockQuoteContent
    | ReviewListContent
    | ReviewFigureContent
    | ReviewTableContent
    | ReviewEquationContent
    | ReviewListingContent
    | ReviewAlgorithmContent
    | ReviewFootnoteContent
    | ReviewBibliographyContent
    | ReviewCoverContent
    | ReviewTocContent
    | ReviewSectionContent
    | ReviewPageBreakContent
)


@dataclass(frozen=True, slots=True)
class ReviewBlock:
    kind: str
    content: ReviewContent
    source: ReviewSource | None = None


@dataclass(frozen=True, slots=True)
class ReviewDocument:
    blocks: tuple[ReviewBlock, ...]
    status: ReviewStatus = "ready"
    issues: tuple[ValidationIssue, ...] = ()


_TECHNICAL_MARKER_RE = re.compile(
    r"\[@[^\]]+\]|\{#[A-Za-z0-9_.:-]+\}|"
    r"(?<![\w-])@?(?:fig|tbl|eq|sec|chap|lst|alg):[A-Za-z0-9_.-]+"
)
_FOOTNOTE_MARKER_RE = re.compile(r"\[\^[^\]]+\]")
_ABSOLUTE_PATH_RE = re.compile(
    r"(?<![\w:])/(?:Users|Volumes|private|tmp|var|home|opt|etc|"
    r"Applications|System|Library)(?:/[^\s]*)?"
)
_WINDOWS_PATH_RE = re.compile(r"(?<![\w])(?:[A-Za-z]:\\|\\\\)[^\s]+")


def _safe_plain_text(value: str) -> str:
    value = _TECHNICAL_MARKER_RE.sub("", value)
    value = _FOOTNOTE_MARKER_RE.sub("脚注", value)
    value = _ABSOLUTE_PATH_RE.sub("", value)
    return _WINDOWS_PATH_RE.sub("", value)


def _visible_reference_text(value: str) -> str:
    value = _safe_plain_text(value)
    return value or "引用"


def _visible_citation_text(run: CitationRun) -> str:
    if run.text and not _TECHNICAL_MARKER_RE.search(run.text):
        return _safe_plain_text(run.text)
    if run.ordinals:
        return "[" + ", ".join(str(ordinal) for ordinal in run.ordinals) + "]"
    return "引用"


def _inline_runs(runs: tuple[InlineRun, ...]) -> tuple[ReviewInline, ...]:
    projected: list[ReviewInline] = []
    for run in runs:
        if isinstance(run, TextRun):
            text = run.text if run.code else _safe_plain_text(run.text)
            projected.append(
                ReviewTextRun(
                    text=text,
                    bold=run.bold,
                    italic=run.italic,
                    code=run.code,
                )
            )
        elif isinstance(run, ReferenceRun):
            projected.append(
                ReviewReferenceRun(text=_visible_reference_text(run.display_text))
            )
        elif isinstance(run, CitationRun):
            projected.append(ReviewCitationRun(text=_visible_citation_text(run)))
        elif isinstance(run, FootnoteReferenceRun):
            projected.append(
                ReviewFootnoteReferenceRun(
                    text=f"脚注{run.footnote_id}",
                    footnote_id=run.footnote_id,
                )
            )
        elif isinstance(run, HyperlinkRun):
            projected.append(
                ReviewHyperlinkRun(
                    text=_safe_plain_text(run.text),
                    destination=run.destination,
                )
            )
        elif isinstance(run, MathRun):
            projected.append(
                ReviewMathRun(
                    text=_safe_plain_text(run.latex),
                    latex=run.latex,
                )
            )
        elif isinstance(run, SoftBreakRun):
            projected.append(ReviewSoftBreakRun())
        elif isinstance(run, HardBreakRun):
            projected.append(ReviewHardBreakRun())
        else:
            raise TypeError(f"unsupported InlineRun: {type(run).__name__}")
    return tuple(projected)


def _visible_text(text: str, runs: tuple[ReviewInline, ...]) -> str:
    if runs:
        return "".join(run.text for run in runs)
    return _safe_plain_text(text)


def _source(block: Block | None) -> ReviewSource | None:
    if block is None:
        return None
    location = block.location
    return ReviewSource(
        node_id=str(block.node_id),
        line=location.line,
        column=location.column,
        end_line=location.end_line,
        end_column=location.end_column,
    )


@dataclass(slots=True)
class _SourceIndex:
    by_id: dict[str, Block]
    anonymous: dict[type[Block], deque[Block]]
    footnotes: dict[str, FootnoteDefinition]
    bibliography: deque[BibliographyBlock]

    @classmethod
    def from_document(cls, document: ThesisDocument) -> _SourceIndex:
        anonymous: dict[type[Block], deque[Block]] = defaultdict(deque)
        footnotes: dict[str, FootnoteDefinition] = {}
        bibliography: deque[BibliographyBlock] = deque()
        for block in document.blocks:
            if block.id is None:
                anonymous[type(block)].append(block)
            if isinstance(block, FootnoteDefinition):
                footnotes[block.label] = block
            if isinstance(block, BibliographyBlock):
                bibliography.append(block)
        return cls(
            by_id=document.index_by_id(),
            anonymous=anonymous,
            footnotes=footnotes,
            bibliography=bibliography,
        )

    def locate(self, instruction: RenderInstruction) -> Block | None:
        source_id = getattr(instruction, "source_id", None)
        if isinstance(source_id, str):
            return self.by_id.get(source_id)
        if isinstance(instruction, FootnoteDefinitionInstruction):
            return self.footnotes.get(instruction.label)
        if isinstance(instruction, BibliographyInstruction):
            return self.bibliography.popleft() if self.bibliography else None

        if isinstance(instruction, HeadingInstruction):
            block_types = (Heading,)
        elif isinstance(instruction, ParagraphInstruction):
            block_types = (Paragraph,)
        elif isinstance(instruction, CodeBlockInstruction):
            block_types = (CodeBlock,)
        elif isinstance(instruction, BlockQuoteInstruction):
            block_types = (BlockQuote,)
        elif isinstance(instruction, ListInstruction):
            block_types = (ListBlock, OrderedList, BulletList)
        elif isinstance(instruction, FigureInstruction):
            block_types = (Figure,)
        elif isinstance(instruction, TableInstruction):
            block_types = (Table,)
        elif isinstance(instruction, EquationInstruction):
            block_types = (Equation,)
        elif isinstance(instruction, ListingInstruction):
            block_types = (Listing,)
        elif isinstance(instruction, AlgorithmInstruction):
            block_types = (Algorithm,)
        else:
            return None

        for block_type in block_types:
            queue = self.anonymous.get(block_type)
            if queue:
                return queue.popleft()
        return None


def _project_heading(instruction: HeadingInstruction) -> ReviewHeadingContent:
    runs = _inline_runs(instruction.inlines)
    return ReviewHeadingContent(
        text=_visible_text(instruction.text, runs),
        level=instruction.level,
        runs=runs,
    )


def _project_paragraph(instruction: ParagraphInstruction) -> ReviewParagraphContent:
    runs = _inline_runs(instruction.inlines)
    return ReviewParagraphContent(
        text=_visible_text(instruction.text, runs),
        runs=runs,
    )


def _project_code_block(
    instruction: CodeBlockInstruction,
) -> ReviewCodeBlockContent:
    return ReviewCodeBlockContent(
        language=instruction.language,
        code=instruction.code,
    )


def _project_blockquote(
    instruction: BlockQuoteInstruction,
) -> ReviewBlockQuoteContent:
    return ReviewBlockQuoteContent(
        children=tuple(project_instruction(child) for child in instruction.children)
    )


def _project_list(instruction: ListInstruction) -> ReviewListContent:
    items = []
    for item in instruction.items:
        runs = _inline_runs(item.inlines)
        items.append(
            ReviewListItem(
                text=_visible_text(item.text, runs),
                level=item.level,
                ordinal=item.ordinal,
                runs=runs,
            )
        )
    return ReviewListContent(
        ordered=instruction.ordered,
        start=instruction.start,
        items=tuple(items),
    )


def _project_figure(instruction: FigureInstruction) -> ReviewFigureContent:
    seed = instruction.source_id or instruction.src or "anonymous"
    safe_handle = sha256(seed.encode("utf-8")).hexdigest()[:16]
    return ReviewFigureContent(
        label=_safe_plain_text(instruction.label),
        caption=_safe_plain_text(instruction.caption),
        asset_handle=f"asset:{safe_handle}",
        available=instruction.asset_path.is_file(),
        width=instruction.width,
    )


def _project_table(instruction: TableInstruction) -> ReviewTableContent:
    rows = tuple(
        ReviewTableRow(
            header=row.header,
            cells=tuple(
                ReviewTableCell(
                    text=_safe_plain_text(cell.text),
                    alignment=cell.alignment,
                )
                for cell in row.cells
            ),
        )
        for row in instruction.rows
    )
    return ReviewTableContent(
        label=_safe_plain_text(instruction.label),
        caption=_safe_plain_text(instruction.caption),
        rows=rows,
    )


def _project_equation(instruction: EquationInstruction) -> ReviewEquationContent:
    return ReviewEquationContent(
        label=_safe_plain_text(instruction.label),
        latex=instruction.latex,
        alignment=instruction.alignment,
    )


def _project_listing(instruction: ListingInstruction) -> ReviewListingContent:
    return ReviewListingContent(
        caption=_safe_plain_text(instruction.caption),
        language=instruction.language,
        code=instruction.code,
    )


def _project_algorithm(instruction: AlgorithmInstruction) -> ReviewAlgorithmContent:
    return ReviewAlgorithmContent(
        caption=_safe_plain_text(instruction.caption),
        body=_safe_plain_text(instruction.body),
    )


def _project_footnote(
    instruction: FootnoteDefinitionInstruction,
) -> ReviewFootnoteContent:
    runs = _inline_runs(instruction.inlines)
    return ReviewFootnoteContent(
        footnote_id=instruction.footnote_id,
        text=_visible_text(instruction.text, runs),
        runs=runs,
    )


def _project_bibliography(
    instruction: BibliographyInstruction,
) -> ReviewBibliographyContent:
    return ReviewBibliographyContent(
        entries=tuple(
            ReviewBibliographyEntry(
                ordinal=entry.ordinal,
                text=_safe_plain_text(entry.text),
            )
            for entry in instruction.entries
        )
    )


def _project_cover(instruction: CoverInstruction) -> ReviewCoverContent:
    fields = (
        ("学校", instruction.university),
        ("学院", instruction.college),
        ("题目", instruction.title),
        ("英文题目", instruction.title_en),
        ("专业", instruction.major),
        ("学位", instruction.degree),
        ("作者", instruction.author),
        ("学号", instruction.student_id),
        ("导师", instruction.advisor),
        ("导师职称", instruction.advisor_title),
        ("完成日期", instruction.completed),
    )
    return ReviewCoverContent(
        fields=tuple(
            ReviewCoverField(label=label, value=_safe_plain_text(value))
            for label, value in fields
            if value
        )
    )


def _project_toc(instruction: TocInstruction) -> ReviewTocContent:
    return ReviewTocContent(
        entries=tuple(
            ReviewTocEntry(
                text=_safe_plain_text(entry.text),
                level=entry.level,
            )
            for entry in instruction.entries
        ),
        min_level=instruction.min_level,
        max_level=instruction.max_level,
    )


def _project_section(instruction: SectionBreakInstruction) -> ReviewSectionContent:
    return ReviewSectionContent(role=instruction.role)


def _project_page_break(
    instruction: PageBreakInstruction,
) -> ReviewPageBreakContent:
    return ReviewPageBreakContent()


ReviewProjector: TypeAlias = Callable[[object], ReviewContent]

REVIEW_PROJECTION_REGISTRY: dict[type[object], ReviewProjector] = {
    HeadingInstruction: _project_heading,
    ParagraphInstruction: _project_paragraph,
    CodeBlockInstruction: _project_code_block,
    BlockQuoteInstruction: _project_blockquote,
    ListInstruction: _project_list,
    FigureInstruction: _project_figure,
    TableInstruction: _project_table,
    EquationInstruction: _project_equation,
    ListingInstruction: _project_listing,
    AlgorithmInstruction: _project_algorithm,
    FootnoteDefinitionInstruction: _project_footnote,
    BibliographyInstruction: _project_bibliography,
    CoverInstruction: _project_cover,
    TocInstruction: _project_toc,
    PageBreakInstruction: _project_page_break,
    SectionBreakInstruction: _project_section,
}


def project_instruction(instruction: RenderInstruction) -> ReviewContent:
    projector = REVIEW_PROJECTION_REGISTRY.get(type(instruction))
    if projector is None:
        raise TypeError(
            f"unsupported RenderInstruction: {type(instruction).__name__}"
        )
    return projector(instruction)


def project_review(result: PreviewResult) -> ReviewDocument:
    if result.plan is None:
        return ReviewDocument(
            blocks=(),
            status="blocked",
            issues=result.issues,
        )

    source_index = _SourceIndex.from_document(result.document)
    blocks = tuple(
        ReviewBlock(
            kind=(
                "footnote"
                if isinstance(instruction, FootnoteDefinitionInstruction)
                else instruction.kind
            ),
            content=project_instruction(instruction),
            source=_source(source_index.locate(instruction)),
        )
        for instruction in result.plan.nodes
    )
    status: ReviewStatus = "partial" if result.errors else "ready"
    return ReviewDocument(
        blocks=blocks,
        status=status,
        issues=result.issues,
    )


def map_review_result(result: PreviewResult) -> ReviewDocument:
    """Public presenter entry matching the existing preview mapper naming."""

    return project_review(result)
