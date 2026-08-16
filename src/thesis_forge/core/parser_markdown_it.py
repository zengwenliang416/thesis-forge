"""markdown-it-py 解析后端（ADR-0001 Phase 2，name=``markdown-it``）。

架构：markdown-it 负责块级分段与行映射（``token.map``，0-based），
项目专属语义全部由自研规则承担，输出与 legacy 后端逐字段平价：

- 六种 ``:::`` 容器：mdit-py-plugins ``container`` 按名注册 ×6，
  ``validate`` 收紧为与 legacy ``CONTAINER_START_RE`` 等价的写法
  （恰好 3 个冒号 + 可选 ``{#id}`` + 行尾无杂物）；容器体不读 mdit
  子树，直接按行切片复用 legacy 的 ``_parse_container`` /
  ``_parse_container_inlines``（kv 元数据、caption inline、listing
  围栏剥离、`$$` 剥离等行为因此逐字节一致）。
- ``[^label]`` 脚注：``footnote`` 插件仅取块级定义（``move_to_end=False``
  使定义保持源码位置；``inline=False`` 关闭 legacy 不支持的 ``^[...]``）；
  定义正文按 legacy 算法（首行 + 四空格/Tab 续行）从源码行重建。
  行内 ``footnote_ref`` 用 ``ruler.at`` 替换为与 legacy 字符集完全一致
  的自研实现（不依赖定义是否存在，label 限定 ``[A-Za-z0-9_.:-]+``）。
- citation ``[@key; @key2, locator]`` 与 crossref ``@fig:x``：
  两条自研 inline rule（``citation`` / ``crossref``），匹配语义逐行
  对齐 legacy 的 ``INLINE_TOKEN_RE``（含 crossref 的 ``(?<!\\[)`` 前视）。
- 行内其余 CommonMark 规则（emphasis/link/image/escape/entity/…）全部
  禁用，与 legacy「未知语法静默降级为段落原文」一致；``text`` /
  ``softbreak`` 之外的意外 token 触发防御性回退（改用 legacy
  ``_parse_inline_content`` 重扫该段，语义保证一致）。
- 块级规则仅保留 heading/list/paragraph + 上述插件；table/fence/
  blockquote/html_block/hr/lheading/reference/code 禁用（禁用后这些
  行按段落原文处理，与 legacy 降级行为一致）。
- 未闭合容器、front matter 强校验由后端无关预检承担，直接复用
  ``parser.py`` 的 ``_parse_front_matter`` 与同构行扫描，ParseError
  消息与行号逐字节一致。

SourceLocation 策略：块级行号 = ``token.map[0] + 1 + front matter 偏移``，
column 恒为 None（与 legacy 现状一致）；行内行列由 inline rule 记录的
段内偏移经 legacy ``_location_for_offset`` 换算，与 legacy 完全一致。

本模块有意复用 ``parser.py`` 的私有函数（冻结维护的对照基准），
凡语义问题一律以 legacy 为准（ADR-0001 §5.2 已知差异见文末清单）。
"""

from __future__ import annotations

import re
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline
from markdown_it.token import Token
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.footnote import footnote_plugin

from .model import (
    Citation,
    CrossReference,
    FootnoteDefinition,
    FootnoteReference,
    Heading,
    Inline,
    ListBlock,
    ListItem,
    Paragraph,
    SourceLocation,
    Text,
    ThesisDocument,
)
from .parser import (
    CITATION_KEY_RE,
    CONTAINER_START_RE,
    FOOTNOTE_DEFINITION_RE,
    LIST_ITEM_RE,
    ParseError,
    _bibliography_config,
    _location_for_offset,
    _parse_container,
    _parse_container_inlines,
    _parse_front_matter,
    _parse_inline_content,
)

__all__ = ["MarkdownItParserBackend"]

CONTAINER_KINDS = ("figure", "table", "equation", "listing", "algorithm", "bibliography")

# 标题行尾 {#id} 提取：与 legacy HEADING_RE 的 (.+?)(?:\s+\{#id\})?\s*$ 同构
_HEADING_ID_RE = re.compile(r"^(.+?)(?:\s+\{#([^}]+)\})?\s*$")
# 容器头 info 中的 {#id}（validate 已保证其位于行尾）
_CONTAINER_ID_RE = re.compile(r"\{#([^}]+)\}")
# 三条自研 inline rule 的匹配式，与 legacy INLINE_TOKEN_RE 各分支逐一对应
_CITATION_AT_RE = re.compile(r"\[[^\]]*@[^\]]+\]")
_CROSSREF_AT_RE = re.compile(r"@(?P<prefix>fig|tbl|eq|alg|lst|sec|chap):(?P<name>[A-Za-z0-9_.:-]+)")
_FOOTNOTE_REF_AT_RE = re.compile(r"\[\^(?P<label>[A-Za-z0-9_.:-]+)\]")

