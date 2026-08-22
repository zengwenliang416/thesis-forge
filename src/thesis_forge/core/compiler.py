from __future__ import annotations

import re
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path

from thesis_forge.bibliography import (
    BibliographyDatabase,
    CitationFormatter,
    resolve_citation_provider,
)
from thesis_forge.templates.model import NumberingSpec, SectionsSpec, ThesisTemplate

from .model import (
    Algorithm,
    BibliographyBlock,
    Block,
    Citation,
    CrossReference,
    Equation,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    Heading,
    Inline,
    InlineCode,
    ListBlock,
    Listing,
    Paragraph,
    Strong,
    Table,
    Text,
    ThesisDocument,
)
from .render_plan import (
    AlgorithmInstruction,
    BibliographyEntryInstruction,
    BibliographyInstruction,
    CitationRun,
    CoverInstruction,
    EquationInstruction,
    FigureInstruction,
    FigureWidthInstruction,
    FootnoteDefinitionInstruction,
    FootnoteReferenceRun,
    HeadingInstruction,
    InlineRun,
    ListingInstruction,
    ListInstruction,
    ListItemInstruction,
    PageBreakInstruction,
    ParagraphInstruction,
    ParagraphRole,
    ReferenceRun,
    RenderInstruction,
    RenderPlan,
    ResolvedReference,
    SectionBreakInstruction,
    SequenceInstruction,
    TableCellInstruction,
    TableInstruction,
    TableRowInstruction,
    TextRun,
    TocEntryInstruction,
    TocInstruction,
)

BOOKMARK_INVALID_RE = re.compile(r"[^A-Za-z0-9_]")
BOOKMARK_MAX_LENGTH = 40
FIGURE_WIDTH_RE = re.compile(
    r"^(?P<value>\d+(?:\.\d+)?)(?P<unit>%|mm|cm|pt|em)$"
)
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
ZH_KEYWORDS_RE = re.compile(r"^\s*(?:\*\*)?关键词\s*[：:](?:\*\*)?")
EN_KEYWORDS_RE = re.compile(
    r"^\s*(?:\*\*)?keywords\s*:(?:\*\*)?",
    re.IGNORECASE,
)

SEMANTIC_HEADING_ROLES: dict[str, ParagraphRole] = {
    "chap:abstract-zh": "abstract.zh.title",
    "chap:abstract-en": "abstract.en.title",
    "chap:toc": "toc.title",
    "chap:contents": "toc.title",
    "chap:bibliography": "bibliography.title",
    "chap:references": "bibliography.title",
    "references": "bibliography.title",
    "chap:acknowledgements": "special.acknowledgements",
    "acknowledgements": "special.acknowledgements",
    "chap:achievements": "special.achievements",
    "achievements": "special.achievements",
}

SEMANTIC_BODY_ROLES: dict[str, ParagraphRole] = {
    "chap:abstract-zh": "abstract.zh.body",
    "chap:abstract-en": "abstract.en.body",
    "chap:bibliography": "bibliography.entry",
    "chap:references": "bibliography.entry",
    "references": "bibliography.entry",
}


class CompilerError(ValueError):
    pass


class BookmarkCollisionError(CompilerError):
    def __init__(self, bookmark: str, source_ids: tuple[str, str]):
        self.bookmark = bookmark
        self.source_ids = source_ids
        super().__init__(
            f"Bookmark name collision: {bookmark}: {source_ids[0]}, {source_ids[1]}"
        )


class UnresolvedReferenceError(CompilerError):
    def __init__(self, target_id: str):
        self.target_id = target_id
        super().__init__(f"Unresolved reference target: {target_id}")


class UnresolvedFootnoteError(CompilerError):
    def __init__(self, label: str):
        self.label = label
        super().__init__(f"Unresolved footnote label: {label}")


class UnresolvedCitationError(CompilerError):
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Unresolved citation key: {key}")


class FigureWidthCompilationError(CompilerError):
    def __init__(self, width: str):
        self.width = width
        super().__init__(
            f"Invalid figure width: {width!r}; expected a positive percentage or mm/cm/pt/em"
        )


