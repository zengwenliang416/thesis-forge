from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from docforge.application.contracts import (
    BuildDiagnostic,
    BuildDiagnosticCategory,
    BuildDiagnosticSeverity,
    BuildReportStage,
    BuildSourceRange,
)
from docforge.core.index import DocumentIndex
from docforge.core.model import (
    BlockQuote,
    ForgeDocument,
    Heading,
    SourceLocation,
    Text,
    ValidationIssue,
)
from docforge.presentation.diagnostics import (
    duplicate_id_diagnostics,
    format_diagnostic,
    localized_build_diagnostic_message,
    localized_issue_message,
)


def _document(*blocks: object) -> ForgeDocument:
    return ForgeDocument(source_path=Path("thesis.md"), blocks=list(blocks))


def test_legacy_validation_issue_messages_use_the_formatter_registry() -> None:
    issue = ValidationIssue(
        code="missing-reference",
        severity="error",
        message="Reference target does not exist",
        target="fig:missing",
    )

    assert localized_issue_message(issue) == "引用目标不存在：fig:missing"
    assert format_diagnostic(issue) == "引用目标不存在：fig:missing"


def test_legacy_duplicate_formatter_does_not_read_canonical_details() -> None:
    issue = ValidationIssue(
        code="duplicate-id",
        severity="error",
        message="Duplicate ID",
        target=None,
        details={"object_id": "sec:legacy"},
    )

    assert localized_issue_message(issue) == "重复 ID："


def test_canonical_build_diagnostic_uses_the_same_registry() -> None:
    diagnostic = BuildDiagnostic(
        id="diag-1",
        severity=BuildDiagnosticSeverity.ERROR,
        category=BuildDiagnosticCategory.SEMANTIC,
        code="TF-SEMANTIC-DUPLICATE-ID",
        stage=BuildReportStage.VALIDATE,
        message="duplicate id",
        target="sec:intro",
    )

    assert localized_build_diagnostic_message(diagnostic) == "重复 ID：sec:intro"
    assert format_diagnostic(diagnostic) == "重复 ID：sec:intro"


def test_unknown_diagnostic_code_preserves_the_canonical_message() -> None:
    diagnostic = BuildDiagnostic(
        id="diag-unknown",
        severity=BuildDiagnosticSeverity.ERROR,
        category=BuildDiagnosticCategory.INTERNAL,
        code="TF-INTERNAL-UNKNOWN",
        stage=BuildReportStage.VALIDATE,
        message="保持原始消息",
    )

    assert localized_build_diagnostic_message(diagnostic) == "保持原始消息"


def test_duplicate_diagnostics_include_nested_locations() -> None:
    first = Heading(
        id="sec:duplicate",
        level=1,
        inlines=[Text(value="第一处")],
        location=SourceLocation(line=3, column=1, end_line=3, end_column=5),
    )
    nested_duplicate = Heading(
        id="sec:duplicate",
        level=2,
        inlines=[Text(value="第二处")],
        location=SourceLocation(line=9, column=2, end_line=9, end_column=6),
    )
    index = DocumentIndex.from_document(
        _document(first, BlockQuote(children=(nested_duplicate,)))
    )

    diagnostics = duplicate_id_diagnostics(index, source_file="thesis.md")

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.id == "duplicate-id:sec:duplicate:1"
    assert diagnostic.code == "TF-SEMANTIC-DUPLICATE-ID"
    assert diagnostic.source == BuildSourceRange(
        file="thesis.md",
        start_line=9,
        start_column=2,
        end_line=9,
        end_column=6,
    )
    assert diagnostic.related_locations[0].source == BuildSourceRange(
        file="thesis.md",
        start_line=3,
        start_column=1,
        end_line=3,
        end_column=5,
    )


def test_locationless_duplicate_diagnostics_still_have_unique_ids() -> None:
    index = DocumentIndex.from_document(
        _document(
            Heading(id="sec:duplicate"),
            Heading(id="sec:duplicate"),
            Heading(id="sec:duplicate"),
        )
    )

    diagnostics = duplicate_id_diagnostics(index, source_file="thesis.md")

    assert len(diagnostics) == 2
    assert len({diagnostic.id for diagnostic in diagnostics}) == 2
    assert [diagnostic.id for diagnostic in diagnostics] == [
        "duplicate-id:sec:duplicate:1",
        "duplicate-id:sec:duplicate:2",
    ]
    assert all(
        diagnostic.source == BuildSourceRange(file="thesis.md")
        for diagnostic in diagnostics
    )
    assert all(
        diagnostic.related_locations[0].source == BuildSourceRange(file="thesis.md")
        for diagnostic in diagnostics
    )


def test_headless_ui_import_does_not_eagerly_load_application_or_rendering() -> None:
    script = """
import json
import sys

import docforge.ui

forbidden = {
    "docx",
    "lxml",
    "docforge.application.services",
    "docforge.core.compiler",
    "docforge.core.parser",
    "docforge.renderers.docx",
}
print(json.dumps(sorted(name for name in forbidden if name in sys.modules)))
raise SystemExit(bool(any(name in sys.modules for name in forbidden)))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout or result.stderr
