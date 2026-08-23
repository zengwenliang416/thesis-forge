"""Serialize the typed Review projection into generated Markdown."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from thesis_forge.presentation.review import (
    ReviewAlgorithmContent,
    ReviewBibliographyContent,
    ReviewBibliographyEntry,
    ReviewBlock,
    ReviewCitationRun,
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
    "serialize_review_markdown",
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
        return f"**{rendered}**" if inline.bold else rendered
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
