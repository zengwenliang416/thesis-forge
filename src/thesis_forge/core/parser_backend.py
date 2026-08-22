"""Parser 后端协议与后端注册表。

隔离 Markdown 解析后端，使 model/validator/compiler/renderer 不随选型震荡。
参见 ``docs/update/adr/ADR-0001.md`` 与 ``docs/update/IR_MODEL_DESIGN.md`` §6.1。

当前契约以现有 ``core.model.ThesisDocument`` 为起点（含 SourceLocation
line/column）；Normalized IR 与 SourceSpan 的迁移不在本模块范围内。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable

from .model import ThesisDocument
from .parser import ParseError, parse_markdown, parse_markdown_text
from .parser_markdown_it import MarkdownItParserBackend

__all__ = [
    "PARSER_BACKENDS",
    "LegacyParserBackend",
    "MarkdownItParserBackend",
    "ParseError",
    "ParserBackend",
    "create_parser_backend",
    "get_parser_backend",
    "parser_backend_names",
]


@runtime_checkable
class ParserBackend(Protocol):
    """Markdown → ThesisDocument 的解析后端协议（ADR-0001）。

    实现必须产出与 ``core.model`` 一致的 ``ThesisDocument``；
    解析错误沿用 ``core.parser.ParseError``（带行号语义由后端无关预检承担）。
    """

    @property
    def name(self) -> str:
        """后端标识（如 ``legacy``、``markdown-it``）。"""
        ...

    def parse_file(self, path: str | Path) -> ThesisDocument:
        """解析磁盘上的 Markdown 文件。"""
        ...

    def parse_text(self, text: str, *, source_path: str | Path) -> ThesisDocument:
        """解析内存中的 Markdown 文本；``source_path`` 仅用于定位与诊断。"""
        ...


def create_parser_backend() -> ParserBackend:
    """创建唯一的生产 v2 parser，不接受后端选择参数。"""
    return MarkdownItParserBackend()


class LegacyParserBackend:
    """包装冻结维护的手写 parser（``core/parser.py``）。

    只做委托，不改 parser.py 内部逻辑（ADR-0001：冻结维护，只修 bug）。
    """

    name = "legacy"

    def parse_file(self, path: str | Path) -> ThesisDocument:
        return parse_markdown(path)

    def parse_text(self, text: str, *, source_path: str | Path) -> ThesisDocument:
        return parse_markdown_text(text, source_path=source_path)


PARSER_BACKENDS: dict[str, Callable[[], ParserBackend]] = {
    LegacyParserBackend.name: LegacyParserBackend,
    MarkdownItParserBackend.name: MarkdownItParserBackend,
}


def parser_backend_names() -> tuple[str, ...]:
    """已注册后端名，按注册顺序返回。"""
    return tuple(PARSER_BACKENDS)


def get_parser_backend(name: str) -> ParserBackend:
    """按名实例化后端；未知名抛 ``ValueError``。"""
    try:
        factory = PARSER_BACKENDS[name]
    except KeyError:
        available = ", ".join(parser_backend_names())
        raise ValueError(f"未知 parser 后端: {name!r}（可用: {available}）") from None
    return factory()
