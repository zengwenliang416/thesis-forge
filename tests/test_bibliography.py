from __future__ import annotations

import json
from pathlib import Path

import pytest

from thesis_forge.bibliography import (
    BibliographyParseError,
    DuplicateBibliographyKeyError,
    Gbt7714Formatter,
    LocalBibTeXLoader,
    MissingBibliographyFieldError,
    UnsupportedBibliographyTypeError,
)

FIXTURES = Path(__file__).parent / "fixtures" / "bibliography"


def test_local_bibtex_loader_normalizes_supported_v1_records():
    database = LocalBibTeXLoader().load(FIXTURES / "gbt7714-v1.bib")

    assert tuple(database.records) == (
        "smith2025",
        "doe2024",
        "lee2023",
        "chen2022",
        "liu2021",
        "uncited2020",
    )
    article = database.records["smith2025"]
    assert article.entry_type == "article"
    assert article.authors == ("Smith, John", "Wang, Li")
    assert article.title == "Deterministic Thesis Compilation"
    assert article.pages == "101-118"
    assert article.doi == "10.1000/tf.2025.001"
    assert database.records["chen2022"].school == "Tsinghua University"


def test_gbt7714_v1_formatter_matches_reviewed_golden_fixture():
    expected = json.loads(
        (FIXTURES / "gbt7714-v1.json").read_text(encoding="utf-8")
    )
    database = LocalBibTeXLoader().load(FIXTURES / "gbt7714-v1.bib")
    formatter = Gbt7714Formatter()
    citation = expected["citation"]
    citation_records = tuple(database.records[key] for key in citation["keys"])
    bibliography_keys = ("doe2024", "smith2025", "lee2023", "chen2022", "liu2021")
    bibliography_records = tuple(database.records[key] for key in bibliography_keys)

    assert formatter.format_citation(
        citation_records,
        tuple(citation["ordinals"]),
        locator=citation["locator"],
    ) == citation["text"]
    assert formatter.format_bibliography(
        bibliography_records,
        tuple(range(1, len(bibliography_records) + 1)),
    ) == tuple(expected["bibliography"])
    assert all("This Record Must Not Render" not in item for item in expected["bibliography"])


@pytest.mark.parametrize(
    ("content", "error_type", "message"),
    [
        (
            "@article{broken, author={Smith, John}, title={Missing close}",
            BibliographyParseError,
            "unterminated",
        ),
        (
            (
                "@book{duplicate, author={Doe, Jane}, title={One}, "
                "publisher={P}, year={2024}}\n"
                "@book{duplicate, author={Doe, Jane}, title={Two}, "
                "publisher={P}, year={2025}}"
            ),
            DuplicateBibliographyKeyError,
            "duplicate",
        ),
        (
            "@misc{unsupported, author={Doe, Jane}, title={Unknown}, year={2024}}",
            UnsupportedBibliographyTypeError,
            "misc",
        ),
        (
            "@article{missing, author={Doe, Jane}, title={No Journal}, year={2024}}",
            MissingBibliographyFieldError,
            "journal",
        ),
    ],
)
def test_local_bibtex_loader_rejects_invalid_input(
    tmp_path: Path,
    content: str,
    error_type: type[ValueError],
    message: str,
):
    path = tmp_path / "invalid.bib"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(error_type, match=message):
        LocalBibTeXLoader().load(path)