class TableCompilationError(CompilerError):
    def __init__(self, source_id: str | None, detail: str):
        self.source_id = source_id
        self.detail = detail
        super().__init__(f"Invalid Markdown table {source_id or '<anonymous>'}: {detail}")


@dataclass(frozen=True, slots=True)
class _ResolvedBlock:
    chapter: int
    number: str | None
    label: str
    bookmark: str | None
    sequence: SequenceInstruction | None


def _bookmark_name(source_id: str) -> str:
    normalized = BOOKMARK_INVALID_RE.sub("_", source_id)
    return f"tf_{normalized}"[:BOOKMARK_MAX_LENGTH]


def _numbering_spec(template: ThesisTemplate | None, kind: str) -> NumberingSpec | None:
    style = getattr(template, kind, None) if template is not None else None
    return getattr(style, "numbering", None)


def _caption_prefix(template: ThesisTemplate | None, kind: str) -> str:
    style = getattr(template, kind, None) if template is not None else None
    caption = getattr(style, "caption", None)
    return getattr(caption, "prefix", "")


def _sequence_instruction(
    *,
    kind: str,
    numbering: NumberingSpec,
    chapter: int,
    value: int,
    label: str,
    template: ThesisTemplate | None,
) -> SequenceInstruction:
    name = f"TF_{kind.title()}"
    suffix = ""
    if numbering.mode == "chapter":
        name = f"{name}_{chapter}"
        separator = numbering.separator
        if kind == "equation":
            prefix = f"({chapter}{separator}"
            suffix = ")"
        else:
            prefix = f"{_caption_prefix(template, kind)}{chapter}{separator}"
    elif kind == "equation":
        prefix = "("
        suffix = ")"
    else:
        prefix = _caption_prefix(template, kind)
    return SequenceInstruction(
        name=name,
        value=value,
        prefix=prefix,
        suffix=suffix,
        result=label,
    )


def _resolved_figure_width(
    width: str | None,
    template: ThesisTemplate | None,
) -> FigureWidthInstruction | None:
    if width is not None:
        match = FIGURE_WIDTH_RE.fullmatch(width.strip())
        if match is None:
            raise FigureWidthCompilationError(width)
        try:
            value = Decimal(match.group("value"))
        except InvalidOperation as error:
            raise FigureWidthCompilationError(width) from error
        if value <= 0:
            raise FigureWidthCompilationError(width)
        unit = match.group("unit")
        if unit == "%" and value > 100:
            raise FigureWidthCompilationError(width)
        return FigureWidthInstruction(
            value=value,
            unit="percent" if unit == "%" else unit,
            origin="source",
        )

    default_width = (
        template.figure.default_width
        if template is not None and template.figure is not None
        else None
    )
    if default_width is None:
        return None
    return FigureWidthInstruction(
        value=default_width.value,
        unit=default_width.unit,
        origin="template",
    )


def _resolve_figure_asset(source_path: Path, src: str) -> Path:
    asset_path = Path(src)
    if not asset_path.is_absolute():
        asset_path = source_path.parent / asset_path
    return asset_path.resolve()


def _split_table_row(line: str, source_id: str | None) -> tuple[str, ...]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise TableCompilationError(source_id, "rows must start and end with '|'")
    return tuple(cell.strip() for cell in stripped[1:-1].split("|"))


def _separator_alignment(cell: str, source_id: str | None) -> str | None:
    if TABLE_SEPARATOR_RE.fullmatch(cell) is None:
        raise TableCompilationError(source_id, f"invalid separator cell {cell!r}")
    if cell.startswith(":") and cell.endswith(":"):
        return "center"
    if cell.endswith(":"):
        return "right"
    if cell.startswith(":"):
        return "left"
    return None


