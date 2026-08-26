"""Focused tests that validation reads semantic collections from DocumentIndex."""

from __future__ import annotations

from pathlib import Path

from thesis_forge.core.model import (
    Algorithm,
    Citation,
    CrossReference,
    Figure,
    ForgeDocument,
    SourceLocation,
    Table,
    TableCell,
    TableRow,
    Text,
)
from thesis_forge.core.validator import ValidationContext, validate_document


def _document(*blocks) -> ForgeDocument:
    return ForgeDocument(source_path=Path("thesis.md"), blocks=list(blocks))


def _issues(document: ForgeDocument):
    return validate_document(document, ValidationContext.from_document(document))


def test_caption_citation_without_bibliography_reports_caption_line() -> None:
    document = _document(
        Figure(
            src="model.png",
            caption_inlines=(
                Text(value="模型"),
                Citation(
                    keys=["smith2025"], location=SourceLocation(line=7, column=11)
                ),
            ),
        )
    )
    issue = next(i for i in _issues(document) if i.code == "missing-bibliography")
    assert issue.line == 7


def test_table_cell_cross_reference_reports_cell_line() -> None:
    document = _document(
        Table(
            rows=(
                TableRow(
                    cells=(
                        TableCell(
                            inlines=(
                                CrossReference(
                                    target="fig:missing",
                                    location=SourceLocation(line=12, column=4),
                                ),
                            )
                        ),
                    )
                ),
            )
        )
    )
    issue = next(i for i in _issues(document) if i.code == "missing-reference")
    assert issue.line == 12
    assert issue.target == "fig:missing"


def test_algorithm_body_citation_requires_bibliography() -> None:
    document = _document(
        Algorithm(
            body_lines=(
                (Text(value="1. 初始化参数"),),
                (
                    Text(value="2. 引用 "),
                    Citation(
                        keys=["alg-src"], location=SourceLocation(line=9, column=6)
                    ),
                ),
            )
        )
    )
    issue = next(i for i in _issues(document) if i.code == "missing-bibliography")
    assert issue.line == 9
