from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from typer.testing import CliRunner

from docforge.application.contracts import (
    PreviewResult,
    ProjectRequestIntent,
)
from docforge.cli import app
from docforge.core.model import (
    ForgeDocument,
    Heading,
    SourceLocation,
    Text,
    ValidationIssue,
)
from docforge.core.render_plan import (
    HeadingInstruction,
    ParagraphInstruction,
    RenderPlan,
    TextRun,
)
from docforge.core.validator import ValidationContext

PROJECT = Path(__file__).resolve().parents[1] / "fixtures" / "docforge-academic"


def _preview(*, blocked: bool = False) -> PreviewResult:
    document = ForgeDocument(
        source_path=PROJECT / "document.md",
        blocks=[
            Heading(
                id="chap:introduction",
                inlines=[Text(value="绪论")],
                location=SourceLocation(line=1),
            )
        ],
    )
    if blocked:
        return PreviewResult(
            document=document,
            context=ValidationContext(),
            issues=(
                ValidationIssue(
                    code="missing-reference",
                    severity="error",
                    message="missing reference",
                    line=2,
                    target="fig:missing",
                ),
            ),
            plan=None,
        )
    return PreviewResult(
        document=document,
        context=ValidationContext(),
        issues=(),
        plan=RenderPlan(
            nodes=[
                HeadingInstruction(
                    source_id="chap:introduction",
                    level=1,
                    text="绪论",
                    inlines=(TextRun("绪论"),),
                ),
                ParagraphInstruction(
                    text="Review 正文",
                    inlines=(TextRun("Review 正文"),),
                ),
            ]
        ),
    )


class RecordingReviewService:
    def __init__(self, *, blocked: bool = False) -> None:
        self.blocked = blocked
        self.requests = []

    def preview(self, request):
        self.requests.append(request)
        return _preview(blocked=self.blocked)