def _compile_table_rows(
    markdown: str,
    source_id: str | None,
) -> tuple[TableRowInstruction, ...]:
    lines = [line for line in markdown.splitlines() if line.strip()]
    if not lines:
        return ()
    if len(lines) < 2:
        raise TableCompilationError(source_id, "header separator row is required")

    header = _split_table_row(lines[0], source_id)
    separator = _split_table_row(lines[1], source_id)
    if not header or len(header) != len(separator):
        raise TableCompilationError(source_id, "header and separator column count differs")
    alignments = tuple(_separator_alignment(cell, source_id) for cell in separator)
    rows = [
        TableRowInstruction(
            header=True,
            cells=tuple(
                TableCellInstruction(text=text, alignment=alignment)
                for text, alignment in zip(header, alignments, strict=True)
            ),
        )
    ]
    for line in lines[2:]:
        values = _split_table_row(line, source_id)
        if len(values) != len(header):
            raise TableCompilationError(source_id, "body row column count differs")
        rows.append(
            TableRowInstruction(
                header=False,
                cells=tuple(
                    TableCellInstruction(text=text, alignment=alignment)
                    for text, alignment in zip(values, alignments, strict=True)
                ),
            )
        )
    return tuple(rows)


def _resolve_blocks(
    document: ThesisDocument,
    template: ThesisTemplate | None,
) -> tuple[dict[str, _ResolvedBlock], dict[str, str]]:
    resolved: dict[str, _ResolvedBlock] = {}
    bookmarks: dict[str, str] = {}
    bookmark_sources: dict[str, str] = {}
    chapter = 0
    chapter_counters: dict[tuple[str, int], int] = {}
    continuous_counters: dict[str, int] = {}
    has_front_matter = (
        template is not None and template.sections.front_matter is not None
    )

    for block in document.blocks:
        if (
            isinstance(block, Heading)
            and block.level == 1
            and (not has_front_matter or not _is_front_matter_heading(block))
        ):
            chapter += 1

        bookmark = None
        if block.id:
            bookmark = _bookmark_name(block.id)
            previous = bookmark_sources.get(bookmark)
            if previous is not None and previous != block.id:
                raise BookmarkCollisionError(bookmark, (previous, block.id))
            bookmark_sources[bookmark] = block.id
            bookmarks[block.id] = bookmark

        number = None
        label = ""
        sequence = None
        kind = None
        if isinstance(block, Figure):
            kind = "figure"
        elif isinstance(block, Table):
            kind = "table"
        elif isinstance(block, Equation):
            kind = "equation"

        if kind is not None:
            numbering = _numbering_spec(template, kind)
            if numbering is not None and numbering.mode != "none":
                active_chapter = chapter or 1
                if numbering.mode == "chapter":
                    key = (kind, active_chapter)
                    chapter_counters[key] = chapter_counters.get(key, 0) + 1
                    sequence_value = chapter_counters[key]
                    number = (
                        f"{active_chapter}{numbering.separator}{sequence_value}"
                    )
                else:
                    continuous_counters[kind] = continuous_counters.get(kind, 0) + 1
                    sequence_value = continuous_counters[kind]
                    number = str(sequence_value)
            if isinstance(block, Equation):
                label = f"({number})" if number else block.id or ""
            else:
                prefix = _caption_prefix(template, kind)
                label = f"{prefix}{number}" if number else block.caption
            if numbering is not None and number is not None:
                sequence = _sequence_instruction(
                    kind=kind,
                    numbering=numbering,
                    chapter=chapter or 1,
                    value=sequence_value,
                    label=label,
                    template=template,
                )
        elif isinstance(block, Heading):
            label = block.text
        elif isinstance(block, (Listing, Algorithm)):
            label = block.caption
        elif block.id:
            label = block.id

        if block.id:
            resolved[block.id] = _ResolvedBlock(
                chapter=chapter or 1,
                number=number,
                label=label,
                bookmark=bookmark,
                sequence=sequence,
            )

    return resolved, bookmarks


