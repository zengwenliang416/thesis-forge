"""markdown-it-py 解析后端（ADR-0001 Phase 2，name=``markdown-it``）。

架构：markdown-it 负责块级分段与行映射（``token.map``，0-based），
项目专属语义全部由自研规则承担，输出与 legacy 后端逐字段平价：

- 旧 Front Matter、``:::`` 学术对象容器和 ``@prefix:id`` 交叉引用在
  markdown-it 通用解析前显式拒绝；代码块和 inline code 中的字面量不触发
  旧格式诊断。拒绝消息带稳定 ``TF-SOURCE-LEGACY-*`` code 和替代示例。
- 现有容器插件与行级消费者暂留在后端内部，供后续 capability 切片迁移；
  legacy preflight 保证它们不会把旧输入静默转换为 v2 文档。
- ``[^label]`` 脚注：``footnote`` 插件仅取块级定义（``move_to_end=False``
  使定义保持源码位置；``inline=False`` 关闭 legacy 不支持的 ``^[...]``）；
  定义正文按 legacy 算法（首行 + 四空格/Tab 续行）从源码行重建。
- 标准 inline token（text / break / strong / emphasis / code / link）由本模块
  递归转换为 typed Inline；inline math ``$...$`` 在 text token 中显式识别。
  语义标记 ``[@key; @key2, locator]`` / semantic links /
  footnote_ref 仍通过公开的 ``parse_inline_content`` 原语处理，直到后续
  semantic-inline 切片完成；未知 token 统一走显式 ParseError。
- 块级规则使用 ``markdown-it-py`` 的 default preset；table/fence/
  blockquote/setext heading 等标准 token 由 typed consumer 消费，
  未支持的 token 统一走显式 ParseError，不再静默降级或丢弃。
- 未闭合容器、front matter 强校验由后端无关预检承担，直接复用
  ``parser.py`` 的 ``parse_front_matter`` 与同构行扫描，ParseError
  消息与行号逐字节一致。

SourceLocation 策略：块级行号 = ``token.map[0] + 1 + front matter 偏移``，
column 恒为 None（与 legacy 现状一致）；标准 inline 节点记录起止行列，
语义节点继续沿用 ``parse_inline_content`` 的起始行列。

本模块通过 ``parser.py`` 的公开共享原语复用现有解析语义；
凡语义问题一律以 legacy 为准（ADR-0001 §5.2 已知差异见文末清单）。
"""

from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from typing import ClassVar

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.footnote import footnote_plugin

from .model import (
    BlockQuote,
    CodeBlock,
    CrossReference,
    Emphasis,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    HardBreak,
    Heading,
    Inline,
    InlineCode,
    InlineMath,
    Link,
    ListBlock,
    ListItem,
    Paragraph,
    SoftBreak,
    SourceLocation,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
    ThesisDocument,
    inline_plain_text,
)
from .parser import (
    CONTAINER_START_RE,
    FOOTNOTE_DEFINITION_RE,
    LIST_ITEM_RE,
    ParseError,
    bibliography_config,
    parse_container,
    parse_front_matter,
    parse_inline_content,
)

__all__ = ["MarkdownItParserBackend"]

CONTAINER_KINDS = ("figure", "table", "equation", "listing", "algorithm", "bibliography")

# 标题行尾 {#id} 提取：与 legacy HEADING_RE 的 (.+?)(?:\s+\{#id\})?\s*$ 同构
_HEADING_ID_RE = re.compile(r"^(.+?)(?:\s+\{#([^}]+)\})?\s*$")
# 容器头 info 中的 {#id}（validate 已保证其位于行尾）
_CONTAINER_ID_RE = re.compile(r"\{#([^}]+)\}")
_LEGACY_REFERENCE_RE = re.compile(
    r"(?<![\w\[])@(?P<prefix>fig|tbl|eq|sec|chap|lst|alg):"
    r"(?P<name>[A-Za-z0-9_.:-]+)"
)
_SEMANTIC_LINK_RE = re.compile(
    r"^#(?P<target>(?:fig|tbl|eq|sec|chap|lst|alg):[A-Za-z0-9_.:-]+)$"
)
_FIGURE_ATTRIBUTE_RE = re.compile(r"^\{#(?P<id>fig:[A-Za-z0-9_.:-]+)\}$")
_FENCE_START_RE = re.compile(r"^ {0,3}(?P<marker>`{3,}|~{3,})")

_UNSUPPORTED_BLOCK_TOKEN_TYPES = frozenset(
    {"code_block", "hr", "html_block", "reference"}
)
_LIST_BLOCK_TOKEN_TYPES = frozenset(
    {"blockquote_open", "fence", "heading_open", "table_open", *_UNSUPPORTED_BLOCK_TOKEN_TYPES}
)


