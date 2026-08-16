from __future__ import annotations

import re
from pathlib import Path

from .engine import (
    BibliographyDatabase,
    BibliographyParseError,
    BibliographyRecord,
    DuplicateBibliographyKeyError,
    MissingBibliographyFieldError,
    UnsupportedBibliographyTypeError,
)

SUPPORTED_TYPES: set[str] = {
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
}
REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    # article 的 year 允许由 biblatex `date` 派生（报纸条目只有 date）。
    "article": ("author", "title", "journal"),
    "book": ("author", "title", "publisher", "year"),
    "incollection": ("author", "title", "booktitle", "year"),
    "inproceedings": ("author", "title", "booktitle", "year"),
    # 汇编 [G]：著者可为 editor（责任者替代）。
    "collection": ("title", "publisher", "year"),
    "mastersthesis": ("author", "title", "school", "year"),
    "phdthesis": ("author", "title", "school", "year"),
    "techreport": ("author", "title", "institution", "year"),
    # 标准 [S] 通常无个人著者（题名居首）。
    "standard": ("title", "year"),
    "patent": ("author", "title", "number", "year"),
    "online": ("title", "url"),
    "electronic": ("title", "url"),
    "dataset": ("author", "title", "publisher", "year"),
    "map": ("author", "title", "publisher", "year"),
    "unpublished": ("author", "title", "year"),
}
# 著者可缺省（题名居首）的条目类型。
AUTHOR_OPTIONAL_TYPES: set[str] = {"standard", "online", "electronic"}
IDENTIFIER_RE = re.compile(r"[A-Za-z][A-Za-z0-9_:-]*")
WHITESPACE_RE = re.compile(r"\s+")
YEAR_PREFIX_RE = re.compile(r"\d{4}")


def _normalize_value(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value.replace("{", "").replace("}", "")).strip()


