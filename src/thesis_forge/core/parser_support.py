"""Parser-neutral syntax and semantic helpers shared by parser implementations."""

from __future__ import annotations

import re
from typing import Any, Literal

import yaml

from .model import (
    Algorithm,
    BibliographyBlock,
    BibliographyConfig,
    Citation,
    CrossReference,
    Equation,
    Figure,
    FootnoteReference,
    Inline,
    InlineCode,
    Listing,
    SourceLocation,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
)

CONTAINER_START_RE = re.compile(
    r"^:::\s+(figure|table|equation|listing|algorithm|bibliography)"
    r"(?:\s+\{#([^}]+)\})?\s*$"
)
CITATION_KEY_RE = re.compile(r"@([A-Za-z0-9_.:-]+)")
KV_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_-]*):\s*"?(.+?)"?\s*$')
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")
LIST_ITEM_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>[-+*]|\d+[.)])\s+(?P<text>.+?)\s*$")
FOOTNOTE_DEFINITION_RE = re.compile(r"^\[\^(?P<label>[A-Za-z0-9_.:-]+)\]:\s*(?P<text>.*)$")
INLINE_TOKEN_RE = re.compile(
    r"(?P<code>`(?P<code_text>[^`\n]+)`)"
    r"|(?P<strong>\*\*(?P<strong_text>[^*\n]+)\*\*)"
    r"|(?P<footnote>\[\^(?P<footnote_label>[A-Za-z0-9_.:-]+)\])"
    r"|(?P<citation>\[(?P<citation_body>[^\]]*@[^\]]+)\])"
    r"|(?P<crossref>(?<!\[)@(?P<ref_prefix>fig|tbl|eq|alg|lst|sec|chap):"
    r"(?P<ref_name>[A-Za-z0-9_.:-]+))"
)


class ParseError(ValueError):
    pass