def _make_container_validate(kind: str):
    """生成与 legacy CONTAINER_START_RE 等价的 container 插件 validate。

    收紧点：markup 必须恰好为 ``:::``（legacy 不接受 ``::::``），
    参数只允许 `` kind`` + 可选 `` {#id}`` + 行尾空白。
    """
    pattern = re.compile(r"^\s+" + kind + r"(?:\s+\{#[^}]+\})?\s*$")

    def validate(params: str, markup: str) -> bool:
        return markup == ":::" and pattern.match(params) is not None

    return validate


def _strip_inline_code(line: str) -> str:
    """Blank out closed backtick spans before legacy-marker scanning."""
    chars = list(line)
    cursor = 0
    while cursor < len(line):
        if line[cursor] != "`":
            cursor += 1
            continue
        start = cursor
        while cursor < len(line) and line[cursor] == "`":
            cursor += 1
        marker = line[start:cursor]
        close = line.find(marker, cursor)
        if close < 0:
            continue
        for index in range(start, close + len(marker)):
            chars[index] = " "
        cursor = close + len(marker)
    return "".join(chars)


def _legacy_source_error(
    code: str,
    line: int,
    message: str,
    replacement: str,
) -> ParseError:
    return ParseError(
        f"{code} at line {line}: {message}. "
        f"Replacement example: {replacement}"
    )


def _reject_legacy_source(lines: list[str]) -> None:
    """Reject v1 source constructs before markdown-it can flatten them."""
    if lines and lines[0].strip() == "---":
        raise _legacy_source_error(
            "TF-SOURCE-LEGACY-001",
            1,
            "YAML Front Matter is not supported in thesis.md",
            "move project metadata to thesisforge.yaml",
        )

    fence_char: str | None = None
    fence_length = 0
    for line_number, raw in enumerate(lines, start=1):
        if fence_char is not None:
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_char)}{{{fence_length},}}\s*$",
                raw,
            )
            if closing:
                fence_char = None
                fence_length = 0
            continue

        opening = _FENCE_START_RE.match(raw)
        if opening:
            marker = opening.group("marker")
            fence_char = marker[0]
            fence_length = len(marker)
            continue

        if raw.startswith(("    ", "\t")):
            continue

        visible = _strip_inline_code(raw)
        container = CONTAINER_START_RE.match(visible.strip())
        if container:
            kind = container.group(1)
            raise _legacy_source_error(
                "TF-SOURCE-LEGACY-002",
                line_number,
                f"legacy ::: {kind} containers are not supported",
                "![caption](assets/image.png){#fig:example}",
            )

        reference = _LEGACY_REFERENCE_RE.search(visible)
        if reference:
            prefix = reference.group("prefix")
            raise _legacy_source_error(
                "TF-SOURCE-LEGACY-003",
                line_number,
                f"legacy @{prefix}:id cross-references are not supported",
                f"[label](#{prefix}:example)",
            )


def _build_markdown_it() -> MarkdownIt:
    md = MarkdownIt("default")
    md.use(footnote_plugin, inline=False, move_to_end=False)
    for kind in CONTAINER_KINDS:
        md.use(container_plugin, kind, validate=_make_container_validate(kind))
    return md


def _check_containers_closed(lines: list[str], start: int) -> None:
    """未闭合容器预检：与 legacy 主循环同构的行扫描，ParseError 消息一致。

    legacy 中脚注定义（含续行）与容器体会吞掉 ``:::`` 行，本预检按同样
    的顺序跳过这两类结构，避免误报。
    """
    i = start
    fence_char: str | None = None
    fence_length = 0
    while i < len(lines):
        raw = lines[i]
        if fence_char is not None:
            closing = re.match(
                rf"^ {{0,3}}{re.escape(fence_char)}{{{fence_length},}}\s*$",
                raw,
            )
            if closing:
                fence_char = None
                fence_length = 0
            i += 1
            continue

        opening = _FENCE_START_RE.match(raw)
        if opening:
            marker = opening.group("marker")
            fence_char = marker[0]
            fence_length = len(marker)
            i += 1
            continue

        if raw.startswith(("    ", "\t")):
            i += 1
            continue

        stripped = raw.strip()
        if FOOTNOTE_DEFINITION_RE.match(raw):
            i += 1
            while i < len(lines) and (lines[i].startswith("    ") or lines[i].startswith("\t")):
                i += 1
            continue
        container = CONTAINER_START_RE.match(stripped)
        if container:
            kind = container.group(1)
            line_no = i + 1
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                i += 1
            if i >= len(lines):
                raise ParseError(f"第 {line_no} 行的 {kind} 容器未闭合")
            i += 1
            continue
        i += 1