def _normalize_pages(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s*--+\s*", "-", value)


class _BibTeXParser:
    def __init__(self, text: str, path: Path):
        self.text = text
        self.path = path
        self.index = 0

    def parse(self) -> list[tuple[str, str, dict[str, str]]]:
        entries: list[tuple[str, str, dict[str, str]]] = []
        self._skip_ignored()
        while self.index < len(self.text):
            entries.append(self._parse_entry())
            self._skip_ignored()
        return entries

    def _parse_entry(self) -> tuple[str, str, dict[str, str]]:
        self._expect("@")
        entry_type = self._identifier("entry type").lower()
        self._skip_ignored()
        opening = self._current()
        if opening not in "{(":
            self._fail("expected '{' or '(' after entry type")
        self.index += 1
        closing = "}" if opening == "{" else ")"
        self._skip_ignored()
        key_start = self.index
        while self.index < len(self.text) and self._current() not in {",", closing}:
            self.index += 1
        if self.index >= len(self.text):
            self._fail("unterminated bibliography entry")
        key = self.text[key_start : self.index].strip()
        if not key:
            self._fail("bibliography entry key is empty")
        if self._current() == closing:
            self.index += 1
            return entry_type, key, {}
        self.index += 1

        fields: dict[str, str] = {}
        while True:
            self._skip_ignored()
            if self.index >= len(self.text):
                self._fail("unterminated bibliography entry")
            if self._current() == closing:
                self.index += 1
                return entry_type, key, fields

            name = self._identifier("field name").lower()
            self._skip_ignored()
            self._expect("=")
            self._skip_ignored()
            fields[name] = _normalize_value(self._value(closing))
            self._skip_ignored()
            if self.index >= len(self.text):
                self._fail("unterminated bibliography entry")
            if self._current() == ",":
                self.index += 1
            elif self._current() != closing:
                self._fail("expected ',' or entry terminator after field value")

    def _value(self, entry_closing: str) -> str:
        current = self._current()
        if current == "{":
            return self._braced_value()
        if current == '"':
            return self._quoted_value()

        start = self.index
        while self.index < len(self.text) and self._current() not in {",", entry_closing}:
            self.index += 1
        value = self.text[start : self.index].strip()
        if not value:
            self._fail("bibliography field value is empty")
        return value

    def _braced_value(self) -> str:
        self.index += 1
        start = self.index
        depth = 1
        while self.index < len(self.text):
            current = self._current()
            if current == "\\":
                self.index += min(2, len(self.text) - self.index)
                continue
            if current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
                if depth == 0:
                    value = self.text[start : self.index]
                    self.index += 1
                    return value
            self.index += 1
        self._fail("unterminated braced bibliography value")

    def _quoted_value(self) -> str:
        self.index += 1
        start = self.index
        while self.index < len(self.text):
            current = self._current()
            if current == "\\":
                self.index += min(2, len(self.text) - self.index)
                continue
            if current == '"':
                value = self.text[start : self.index]
                self.index += 1
                return value
            self.index += 1
        self._fail("unterminated quoted bibliography value")

    def _identifier(self, label: str) -> str:
        self._skip_ignored()
        match = IDENTIFIER_RE.match(self.text, self.index)
        if match is None:
            self._fail(f"expected {label}")
        self.index = match.end()
        return match.group(0)

    def _skip_ignored(self) -> None:
        while self.index < len(self.text):
            if self._current().isspace():
                self.index += 1
                continue
            if self._current() == "%":
                newline = self.text.find("\n", self.index)
                self.index = len(self.text) if newline == -1 else newline + 1
                continue
            break

    def _expect(self, value: str) -> None:
        if not self.text.startswith(value, self.index):
            self._fail(f"expected {value!r}")
        self.index += len(value)

    def _current(self) -> str:
        return self.text[self.index]

    def _fail(self, detail: str):
        line = self.text.count("\n", 0, self.index) + 1
        raise BibliographyParseError(self.path, line, detail)


def _split_names(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(
        name.strip()
        for name in re.split(r"\s+and\s+", value, flags=re.IGNORECASE)
        if name.strip()
    )


def _year_from_date(date: str | None) -> str | None:
    if date is None:
        return None
    match = YEAR_PREFIX_RE.match(date.strip())
    return match.group(0) if match else None


def _record(
    entry_type: str,
    key: str,
    fields: dict[str, str],
) -> BibliographyRecord:
    if entry_type not in SUPPORTED_TYPES:
        raise UnsupportedBibliographyTypeError(entry_type, key)
    for name in REQUIRED_FIELDS[entry_type]:
        if not fields.get(name):
            raise MissingBibliographyFieldError(key, entry_type, name)

    year = fields.get("year") or _year_from_date(fields.get("date"))
    if entry_type == "article" and not year:
        raise MissingBibliographyFieldError(key, entry_type, "year")
    entrysubtype = fields.get("entrysubtype")
    if entrysubtype == "newspaper" and not fields.get("date"):
        raise MissingBibliographyFieldError(key, entry_type, "date")

    authors = _split_names(fields.get("author"))
    editors = _split_names(fields.get("editor"))
    if (
        not authors
        and entry_type not in AUTHOR_OPTIONAL_TYPES
        and not (entry_type == "collection" and editors)
    ):
        raise MissingBibliographyFieldError(key, entry_type, "author")

    return BibliographyRecord(
        key=key,
        entry_type=entry_type,  # type: ignore[arg-type]
        authors=authors,
        title=fields["title"],
        year=year,
        journal=fields.get("journal"),
        booktitle=fields.get("booktitle"),
        publisher=fields.get("publisher"),
        address=fields.get("address"),
        volume=fields.get("volume"),
        number=fields.get("number"),
        pages=_normalize_pages(fields.get("pages")),
        school=fields.get("school") or fields.get("institution"),
        doi=fields.get("doi"),
        date=fields.get("date"),
        urldate=fields.get("urldate"),
        url=fields.get("url"),
        edition=fields.get("edition"),
        translators=_split_names(fields.get("translator")),
        editors=editors,
        entrysubtype=entrysubtype,
        language=fields.get("langid") or fields.get("language"),
        note=fields.get("note"),
    )


class LocalBibTeXLoader:
    """Load the documented ThesisForge V1 BibTeX subset from local disk."""

    def load(self, path: str | Path) -> BibliographyDatabase:
        source_path = Path(path).expanduser().resolve()
        try:
            text = source_path.read_text(encoding="utf-8")
        except UnicodeError as error:
            raise BibliographyParseError(source_path, 1, "bibliography is not UTF-8") from error

        records: dict[str, BibliographyRecord] = {}
        for entry_type, key, fields in _BibTeXParser(text, source_path).parse():
            if key in records:
                raise DuplicateBibliographyKeyError(key)
            records[key] = _record(entry_type, key, fields)
        return BibliographyDatabase(records=records, source_path=source_path)