def _compile_inlines(
    inlines: list[Inline],
    resolved: dict[str, _ResolvedBlock],
    citation_numbers: dict[str, int],
    footnote_ids: dict[str, int],
    bibliography_database: BibliographyDatabase | None,
    citation_formatter: CitationFormatter | None,
) -> tuple[InlineRun, ...]:
    runs: list[InlineRun] = []
    for inline in inlines:
        if isinstance(inline, Text):
            runs.append(TextRun(inline.value))
        elif isinstance(inline, InlineCode):
            runs.append(TextRun(inline.value, code=True))
        elif isinstance(inline, Strong):
            runs.append(TextRun(inline.value, bold=True))
        elif isinstance(inline, CrossReference):
            target = resolved.get(inline.target)
            if target is None or target.bookmark is None:
                raise UnresolvedReferenceError(inline.target)
            runs.append(
                ReferenceRun(
                    target_id=inline.target,
                    bookmark=target.bookmark,
                    display_text=target.label or inline.target,
                )
            )
        elif isinstance(inline, Citation):
            ordinals = []
            records = []
            for key in inline.keys:
                if key not in citation_numbers:
                    citation_numbers[key] = len(citation_numbers) + 1
                ordinals.append(citation_numbers[key])
                if bibliography_database is not None:
                    record = bibliography_database.records.get(key)
                    if record is None:
                        raise UnresolvedCitationError(key)
                    records.append(record)
            if citation_formatter is not None and bibliography_database is not None:
                text = citation_formatter.format_citation(
                    records,
                    ordinals,
                    locator=inline.locator,
                )
            else:
                content = ",".join(str(ordinal) for ordinal in ordinals)
                if inline.locator:
                    content = f"{content}, {inline.locator}"
                text = f"[{content}]"
            runs.append(
                CitationRun(
                    keys=tuple(inline.keys),
                    ordinals=tuple(ordinals),
                    locator=inline.locator,
                    raw=inline.raw,
                    text=text,
                )
            )
        elif isinstance(inline, FootnoteReference):
            footnote_id = footnote_ids.get(inline.label)
            if footnote_id is None:
                raise UnresolvedFootnoteError(inline.label)
            runs.append(FootnoteReferenceRun(inline.label, footnote_id))
    return tuple(runs)


def _fallback_text_runs(text: str, runs: tuple[InlineRun, ...]) -> tuple[InlineRun, ...]:
    return runs or ((TextRun(text),) if text else ())


def _initial_section_role(template: ThesisTemplate | None) -> str | None:
    sections = template.sections if template is not None else None
    if sections is None:
        return None
    for role in ("cover", "front_matter", "main"):
        if getattr(sections, role) is not None:
            return role
    return None


def _metadata_text(metadata: dict, *path: str) -> str:
    value = metadata
    for part in path:
        if not isinstance(value, dict):
            return ""
        value = value.get(part)
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


def _compile_cover(document: ThesisDocument) -> CoverInstruction | None:
    metadata = document.metadata
    instruction = CoverInstruction(
        university=_metadata_text(metadata, "university", "name"),
        college=_metadata_text(metadata, "university", "college"),
        title=_metadata_text(metadata, "thesis", "title"),
        title_en=_metadata_text(metadata, "thesis", "title_en"),
        major=_metadata_text(metadata, "thesis", "major"),
        degree=_metadata_text(metadata, "thesis", "degree"),
        author=_metadata_text(metadata, "author", "name"),
        student_id=_metadata_text(metadata, "author", "student_id"),
        advisor=_metadata_text(metadata, "advisor", "name"),
        advisor_title=_metadata_text(metadata, "advisor", "title"),
        completed=_metadata_text(metadata, "dates", "completed"),
    )
    return instruction if any(instruction.payload.values()) else None


def _is_front_matter_heading(block: Heading) -> bool:
    source_id = block.id or ""
    normalized_text = block.text.strip().lower()
    return source_id.startswith(("chap:abstract", "chap:toc", "chap:contents")) or (
        normalized_text in {"摘要", "abstract", "目录", "contents"}
    )


@dataclass(slots=True)
class _SectionPlanner:
    initial_role: str | None
    sections: SectionsSpec | None
    main_started: bool

    @classmethod
    def from_template(cls, template: ThesisTemplate | None) -> _SectionPlanner:
        initial_role = _initial_section_role(template)
        return cls(
            initial_role=initial_role,
            sections=template.sections if template is not None else None,
            main_started=initial_role == "main",
        )

    def initial_instructions(self) -> tuple[RenderInstruction, ...]:
        if self.initial_role != "cover" or self.sections is None:
            return ()
        if self.sections.front_matter is not None:
            return (SectionBreakInstruction(role="front_matter"),)
        if self.sections.main is not None:
            self.main_started = True
            return (SectionBreakInstruction(role="main"),)
        return ()

    def before_block(self, block: Block) -> tuple[RenderInstruction, ...]:
        if (
            self.main_started
            or not isinstance(block, Heading)
            or block.level != 1
            or _is_front_matter_heading(block)
            or self.sections is None
            or self.sections.front_matter is None
        ):
            return ()

        self.main_started = True
        instructions: list[RenderInstruction] = [PageBreakInstruction(), TocInstruction()]
        if self.sections.main is not None:
            instructions.append(SectionBreakInstruction(role="main"))
        return tuple(instructions)


