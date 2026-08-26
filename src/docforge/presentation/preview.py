from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from docforge.application.contracts import PreviewResult
from docforge.core.model import (
    Algorithm,
    BibliographyBlock,
    Block,
    BlockQuote,
    CodeBlock,
    Equation,
    Figure,
    FootnoteDefinition,
    Heading,
    ListBlock,
    Listing,
    Paragraph,
    Table,
    ValidationIssue,
    inline_plain_text,
)
from docforge.core.render_plan import (
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
    ParagraphInstruction,
    ReferenceRun,
    SectionBreakInstruction,
    SoftBreakRun,
    TableInstruction,
    TextRun,
    TocInstruction,
    ensure_inline_run,
)

PREVIEW_SCHEMA_VERSION = 1
PREVIEW_DISCLAIMER = "结构预览不代表 Word 最终分页。"
_TECHNICAL_MARKER_RE = re.compile(
    r"\[@[^\]]+\]|(?:fig|tbl|eq|sec|chap|lst|alg):[A-Za-z0-9_.:-]+"
)


def _marker(issue: ValidationIssue) -> dict[str, str]:
    return {"severity": issue.severity, "code": issue.code}


def _markers(
    issues: tuple[ValidationIssue, ...],
    semantic_id: str | None,
    line: int | None,
) -> list[dict[str, str]]:
    matched: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for issue in issues:
        if not (
            (semantic_id is not None and issue.target == semantic_id)
            or (line is not None and issue.line == line)
        ):
            continue
        key = (issue.severity, issue.code)
        if key not in seen:
            seen.add(key)
            matched.append(_marker(issue))
    return matched


def _selection_id(
    kind: str,
    line: int | None,
    plan_index: int,
    semantic_id: str | None,
) -> str:
    if semantic_id is not None:
        return semantic_id
    if line is not None:
        return f"{kind}:line:{line}"
    return f"{kind}:plan:{plan_index}"


def _citation_text(run: CitationRun) -> str:
    if run.text and not _TECHNICAL_MARKER_RE.search(run.text):
        return run.text
    if run.ordinals:
        return "[" + ", ".join(str(ordinal) for ordinal in run.ordinals) + "]"
    return "引用"