def _find_close(tokens: list[Token], idx: int, open_type: str, close_type: str) -> int:
    """从 idx 起按深度配对找到对应 close token 的下标（同类型可嵌套时仍正确）。

    预检已保证容器闭合；找不到时兜底返回末尾，防御性避免越界。
    """
    depth = 0
    for j in range(idx, len(tokens)):
        if tokens[j].type == open_type:
            depth += 1
        elif tokens[j].type == close_type:
            depth -= 1
            if depth == 0:
                return j
    return len(tokens) - 1


def _location_at(
    text: str,
    offset: int,
    start_line: int,
    start_column: int,
) -> SourceLocation:
    prefix = text[:offset]
    newline_count = prefix.count("\n")
    if newline_count:
        column = len(prefix.rsplit("\n", 1)[-1]) + 1
    else:
        column = start_column + len(prefix)
    return SourceLocation(line=start_line + newline_count, column=column)


def _span(
    text: str,
    start: int,
    end: int,
    start_line: int,
    start_column: int,
) -> SourceLocation:
    location = _location_at(text, start, start_line, start_column)
    end_location = _location_at(text, end, start_line, start_column)
    location.end_line = end_location.line
    location.end_column = end_location.column
    return location


def _find_inline_math(text: str, start: int = 0) -> tuple[int, int, str] | None:
    """Return the next single-dollar inline math span in ``text``."""
    opening = start
    while opening < len(text):
        if text[opening] != "$":
            opening += 1
            continue
        if opening > 0 and text[opening - 1] == "\\":
            opening += 1
            continue
        if (opening > 0 and text[opening - 1] == "$") or (
            opening + 1 < len(text) and text[opening + 1] == "$"
        ):
            opening += 1
            continue

        closing = opening + 1
        while closing < len(text):
            if text[closing] == "$" and text[closing - 1] != "\\":
                if closing + 1 < len(text) and text[closing + 1] == "$":
                    closing += 1
                    continue
                latex = text[opening + 1 : closing]
                if latex:
                    return opening, closing + 1, latex
                break
            closing += 1
        opening += 1
    return None