@dataclass(slots=True)
class _SemanticContext:
    active_paragraph_role: ParagraphRole = "body"

    def role_for(self, block: Heading | Paragraph) -> ParagraphRole | None:
        if isinstance(block, Heading):
            if block.level != 1:
                return None
            self.active_paragraph_role = "body"
            if block.id is None:
                return None
            self.active_paragraph_role = SEMANTIC_BODY_ROLES.get(block.id, "body")
            return SEMANTIC_HEADING_ROLES.get(block.id)

        if (
            self.active_paragraph_role == "abstract.zh.body"
            and ZH_KEYWORDS_RE.match(block.text)
        ):
            return "keywords.zh"
        if (
            self.active_paragraph_role == "abstract.en.body"
            and EN_KEYWORDS_RE.match(block.text)
        ):
            return "keywords.en"
        return self.active_paragraph_role


@dataclass(slots=True)
class _CompilationContext:
    document: ThesisDocument
    template: ThesisTemplate | None
    resolved: dict[str, _ResolvedBlock]
    citation_numbers: dict[str, int]
    footnote_ids: dict[str, int]
    bibliography_database: BibliographyDatabase | None
    citation_formatter: CitationFormatter | None
    semantic: _SemanticContext
    bibliography_emitted: bool = False

    def inlines(self, values: list[Inline]) -> tuple[InlineRun, ...]:
        return _compile_inlines(
            values,
            self.resolved,
            self.citation_numbers,
            self.footnote_ids,
            self.bibliography_database,
            self.citation_formatter,
        )

    def bibliography(self) -> BibliographyInstruction:
        self.bibliography_emitted = True
        if self.bibliography_database is None or self.citation_formatter is None:
            return BibliographyInstruction()

        keys = _citation_order(self.citation_numbers)
        records = []
        ordinals = []
        for key in keys:
            record = self.bibliography_database.records.get(key)
            if record is None:
                raise UnresolvedCitationError(key)
            records.append(record)
            ordinals.append(self.citation_numbers[key])
        texts = self.citation_formatter.format_bibliography(records, ordinals)
        return BibliographyInstruction(
            entries=tuple(
                BibliographyEntryInstruction(
                    key=record.key,
                    ordinal=ordinal,
                    text=text,
                )
                for record, ordinal, text in zip(
                    records,
                    ordinals,
                    texts,
                    strict=True,
                )
            )
        )


def _initial_citation_numbers(document: ThesisDocument) -> dict[str, int]:
    definitions = {
        block.label: block
        for block in document.blocks
        if isinstance(block, FootnoteDefinition)
    }
    referenced_labels = {
        reference.label for reference in document.footnote_references
    }
    expanded_footnotes: set[str] = set()
    seen_citations: set[int] = set()

    def citations_from_inlines(inlines: list[Inline]):
        for inline in inlines:
            if isinstance(inline, Citation):
                identity = id(inline)
                if identity not in seen_citations:
                    seen_citations.add(identity)
                    yield inline
            elif isinstance(inline, FootnoteReference):
                definition = definitions.get(inline.label)
                if definition is not None and inline.label not in expanded_footnotes:
                    expanded_footnotes.add(inline.label)
                    yield from citations_from_inlines(definition.inlines)

    def citations_from_block(block: Block):
        if isinstance(block, (Heading, Paragraph)):
            yield from citations_from_inlines(block.inlines)
        elif isinstance(block, ListBlock):
            for item in block.items:
                yield from citations_from_inlines(item.inlines)
        elif (
            isinstance(block, FootnoteDefinition)
            and block.label not in referenced_labels
            and block.label not in expanded_footnotes
        ):
            expanded_footnotes.add(block.label)
            yield from citations_from_inlines(block.inlines)

    numbers: dict[str, int] = {}
    ordered_citations = (
        citation
        for block in document.blocks
        for citation in citations_from_block(block)
    )
    for citation in ordered_citations:
        for key in citation.keys:
            if key not in numbers:
                numbers[key] = len(numbers) + 1
    for citation in document.citations:
        if id(citation) in seen_citations:
            continue
        for key in citation.keys:
            if key not in numbers:
                numbers[key] = len(numbers) + 1
    return numbers