def test_review_exports_markdown_and_source_map(
    monkeypatch,
    tmp_path: Path,
) -> None:
    service = RecordingReviewService()
    monkeypatch.setattr(
        "docforge.cli.ProjectApplicationService",
        lambda: service,
    )
    output_dir = tmp_path / "review-export"

    result = CliRunner().invoke(
        app,
        ["review", str(PROJECT), "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 0, result.stdout
    markdown_path = output_dir / "document.review.md"
    source_map_path = output_dir / "document.review-map.json"
    assert markdown_path.is_file()
    assert source_map_path.is_file()
    markdown = markdown_path.read_text(encoding="utf-8")
    source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
    assert "GENERATED FILE" in markdown
    assert "Review 正文" in markdown
    assert "chap:introduction" not in markdown
    assert source_map["schemaVersion"] == 1
    assert source_map["blocks"][0]["source"] is not None
    assert "Review 正文" not in source_map_path.read_text(encoding="utf-8")
    assert service.requests[0].intent is ProjectRequestIntent.REVIEW

    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["markdown"] == str(markdown_path.resolve())
    assert payload["sourceMap"] == str(source_map_path.resolve())
    assert payload["issues"] == []


def test_review_uses_manifest_paths_when_output_dir_is_omitted(
    monkeypatch,
    tmp_path: Path,
) -> None:
    service = RecordingReviewService()
    monkeypatch.setattr(
        "docforge.cli.ProjectApplicationService",
        lambda: service,
    )
    project = tmp_path / "project"
    shutil.copytree(PROJECT, project)

    result = CliRunner().invoke(app, ["review", str(project)])

    assert result.exit_code == 0, result.stdout
    markdown_path = project / "review" / "document.review.md"
    source_map_path = project / "review" / "document.review-map.json"
    assert markdown_path.is_file()
    assert source_map_path.is_file()
    payload = json.loads(result.stdout)
    assert payload["markdown"] == str(markdown_path.resolve())
    assert payload["sourceMap"] == str(source_map_path.resolve())


def test_review_accepts_manifest_path(monkeypatch, tmp_path: Path) -> None:
    service = RecordingReviewService()
    monkeypatch.setattr(
        "docforge.cli.ProjectApplicationService",
        lambda: service,
    )

    result = CliRunner().invoke(
        app,
        [
            "review",
            str(PROJECT / "docforge.yaml"),
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert service.requests[0].project.manifest_path == (
        PROJECT / "docforge.yaml"
    ).resolve()


def test_review_rejects_bare_markdown_with_structured_error(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "review",
            str(PROJECT / "document.md"),
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "TF-PROJECT-ENTRY-REQUIRED"
    assert not (tmp_path / "document.review.md").exists()
    assert "Traceback" not in result.stdout


def test_review_writes_blocked_artifacts_and_returns_diagnostic(
    monkeypatch,
    tmp_path: Path,
) -> None:
    service = RecordingReviewService(blocked=True)
    monkeypatch.setattr(
        "docforge.cli.ProjectApplicationService",
        lambda: service,
    )
    output_dir = tmp_path / "blocked-review"

    result = CliRunner().invoke(
        app,
        ["review", str(PROJECT), "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 1, result.stdout
    markdown = (output_dir / "document.review.md").read_text(encoding="utf-8")
    source_map = json.loads(
        (output_dir / "document.review-map.json").read_text(encoding="utf-8")
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["issues"][0]["code"] == "missing-reference"
    assert "Review status: blocked" in markdown
    assert "missing-reference" not in markdown
    assert source_map["blocks"] == []


def test_review_second_output_failure_preserves_existing_outputs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    service = RecordingReviewService()
    monkeypatch.setattr(
        "docforge.cli.ProjectApplicationService",
        lambda: service,
    )
    output_dir = tmp_path / "review-export"
    output_dir.mkdir()
    markdown_path = output_dir / "document.review.md"
    source_map_path = output_dir / "document.review-map.json"
    previous_markdown = "# Previous Review\n"
    previous_source_map = '{"schemaVersion": 1, "blocks": []}\n'
    markdown_path.write_text(previous_markdown, encoding="utf-8")
    source_map_path.write_text(previous_source_map, encoding="utf-8")

    original_replace = os.replace
    failed = False

    def fail_source_map_replace(source: Path, target: Path) -> None:
        nonlocal failed
        if (
            target == source_map_path
            and source.name.startswith(f".{source_map_path.name}.")
            and not failed
        ):
            failed = True
            raise OSError("source map replace denied")
        original_replace(source, target)

    monkeypatch.setattr("docforge.cli.os.replace", fail_source_map_replace)

    result = CliRunner().invoke(
        app,
        ["review", str(PROJECT), "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 2, result.stdout
    assert failed
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "TF-REVIEW-OUTPUT-WRITE"
    assert markdown_path.read_text(encoding="utf-8") == previous_markdown
    assert source_map_path.read_text(encoding="utf-8") == previous_source_map
    assert list(output_dir.glob(".*.tmp")) == []


def test_review_second_output_failure_leaves_no_partial_outputs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    service = RecordingReviewService()
    monkeypatch.setattr(
        "docforge.cli.ProjectApplicationService",
        lambda: service,
    )
    output_dir = tmp_path / "review-export"
    markdown_path = output_dir / "document.review.md"
    source_map_path = output_dir / "document.review-map.json"
    original_replace = os.replace
    failed = False

    def fail_source_map_replace(source: Path, target: Path) -> None:
        nonlocal failed
        if target == source_map_path and not failed:
            failed = True
            raise OSError("source map replace denied")
        original_replace(source, target)

    monkeypatch.setattr("docforge.cli.os.replace", fail_source_map_replace)

    result = CliRunner().invoke(
        app,
        ["review", str(PROJECT), "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 2, result.stdout
    assert failed
    assert not markdown_path.exists()
    assert not source_map_path.exists()
    assert list(output_dir.glob(".*.tmp")) == []
