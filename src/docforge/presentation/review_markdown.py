"""Serialize the typed Review projection into generated Markdown."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from docforge.presentation.review import (
    ReviewAlgorithmContent,
    ReviewBibliographyContent,
    ReviewBibliographyEntry,
    ReviewBlock,
    ReviewBlockQuoteContent,
    ReviewCitationRun,
    ReviewCodeBlockContent,
    ReviewCoverContent,
    ReviewCoverField,
    ReviewDocument,
    ReviewEquationContent,
    ReviewFigureContent,
    ReviewFootnoteContent,
    ReviewFootnoteReferenceRun,
    ReviewHardBreakRun,
    ReviewHeadingContent,
    ReviewHyperlinkRun,
    ReviewInline,
    ReviewListContent,
    ReviewListingContent,
    ReviewListItem,
    ReviewMathRun,
    ReviewPageBreakContent,
    ReviewParagraphContent,
    ReviewReferenceRun,
    ReviewSectionContent,
    ReviewSoftBreakRun,
    ReviewSource,
    ReviewTableCell,
    ReviewTableContent,
    ReviewTableRow,
    ReviewTextRun,
    ReviewTocContent,
    ReviewTocEntry,
)

__all__ = [
    "ReviewMarkdownBlock",
    "ReviewMarkdownResult",
    "render_review_markdown",
    "render_review_source_map",
    "serialize_review_markdown",
    "serialize_review_source_map",
]


@dataclass(frozen=True, slots=True)
class ReviewMarkdownBlock:
    kind: str
    start_line: int
    end_line: int
    source: ReviewSource | None
    generated: bool


@dataclass(frozen=True, slots=True)
class ReviewMarkdownResult:
    markdown: str
    blocks: tuple[ReviewMarkdownBlock, ...]


_BLOCK_KINDS = frozenset(
    {
        "cover",
        "section_break",
        "toc",
        "heading",
        "paragraph",
        "code_block",
        "blockquote",
        "list",
        "figure",
        "table",
        "equation",
        "listing",
        "algorithm",
        "footnote",
        "bibliography",
        "page_break",
    }
)
_CONTENT_TYPES = (
    ReviewHeadingContent,
    ReviewParagraphContent,
    ReviewCodeBlockContent,
    ReviewBlockQuoteContent,
    ReviewListContent,
    ReviewFigureContent,
    ReviewTableContent,
    ReviewEquationContent,
    ReviewListingContent,
    ReviewAlgorithmContent,
    ReviewFootnoteContent,
    ReviewBibliographyContent,
    ReviewCoverContent,
    ReviewTocContent,
    ReviewSectionContent,
    ReviewPageBreakContent,
)
_INLINE_TYPES = (
    ReviewTextRun,
    ReviewReferenceRun,
    ReviewCitationRun,
    ReviewFootnoteReferenceRun,
    ReviewHyperlinkRun,
    ReviewMathRun,
    ReviewSoftBreakRun,
    ReviewHardBreakRun,
)

_CITATION_RE = re.compile(r"\[@[^\]]+\]")
_STABLE_ID_RE = re.compile(r"\{#[A-Za-z0-9_.:-]+\}")
_REFERENCE_RE = re.compile(
    r"(?<![\w-])@?(?:fig|tbl|eq|sec|chap|lst|alg):[A-Za-z0-9_.-]+"
)
_UNC_PATH_RE = re.compile(r"(?<![A-Za-z0-9:])//[^\s<>\"']+")
_POSIX_PATH_RE = re.compile(r"(?<![A-Za-z0-9_:/])/(?!/)[^\s<>\"']+")
_WINDOWS_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/]|\\\\)[^\s<>\"']+"
)
_INLINE_CODE_RE = re.compile(r"`+")
_LANGUAGE_RE = re.compile(r"^[A-Za-z0-9_+.-]+$")
_MAX_ASSET_DECODE_ROUNDS = 16


def _require_text(value: object, field: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be str")
    return value


def _require_bool(value: object, field: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"{field} must be bool")


def _require_int(value: object, field: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{field} must be int")


def _require_optional_int(value: object, field: str) -> None:
    if value is not None:
        _require_int(value, field)


def _validate_inline(inline: object) -> None:
    if type(inline) not in _INLINE_TYPES:
        raise TypeError(f"unsupported ReviewInline: {type(inline).__name__}")

    _require_text(inline.text, "ReviewInline.text")
    if type(inline) is ReviewTextRun:
        _require_bool(inline.bold, "ReviewTextRun.bold")
        _require_bool(inline.italic, "ReviewTextRun.italic")
        _require_bool(inline.code, "ReviewTextRun.code")
    elif type(inline) is ReviewFootnoteReferenceRun:
        _require_int(inline.footnote_id, "ReviewFootnoteReferenceRun.footnote_id")
    elif type(inline) is ReviewHyperlinkRun:
        _require_text(inline.destination, "ReviewHyperlinkRun.destination")
    elif type(inline) is ReviewMathRun:
        _require_text(inline.latex, "ReviewMathRun.latex")


def _validate_inline_tuple(value: object, field: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be tuple")
    for inline in value:
        _validate_inline(inline)


def _validate_text_content(content: object) -> None:
    _require_text(content.text, f"{type(content).__name__}.text")
    _validate_inline_tuple(content.runs, f"{type(content).__name__}.runs")


def _validate_list_content(content: object) -> None:
    if type(content.ordered) is not bool:
        raise TypeError("ReviewListContent.ordered must be bool")
    _require_optional_int(content.start, "ReviewListContent.start")
    if type(content.items) is not tuple:
        raise TypeError("ReviewListContent.items must be tuple")
    for item in content.items:
        if type(item) is not ReviewListItem:
            raise TypeError(f"unsupported ReviewListItem: {type(item).__name__}")
        _require_text(item.text, "ReviewListItem.text")
        _require_int(item.level, "ReviewListItem.level")
        _require_optional_int(item.ordinal, "ReviewListItem.ordinal")
        _validate_inline_tuple(item.runs, "ReviewListItem.runs")


def _validate_code_block_content(content: object) -> None:
    if content.language is not None:
        _require_text(content.language, "ReviewCodeBlockContent.language")
    _require_text(content.code, "ReviewCodeBlockContent.code")


def _validate_blockquote_content(content: object) -> None:
    if type(content.children) is not tuple:
        raise TypeError("ReviewBlockQuoteContent.children must be tuple")
    for child in content.children:
        _validate_content(child)


def _validate_figure_content(content: object) -> None:
    for field in ("label", "caption", "asset_handle"):
        _require_text(getattr(content, field), f"ReviewFigureContent.{field}")
    _require_bool(content.available, "ReviewFigureContent.available")
    if content.width is not None:
        _require_text(content.width, "ReviewFigureContent.width")


def _validate_table_content(content: object) -> None:
    _require_text(content.label, "ReviewTableContent.label")
    _require_text(content.caption, "ReviewTableContent.caption")
    if type(content.rows) is not tuple:
        raise TypeError("ReviewTableContent.rows must be tuple")
    for row in content.rows:
        if type(row) is not ReviewTableRow:
            raise TypeError(f"unsupported ReviewTableRow: {type(row).__name__}")
        _require_bool(row.header, "ReviewTableRow.header")
        if type(row.cells) is not tuple:
            raise TypeError("ReviewTableRow.cells must be tuple")
        for cell in row.cells:
            if type(cell) is not ReviewTableCell:
                raise TypeError(f"unsupported ReviewTableCell: {type(cell).__name__}")
            _require_text(cell.text, "ReviewTableCell.text")
            if cell.alignment is not None:
                _require_text(cell.alignment, "ReviewTableCell.alignment")


def _validate_equation_content(content: object) -> None:
    _require_text(content.label, "ReviewEquationContent.label")
    _require_text(content.latex, "ReviewEquationContent.latex")
    _require_text(content.alignment, "ReviewEquationContent.alignment")


def _validate_listing_content(content: object) -> None:
    _require_text(content.caption, "ReviewListingContent.caption")
    if content.language is not None:
        _require_text(content.language, "ReviewListingContent.language")
    _require_text(content.code, "ReviewListingContent.code")


def _validate_algorithm_content(content: object) -> None:
    _require_text(content.caption, "ReviewAlgorithmContent.caption")
    _require_text(content.body, "ReviewAlgorithmContent.body")


def _validate_footnote_content(content: object) -> None:
    _require_int(content.footnote_id, "ReviewFootnoteContent.footnote_id")
    _require_text(content.text, "ReviewFootnoteContent.text")
    _validate_inline_tuple(content.runs, "ReviewFootnoteContent.runs")


def _validate_bibliography_content(content: object) -> None:
    if type(content.entries) is not tuple:
        raise TypeError("ReviewBibliographyContent.entries must be tuple")
    for entry in content.entries:
        if type(entry) is not ReviewBibliographyEntry:
            raise TypeError(
                f"unsupported ReviewBibliographyEntry: {type(entry).__name__}"
            )
        _require_int(entry.ordinal, "ReviewBibliographyEntry.ordinal")
        _require_text(entry.text, "ReviewBibliographyEntry.text")


def _validate_cover_content(content: object) -> None:
    if type(content.fields) is not tuple:
        raise TypeError("ReviewCoverContent.fields must be tuple")
    for field in content.fields:
        if type(field) is not ReviewCoverField:
            raise TypeError(f"unsupported ReviewCoverField: {type(field).__name__}")
        _require_text(field.label, "ReviewCoverField.label")
        _require_text(field.value, "ReviewCoverField.value")


def _validate_toc_content(content: object) -> None:
    if type(content.entries) is not tuple:
        raise TypeError("ReviewTocContent.entries must be tuple")
    _require_int(content.min_level, "ReviewTocContent.min_level")
    _require_int(content.max_level, "ReviewTocContent.max_level")
    for entry in content.entries:
        if type(entry) is not ReviewTocEntry:
            raise TypeError(f"unsupported ReviewTocEntry: {type(entry).__name__}")
        _require_text(entry.text, "ReviewTocEntry.text")
        _require_int(entry.level, "ReviewTocEntry.level")


def _validate_section_content(content: object) -> None:
    if content.role not in {"cover", "front_matter", "main"}:
        raise TypeError("ReviewSectionContent.role is invalid")


_CONTENT_VALIDATORS: dict[type[object], Callable[[object], None]] = {
    ReviewHeadingContent: _validate_text_content,
    ReviewParagraphContent: _validate_text_content,
    ReviewCodeBlockContent: _validate_code_block_content,
    ReviewBlockQuoteContent: _validate_blockquote_content,
    ReviewListContent: _validate_list_content,
    ReviewFigureContent: _validate_figure_content,
    ReviewTableContent: _validate_table_content,
    ReviewEquationContent: _validate_equation_content,
    ReviewListingContent: _validate_listing_content,
    ReviewAlgorithmContent: _validate_algorithm_content,
    ReviewFootnoteContent: _validate_footnote_content,
    ReviewBibliographyContent: _validate_bibliography_content,
    ReviewCoverContent: _validate_cover_content,
    ReviewTocContent: _validate_toc_content,
    ReviewSectionContent: _validate_section_content,
    ReviewPageBreakContent: lambda _content: None,
}


def _validate_content(content: object) -> None:
    if type(content) not in _CONTENT_TYPES:
        raise TypeError(f"unsupported ReviewContent: {type(content).__name__}")
    _CONTENT_VALIDATORS[type(content)](content)


def _validate_source(source: object) -> None:
    if source is None:
        return
    if type(source) is not ReviewSource:
        raise TypeError(f"unsupported ReviewSource: {type(source).__name__}")
    _require_text(source.node_id, "ReviewSource.node_id")
    for field in ("line", "column", "end_line", "end_column"):
        _require_optional_int(getattr(source, field), f"ReviewSource.{field}")


def _validate_review(review: object) -> ReviewDocument:
    if type(review) is not ReviewDocument:
        raise TypeError(f"review must be ReviewDocument, got {type(review).__name__}")
    if review.status not in {"ready", "partial", "blocked"}:
        raise TypeError("ReviewDocument.status is invalid")
    if type(review.blocks) is not tuple:
        raise TypeError("ReviewDocument.blocks must be tuple")
    for block in review.blocks:
        if type(block) is not ReviewBlock:
            raise TypeError(f"unsupported ReviewBlock: {type(block).__name__}")
        if block.kind not in _BLOCK_KINDS:
            raise TypeError(f"unsupported ReviewBlock kind: {block.kind!r}")
        _validate_source(block.source)
        _validate_content(block.content)
    return review


def _sanitize_visible_text(value: str) -> str:
    """Remove compiler syntax and machine paths from reader-facing text."""

    value = _CITATION_RE.sub("", value)
    value = _STABLE_ID_RE.sub("", value)
    value = _REFERENCE_RE.sub("", value)
    value = value.replace(":::", "")
    value = _UNC_PATH_RE.sub("", value)
    value = _POSIX_PATH_RE.sub("", value)
    return _WINDOWS_PATH_RE.sub("", value)


def _escape_markdown_text(value: str) -> str:
    return re.sub(r"([\\`*_\[\]])", r"\\\1", value)


def _safe_inline_code(value: str) -> str:
    run_length = max(
        (len(match.group(0)) for match in _INLINE_CODE_RE.finditer(value)),
        default=0,
    )
    fence = "`" * max(1, run_length + 1)
    if value.startswith(" ") or value.endswith(" "):
        return f"{fence}{value}{fence}"
    return f"{fence}{value}{fence}"


def _render_inline(inline: ReviewInline) -> str:
    if type(inline) is ReviewTextRun:
        text = inline.text if inline.code else _sanitize_visible_text(inline.text)
        rendered = _safe_inline_code(text) if inline.code else _escape_markdown_text(text)
        if inline.bold and inline.italic:
            return f"***{rendered}***"
        if inline.bold:
            return f"**{rendered}**"
        return f"*{rendered}*" if inline.italic else rendered
    if type(inline) is ReviewReferenceRun:
        text = _sanitize_visible_text(inline.text) or "引用"
        return _escape_markdown_text(text)
    if type(inline) is ReviewCitationRun:
        text = _sanitize_visible_text(inline.text) or "引用"
        return _escape_markdown_text(text)
    if type(inline) is ReviewFootnoteReferenceRun:
        return f"脚注{inline.footnote_id}"
    if type(inline) is ReviewHyperlinkRun:
        text = _sanitize_visible_text(inline.text) or "链接"
        destination = _safe_hyperlink_destination(inline.destination)
        if destination is None:
            return _escape_markdown_text(text)
        return f"[{_escape_markdown_text(text)}]({destination})"
    if type(inline) is ReviewMathRun:
        text = _sanitize_visible_text(inline.text or inline.latex)
        return f"\\({text}\\)" if text else "公式"
    if type(inline) is ReviewSoftBreakRun:
        return " "
    if type(inline) is ReviewHardBreakRun:
        return "  \n"
    raise TypeError(f"unsupported ReviewInline: {type(inline).__name__}")


def _render_inline_sequence(
    text: str,
    runs: tuple[ReviewInline, ...],
) -> list[str]:
    rendered = (
        "".join(_render_inline(inline) for inline in runs)
        if runs
        else _escape_markdown_text(_sanitize_visible_text(text))
    )
    return rendered.split("\n") or [""]


def _decode_asset_value(value: str) -> str | None:
    current = value
    for _ in range(_MAX_ASSET_DECODE_ROUNDS):
        decoded = unquote(current)
        if decoded == current:
            break
        current = decoded
    else:
        return None
    return current


def _safe_relative_path(value: str) -> str | None:
    if not value or any(char in value for char in "\x00\r\n"):
        return None

    decoded = _decode_asset_value(value)
    if decoded is None:
        return None
    if not decoded or any(char in decoded for char in "\x00\r\n"):
        return None
    parsed = urlsplit(decoded)
    if parsed.scheme or parsed.netloc:
        return None

    path = parsed.path.replace("\\", "/")
    if not path or path.startswith(("/", "//")):
        return None
    if re.match(r"^[A-Za-z]:/", path):
        return None

    segments = path.split("/")
    if any(segment == ".." for segment in segments):
        return None
    if any(segment == "" for segment in segments[:-1]):
        return None
    return decoded


def _sanitize_asset_link(value: object) -> str | None:
    if type(value) is not str:
        raise TypeError("asset link must be str")
    return _safe_relative_path(value)


def _safe_hyperlink_destination(value: str) -> str | None:
    if any(char in value for char in "\x00\r\n"):
        return None
    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https", "mailto"}:
        if parsed.scheme in {"http", "https"} and not parsed.netloc:
            return None
        return value
    return _safe_relative_path(value)


def _safe_source_name(source_name: str | Path) -> str:
    if type(source_name) is not str and not isinstance(source_name, Path):
        raise TypeError("source_name must be str or Path")
    value = source_name.as_posix() if isinstance(source_name, Path) else source_name
    value = value.replace("\\", "/").rstrip("/")
    basename = value.rsplit("/", 1)[-1]
    basename = _sanitize_visible_text(basename).replace("`", "")
    return basename or "thesis.md"


def _safe_language(language: str | None) -> str:
    if language is None or not _LANGUAGE_RE.fullmatch(language):
        return ""
    return language


def _caption_line(label: str, caption: str) -> str:
    label = _sanitize_visible_text(label)
    caption = _sanitize_visible_text(caption)
    if label and caption:
        return f"**{_escape_markdown_text(label)}**：{_escape_markdown_text(caption)}"
    if label:
        return f"**{_escape_markdown_text(label)}**"
    return _escape_markdown_text(caption)


def _code_fence(value: str) -> str:
    run_length = max(
        (len(match.group(0)) for match in re.finditer(r"`+", value)),
        default=0,
    )
    return "`" * max(3, run_length + 1)


def _render_code_block(code: str, language: str | None) -> list[str]:
    fence = _code_fence(code)
    info = _safe_language(language)
    opening = f"{fence}{info}"
    return [opening, *code.split("\n"), fence]


def _render_table(content: ReviewTableContent) -> list[str]:
    lines = [_caption_line(content.label, content.caption)]
    if not content.rows:
        return lines

    def row_text(row: object) -> str:
        cells = [
            _escape_markdown_text(_sanitize_visible_text(cell.text))
            .replace("|", r"\|")
            .replace("\n", "<br>")
            for cell in row.cells
        ]
        return "| " + " | ".join(cells) + " |"

    lines.append(row_text(content.rows[0]))
    lines.append("| " + " | ".join("---" for _ in content.rows[0].cells) + " |")
    lines.extend(row_text(row) for row in content.rows[1:])
    return lines


def _render_figure(
    content: ReviewFigureContent,
    asset_links: Mapping[str, str] | None,
) -> list[str]:
    label = _sanitize_visible_text(content.label) or "图片"
    caption = _sanitize_visible_text(content.caption)
    alternative = " ".join(part for part in (label, caption) if part)
    link = None
    if content.available and asset_links is not None and content.asset_handle in asset_links:
        link = _sanitize_asset_link(asset_links[content.asset_handle])
    if link is not None:
        return [f"![{_escape_markdown_text(alternative)}]({link})"]
    suffix = f"：{_escape_markdown_text(caption)}" if caption else ""
    return [f"**{_escape_markdown_text(label)}**{suffix}（图片资源不可用或未提供安全链接）"]


def _render_heading_content(
    content: ReviewHeadingContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    if not 1 <= content.level <= 6:
        raise ValueError("ReviewHeadingContent.level must be between 1 and 6")
    text = _render_inline_sequence(content.text, content.runs)
    return [f"{'#' * content.level} {line}" for line in text]


def _render_paragraph_content(
    content: ReviewParagraphContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    return _render_inline_sequence(content.text, content.runs)


def _render_code_block_content(
    content: ReviewCodeBlockContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    return _render_code_block(content.code, content.language)


def _render_blockquote_content(
    content: ReviewBlockQuoteContent,
    asset_links: Mapping[str, str] | None,
) -> list[str]:
    lines: list[str] = []
    for child in content.children:
        if lines:
            lines.append("")
        renderer = _CONTENT_RENDERERS.get(type(child))
        if renderer is None:
            raise TypeError(f"unsupported ReviewContent: {type(child).__name__}")
        lines.extend(renderer(child, asset_links))
    return [f"> {line}" if line else ">" for line in lines] or [">"]


def _render_list_content(
    content: ReviewListContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    lines = []
    next_ordinal = content.start or 1
    for item in content.items:
        rendered = _render_inline_sequence(item.text, item.runs)
        marker = f"{item.ordinal if item.ordinal is not None else next_ordinal}."
        if not content.ordered:
            marker = "-"
        indent = "  " * max(item.level, 0)
        lines.extend(
            f"{indent}{marker} {line}" if index == 0 else f"{indent}  {line}"
            for index, line in enumerate(rendered)
        )
        next_ordinal += 1
    return lines or [""]


def _render_figure_content(
    content: ReviewFigureContent,
    asset_links: Mapping[str, str] | None,
) -> list[str]:
    return _render_figure(content, asset_links)


def _render_table_content(
    content: ReviewTableContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    return _render_table(content)


def _render_equation_content(
    content: ReviewEquationContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    label = _caption_line(content.label, "")
    equation = _sanitize_visible_text(content.latex)
    lines = [label] if label else []
    lines.extend(["$$", equation, "$$"])
    return lines


def _render_listing_content(
    content: ReviewListingContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    caption = _caption_line("", content.caption)
    return ([caption] if caption else []) + _render_code_block(
        content.code,
        content.language,
    )


def _render_algorithm_content(
    content: ReviewAlgorithmContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    caption = _caption_line("", content.caption)
    body = _sanitize_visible_text(content.body)
    return ([caption] if caption else []) + _render_code_block(body, "text")


def _render_footnote_content(
    content: ReviewFootnoteContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    return [
        f"**脚注 {content.footnote_id}**",
        *_render_inline_sequence(content.text, content.runs),
    ]


def _render_bibliography_content(
    content: ReviewBibliographyContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    return [
        f"{entry.ordinal}. {_escape_markdown_text(_sanitize_visible_text(entry.text))}"
        for entry in content.entries
    ] or [""]


def _render_cover_content(
    content: ReviewCoverContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    return [
        f"**{_escape_markdown_text(_sanitize_visible_text(field.label))}**："
        f"{_escape_markdown_text(_sanitize_visible_text(field.value))}"
        for field in content.fields
    ] or [""]


def _render_toc_content(
    content: ReviewTocContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    lines = ["## 目录"]
    lines.extend(
        f"{'  ' * max(entry.level - content.min_level, 0)}- "
        f"{_escape_markdown_text(_sanitize_visible_text(entry.text))}"
        for entry in content.entries
    )
    return lines


def _render_section_content(
    content: ReviewSectionContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    labels = {
        "cover": "封面",
        "front_matter": "前置部分",
        "main": "正文",
    }
    return [f"## {labels[content.role]}"]


def _render_page_break_content(
    _content: ReviewPageBreakContent,
    _asset_links: Mapping[str, str] | None,
) -> list[str]:
    return ["**分页**"]


_CONTENT_RENDERERS: dict[
    type[object],
    Callable[[object, Mapping[str, str] | None], list[str]],
] = {
    ReviewHeadingContent: _render_heading_content,
    ReviewParagraphContent: _render_paragraph_content,
    ReviewCodeBlockContent: _render_code_block_content,
    ReviewBlockQuoteContent: _render_blockquote_content,
    ReviewListContent: _render_list_content,
    ReviewFigureContent: _render_figure_content,
    ReviewTableContent: _render_table_content,
    ReviewEquationContent: _render_equation_content,
    ReviewListingContent: _render_listing_content,
    ReviewAlgorithmContent: _render_algorithm_content,
    ReviewFootnoteContent: _render_footnote_content,
    ReviewBibliographyContent: _render_bibliography_content,
    ReviewCoverContent: _render_cover_content,
    ReviewTocContent: _render_toc_content,
    ReviewSectionContent: _render_section_content,
    ReviewPageBreakContent: _render_page_break_content,
}


def _render_block(
    block: ReviewBlock,
    asset_links: Mapping[str, str] | None,
) -> list[str]:
    renderer = _CONTENT_RENDERERS.get(type(block.content))
    if renderer is None:
        raise TypeError(f"unsupported ReviewContent: {type(block.content).__name__}")
    return renderer(block.content, asset_links)


def render_review_markdown(
    review: ReviewDocument,
    *,
    source_name: str | Path = "thesis.md",
    asset_links: Mapping[str, str] | None = None,
) -> ReviewMarkdownResult:
    """Render Review content and retain source navigation metadata separately."""

    review = _validate_review(review)
    if asset_links is not None and not isinstance(asset_links, Mapping):
        raise TypeError("asset_links must be a Mapping")
    display_name = _safe_source_name(source_name)
    lines = [
        "> GENERATED FILE - read-only Review export.",
        f"> Source: `{display_name}`.",
    ]

    if review.status == "blocked":
        lines.extend(
            [
                "",
                "> Review status: blocked. No Review blocks were rendered.",
            ]
        )
        return ReviewMarkdownResult(markdown="\n".join(lines) + "\n", blocks=())

    lines.extend(["", "# Review"])
    if review.status == "partial":
        lines.extend(
            [
                "",
                "> Review status: partial. Some localized validation issues may remain.",
            ]
        )

    mapped: list[ReviewMarkdownBlock] = []
    for block in review.blocks:
        lines.append("")
        start_line = len(lines) + 1
        rendered = _render_block(block, asset_links)
        lines.extend(rendered)
        mapped.append(
            ReviewMarkdownBlock(
                kind=block.kind,
                start_line=start_line,
                end_line=len(lines),
                source=block.source,
                generated=block.source is None,
            )
        )

    return ReviewMarkdownResult(
        markdown="\n".join(lines) + "\n",
        blocks=tuple(mapped),
    )


def serialize_review_markdown(
    review: ReviewDocument,
    *,
    source_name: str | Path = "thesis.md",
    asset_links: Mapping[str, str] | None = None,
) -> str:
    """Return only the generated reader-facing Markdown."""

    return render_review_markdown(
        review,
        source_name=source_name,
        asset_links=asset_links,
    ).markdown


def _contains_absolute_source_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    if (
        normalized.startswith(("/", "//"))
        or re.match(r"^[A-Za-z]:/", normalized)
        or re.search(r"(?<![A-Za-z0-9_./-])/(?!/)", normalized)
    ):
        return True

    parsed = urlsplit(value)
    if parsed.netloc or parsed.path.startswith("/"):
        return True
    if parsed.scheme and parsed.path != value:
        return _contains_absolute_source_path(parsed.path)
    return False


def _validate_source_map_node_id(node_id: str) -> None:
    decoded = _decode_asset_value(node_id)
    if decoded is None or _contains_absolute_source_path(decoded):
        raise ValueError("ReviewSource.node_id must not contain an absolute path")


def _validate_source_map_source(source: ReviewSource | None) -> None:
    _validate_source(source)
    if source is None:
        return
    _validate_source_map_node_id(source.node_id)
    for field in ("line", "column", "end_line", "end_column"):
        value = getattr(source, field)
        if value is not None and value < 1:
            raise ValueError(f"ReviewSource.{field} must be 1-based")
    if (
        source.line is not None
        and source.end_line is not None
        and source.end_line < source.line
    ):
        raise ValueError("ReviewSource source span lines must be ordered")
    if (
        source.column is not None
        and source.end_column is not None
        and (
            source.line is None
            or source.end_line is None
            or source.end_line == source.line
        )
        and source.end_column < source.column
    ):
        raise ValueError("ReviewSource source span columns must be ordered")


def _validate_review_markdown_result(result: object) -> ReviewMarkdownResult:
    if type(result) is not ReviewMarkdownResult:
        raise TypeError(
            "result must be ReviewMarkdownResult, "
            f"got {type(result).__name__}"
        )
    _require_text(result.markdown, "ReviewMarkdownResult.markdown")
    if type(result.blocks) is not tuple:
        raise TypeError("ReviewMarkdownResult.blocks must be tuple")

    markdown_line_count = len(result.markdown.splitlines())
    for block in result.blocks:
        if type(block) is not ReviewMarkdownBlock:
            raise TypeError(
                "unsupported ReviewMarkdownBlock: "
                f"{type(block).__name__}"
            )
        _require_text(block.kind, "ReviewMarkdownBlock.kind")
        if block.kind not in _BLOCK_KINDS:
            raise TypeError(f"unsupported ReviewMarkdownBlock kind: {block.kind!r}")
        _require_int(block.start_line, "ReviewMarkdownBlock.start_line")
        _require_int(block.end_line, "ReviewMarkdownBlock.end_line")
        if block.start_line < 1 or block.end_line < block.start_line:
            raise ValueError("ReviewMarkdownBlock line range must be 1-based and ordered")
        if block.end_line > markdown_line_count:
            raise ValueError(
                "ReviewMarkdownBlock line range exceeds rendered Markdown"
            )
        _validate_source_map_source(block.source)
        _require_bool(block.generated, "ReviewMarkdownBlock.generated")
        if block.generated is not (block.source is None):
            raise ValueError(
                "ReviewMarkdownBlock.generated must match whether source is absent"
            )
    return result


def _serialize_review_source(source: ReviewSource) -> dict[str, object]:
    return {
        "nodeId": source.node_id,
        "sourceSpan": {
            "line": source.line,
            "column": source.column,
            "endLine": source.end_line,
            "endColumn": source.end_column,
        },
    }


def render_review_source_map(
    result: ReviewMarkdownResult,
) -> dict[str, object]:
    """Project generated Markdown ranges into source navigation metadata."""

    result = _validate_review_markdown_result(result)
    blocks: list[dict[str, object]] = []
    for block in result.blocks:
        blocks.append(
            {
                "kind": block.kind,
                "startLine": block.start_line,
                "endLine": block.end_line,
                "generated": block.generated,
                "source": (
                    None
                    if block.source is None
                    else _serialize_review_source(block.source)
                ),
            }
        )
    return {"schemaVersion": 1, "blocks": blocks}


def serialize_review_source_map(
    result: ReviewMarkdownResult,
) -> str:
    """Return a deterministic JSON source map without visible Markdown text."""

    return (
        json.dumps(
            render_review_source_map(result),
            ensure_ascii=False,
            indent=2,
            sort_keys=False,
        )
        + "\n"
    )
