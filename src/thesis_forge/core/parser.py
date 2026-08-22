from __future__ import annotations

import re
from pathlib import Path

from .model import (
    FootnoteDefinition,
    Heading,
    ListBlock,
    ListItem,
    Paragraph,
    SourceLocation,
    ThesisDocument,
)
from .parser_support import (
    CONTAINER_START_RE,
    FOOTNOTE_DEFINITION_RE,
    LIST_ITEM_RE,
    ParseError,
    bibliography_config,
    parse_container,
    parse_front_matter,
    parse_inline_content,
)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+\{#([^}]+)\})?\s*$")
def parse_markdown_text(
    text: str,
    *,
    source_path: str | Path,
) -> ThesisDocument:
    resolved_source_path = Path(source_path).resolve()
    lines = text.splitlines()
    metadata, start = parse_front_matter(lines)
    doc = ThesisDocument(
        source_path=resolved_source_path,
        metadata=metadata,
        bibliography=bibliography_config(metadata),
    )

    paragraph_buffer: list[str] = []
    paragraph_start: int | None = None

    def flush_paragraph() -> None:
        nonlocal paragraph_buffer, paragraph_start
        text = "\n".join(paragraph_buffer).strip()
        if text:
            line = paragraph_start or 1
            inlines = parse_inline_content(text, line)
            doc.blocks.append(
                Paragraph(inlines=inlines, location=SourceLocation(line=line))
            )
        paragraph_buffer = []
        paragraph_start = None

    i = start
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        line_no = i + 1

        footnote = FOOTNOTE_DEFINITION_RE.match(raw)
        if footnote:
            flush_paragraph()
            label = footnote.group("label")
            first_text = footnote.group("text")
            body_segments = [(first_text, line_no, footnote.start("text") + 1)]
            i += 1
            while i < len(lines) and (lines[i].startswith("    ") or lines[i].startswith("\t")):
                continuation = lines[i].lstrip()
                column = len(lines[i]) - len(continuation) + 1
                body_segments.append((continuation, i + 1, column))
                i += 1
            text = "\n".join(segment[0] for segment in body_segments).strip()
            inlines = []
            for segment_text, segment_line, segment_column in body_segments:
                inlines.extend(
                    parse_inline_content(segment_text, segment_line, segment_column)
                )
            doc.blocks.append(
                FootnoteDefinition(
                    label=label,
                    inlines=inlines,
                    location=SourceLocation(line=line_no),
                )
            )
            continue

        container = CONTAINER_START_RE.match(stripped)
        if container:
            flush_paragraph()
            kind, block_id = container.groups()
            body: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                body.append(lines[i])
                i += 1
            if i >= len(lines):
                raise ParseError(f"第 {line_no} 行的 {kind} 容器未闭合")
            block = parse_container(kind, block_id, body, line_no)
            doc.blocks.append(block)
            i += 1
            continue

        heading = HEADING_RE.match(raw)
        if heading:
            flush_paragraph()
            marks, text, block_id = heading.groups()
            inlines = parse_inline_content(text.strip(), line_no, len(marks) + 2)
            doc.blocks.append(
                Heading(
                    id=block_id,
                    level=len(marks),
                    inlines=inlines,
                    location=SourceLocation(line=line_no),
                )
            )
            i += 1
            continue

        list_item = LIST_ITEM_RE.match(raw)
        if list_item:
            flush_paragraph()
            marker = list_item.group("marker")
            ordered = marker[0].isdigit()
            items: list[ListItem] = []
            start_number = int(marker.rstrip(".)")) if ordered else None

            while i < len(lines):
                item_match = LIST_ITEM_RE.match(lines[i])
                if item_match is None:
                    break
                item_marker = item_match.group("marker")
                if item_marker[0].isdigit() != ordered:
                    break
                item_text = item_match.group("text")
                indent = len(item_match.group("indent").expandtabs(4))
                item_line = i + 1
                item_inlines = parse_inline_content(
                    item_text,
                    item_line,
                    item_match.start("text") + 1,
                )
                items.append(
                    ListItem(
                        level=indent // 2,
                        marker=item_marker,
                        ordinal=int(item_marker.rstrip(".)")) if ordered else None,
                        location=SourceLocation(line=item_line),
                        inlines=item_inlines,
                    )
                )
                i += 1

            doc.blocks.append(
                ListBlock(
                    ordered=ordered,
                    start=start_number,
                    items=items,
                    location=SourceLocation(line=line_no),
                )
            )
            continue

        if not stripped:
            flush_paragraph()
        else:
            if paragraph_start is None:
                paragraph_start = line_no
            paragraph_buffer.append(raw)
        i += 1

    flush_paragraph()
    return doc


def parse_markdown(path: str | Path) -> ThesisDocument:
    source_path = Path(path).resolve()
    return parse_markdown_text(
        source_path.read_text(encoding="utf-8"),
        source_path=source_path,
    )
