from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .engine import (
    BibliographyRecord,
    UnsupportedBibliographyTypeError,
)

# "等/et al" 截断参数，对齐官方 GB/T 7714-2025 CSL（ADR-0004 §2.2）。
ET_AL_MIN = 4
ET_AL_USE_FIRST = 3

_CJK_RE = re.compile(r"[㐀-䶿一-鿿\uf900-\ufaff]")
_WESTERN_LANGUAGE_RE = re.compile(r"en|english|american|british", re.IGNORECASE)
_CHINESE_LANGUAGE_RE = re.compile(r"zh|chinese", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class _Punctuation:
    """条目级标点体系：中文条目全角，西文条目半角（任务书 / ADR-0004 §2.2）。"""

    comma: str
    colon: str
    lparen: str
    rparen: str
    et_al: str


_ZH_PUNCT = _Punctuation(comma="，", colon="：", lparen="（", rparen="）", et_al="等")
_EN_PUNCT = _Punctuation(comma=", ", colon=": ", lparen="(", rparen=")", et_al="et al")


def _is_chinese(record: BibliographyRecord) -> bool:
    """条目语言判定：language/langid 字段优先，否则按题名/著者字符启发式。

    可判定规则（写入 BIBLIOGRAPHY_SPEC）：
    - `langid`/`language` 命中 zh|chinese → 中文；命中 en|english|american|
      british → 西文；
    - 字段缺省或无法识别时，题名、著者、编者、译者任一含 CJK 字符 → 中文，
      否则 → 西文。
    """

    language = (record.language or "").strip()
    if language:
        if _CHINESE_LANGUAGE_RE.search(language):
            return True
        if _WESTERN_LANGUAGE_RE.search(language):
            return False
    texts = (record.title, *record.authors, *record.editors, *record.translators)
    return any(_CJK_RE.search(text) for text in texts)


def _name_text(name: str) -> str:
    if "," in name:
        family, given = (part.strip() for part in name.split(",", 1))
    else:
        parts = name.split()
        family = parts[-1]
        given = " ".join(parts[:-1])
    initials = "".join(part[0].upper() for part in given.replace("-", " ").split() if part)
    return f"{family.upper()} {initials}".rstrip()


def _names_text(names: Sequence[str], punct: _Punctuation) -> str:
    """著者/编者/译者列表：≥4 名时截断为前 3 名 + "等"/"et al"。"""

    rendered = [_name_text(name) for name in names]
    if len(rendered) >= ET_AL_MIN:
        rendered = [*rendered[:ET_AL_USE_FIRST], punct.et_al]
    return punct.comma.join(rendered)


def _location_publisher(
    address: str | None,
    publisher: str | None,
    punct: _Punctuation,
) -> str:
    if address and publisher:
        return f"{address}{punct.colon}{publisher}"
    return address or publisher or ""


def _english_ordinal(value: str) -> str | None:
    if not value.isdigit():
        return None
    number = int(value)
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _edition_text(edition: str, chinese: bool) -> str:
    # 返回值不带句点；结尾句点由调用方统一追加（避免 "2nd ed.." 双点）。
    if chinese:
        return f"{edition} 版" if edition.isdigit() else edition
    ordinal = _english_ordinal(edition)
    return f"{ordinal} ed" if ordinal else edition


class Gbt7714Formatter:
    """Deterministic GB/T 7714-2025 formatter covering the golden corpus types.

    覆盖 ADR-0004 §2.2 扩展范围：[J]/[N]/[M]/[M]//[C]//[G]/[D]/[R]/[S]/[P]/
    [EB/OL]/[DS]/[CM]/[A]；著者 ≥4 截断为前 3 + "等/et al"；标点按条目语言
    切换全角/半角；版本项与译者著录。含 DOI/URL 的印刷型条目不自动附加
    /OL 载体标识（与 pending-human-review 条目对应的开放问题，见 ADR §5.2）。
    """

    def format_citation(
        self,
        records: Sequence[BibliographyRecord],
        ordinals: Sequence[int],
        *,
        locator: str | None = None,
    ) -> str:
        if len(records) != len(ordinals):
            raise ValueError("citation records and ordinals must have equal length")
        content = ",".join(str(ordinal) for ordinal in ordinals)
        if locator:
            content = f"{content}, {locator.strip()}"
        return f"[{content}]"

    def format_bibliography(
        self,
        records: Sequence[BibliographyRecord],
        ordinals: Sequence[int],
    ) -> tuple[str, ...]:
        if len(records) != len(ordinals):
            raise ValueError("bibliography records and ordinals must have equal length")
        return tuple(
            self._format_record(record, ordinal)
            for record, ordinal in zip(records, ordinals, strict=True)
        )

    def _format_record(self, record: BibliographyRecord, ordinal: int) -> str:
        chinese = _is_chinese(record)
        punct = _ZH_PUNCT if chinese else _EN_PUNCT
        contributors = record.authors or record.editors
        head = f"{_names_text(contributors, punct)}. " if contributors else ""
        title = record.title
        if record.entry_type in {"techreport", "standard", "patent"} and record.number:
            title = f"{title}{punct.colon}{record.number}"
        prefix = f"[{ordinal}] {head}{title}"

        if record.entry_type == "article":
            if record.entrysubtype == "newspaper":
                return self._format_newspaper(record, prefix, punct)
            return self._format_article(record, prefix, punct)
        if record.entry_type == "book":
            return self._format_book(record, prefix, punct, chinese)
        if record.entry_type == "incollection":
            return self._format_incollection(record, prefix, punct)
        if record.entry_type == "inproceedings":
            return self._format_inproceedings(record, prefix, punct)
        if record.entry_type == "collection":
            publication = _location_publisher(record.address, record.publisher, punct)
            return f"{prefix}[G]. {publication}{punct.comma}{record.year}."
        if record.entry_type in {"mastersthesis", "phdthesis"}:
            publication = _location_publisher(record.address, record.school, punct)
            return f"{prefix}[D]. {publication}{punct.comma}{record.year}."
        if record.entry_type == "techreport":
            publication = _location_publisher(record.address, record.school, punct)
            return f"{prefix}[R]. {publication}{punct.comma}{record.year}."
        if record.entry_type == "standard":
            publication = _location_publisher(record.address, record.publisher, punct)
            return f"{prefix}[S]. {publication}{punct.comma}{record.year}."
        if record.entry_type == "patent":
            result = f"{prefix}[P]."
            publication = _location_publisher(record.address, record.publisher, punct)
            if publication:
                return f"{result} {publication}{punct.comma}{record.year}."
            return f"{result} {record.year}."
        if record.entry_type in {"online", "electronic"}:
            return self._format_online(record, prefix, punct)
        if record.entry_type == "dataset":
            result = f"{prefix}[DS]."
            publication = _location_publisher(record.address, record.publisher, punct)
            result += f" {publication}{punct.comma}{record.year}."
            if record.urldate:
                result += f" [{record.urldate}]."
            if record.url:
                result += f" {record.url}."
            return result
        if record.entry_type == "map":
            publication = _location_publisher(record.address, record.publisher, punct)
            return f"{prefix}[CM]. {publication}{punct.comma}{record.year}."
        if record.entry_type == "unpublished":
            return f"{prefix}[A]. {record.year}."
        raise UnsupportedBibliographyTypeError(record.entry_type, record.key)

    def _format_article(
        self,
        record: BibliographyRecord,
        prefix: str,
        punct: _Punctuation,
    ) -> str:
        publication = f"{record.journal}{punct.comma}{record.year}"
        if record.volume:
            publication += f"{punct.comma}{record.volume}"
        if record.number:
            publication += f"{punct.lparen}{record.number}{punct.rparen}"
        if record.pages:
            publication += f"{punct.colon}{record.pages}"
        result = f"{prefix}[J]. {publication}."
        if record.doi:
            result += f" DOI:{record.doi}."
        return result

    def _format_newspaper(
        self,
        record: BibliographyRecord,
        prefix: str,
        punct: _Punctuation,
    ) -> str:
        result = f"{prefix}[N]. {record.journal}{punct.comma}{record.date}"
        if record.pages:
            result += f"{punct.lparen}{record.pages}{punct.rparen}"
        return f"{result}."

    def _format_book(
        self,
        record: BibliographyRecord,
        prefix: str,
        punct: _Punctuation,
        chinese: bool,
    ) -> str:
        result = f"{prefix}[M]."
        if record.edition:
            result += f" {_edition_text(record.edition, chinese)}."
        if record.translators:
            label = "译" if chinese else "trans"
            result += f" {_names_text(record.translators, punct)}{punct.comma}{label}."
        publication = _location_publisher(record.address, record.publisher, punct)
        return f"{result} {publication}{punct.comma}{record.year}."

    def _format_incollection(
        self,
        record: BibliographyRecord,
        prefix: str,
        punct: _Punctuation,
    ) -> str:
        result = f"{prefix}[M]//"
        if record.editors:
            result += f"{_names_text(record.editors, punct)}. "
        result += f"{record.booktitle}."
        publication = _location_publisher(record.address, record.publisher, punct)
        if publication:
            result += f" {publication}{punct.comma}{record.year}"
        else:
            result += f" {record.year}"
        if record.pages:
            result += f"{punct.colon}{record.pages}"
        return f"{result}."

    def _format_inproceedings(
        self,
        record: BibliographyRecord,
        prefix: str,
        punct: _Punctuation,
    ) -> str:
        result = f"{prefix}[C]//{record.booktitle}."
        publication = _location_publisher(record.address, record.publisher, punct)
        if publication:
            result += f" {publication}{punct.comma}{record.year}"
        else:
            result += f" {record.year}"
        if record.pages:
            result += f"{punct.colon}{record.pages}"
        return f"{result}."

    def _format_online(
        self,
        record: BibliographyRecord,
        prefix: str,
        punct: _Punctuation,
    ) -> str:
        result = f"{prefix}[EB/OL]."
        if record.date or record.urldate:
            dates = ""
            if record.date:
                dates += f"{punct.lparen}{record.date}{punct.rparen}"
            if record.urldate:
                dates += f"[{record.urldate}]"
            result += f" {dates}."
        return f"{result} {record.url}."
