from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, TypeAlias

SupportedEntryType: TypeAlias = Literal[
    "article",
    "book",
    "incollection",
    "inproceedings",
    "collection",
    "mastersthesis",
    "phdthesis",
    "techreport",
    "standard",
    "patent",
    "online",
    "electronic",
    "dataset",
    "map",
    "unpublished",
]


class BibliographyError(ValueError):
    """Base class for deterministic local bibliography failures."""


class BibliographyParseError(BibliographyError):
    def __init__(self, path: Path, line: int, detail: str):
        self.path = path
        self.line = line
        self.detail = detail
        super().__init__(f"{path}:{line}: {detail}")


class DuplicateBibliographyKeyError(BibliographyError):
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"duplicate bibliography key: {key}")


class UnsupportedBibliographyTypeError(BibliographyError):
    def __init__(self, entry_type: str, key: str):
        self.entry_type = entry_type
        self.key = key
        super().__init__(f"unsupported bibliography type {entry_type}: {key}")


class MissingBibliographyFieldError(BibliographyError):
    def __init__(self, key: str, entry_type: str, field: str):
        self.key = key
        self.entry_type = entry_type
        self.field = field
        super().__init__(
            f"missing required bibliography field {field}: {entry_type}:{key}"
        )


class UnsupportedCitationStyleError(BibliographyError):
    """Raised when a citation style selects no registered provider (D-07)."""

    def __init__(self, style: str, supported_styles: Sequence[str]):
        self.style = style
        self.supported_styles = tuple(supported_styles)
        super().__init__(
            f"unsupported citation style {style!r}: "
            f"supported styles: {', '.join(self.supported_styles)}"
        )


@dataclass(frozen=True, slots=True)
class BibliographyRecord:
    key: str
    entry_type: SupportedEntryType
    authors: tuple[str, ...]
    title: str
    year: str | None = None
    journal: str | None = None
    booktitle: str | None = None
    publisher: str | None = None
    address: str | None = None
    volume: str | None = None
    number: str | None = None
    pages: str | None = None
    school: str | None = None
    doi: str | None = None
    # GB/T 7714-2025 corpus 扩展字段（ADR-0004 §2.2）
    date: str | None = None
    urldate: str | None = None
    url: str | None = None
    edition: str | None = None
    translators: tuple[str, ...] = ()
    editors: tuple[str, ...] = ()
    entrysubtype: str | None = None
    language: str | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class BibliographyDatabase:
    records: dict[str, BibliographyRecord]
    source_path: Path | None = None

    def require(self, key: str) -> BibliographyRecord:
        try:
            return self.records[key]
        except KeyError as error:
            raise KeyError(f"unknown bibliography key: {key}") from error


class BibliographyLoader(Protocol):
    def load(self, path: str | Path) -> BibliographyDatabase: ...


class CitationFormatter(Protocol):
    def format_citation(
        self,
        records: Sequence[BibliographyRecord],
        ordinals: Sequence[int],
        *,
        locator: str | None = None,
    ) -> str: ...

    def format_bibliography(
        self,
        records: Sequence[BibliographyRecord],
        ordinals: Sequence[int],
    ) -> tuple[str, ...]: ...