def _inline_runs(runs: tuple[InlineRun, ...]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for value in runs:
        run = ensure_inline_run(value)
        if isinstance(run, TextRun):
            item: dict[str, Any] = {"type": "text", "text": run.text}
            if run.bold:
                item["bold"] = True
            if run.italic:
                item["italic"] = True
            if run.code:
                item["code"] = True
            serialized.append(item)
        elif isinstance(run, ReferenceRun):
            serialized.append(
                {
                    "type": "reference",
                    "targetId": run.target_id,
                    "text": run.display_text,
                }
            )
        elif isinstance(run, CitationRun):
            serialized.append(
                {
                    "type": "citation",
                    "keys": list(run.keys),
                    "ordinals": list(run.ordinals),
                    "locator": run.locator,
                    "text": _citation_text(run),
                }
            )
        elif isinstance(run, FootnoteReferenceRun):
            serialized.append(
                {
                    "type": "footnote-reference",
                    "label": run.label,
                    "footnoteId": run.footnote_id,
                    "text": f"脚注{run.footnote_id}",
                }
            )
        elif isinstance(run, SoftBreakRun):
            serialized.append({"type": "soft-break", "text": " "})
        elif isinstance(run, HardBreakRun):
            serialized.append({"type": "hard-break", "text": "\n"})
        elif isinstance(run, HyperlinkRun):
            serialized.append(
                {
                    "type": "hyperlink",
                    "text": run.text,
                    "destination": run.destination,
                }
            )
        elif isinstance(run, MathRun):
            serialized.append(
                {
                    "type": "math",
                    "latex": run.latex,
                    "text": run.latex,
                }
            )
    return serialized


@dataclass(slots=True)
class _SourceIndex:
    by_id: dict[str, Block]
    anonymous: dict[type[Block], deque[Block]]
    footnotes: dict[str, FootnoteDefinition]
    bibliography: deque[BibliographyBlock]

    @classmethod
    def from_result(cls, result: PreviewResult) -> _SourceIndex:
        anonymous: dict[type[Block], deque[Block]] = defaultdict(deque)
        footnotes: dict[str, FootnoteDefinition] = {}
        bibliography: deque[BibliographyBlock] = deque()
        for block in result.document.blocks:
            if block.id is None:
                anonymous[type(block)].append(block)
            if isinstance(block, FootnoteDefinition):
                footnotes[block.label] = block
            if isinstance(block, BibliographyBlock):
                bibliography.append(block)
        return cls(
            by_id=result.document.index_by_id(),
            anonymous=anonymous,
            footnotes=footnotes,
            bibliography=bibliography,
        )

    def locate(self, instruction: object) -> Block | None:
        source_id = getattr(instruction, "source_id", None)
        if isinstance(source_id, str):
            return self.by_id.get(source_id)
        if isinstance(instruction, FootnoteDefinitionInstruction):
            return self.footnotes.get(instruction.label)
        if isinstance(instruction, BibliographyInstruction):
            return self.bibliography.popleft() if self.bibliography else None
        block_type = {
            HeadingInstruction: Heading,
            ParagraphInstruction: Paragraph,
            CodeBlockInstruction: CodeBlock,
            BlockQuoteInstruction: BlockQuote,
            ListInstruction: ListBlock,
            FigureInstruction: Figure,
            TableInstruction: Table,
            EquationInstruction: Equation,
            ListingInstruction: Listing,
            AlgorithmInstruction: Algorithm,
        }.get(type(instruction))
        if block_type is None:
            return None
        queue = self.anonymous.get(block_type)
        return queue.popleft() if queue else None


def _cover_content(instruction: CoverInstruction) -> dict[str, Any]:
    fields = [
        {"label": label, "value": value}
        for label, value in (
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
        if value
    ]
    return {"type": "cover", "fields": fields}


def _content(instruction: object) -> tuple[str, str, dict[str, Any]]:
    if isinstance(instruction, CoverInstruction):
        return "cover", "ready", _cover_content(instruction)
    if isinstance(instruction, SectionBreakInstruction):
        return (
            "section",
            "ready",
            {"type": "section", "role": instruction.role},
        )
    if isinstance(instruction, TocInstruction):
        return (
            "toc",
            "ready",
            {
                "type": "toc",
                "minLevel": instruction.min_level,
                "maxLevel": instruction.max_level,
            },
        )
    if isinstance(instruction, HeadingInstruction):
        return (
            "heading",
            "ready",
            {
                "type": "text",
                "text": instruction.text,
                "level": instruction.level,
                "runs": _inline_runs(instruction.inlines),
            },
        )
    if isinstance(instruction, ParagraphInstruction):
        return (
            "paragraph",
            "ready",
            {
                "type": "text",
                "text": instruction.text,
                "level": None,
                "runs": _inline_runs(instruction.inlines),
            },
        )
    if isinstance(instruction, CodeBlockInstruction):
        return (
            "code_block",
            "ready",
            {
                "type": "code-block",
                "language": instruction.language,
                "code": instruction.code,
            },
        )
    if isinstance(instruction, BlockQuoteInstruction):
        return (
            "blockquote",
            "ready",
            {
                "type": "blockquote",
                "children": [
                    {
                        "kind": kind,
                        "state": state,
                        "content": content,
                    }
                    for kind, state, content in (
                        _content(child) for child in instruction.children
                    )
                ],
            },
        )
    if isinstance(instruction, ListInstruction):
        return (
            "list",
            "ready",
            {
                "type": "list",
                "ordered": instruction.ordered,
                "start": instruction.start,
                "items": [
                    {
                        "text": item.text,
                        "level": item.level,
                        "ordinal": item.ordinal,
                        "runs": _inline_runs(item.inlines),
                    }
                    for item in instruction.items
                ],
            },
        )
    if isinstance(instruction, FigureInstruction):
        return (
            "figure",
            "ready",
            {
                "type": "figure",
                "src": instruction.src,
                "caption": instruction.caption,
                "label": instruction.label,
                "width": instruction.width,
                "available": instruction.asset_path.is_file(),
            },
        )
    if isinstance(instruction, TableInstruction):
        return (
            "table",
            "ready",
            {
                "type": "table",
                "caption": instruction.caption,
                "label": instruction.label,
                "rows": [
                    {
                        "header": row.header,
                        "cells": [
                            {
                                "text": cell.text,
                                "alignment": cell.alignment,
                            }
                            for cell in row.cells
                        ],
                    }
                    for row in instruction.rows
                ],
            },
        )
    if isinstance(instruction, EquationInstruction):
        return (
            "equation",
            "ready",
            {
                "type": "equation",
                "latex": instruction.latex,
                "label": instruction.label,
            },
        )
    if isinstance(instruction, ListingInstruction):
        return (
            "listing",
            "ready",
            {
                "type": "listing",
                "caption": instruction.caption,
                "language": instruction.language,
                "code": instruction.code,
            },
        )
    if isinstance(instruction, AlgorithmInstruction):
        return (
            "algorithm",
            "ready",
            {
                "type": "algorithm",
                "caption": instruction.caption,
                "body": instruction.body,
            },
        )
    if isinstance(instruction, FootnoteDefinitionInstruction):
        return (
            "footnote",
            "ready",
            {
                "type": "footnote",
                "label": instruction.label,
                "footnoteId": instruction.footnote_id,
                "text": instruction.text,
                "runs": _inline_runs(instruction.inlines),
            },
        )
    if isinstance(instruction, BibliographyInstruction):
        return (
            "bibliography",
            "ready",
            {
                "type": "bibliography",
                "entries": [
                    {
                        "key": entry.key,
                        "ordinal": entry.ordinal,
                        "text": entry.text,
                    }
                    for entry in instruction.entries
                ],
            },
        )
    return (
        "unsupported",
        "unsupported",
        {"type": "unsupported", "originalKind": type(instruction).__name__},
    )


def _outline(result: PreviewResult) -> list[dict[str, Any]]:
    return [
        {
            "selectionId": _selection_id(
                "heading",
                block.location.line,
                index,
                block.id,
            ),
            "semanticId": block.id,
            "level": block.level,
            "text": inline_plain_text(block.inlines),
            "line": block.location.line,
            "markers": _markers(result.issues, block.id, block.location.line),
        }
        for index, block in enumerate(result.document.blocks)
        if isinstance(block, Heading)
    ]


def map_preview_result(result: PreviewResult) -> dict[str, Any]:
    outline = _outline(result)
    if result.plan is None:
        error_count = len(result.errors)
        message = (
            f"存在 {error_count} 个错误诊断，无法生成结构预览。"
            if error_count
            else "模板不可用，无法生成结构预览。"
        )
        return {
            "schemaVersion": PREVIEW_SCHEMA_VERSION,
            "outline": outline,
            "preview": {
                "status": "blocked",
                "message": message,
                "disclaimer": PREVIEW_DISCLAIMER,
                "blocks": [],
            },
        }

    source_index = _SourceIndex.from_result(result)
    blocks: list[dict[str, Any]] = []
    for index, instruction in enumerate(result.plan.nodes):
        source = source_index.locate(instruction)
        semantic_id = source.id if source is not None else getattr(
            instruction,
            "source_id",
            None,
        )
        line = source.location.line if source is not None else None
        kind, state, content = _content(instruction)
        blocks.append(
            {
                "selectionId": _selection_id(kind, line, index, semantic_id),
                "semanticId": semantic_id,
                "kind": kind,
                "line": line,
                "state": state,
                "markers": _markers(result.issues, semantic_id, line),
                "content": content,
            }
        )
    return {
        "schemaVersion": PREVIEW_SCHEMA_VERSION,
        "outline": outline,
        "preview": {
            "status": "ready",
            "message": None,
            "disclaimer": PREVIEW_DISCLAIMER,
            "blocks": blocks,
        },
    }
