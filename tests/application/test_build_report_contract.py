from __future__ import annotations

from pathlib import Path

import pytest

from thesis_forge.application.contracts import (
    BuildDiagnosticCategory,
    BuildDiagnosticSeverity,
    BuildIntent,
    BuildLogEntry,
    BuildLogLevel,
    BuildOutcome,
    BuildOutput,
    BuildReport,
    BuildReportStage,
    BuildStage,
    BuildStageState,
    BuildStageStatus,
    BuildValidationError,
    ApplicationStageError,
)
from thesis_forge.core.model import ValidationIssue


def _issue(
    code: str,
    *,
    severity: str = "error",
    line: int | None = None,
    target: str | None = None,
    details: dict[str, str | int] | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        severity=severity,
        message=f"message for {code}",
        line=line,
        target=target,
        details=details or {},
    )


def test_success_report_contains_typed_lifecycle_and_output_policy() -> None:
    output = BuildOutput(
        docx_path=Path("build/thesis.docx"),
        pdf_path=Path("build/thesis.pdf"),
        preview_stale=False,
        successful_build_id="build-0001",
    )
    report = BuildReport(
        schema_version=BuildReport.SCHEMA_VERSION,
        build_id="build-0001",
        intent=BuildIntent.PUBLISH,
        outcome=BuildOutcome.SUCCEEDED,
        stages=BuildReport.default_stages(
            failed_stage=None,
            outcome=BuildOutcome.SUCCEEDED,
        ),
        failed_stage=None,
        primary_diagnostic_id=None,
        diagnostics=(),
        logs=(
            BuildLogEntry(
                sequence=0,
                stage=BuildReportStage.PARSE,
                level=BuildLogLevel.INFO,
                message="Project parsed.",
            ),
        ),
        output=output,
    )

    assert all(
        stage.status is BuildStageStatus.SUCCEEDED for stage in report.stages
    )
    assert report.output == output
    assert report.failed_stage is None


def test_validation_report_preserves_every_issue_in_original_order() -> None:
    issues = (
        _issue(
            "missing-image",
            line=14,
            target="fig:model",
            details={"figureId": "fig:model", "attempt": 1},
        ),
        _issue(
            "heading-level-jump",
            severity="warning",
            line=22,
            target="sec:method",
            details={"expected": 2},
        ),
    )
    error = BuildValidationError(issues)

    report = error.to_report(
        build_id="build-0002",
        intent="publish",
        source_file="thesis.md",
    )

    assert report.outcome is BuildOutcome.FAILED
    assert report.failed_stage is BuildReportStage.VALIDATE
    assert [diagnostic.code for diagnostic in report.diagnostics] == [
        "missing-image",
        "heading-level-jump",
    ]
    assert [diagnostic.line for diagnostic in report.diagnostics] == [14, 22]
    assert [diagnostic.target for diagnostic in report.diagnostics] == [
        "fig:model",
        "sec:method",
    ]
    assert report.diagnostics[0].details == {
        "figureId": "fig:model",
        "attempt": 1,
    }
    assert report.primary_diagnostic_id == "validation-1"
    assert not hasattr(report, "message")


@pytest.mark.parametrize(
    ("error", "outcome", "category", "code"),
    [
        (
            ApplicationStageError(
                BuildStage.RENDER,
                RuntimeError("renderer exploded"),
            ),
            BuildOutcome.FAILED,
            BuildDiagnosticCategory.INTERNAL,
            "TF-BUILD-RENDER-FAILED",
        ),
        (
            __import__(
                "thesis_forge.application.contracts",
                fromlist=["BuildCanceledError"],
            ).BuildCanceledError(BuildStage.COMPILE),
            BuildOutcome.CANCELED,
            BuildDiagnosticCategory.INTERNAL,
            "TF-BUILD-CANCELED",
        ),
        (
            ApplicationStageError(
                BuildStage.FINALIZE,
                PermissionError("permission denied"),
            ),
            BuildOutcome.FAILED,
            BuildDiagnosticCategory.PERMISSION,
            "TF-PERMISSION-DENIED",
        ),
    ],
)
def test_terminal_failures_have_typed_diagnostics(
    error: ApplicationStageError,
    outcome: BuildOutcome,
    category: BuildDiagnosticCategory,
    code: str,
) -> None:
    report = BuildReport.from_error(
        error,
        build_id="build-terminal",
        intent=BuildIntent.LIVE_PREVIEW,
    )

    assert report.outcome is outcome
    assert report.failed_stage is not None
    assert report.primary_diagnostic_id == report.diagnostics[0].id
    assert report.diagnostics[0].category is category
    assert report.diagnostics[0].code == code
    assert report.diagnostics[0].message


def test_stage_statuses_and_log_bounds_are_enforced() -> None:
    states = (
        BuildStageState(
            name=BuildReportStage.PARSE,
            status=BuildStageStatus.PENDING,
        ),
        BuildStageState(
            name=BuildReportStage.VALIDATE,
            status=BuildStageStatus.RUNNING,
        ),
        BuildStageState(
            name=BuildReportStage.COMPILE,
            status=BuildStageStatus.SUCCEEDED,
        ),
        BuildStageState(
            name=BuildReportStage.RENDER,
            status=BuildStageStatus.FAILED,
        ),
        BuildStageState(
            name=BuildReportStage.FINALIZE,
            status=BuildStageStatus.SKIPPED,
        ),
    )
    report = BuildReport(
        schema_version=BuildReport.SCHEMA_VERSION,
        build_id="build-stages",
        intent=BuildIntent.PUBLISH,
        outcome=BuildOutcome.FAILED,
        stages=states,
        failed_stage=BuildReportStage.RENDER,
        primary_diagnostic_id=None,
        diagnostics=(),
        logs=(),
        output=None,
    )

    assert [stage.status for stage in report.stages] == [
        BuildStageStatus.PENDING,
        BuildStageStatus.RUNNING,
        BuildStageStatus.SUCCEEDED,
        BuildStageStatus.FAILED,
        BuildStageStatus.SKIPPED,
    ]

    with pytest.raises(ValueError, match="at most 4000"):
        BuildLogEntry(
            sequence=0,
            stage=BuildReportStage.RENDER,
            level=BuildLogLevel.ERROR,
            message="x" * 4001,
        )

    too_many_logs = tuple(
        BuildLogEntry(
            sequence=index,
            stage=BuildReportStage.PARSE,
            level=BuildLogLevel.DEBUG,
            message="log",
        )
        for index in range(501)
    )
    with pytest.raises(ValueError, match="at most 500"):
        BuildReport(
            schema_version=BuildReport.SCHEMA_VERSION,
            build_id="build-too-many-logs",
            intent=BuildIntent.PUBLISH,
            outcome=BuildOutcome.SUCCEEDED,
            stages=(
                BuildStageState(
                    name=BuildReportStage.PARSE,
                    status=BuildStageStatus.SUCCEEDED,
                ),
            ),
            failed_stage=None,
            primary_diagnostic_id=None,
            diagnostics=(),
            logs=too_many_logs,
            output=None,
        )
