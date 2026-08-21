from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from thesis_forge.application import (
    BuildResult,
    BuildStage,
    BuildValidationError,
    InspectionResult,
    ValidationResult,
)
from thesis_forge.application.contracts import ProjectRequestIntent
from thesis_forge.cli import app
from thesis_forge.core.model import Heading, ThesisDocument, ValidationIssue
from thesis_forge.core.validator import ValidationContext

PROJECT = Path(__file__).resolve().parents[1] / "fixtures" / "v2-project"


class RecordingProjectService:
    def __init__(self) -> None:
        self.requests = []

    def inspect(self, request):
        self.requests.append(request)
        return InspectionResult(
            ThesisDocument(
                source_path=PROJECT / "thesis.md",
                blocks=[Heading(level=1, text="项目论文")],
            )
        )

    def validate(self, request):
        self.requests.append(request)
        return ValidationResult(
            document=ThesisDocument(source_path=PROJECT / "thesis.md"),
            context=ValidationContext(),
            issues=(),
        )

    def build(self, request):
        self.requests.append(request)
        assert request.output is not None
        return BuildResult(output_path=request.output.path, issues=())


def test_project_commands_construct_typed_requests(monkeypatch, tmp_path: Path) -> None:
    service = RecordingProjectService()
    monkeypatch.setattr(
        "thesis_forge.cli.ProjectApplicationService",
        lambda: service,
    )
    runner = CliRunner()

    inspect_result = runner.invoke(app, ["inspect", str(PROJECT)])
    validate_result = runner.invoke(app, ["validate", str(PROJECT), "--json"])
    output = tmp_path / "project.docx"
    build_result = runner.invoke(
        app,
        ["build", str(PROJECT), "-o", str(output)],
    )

    assert inspect_result.exit_code == 0, inspect_result.stdout
    assert validate_result.exit_code == 0, validate_result.stdout
    assert build_result.exit_code == 0, build_result.stdout
    assert json.loads(validate_result.stdout) == {"issues": []}
    assert [request.intent for request in service.requests] == [
        ProjectRequestIntent.INSPECT,
        ProjectRequestIntent.VALIDATE,
        ProjectRequestIntent.BUILD,
    ]
    assert all(request.project.project_id == "goal-fixture" for request in service.requests)
    assert service.requests[-1].output is not None
    assert service.requests[-1].output.path == output


def test_project_manifest_path_is_accepted(tmp_path: Path, monkeypatch) -> None:
    service = RecordingProjectService()
    monkeypatch.setattr(
        "thesis_forge.cli.ProjectApplicationService",
        lambda: service,
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["inspect", str(PROJECT / "thesisforge.yaml")],
    )

    assert result.exit_code == 0, result.stdout
    assert service.requests[0].project.manifest_path == (
        PROJECT / "thesisforge.yaml"
    ).resolve()


def test_project_path_boundary_error_is_structured(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / "thesis.md").write_text("# 绪论\n", encoding="utf-8")
    (project / "thesisforge.yaml").write_text(
        """
schema: thesisforge.project.v2
project:
  id: symlink-fixture
  language: zh-CN
document:
  source: thesis.md
resources:
  assets: assets
render:
  template_id: example-university-2026
""".lstrip(),
        encoding="utf-8",
    )
    try:
        os.symlink(outside, project / "assets", target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")

    result = CliRunner().invoke(app, ["inspect", str(project)])

    assert result.exit_code == 2
    assert "TF-PROJECT-PATH-SYMLINK-ESCAPE" in result.stdout
    assert "Traceback" not in result.stdout


def test_project_build_validation_failure_emits_typed_report(monkeypatch) -> None:
    class FailingProjectService(RecordingProjectService):
        def build(self, request):
            self.requests.append(request)
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

    service = FailingProjectService()
    monkeypatch.setattr(
        "thesis_forge.cli.ProjectApplicationService",
        lambda: service,
    )
    result = CliRunner().invoke(app, ["build", str(PROJECT)])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["report"]["schemaVersion"] == "thesisforge.build-report.v2"
    assert payload["report"]["outcome"] == "failed"
    assert payload["report"]["failedStage"] == BuildStage.VALIDATE.value
    assert payload["report"]["diagnostics"][0]["code"] == "missing-image"
    assert "编译停止" in payload["message"]