def parse_front_matter(lines: list[str]) -> tuple[dict[str, Any], int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            raw = "\n".join(lines[1:i])
            try:
                value = yaml.safe_load(raw) or {}
            except yaml.YAMLError as error:
                line = getattr(getattr(error, "problem_mark", None), "line", None)
                suffix = f"（第 {line + 2} 行）" if line is not None else ""
                raise ParseError(f"YAML Front Matter 无效{suffix}") from error
            if not isinstance(value, dict):
                raise ParseError("YAML Front Matter 必须是键值映射")
            return value, i + 1
    raise ParseError("YAML Front Matter 缺少结束分隔符 ---")


def _location_for_offset(
    text: str,
    offset: int,
    start_line: int,
    start_column: int = 1,
) -> SourceLocation:
    prefix = text[:offset]
    newline_count = prefix.count("\n")
    if newline_count:
        column = len(prefix.rsplit("\n", 1)[-1]) + 1
    else:
        column = start_column + len(prefix)
    return SourceLocation(line=start_line + newline_count, column=column)


def parse_inline_content(
    text: str,
    start_line: int,
    start_column: int = 1,
) -> list[Inline]:
    inlines: list[Inline] = []
    cursor = 0
    for match in INLINE_TOKEN_RE.finditer(text):
        if match.start() > cursor:
            inlines.append(
                Text(
                    value=text[cursor : match.start()],
                    location=_location_for_offset(text, cursor, start_line, start_column),
                )
            )

        location = _location_for_offset(text, match.start(), start_line, start_column)
        if match.group("code"):
            inlines.append(InlineCode(value=match.group("code_text"), location=location))
        elif match.group("strong"):
            inner_text = match.group("strong_text")
            inner_location = _location_for_offset(
                text, match.start("strong_text"), start_line, start_column
            )
            children = tuple(
                parse_inline_content(inner_text, inner_location.line, inner_location.column)
            )
            inlines.append(Strong(children=children, location=location))
        elif match.group("footnote"):
            inlines.append(FootnoteReference(label=match.group("footnote_label"), location=location))
        elif match.group("citation"):
            body = match.group("citation_body")
            keys = CITATION_KEY_RE.findall(body)
            locator = CITATION_KEY_RE.sub("", body).strip(" \t;,")
            inlines.append(
                Citation(
                    keys=keys,
                    locator=locator or None,
                    raw=match.group("citation"),
                    location=location,
                )
            )
        else:
            inlines.append(
                CrossReference(
                    target=f"{match.group('ref_prefix')}:{match.group('ref_name')}",
                    location=location,
                )
            )
        cursor = match.end()

    if cursor < len(text):
        inlines.append(
            Text(
                value=text[cursor:],
                location=_location_for_offset(text, cursor, start_line, start_column),
            )
        )
    return inlines


def bibliography_config(metadata: dict[str, Any]) -> BibliographyConfig | None:
    render = metadata.get("render")
    if not isinstance(render, dict):
        return None
    path = render.get("bibliography")
    citation_style = render.get("citation_style")
    if path is None and citation_style is None:
        return None
    return BibliographyConfig(
        path=str(path) if path is not None else None,
        citation_style=str(citation_style) if citation_style is not None else None,
    )


def _strip_listing_fence(content: str, language: str | None) -> tuple[str, str | None]:
    lines = content.splitlines()
    if len(lines) < 2 or not lines[0].strip().startswith("```") or lines[-1].strip() != "```":
        return content, language
    fence_language = lines[0].strip()[3:].strip() or None
    return "\n".join(lines[1:-1]), language or fence_language


def _parse_container_inlines(kind: str, body: list[str], start_line: int) -> list[Inline]:
    inlines: list[Inline] = []
    metadata_phase = True

    for offset, raw in enumerate(body):
        stripped = raw.strip()
        match = KV_RE.match(stripped) if metadata_phase else None
        if match:
            if match.group(1) == "caption":
                value = match.group(2).strip('"')
                column = raw.find(value) + 1
                inlines.extend(parse_inline_content(value, start_line + offset, column))
            continue

        if stripped:
            metadata_phase = False
        if not stripped or kind not in {"table", "algorithm"}:
            continue
        inlines.extend(parse_inline_content(raw, start_line + offset))

    return inlines


def _split_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _table_alignment(cell: str) -> Literal["left", "center", "right"] | None:
    if TABLE_SEPARATOR_RE.fullmatch(cell) is None:
        raise ValueError(f"invalid table separator cell: {cell!r}")
    if cell.startswith(":") and cell.endswith(":"):
        return "center"
    if cell.endswith(":"):
        return "right"
    if cell.startswith(":"):
        return "left"
    return None


def _parse_table_rows(rows: list[tuple[int, str]]) -> tuple[TableRow, ...]:
    meaningful = [(line_no, raw) for line_no, raw in rows if raw.strip()]
    if len(meaningful) < 2:
        return ()
    header_line, header_raw = meaningful[0]
    header = _split_table_row(header_raw)
    separator = _split_table_row(meaningful[1][1])
    if header is None or separator is None or len(header) != len(separator):
        return ()
    try:
        alignments = tuple(_table_alignment(cell) for cell in separator)
    except ValueError:
        return ()

    def make_row(values: list[str], *, is_header: bool, line: int) -> TableRow:
        return TableRow(
            header=is_header,
            cells=tuple(
                TableCell(
                    inlines=tuple(parse_inline_content(value, line)),
                    alignment=alignment,
                    location=SourceLocation(line=line),
                )
                for value, alignment in zip(values, alignments, strict=True)
            ),
            location=SourceLocation(line=line),
        )

    rows = [make_row(header, is_header=True, line=header_line)]
    for line_no, raw in meaningful[2:]:
        values = _split_table_row(raw)
        if values is None or len(values) != len(header):
            return ()
        rows.append(make_row(values, is_header=False, line=line_no))
    return tuple(rows)


def parse_container(kind: str, block_id: str | None, body: list[str], line: int):
    values: dict[str, str] = {}
    content_lines: list[str] = []
    located_lines: list[tuple[int, str]] = []
    caption_line = line
    caption_column = 1
    metadata_phase = True

    for offset, item in enumerate(body):
        match = KV_RE.match(item.strip()) if metadata_phase else None
        if match:
            value = match.group(2).strip('"')
            values[match.group(1)] = value
            if match.group(1) == "caption":
                caption_line = line + 1 + offset
                caption_column = item.find(value) + 1
        else:
            if item.strip():
                metadata_phase = False
            content_lines.append(item)
            located_lines.append((line + 1 + offset, item))

    content = "\n".join(content_lines).strip()
    location = SourceLocation(line=line)
    caption = values.get("caption", "")
    caption_inlines = tuple(parse_inline_content(caption, caption_line, caption_column))
    table_rows = _parse_table_rows(located_lines) if kind == "table" else ()

    if kind == "figure":
        return Figure(
            id=block_id,
            src=values.get("src", ""),
            caption_inlines=caption_inlines,
            width=values.get("width"),
            location=location,
        )
    if kind == "table":
        return Table(
            id=block_id,
            caption_inlines=caption_inlines,
            rows=table_rows,
            location=location,
        )
    if kind == "equation":
        latex = content
        if latex.startswith("$$") and latex.endswith("$$"):
            latex = latex[2:-2].strip()
        return Equation(
            id=block_id,
            latex=latex,
            display=True,
            location=location,
        )
    if kind == "listing":
        code, language = _strip_listing_fence(content, values.get("language"))
        return Listing(
            id=block_id,
            caption_inlines=caption_inlines,
            language=language,
            code=code,
            location=location,
        )
    if kind == "algorithm":
        body_lines = tuple(
            tuple(parse_inline_content(raw, body_line))
            for body_line, raw in located_lines
            if raw.strip()
        )
        return Algorithm(
            id=block_id,
            caption_inlines=caption_inlines,
            body=content,
            body_lines=body_lines,
            location=location,
        )
    if kind == "bibliography":
        return BibliographyBlock(id=block_id, location=location)
    raise ParseError(f"未知容器类型: {kind}")


__all__ = [
    "CONTAINER_START_RE",
    "FOOTNOTE_DEFINITION_RE",
    "LIST_ITEM_RE",
    "ParseError",
    "bibliography_config",
    "parse_container",
    "parse_front_matter",
    "parse_inline_content",
]
