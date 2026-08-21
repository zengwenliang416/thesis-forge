from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from thesis_forge.application import (
    BuildResult,
    BuildValidationError,
    ValidationResult,
)
from thesis_forge.application.contracts import BuildStage
from thesis_forge.cli import app
from thesis_forge.core.model import ThesisDocument, ValidationIssue
from thesis_forge.core.validator import ValidationContext

PROJECT = Path(__file__).resolve().parents[1] / "fixtures" / "v2-project"


class ReportService:
    def __init__(self, *, failure: bool = False) -> None:
        self.failure = failure

    def build(self, request):
        if self.failure:
            raise BuildValidationError(
                (
                    ValidationIssue(
                        code="missing-image",
                        severity="error",
                        message="missing image",
                        line=12,
                        target="fig:model",
                    ),
                )
            )
        assert request.output is not None
        return BuildResult(output_path=request.output.path, issues=())

    def validate(self, request):
        return ValidationResult(
            document=ThesisDocument(source_path=PROJECT / "thesis.md"),
            context=ValidationContext(),
            issues=(),
        )


def test_validate_json_is_deterministic(monkeypatch) -> None:
    monkeypatch.setattr(
        "thesis_forge.cli.ProjectApplicationService",
        lambda: ReportService(),
    )
    runner = CliRunner()

    first = runner.invoke(app, ["validate", str(PROJECT), "--json"])
    second = runner.invoke(app, ["validate", str(PROJECT), "--json"])

    assert first.exit_code == 0, first.stdout
    assert first.stdout == second.stdout
    assert json.loads(first.stdout) == {"issues": []}


def test_build_success_writes_deterministic_typed_report(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "thesis_forge.cli.ProjectApplicationService",
        lambda: ReportService(),
    )
    runner = CliRunner()
    report_path = tmp_path / "build-report.json"

    result = runner.invoke(
        app,
        [
            "build",
            str(PROJECT),
            "--report-json",
            str(report_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["report"]["schemaVersion"] == "thesisforge.build-report.v2"
    assert payload["report"]["outcome"] == "succeeded"
    assert payload["report"]["output"]["docxPath"] == "<path>"
    assert json.loads(result.stdout) == payload


def test_build_failure_writes_complete_typed_report(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "thesis_forge.cli.ProjectApplicationService",
        lambda: ReportService(failure=True),
    )
    runner = CliRunner()
    report_path = tmp_path / "failed-report.json"

    result = runner.invoke(
        app,
        [
            "build",
            str(PROJECT),
            "--report-json",
            str(report_path),
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["report"]["schemaVersion"] == "thesisforge.build-report.v2"
    assert payload["report"]["outcome"] == "failed"
    assert payload["report"]["failedStage"] == BuildStage.VALIDATE.value
    assert payload["report"]["diagnostics"][0]["code"] == "missing-image"
    assert json.loads(result.stdout) == payload