def _footnote_ids(document: ThesisDocument) -> dict[str, int]:
    return {
        block.label: index
        for index, block in enumerate(
            (
                item
                for item in document.blocks
                if isinstance(item, FootnoteDefinition)
            ),
            start=1,
        )
    }


def _compile_list(block: ListBlock, context: _CompilationContext) -> ListInstruction:
    return ListInstruction(
        ordered=block.ordered,
        start=block.start,
        items=tuple(
            ListItemInstruction(
                text=item.text,
                level=item.level,
                ordinal=item.ordinal,
                inlines=_fallback_text_runs(item.text, context.inlines(item.inlines)),
            )
            for item in block.items
        ),
    )


def _compile_block(
    block: Block,
    context: _CompilationContext,
) -> RenderInstruction | None:
    block_resolution = context.resolved.get(block.id) if block.id else None
    bookmark = block_resolution.bookmark if block_resolution else None
    chapter = block_resolution.chapter if block_resolution else 1
    number = block_resolution.number if block_resolution else None
    label = block_resolution.label if block_resolution else ""
    sequence = block_resolution.sequence if block_resolution else None

    if isinstance(block, Heading):
        return HeadingInstruction(
            source_id=block.id,
            level=block.level,
            text=block.text,
            inlines=_fallback_text_runs(block.text, context.inlines(block.inlines)),
            bookmark=bookmark,
            role=context.semantic.role_for(block),
        )
    if isinstance(block, Paragraph):
        return ParagraphInstruction(
            text=block.text,
            inlines=_fallback_text_runs(block.text, context.inlines(block.inlines)),
            role=context.semantic.role_for(block) or "body",
        )
    if isinstance(block, ListBlock):
        return _compile_list(block, context)
    if isinstance(block, Figure):
        return FigureInstruction(
            source_id=block.id,
            src=block.src,
            asset_path=_resolve_figure_asset(context.document.source_path, block.src),
            caption=block.caption,
            width=block.width,
            resolved_width=_resolved_figure_width(block.width, context.template),
            chapter=chapter,
            number=number,
            label=label,
            bookmark=bookmark,
            sequence=sequence,
        )
    if isinstance(block, Table):
        return TableInstruction(
            source_id=block.id,
            caption=block.caption,
            markdown=block.markdown,
            rows=_compile_table_rows(block.markdown, block.id),
            chapter=chapter,
            number=number,
            label=label,
            bookmark=bookmark,
            sequence=sequence,
        )
    if isinstance(block, Equation):
        alignment = (
            context.template.equation.alignment
            if context.template is not None and context.template.equation is not None
            else "center"
        )
        return EquationInstruction(
            source_id=block.id,
            latex=block.latex,
            alignment=alignment,
            chapter=chapter,
            number=number,
            label=label,
            bookmark=bookmark,
            sequence=sequence,
        )
    if isinstance(block, Listing):
        return ListingInstruction(
            source_id=block.id,
            caption=block.caption,
            language=block.language,
            code=block.code,
            bookmark=bookmark,
        )
    if isinstance(block, Algorithm):
        return AlgorithmInstruction(
            source_id=block.id,
            caption=block.caption,
            body=block.body,
            bookmark=bookmark,
        )
    if isinstance(block, FootnoteDefinition):
        return FootnoteDefinitionInstruction(
            label=block.label,
            footnote_id=context.footnote_ids[block.label],
            text=block.text,
            inlines=_fallback_text_runs(block.text, context.inlines(block.inlines)),
        )
    if isinstance(block, BibliographyBlock):
        if context.bibliography_emitted:
            return None
        return context.bibliography()
    return None