class _InlineTokenConverter:
    """Convert one markdown-it ``inline`` token tree into typed Inline nodes."""

    _CLOSE_FOR_OPEN: ClassVar[dict[str, str]] = {
        "strong_open": "strong_close",
        "em_open": "em_close",
        "link_open": "link_close",
    }

    def __init__(
        self,
        content: str,
        tokens: list[Token],
        *,
        start_line: int,
        start_column: int,
    ) -> None:
        self.content = content
        self.tokens = tokens
        self.start_line = start_line
        self.start_column = start_column
        self.cursor = 0

    def convert(self) -> list[Inline]:
        inlines, next_index = self._convert_until(0)
        if next_index != len(self.tokens):
            raise ParseError(
                f"未消费的 markdown-it 行内 token: {self.tokens[next_index].type}"
            )
        if self.cursor != len(self.content):
            location = self._location(self.cursor)
            raise ParseError(
                "未消费的 markdown-it 行内源码: "
                f"第 {location.line} 行第 {location.column} 列"
            )
        return inlines

    def _location(self, offset: int) -> SourceLocation:
        return _location_at(self.content, offset, self.start_line, self.start_column)

    def _span(self, start: int, end: int) -> SourceLocation:
        return _span(
            self.content,
            start,
            end,
            self.start_line,
            self.start_column,
        )

    def _decode_one(self, offset: int) -> tuple[str, int]:
        current = self.content[offset]
        if (
            current == "\\"
            and offset + 1 < len(self.content)
            and self.content[offset + 1] in r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
        ):
            return self.content[offset + 1], offset + 2

        if current == "&":
            semicolon = self.content.find(";", offset + 1)
            if semicolon >= 0:
                entity = self.content[offset : semicolon + 1]
                decoded = unescape(entity)
                if decoded != entity:
                    return decoded, semicolon + 1

        return current, offset + 1

    def _decode_fragment(self, value: str) -> str:
        decoded: list[str] = []
        offset = 0
        while offset < len(value):
            current = value[offset]
            if (
                current == "\\"
                and offset + 1 < len(value)
                and value[offset + 1] in r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
            ):
                decoded.append(value[offset + 1])
                offset += 2
                continue
            if current == "&":
                semicolon = value.find(";", offset + 1)
                if semicolon >= 0:
                    entity = value[offset : semicolon + 1]
                    replacement = unescape(entity)
                    if replacement != entity:
                        decoded.append(replacement)
                        offset = semicolon + 1
                        continue
            decoded.append(current)
            offset += 1
        return "".join(decoded)

    def _match_decoded(
        self,
        start: int,
        target: str,
        *,
        allow_prefix: bool,
    ) -> tuple[int, str] | None:
        offset = start
        decoded: list[str] = []
        while offset < len(self.content) and len("".join(decoded)) < len(target):
            value, next_offset = self._decode_one(offset)
            candidate = "".join(decoded) + value
            if not target.startswith(candidate):
                return None
            decoded.append(value)
            offset = next_offset
        value = "".join(decoded)
        if value == target or (allow_prefix and offset == len(self.content)):
            return offset, value
        return None

    def _consume_markup(self, markup: str) -> tuple[int, int]:
        if not markup:
            raise ParseError("markdown-it 行内标记缺少 markup")
        start = self.cursor
        if not self.content.startswith(markup, start):
            start = self.content.find(markup, self.cursor)
            if start < 0:
                raise ParseError(f"未消费的 markdown-it 行内标记: {markup}")
        self.cursor = start + len(markup)
        return start, self.cursor

    def _consume_text(
        self,
        token_content: str,
    ) -> tuple[str, str, int, int, str]:
        if not token_content:
            return "", "", self.cursor, self.cursor, ""

        search_start = self.cursor
        match = self._match_decoded(
            search_start,
            token_content,
            allow_prefix=True,
        )
        start = search_start
        if match is None:
            for candidate in range(search_start + 1, len(self.content)):
                match = self._match_decoded(candidate, token_content, allow_prefix=True)
                if match is not None:
                    start = candidate
                    break
        if match is None:
            raise ParseError(
                "markdown-it text token 无法映射到源码: "
                f"{token_content!r}"
            )

        end, decoded = match
        gap = self.content[search_start:start]
        self.cursor = end
        return self.content[start:end], decoded, start, end, gap

    def _convert_text(self, token: Token) -> list[Inline]:
        raw, _, start, _, gap = self._consume_text(token.content)
        result: list[Inline] = []
        if gap:
            if gap.strip(" \t") != "":
                raise ParseError(
                    "markdown-it text token 前存在未消费的行内源码: "
                    f"{gap!r}"
                )
            result.append(Text(value=gap, location=self._span(start - len(gap), start)))

        if not raw:
            return result

        cursor = 0
        while cursor < len(raw):
            math_span = _find_inline_math(raw, cursor)
            if math_span is None:
                value = self._decode_fragment(raw[cursor:])
                result.extend(
                    self._convert_semantic_text(
                        value,
                        start + cursor,
                        len(raw) - cursor,
                    )
                )
                break

            math_start, math_end, latex = math_span
            if math_start > cursor:
                value = self._decode_fragment(raw[cursor:math_start])
                result.extend(
                    self._convert_semantic_text(
                        value,
                        start + cursor,
                        math_start - cursor,
                    )
                )
            result.append(
                InlineMath(
                    latex=self._decode_fragment(latex),
                    location=self._span(start + math_start, start + math_end),
                )
            )
            cursor = math_end
        return result

    def _convert_semantic_text(
        self,
        value: str,
        offset: int,
        raw_length: int,
    ) -> list[Inline]:
        if not value:
            return []
        location = self._location(offset)
        parsed = parse_inline_content(value, location.line or 1, location.column or 1)
        if len(parsed) == 1 and isinstance(parsed[0], Text) and parsed[0].value == value:
            return [Text(value=value, location=self._span(offset, offset + raw_length))]
        return parsed

    def _consume_break(self) -> tuple[int, int]:
        start = self.cursor
        newline = self.content.find("\n", start)
        if newline < 0:
            raise ParseError("markdown-it break token 无法映射到源码换行")
        self.cursor = newline + 1
        return start, self.cursor

    def _consume_code(self, token: Token) -> tuple[int, int]:
        markup = token.markup or "`"
        start = self.cursor
        if not self.content.startswith(markup, start):
            found = self.content.find(markup, start)
            if found < 0:
                raise ParseError("markdown-it code token 无法映射到源码")
            start = found
        content_start = start + len(markup)
        closing = self.content.find(markup, content_start)
        if closing < 0:
            raise ParseError("markdown-it code token 缺少结束标记")
        self.cursor = closing + len(markup)
        return start, self.cursor

    def _find_balanced_close(self, open_index: int, opening: str, closing: str) -> int:
        depth = 0
        escaped = False
        for offset in range(open_index, len(self.content)):
            current = self.content[offset]
            if escaped:
                escaped = False
                continue
            if current == "\\":
                escaped = True
                continue
            if current == opening:
                depth += 1
            elif current == closing:
                depth -= 1
                if depth == 0:
                    return offset
        return -1

    def _consume_link(self, link_start: int) -> int:
        label_open = link_start
        label_close = self._find_balanced_close(label_open, "[", "]")
        if label_close < 0:
            raise ParseError("markdown-it link token 缺少结束标签")

        after_label = label_close + 1
        if self.content.startswith("(", after_label):
            destination_close = self._find_balanced_close(
                after_label,
                "(",
                ")",
            )
            if destination_close < 0:
                raise ParseError("markdown-it link token 缺少结束地址")
            self.cursor = destination_close + 1
        elif self.content.startswith("[", after_label):
            reference_close = self._find_balanced_close(
                after_label,
                "[",
                "]",
            )
            if reference_close < 0:
                raise ParseError("markdown-it reference link token 缺少结束标签")
            self.cursor = reference_close + 1
        else:
            self.cursor = after_label
        return self.cursor

    def _convert_until(
        self,
        index: int,
        stop_type: str | None = None,
    ) -> tuple[list[Inline], int]:
        result: list[Inline] = []
        while index < len(self.tokens):
            token = self.tokens[index]
            if stop_type is not None and token.type == stop_type:
                return result, index

            token_type = token.type
            if token_type == "text":
                result.extend(self._convert_text(token))
                index += 1
            elif token_type in {"softbreak", "hardbreak"}:
                start, end = self._consume_break()
                node_type = SoftBreak if token_type == "softbreak" else HardBreak
                result.append(node_type(location=self._span(start, end)))
                index += 1
            elif token_type in {"strong_open", "em_open"}:
                close_type = self._CLOSE_FOR_OPEN[token_type]
                start, _ = self._consume_markup(token.markup)
                children, close_index = self._convert_until(index + 1, close_type)
                if close_index >= len(self.tokens):
                    raise ParseError(f"未闭合的 markdown-it 行内 token: {token_type}")
                close = self.tokens[close_index]
                _, end = self._consume_markup(close.markup or token.markup)
                node_type = Strong if token_type == "strong_open" else Emphasis
                result.append(
                    node_type(children=tuple(children), location=self._span(start, end))
                )
                index = close_index + 1
            elif token_type == "code_inline":
                start, end = self._consume_code(token)
                result.append(
                    InlineCode(value=token.content, location=self._span(start, end))
                )
                index += 1
            elif token_type == "footnote_ref":
                label = str((token.meta or {}).get("label", ""))
                if not label:
                    raise ParseError("markdown-it footnote_ref 缺少 label")
                raw = f"[^{label}]"
                start = self.cursor
                if not self.content.startswith(raw, start):
                    found = self.content.find(raw, start)
                    if found < 0:
                        raise ParseError("markdown-it footnote_ref 无法映射到源码")
                    start = found
                self.cursor = start + len(raw)
                result.append(
                    FootnoteReference(
                        label=label,
                        location=self._span(start, self.cursor),
                    )
                )
                index += 1
            elif token_type == "link_open":
                is_autolink = token.markup == "autolink"
                start, _ = self._consume_markup("<" if is_autolink else "[")
                children, close_index = self._convert_until(index + 1, "link_close")
                if close_index >= len(self.tokens):
                    raise ParseError("未闭合的 markdown-it 行内 token: link_open")
                if is_autolink:
                    _, end = self._consume_markup(">")
                else:
                    end = self._consume_link(start)
                href = token.attrGet("href") or ""
                semantic_match = _SEMANTIC_LINK_RE.fullmatch(href)
                if semantic_match is not None:
                    fallback = inline_plain_text(children)
                    result.append(
                        CrossReference(
                            target=semantic_match.group("target"),
                            fallback=fallback or None,
                            location=self._span(start, end),
                        )
                    )
                else:
                    result.append(
                        Link(
                            label=inline_plain_text(children),
                            destination=href,
                            location=self._span(start, end),
                        )
                    )
                index = close_index + 1
            elif token_type in {"strong_close", "em_close", "link_close"}:
                if stop_type is None:
                    raise ParseError(f"未配对的 markdown-it 行内 token: {token_type}")
                return result, index
            else:
                raise ParseError(f"不支持的 markdown-it 行内 token: {token_type}")
        if stop_type is not None:
            raise ParseError(f"未闭合的 markdown-it 行内 token: {stop_type}")
        return result, index