# inline children 中允许出现的 token 类型；其余一律触发 legacy 重扫兜底
_SUPPORTED_INLINE_TOKENS = frozenset(
    {"text", "softbreak", "hardbreak", "citation", "crossref", "footnote_ref"}
)

# legacy 不支持的 CommonMark 块级结构：禁用后按段落原文降级（与 legacy 一致）
_DISABLED_BLOCK_RULES = (
    "blockquote",
    "code",
    "fence",
    "hr",
    "html_block",
    "lheading",
    "reference",
)
# legacy 不支持的行内结构：禁用后保留原文（text/softbreak 之外只剩三条自研规则）
_DISABLED_INLINE_RULES = (
    "autolink",
    "backticks",
    "emphasis",
    "entity",
    "escape",
    "html_inline",
    "image",
    "link",
)


# ---------------------------------------------------------------------------
# 自研 inline rule（state.src 为段落文本，state.pos 为段内偏移）
# ---------------------------------------------------------------------------


def _footnote_ref_rule(state: StateInline, silent: bool) -> bool:
    """``[^label]`` 脚注引用；label 字符集与 legacy 一致，不要求定义存在。"""
    start = state.pos
    match = _FOOTNOTE_REF_AT_RE.match(state.src, start)
    if match is None:
        return False
    if not silent:
        token = state.push("footnote_ref", "", 0)
        token.meta = {
            "label": match.group("label"),
            "offset": start,
            "length": match.end() - start,
        }
    state.pos = match.end()
    return True


def _citation_rule(state: StateInline, silent: bool) -> bool:
    """``[@key; @key2, locator]`` 文献引用；多 key 拆分与 locator 解析在转换层完成。"""
    start = state.pos
    if start >= state.posMax or state.src[start] != "[":
        return False
    match = _CITATION_AT_RE.match(state.src, start)
    if match is None:
        return False
    if not silent:
        token = state.push("citation", "", 0)
        token.meta = {"offset": start, "raw": match.group(0)}
    state.pos = match.end()
    return True


def _crossref_rule(state: StateInline, silent: bool) -> bool:
    """``@fig|tbl|eq|alg|lst|sec|chap:name`` 交叉引用（含 legacy 的 ``(?<!\\[)`` 前视）。"""
    start = state.pos
    if start >= state.posMax or state.src[start] != "@":
        return False
    if start > 0 and state.src[start - 1] == "[":
        return False
    match = _CROSSREF_AT_RE.match(state.src, start)
    if match is None:
        return False
    if not silent:
        token = state.push("crossref", "", 0)
        token.meta = {
            "offset": start,
            "target": f"{match.group('prefix')}:{match.group('name')}",
            "length": match.end() - start,
        }
    state.pos = match.end()
    return True


def _make_container_validate(kind: str):
    """生成与 legacy CONTAINER_START_RE 等价的 container 插件 validate。

    收紧点：markup 必须恰好为 ``:::``（legacy 不接受 ``::::``），
    参数只允许 `` kind`` + 可选 `` {#id}`` + 行尾空白。
    """
    pattern = re.compile(r"^\s+" + kind + r"(?:\s+\{#[^}]+\})?\s*$")

    def validate(params: str, markup: str) -> bool:
        return markup == ":::" and pattern.match(params) is not None

    return validate


def _build_markdown_it() -> MarkdownIt:
    md = MarkdownIt("commonmark")
    md.use(footnote_plugin, inline=False, move_to_end=False)
    for kind in CONTAINER_KINDS:
        md.use(container_plugin, kind, validate=_make_container_validate(kind))
    md.block.ruler.disable(list(_DISABLED_BLOCK_RULES))
    md.inline.ruler.disable(list(_DISABLED_INLINE_RULES))
    md.inline.ruler.at("footnote_ref", _footnote_ref_rule)
    md.inline.ruler.after("footnote_ref", "citation", _citation_rule)
    md.inline.ruler.after("citation", "crossref", _crossref_rule)
    return md


