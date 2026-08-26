"""Canonical Markdown parser backend protocol and factory.

The application uses one production parser implementation. Keeping its
protocol and factory here gives callers a stable seam without a backend
registry or selector.

当前契约以现有 ``core.model.ForgeDocument`` 为起点（含 SourceLocation
line/column）；Normalized IR 与 SourceSpan 的迁移不在本模块范围内。
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from .model import ForgeDocument
from .parser_markdown_it import MarkdownItParserBackend
from .parser_support import ParseError

__all__ = [
    "MarkdownItParserBackend",
    "ParseError",
    "ParserBackend",
    "create_parser_backend",
]


@runtime_checkable
class ParserBackend(Protocol):
    """Markdown → ForgeDocument 的解析后端协议（ADR-0001）。

    实现必须产出与 ``core.model`` 一致的 ``ForgeDocument``；
    解析错误沿用 ``core.parser_support.ParseError``（带行号语义由后端无关预检承担）。
    """

    @property
    def name(self) -> str:
        """Canonical parser implementation name."""
        ...

    def parse_file(self, path: str | Path) -> ForgeDocument:
        """解析磁盘上的 Markdown 文件。"""
        ...

    def parse_text(self, text: str, *, source_path: str | Path) -> ForgeDocument:
        """解析内存中的 Markdown 文本；``source_path`` 仅用于定位与诊断。"""
        ...


def create_parser_backend() -> ParserBackend:
    """创建唯一的生产 v2 parser，不接受后端选择参数。"""
    return MarkdownItParserBackend()