def _parse_inline_token(
    token: Token,
    *,
    content: str | None = None,
    start_line: int,
    start_column: int = 1,
) -> list[Inline]:
    if token.children is None:
        raise ParseError("markdown-it inline token 缺少 children")
    return _InlineTokenConverter(
        token.content if content is None else content,
        token.children,
        start_line=start_line,
        start_column=start_column,
    ).convert()


class MarkdownItParserBackend:
    """基于 markdown-it-py 的 ParserBackend 实现（ADR-0001 目标后端）。"""

    name = "markdown-it"

    def __init__(self) -> None:
        self._md = _build_markdown_it()

    def parse_file(self, path: str | Path) -> ThesisDocument:
        source_path = Path(path).resolve()
        return self.parse_text(source_path.read_text(encoding="utf-8"), source_path=source_path)

    def parse_text(self, text: str, *, source_path: str | Path) -> ThesisDocument:
        lines = text.splitlines()
        _reject_legacy_source(lines)
        metadata, start = parse_front_matter(lines)
        doc = ThesisDocument(
            source_path=Path(source_path).resolve(),
            metadata=metadata,
            bibliography=bibliography_config(metadata),
        )
        _check_containers_closed(lines, start)
        body_lines = lines[start:]
        if body_lines:
            tokens = self._md.parse("\n".join(body_lines), {})
            self._walk(doc, tokens, body_lines, start)
        return doc

    # ------------------------------------------------------------------
    # 块级 token → model
    # ------------------------------------------------------------------

    def _walk(
        self,
        doc: ThesisDocument,
        tokens: list[Token],
        lines: list[str],
        offset: int,
    ) -> None:
        idx = 0
        total = len(tokens)
        while idx < total:
            token = tokens[idx]
            token_type = token.type
            if token_type == "heading_open":
                inline_token = tokens[idx + 1]
                self._emit_heading(doc, token, inline_token, offset)
                idx += 3
            elif token_type == "paragraph_open":
                inline_token = tokens[idx + 1]
                self._emit_paragraph(doc, inline_token, offset)
                idx += 3
            elif token_type in ("bullet_list_open", "ordered_list_open", "list_item_open"):
                # 列表语义以 legacy 逐行扫描为准（缩进 //2、混合 marker 截断、
                # 空行分块）；mdit 只负责发现列表起点，扫描消费的行区间内的
                # mdit token 全部跳过（close token map=None，必然属于已消费结构）。
                assert token.map is not None
                start0 = token.map[0]
                end = self._scan_list(doc, lines, start0, offset)
                idx += 1
                spill = end
                while idx < total:
                    skipped = tokens[idx]
                    skipped_map = skipped.map
                    if skipped_map is None:
                        idx += 1
                        continue
                    if skipped_map[0] >= spill:
                        break
                    if skipped.type in _LIST_BLOCK_TOKEN_TYPES:
                        raise ParseError(
                            "列表中未消费的 markdown-it 块 token: "
                            f"{skipped.type}"
                        )
                    spill = max(spill, skipped_map[1])
                    idx += 1
                if spill > end:
                    # mdit 把列表项续行并进项内段落（map 跨界），legacy 则截断
                    # 列表并把续行落成新段落；按 legacy 补出该段落。
                    self._emit_raw_paragraph(doc, lines, end, spill, offset)
            elif token_type.startswith("container_") and token_type.endswith("_open"):
                idx = self._emit_container(doc, tokens, idx, lines, offset)
            elif token_type == "footnote_reference_open":
                idx = self._emit_footnote_definition(doc, tokens, idx, lines, offset)
            elif token_type == "blockquote_open":
                idx = self._emit_blockquote(doc, tokens, idx, lines, offset)
            elif token_type == "fence":
                idx = self._emit_fence(doc, tokens, idx, offset)
            elif token_type == "table_open":
                idx = self._emit_table(doc, tokens, idx, offset)
            elif token_type in _UNSUPPORTED_BLOCK_TOKEN_TYPES:
                raise ParseError(f"不支持的 markdown-it 块 token: {token_type}")
            else:
                raise ParseError(f"未消费的 markdown-it 块 token: {token_type}")

    def _emit_heading(
        self,
        doc: ThesisDocument,
        open_token: Token,
        inline_token: Token,
        offset: int,
    ) -> None:
        level = int(open_token.tag[1:])
        match = _HEADING_ID_RE.match(inline_token.content)
        text = match.group(1) if match else ""
        block_id = match.group(2) if match else None
        assert open_token.map is not None
        line = open_token.map[0] + 1 + offset
        # legacy 以 len(marks) + 2 为行内列基准（假设 # 后恰好一个空格）
        inlines = _parse_inline_token(
            inline_token,
            content=text,
            start_line=line,
            start_column=level + 2,
        )
        doc.blocks.append(
            Heading(
                id=block_id,
                level=level,
                inlines=inlines,
                location=SourceLocation(line=line),
            )
        )

    def _emit_paragraph(self, doc: ThesisDocument, inline_token: Token, offset: int) -> None:
        # mdit 段落 content = 原始行拼接后整体 strip，与 legacy 段落缓冲语义一致
        text = inline_token.content
        if not text:
            return
        assert inline_token.map is not None
        if inline_token.children and any(
            child.type == "image" for child in inline_token.children
        ):
            self._emit_standard_figure(doc, inline_token, offset)
            return
        line = inline_token.map[0] + 1 + offset
        inlines = _parse_inline_token(
            inline_token,
            start_line=line,
        )
        doc.blocks.append(
            Paragraph(inlines=inlines, location=SourceLocation(line=line))
        )

    def _emit_blockquote(
        self,
        doc: ThesisDocument,
        tokens: list[Token],
        idx: int,
        lines: list[str],
        offset: int,
    ) -> int:
        open_token = tokens[idx]
        close_idx = _find_close(tokens, idx, "blockquote_open", "blockquote_close")
        assert open_token.map is not None
        child_doc = ThesisDocument(
            source_path=doc.source_path,
            metadata=doc.metadata,
            bibliography=doc.bibliography,
        )
        self._walk(child_doc, tokens[idx + 1 : close_idx], lines, offset)
        doc.blocks.append(
            BlockQuote(
                children=tuple(child_doc.blocks),
                location=SourceLocation(line=open_token.map[0] + 1 + offset),
            )
        )
        return close_idx + 1

    def _emit_fence(
        self,
        doc: ThesisDocument,
        tokens: list[Token],
        idx: int,
        offset: int,
    ) -> int:
        token = tokens[idx]
        assert token.map is not None
        info = token.info.strip()
        language = info.split(None, 1)[0] if info else None
        doc.blocks.append(
            CodeBlock(
                language=language,
                code=token.content,
                location=SourceLocation(line=token.map[0] + 1 + offset),
            )
        )
        return idx + 1

    def _emit_table(
        self,
        doc: ThesisDocument,
        tokens: list[Token],
        idx: int,
        offset: int,
    ) -> int:
        open_token = tokens[idx]
        close_idx = _find_close(tokens, idx, "table_open", "table_close")
        assert open_token.map is not None
        rows: list[TableRow] = []
        row_idx = idx + 1
        while row_idx < close_idx:
            if tokens[row_idx].type != "tr_open":
                row_idx += 1
                continue

            row_open = tokens[row_idx]
            row_close = _find_close(tokens, row_idx, "tr_open", "tr_close")
            cells: list[TableCell] = []
            header = False
            cell_idx = row_idx + 1
            while cell_idx < row_close:
                cell_open = tokens[cell_idx]
                if cell_open.type not in {"th_open", "td_open"}:
                    cell_idx += 1
                    continue

                header = header or cell_open.type == "th_open"
                close_type = (
                    "th_close" if cell_open.type == "th_open" else "td_close"
                )
                cell_close = _find_close(tokens, cell_idx, cell_open.type, close_type)
                inline_token = (
                    tokens[cell_idx + 1]
                    if cell_idx + 1 < cell_close
                    and tokens[cell_idx + 1].type == "inline"
                    else None
                )
                if inline_token is None:
                    cell_line = (
                        row_open.map[0] + 1 + offset
                        if row_open.map is not None
                        else open_token.map[0] + 1 + offset
                    )
                else:
                    assert inline_token.map is not None
                    cell_line = inline_token.map[0] + 1 + offset

                style = cell_open.attrGet("style")
                alignment = (
                    style.removeprefix("text-align:")
                    if style is not None
                    else None
                )
                if alignment not in {None, "left", "center", "right"}:
                    alignment = None
                cells.append(
                    TableCell(
                        inlines=tuple(
                            _parse_inline_token(
                                inline_token,
                                start_line=cell_line,
                            )
                            if inline_token is not None
                            else ()
                        ),
                        alignment=alignment,
                        location=SourceLocation(line=cell_line),
                    )
                )
                cell_idx = cell_close + 1

            if cells:
                row_line = (
                    row_open.map[0] + 1 + offset
                    if row_open.map is not None
                    else open_token.map[0] + 1 + offset
                )
                rows.append(
                    TableRow(
                        header=header,
                        cells=tuple(cells),
                        location=SourceLocation(line=row_line),
                    )
                )
            row_idx = row_close + 1

        doc.blocks.append(
            Table(
                rows=tuple(rows),
                location=SourceLocation(line=open_token.map[0] + 1 + offset),
            )
        )
        return close_idx + 1

    def _emit_raw_paragraph(
        self,
        doc: ThesisDocument,
        lines: list[str],
        start0: int,
        end0: int,
        offset: int,
    ) -> None:
        """按 legacy 段落缓冲语义把源码行区间 [start0, end0) 落成段落。"""
        text = "\n".join(lines[start0:end0]).strip()
        if not text:
            return
        line = start0 + 1 + offset
        inlines = parse_inline_content(text, line)
        doc.blocks.append(
            Paragraph(inlines=inlines, location=SourceLocation(line=line))
        )

    def _emit_container(
        self,
        doc: ThesisDocument,
        tokens: list[Token],
        idx: int,
        lines: list[str],
        offset: int,
    ) -> int:
        open_token = tokens[idx]
        open_type = open_token.type
        kind = open_type[len("container_") : -len("_open")]
        close_idx = _find_close(tokens, idx, open_type, f"container_{kind}_close")
        assert open_token.map is not None
        start0, end0 = open_token.map
        body = lines[start0 + 1 : end0]
        id_match = _CONTAINER_ID_RE.search(open_token.info)
        block_id = id_match.group(1) if id_match else None
        line = start0 + 1 + offset
        # 容器体语义（kv 元数据、caption inline、围栏剥离）整体复用 legacy 实现
        doc.blocks.append(parse_container(kind, block_id, body, line))
        return close_idx + 1

    def _emit_footnote_definition(
        self,
        doc: ThesisDocument,
        tokens: list[Token],
        idx: int,
        lines: list[str],
        offset: int,
    ) -> int:
        open_token = tokens[idx]
        close_idx = _find_close(
            tokens, idx, "footnote_reference_open", "footnote_reference_close"
        )
        assert open_token.map is not None
        start0, end0 = open_token.map
        line = start0 + 1 + offset
        match = FOOTNOTE_DEFINITION_RE.match(lines[start0])
        if match is None:
            # label 超出 legacy 字符集：legacy 不视为定义，按段落原文降级
            text = "\n".join(lines[start0:end0]).strip()
            if text:
                inlines = parse_inline_content(text, line)
                doc.blocks.append(
                    Paragraph(inlines=inlines, location=SourceLocation(line=line))
                )
            return close_idx + 1

        label = match.group("label")
        segments = [(match.group("text"), line, match.start("text") + 1)]
        j = start0 + 1
        while j < end0 and (lines[j].startswith("    ") or lines[j].startswith("\t")):
            continuation = lines[j].lstrip()
            column = len(lines[j]) - len(continuation) + 1
            segments.append((continuation, j + 1 + offset, column))
            j += 1
        text = "\n".join(segment[0] for segment in segments).strip()
        inlines: list[Inline] = []
        for segment_text, segment_line, segment_column in segments:
            inlines.extend(parse_inline_content(segment_text, segment_line, segment_column))
        doc.blocks.append(
            FootnoteDefinition(
                label=label,
                inlines=inlines,
                location=SourceLocation(line=line),
            )
        )
        return close_idx + 1

    def _emit_standard_figure(
        self,
        doc: ThesisDocument,
        inline_token: Token,
        offset: int,
    ) -> None:
        children = inline_token.children or []
        if (
            len(children) != 2
            or children[0].type != "image"
            or children[1].type != "text"
        ):
            raise ParseError(
                "标准图片必须独占一个段落并带有效的 fig ID: "
                "![caption](path){#fig:id}"
            )

        id_match = _FIGURE_ATTRIBUTE_RE.fullmatch(children[1].content.strip())
        if id_match is None:
            raise ParseError(
                "标准图片必须带有效的 fig ID: ![caption](path){#fig:id}"
            )

        assert inline_token.map is not None
        line = inline_token.map[0] + 1 + offset
        image = children[0]
        src = image.attrGet("src") or ""
        if not src:
            raise ParseError("标准图片缺少 src")

        caption = image.content
        caption_inlines: tuple[Inline, ...] = ()
        if caption:
            caption_tokens = self._md.parseInline(caption, {})
            if len(caption_tokens) != 1 or caption_tokens[0].type != "inline":
                raise ParseError("标准图片 caption 无法转换为 typed inline")
            image_start = inline_token.content.find("![")
            caption_column = image_start + 3 if image_start >= 0 else 3
            caption_inlines = tuple(
                _parse_inline_token(
                    caption_tokens[0],
                    start_line=line,
                    start_column=caption_column,
                )
            )

        doc.blocks.append(
            Figure(
                id=id_match.group("id"),
                src=src,
                caption_inlines=caption_inlines,
                location=SourceLocation(line=line),
            )
        )

    def _scan_list(
        self,
        doc: ThesisDocument,
        lines: list[str],
        i: int,
        offset: int,
    ) -> int:
        """从第 i 行（0-based）起按 legacy 语义扫描列表，返回消费后的下一行下标。"""
        first = LIST_ITEM_RE.match(lines[i])
        assert first is not None  # mdit 列表规则触发处必然匹配
        marker = first.group("marker")
        ordered = marker[0].isdigit()
        items: list[ListItem] = []
        start_number = int(marker.rstrip(".)")) if ordered else None
        line = i + 1 + offset

        while i < len(lines):
            item_match = LIST_ITEM_RE.match(lines[i])
            if item_match is None:
                break
            item_marker = item_match.group("marker")
            if item_marker[0].isdigit() != ordered:
                break
            item_text = item_match.group("text")
            indent = len(item_match.group("indent").expandtabs(4))
            item_line = i + 1 + offset
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
                location=SourceLocation(line=line),
            )
        )
        return i