def _check_containers_closed(lines: list[str], start: int) -> None:
    """未闭合容器预检：与 legacy 主循环同构的行扫描，ParseError 消息一致。

    legacy 中脚注定义（含续行）与容器体会吞掉 ``:::`` 行，本预检按同样
    的顺序跳过这两类结构，避免误报。
    """
    i = start
    while i < len(lines):
        stripped = lines[i].strip()
        if FOOTNOTE_DEFINITION_RE.match(lines[i]):
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
        metadata, start = _parse_front_matter(lines)
        doc = ThesisDocument(
            source_path=Path(source_path).resolve(),
            metadata=metadata,
            bibliography=_bibliography_config(metadata),
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
                while idx < total and (
                    tokens[idx].map is None or tokens[idx].map[0] < end
                ):
                    skipped_map = tokens[idx].map
                    if skipped_map is not None and skipped_map[1] > spill:
                        spill = skipped_map[1]
                    idx += 1
                if spill > end:
                    # mdit 把列表项续行并进项内段落（map 跨界），legacy 则截断
                    # 列表并把续行落成新段落；按 legacy 补出该段落。
                    self._emit_raw_paragraph(doc, lines, end, spill, offset)
            elif token_type.startswith("container_") and token_type.endswith("_open"):
                idx = self._emit_container(doc, tokens, idx, lines, offset)
            elif token_type == "footnote_reference_open":
                idx = self._emit_footnote_definition(doc, tokens, idx, lines, offset)
            else:
                idx += 1

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
        inlines = self._extract_inlines(text, line, level + 2)
        doc.blocks.append(
            Heading(
                id=block_id,
                level=level,
                text=text,
                inlines=inlines,
                location=SourceLocation(line=line),
            )
        )
        doc.register_inlines(inlines)

    def _emit_paragraph(self, doc: ThesisDocument, inline_token: Token, offset: int) -> None:
        # mdit 段落 content = 原始行拼接后整体 strip，与 legacy 段落缓冲语义一致
        text = inline_token.content
        if not text:
            return
        assert inline_token.map is not None
        line = inline_token.map[0] + 1 + offset
        inlines = self._extract_inlines(text, line)
        doc.blocks.append(
            Paragraph(text=text, inlines=inlines, location=SourceLocation(line=line))
        )
        doc.register_inlines(inlines)

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
        inlines = self._extract_inlines(text, line)
        doc.blocks.append(
            Paragraph(text=text, inlines=inlines, location=SourceLocation(line=line))
        )
        doc.register_inlines(inlines)

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
        doc.blocks.append(_parse_container(kind, block_id, body, line))
        doc.register_inlines(_parse_container_inlines(kind, body, line + 1))
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
                inlines = self._extract_inlines(text, line)
                doc.blocks.append(
                    Paragraph(text=text, inlines=inlines, location=SourceLocation(line=line))
                )
                doc.register_inlines(inlines)
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
            inlines.extend(self._extract_inlines(segment_text, segment_line, segment_column))
        doc.blocks.append(
            FootnoteDefinition(
                label=label,
                text=text,
                inlines=inlines,
                location=SourceLocation(line=line),
            )
        )
        doc.register_inlines(inlines)
        return close_idx + 1

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
            item_inlines = self._extract_inlines(
                item_text,
                item_line,
                item_match.start("text") + 1,
            )
            items.append(
                ListItem(
                    text=item_text,
                    level=indent // 2,
                    marker=item_marker,
                    ordinal=int(item_marker.rstrip(".)")) if ordered else None,
                    location=SourceLocation(line=item_line),
                    inlines=item_inlines,
                )
            )
            doc.register_inlines(item_inlines)
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

    # ------------------------------------------------------------------
    # 行内转换：三条自研规则给出 match 边界，Text 段按原文切片（与 legacy
    # 的 finditer 间隔扫描逐字节等价；mdit newline 规则会吞掉续行前导
    # 空格，因此不能直接拼接 text/softbreak 子 token 的内容）。
    # ------------------------------------------------------------------

    def _extract_inlines(
        self,
        text: str,
        start_line: int,
        start_column: int = 1,
    ) -> list[Inline]:
        children: list[Token] = []
        self._md.inline.parse(text, self._md, {}, children)
        if any(child.type not in _SUPPORTED_INLINE_TOKENS for child in children):
            # 防御性回退：出现未预期 token 时改用 legacy 行内扫描，
            # 保证语义与位置逐字节一致
            return _parse_inline_content(text, start_line, start_column)

        inlines: list[Inline] = []
        cursor = 0

        def emit_text(end: int) -> None:
            if end > cursor:
                inlines.append(
                    Text(
                        value=text[cursor:end],
                        location=_location_for_offset(text, cursor, start_line, start_column),
                    )
                )

        for child in children:
            if child.type in ("text", "softbreak", "hardbreak"):
                continue  # 原文切片已覆盖，无需逐 token 处理
            offset = child.meta["offset"]
            emit_text(offset)
            location = _location_for_offset(text, offset, start_line, start_column)
            if child.type == "citation":
                raw = child.meta["raw"]
                body = raw[1:-1]
                keys = CITATION_KEY_RE.findall(body)
                locator = CITATION_KEY_RE.sub("", body).strip(" \t;,")
                inlines.append(
                    Citation(
                        keys=keys,
                        locator=locator or None,
                        raw=raw,
                        location=location,
                    )
                )
                cursor = offset + len(raw)
            elif child.type == "crossref":
                inlines.append(CrossReference(target=child.meta["target"], location=location))
                cursor = offset + child.meta["length"]
            else:  # footnote_ref
                inlines.append(FootnoteReference(label=child.meta["label"], location=location))
                cursor = offset + child.meta["length"]
        emit_text(len(text))
        return inlines
