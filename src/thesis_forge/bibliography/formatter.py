from __future__ import annotations

from collections.abc import Sequence

from .engine import BibliographyRecord


def _name_text(name: str) -> str:
    if "," in name:
        family, given = (part.strip() for part in name.split(",", 1))
    else:
        parts = name.split()
        family = parts[-1]
        given = " ".join(parts[:-1])
    initials = "".join(part[0].upper() for part in given.replace("-", " ").split() if part)
    return f"{family.upper()} {initials}".rstrip()


def _authors_text(record: BibliographyRecord) -> str:
    return ", ".join(_name_text(author) for author in record.authors)


def _location_publisher(address: str | None, publisher: str | None) -> str:
    if address and publisher:
        return f"{address}: {publisher}"
    return address or publisher or ""


class Gbt7714Formatter:
    """Deterministic GB/T 7714-2025 V1 formatter for documented record types."""

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
        prefix = f"[{ordinal}] {_authors_text(record)}. {record.title}"
        if record.entry_type == "article":
            publication = f"{record.journal}, {record.year}"
            if record.volume:
                publication += f", {record.volume}"
                if record.number:
                    publication += f"({record.number})"
            elif record.number:
                publication += f", ({record.number})"
            if record.pages:
                publication += f": {record.pages}"
            result = f"{prefix}[J]. {publication}."
            if record.doi:
                result += f" DOI:{record.doi}."
            return result

        if record.entry_type == "book":
            publication = _location_publisher(record.address, record.publisher)
            return f"{prefix}[M]. {publication}, {record.year}."

        if record.entry_type == "inproceedings":
            result = f"{prefix}[C]//{record.booktitle}."
            publication = _location_publisher(record.address, record.publisher)
            if publication:
                result += f" {publication}, {record.year}"
            else:
                result += f" {record.year}"
            if record.pages:
                result += f": {record.pages}"
            return f"{result}."

        publication = _location_publisher(record.address, record.school)
        return f"{prefix}[D]. {publication}, {record.year}."