def _resolved_references(
    resolved: dict[str, _ResolvedBlock],
) -> dict[str, ResolvedReference]:
    return {
        source_id: ResolvedReference(
            target_id=source_id,
            bookmark=value.bookmark,
            display_text=value.label or source_id,
        )
        for source_id, value in resolved.items()
        if value.bookmark is not None
    }


def _citation_order(citation_numbers: dict[str, int]) -> tuple[str, ...]:
    return tuple(
        key for key, _ in sorted(citation_numbers.items(), key=lambda item: item[1])
    )


def _attach_toc_entries(
    instructions: list[RenderInstruction],
) -> list[RenderInstruction]:
    """Fill each TOC instruction with cached entries from heading instructions.

    Entries mirror what a Word TOC field (``\\o "min-max" \\u``) would collect:
    every heading inside the level range, in document order, except the TOC
    title itself. Page numbers stay unknown at compile time (no layout engine);
    renderers emit per-entry reference fields with placeholder cached values
    (ADR-0005 §2.1, debt D-11).
    """
    headings = [
        instruction
        for instruction in instructions
        if isinstance(instruction, HeadingInstruction)
        and instruction.role != "toc.title"
    ]
    attached: list[RenderInstruction] = []
    for instruction in instructions:
        if not isinstance(instruction, TocInstruction):
            attached.append(instruction)
            continue
        entries = tuple(
            TocEntryInstruction(
                text=heading.text,
                level=heading.level,
                bookmark=heading.bookmark,
            )
            for heading in headings
            if instruction.min_level <= heading.level <= instruction.max_level
        )
        attached.append(replace(instruction, entries=entries))
    return attached


def _effective_citation_style(
    document: ThesisDocument,
    template: ThesisTemplate | None,
) -> str | None:
    """D-07：文档 render.citation_style 优先，模板 citation.style 兜底。"""

    if document.bibliography is not None and document.bibliography.citation_style:
        return document.bibliography.citation_style
    if template is not None and template.citation is not None:
        return template.citation.style
    return None


def compile_document(
    document: ThesisDocument,
    template: ThesisTemplate | None = None,
    template_path: str | Path | None = None,
    bibliography_database: BibliographyDatabase | None = None,
    citation_formatter: CitationFormatter | None = None,
) -> RenderPlan:
    """Resolve document-wide semantics into renderer-neutral instructions."""
    resolved, bookmarks = _resolve_blocks(document, template)
    context = _CompilationContext(
        document=document,
        template=template,
        resolved=resolved,
        citation_numbers=_initial_citation_numbers(document),
        footnote_ids=_footnote_ids(document),
        bibliography_database=bibliography_database,
        citation_formatter=(
            citation_formatter
            if citation_formatter is not None
            else (
                # D-07：citation_style 真正参与 provider 选择；未知样式在此
                # 抛出 UnsupportedCitationStyleError（正常流程由 validator 的
                # unsupported-citation-style 诊断先行拦截）。
                resolve_citation_provider(_effective_citation_style(document, template))
                if bibliography_database is not None
                else None
            )
        ),
        semantic=_SemanticContext(),
    )
    section_planner = _SectionPlanner.from_template(template)
    instructions: list[RenderInstruction] = []
    if section_planner.initial_role == "cover":
        cover = _compile_cover(document)
        if cover is not None:
            instructions.append(cover)
    instructions.extend(section_planner.initial_instructions())
    for block in document.blocks:
        instructions.extend(section_planner.before_block(block))
        instruction = _compile_block(block, context)
        if instruction is not None:
            instructions.append(instruction)
    if (
        context.bibliography_database is not None
        and context.citation_numbers
        and not context.bibliography_emitted
    ):
        instructions.append(context.bibliography())
    instructions = _attach_toc_entries(instructions)

    return RenderPlan(
        nodes=instructions,
        template=template,
        template_path=Path(template_path) if template_path is not None else None,
        bookmarks=bookmarks,
        references=_resolved_references(resolved),
        citation_order=_citation_order(context.citation_numbers),
        section_policy=template.sections if template is not None else None,
        initial_section_role=section_planner.initial_role,
    )
