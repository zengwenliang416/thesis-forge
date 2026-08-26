from __future__ import annotations

from pathlib import Path

import pytest

from docforge.application.contracts import (
    ApplicationStageError,
    BuildDiagnostic,
    BuildDiagnosticCategory,
    BuildDiagnosticSeverity,
    BuildIntent,
    BuildLogEntry,
    BuildLogLevel,
    BuildOutcome,
    BuildOutput,
    BuildRelatedLocation,
    BuildReport,
    BuildReportStage,
    BuildSourceRange,
    BuildStage,
    BuildStageState,
    BuildStageStatus,
    BuildValidationError,
)
from docforge.core.model import ValidationIssue


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
    ("field", "value"),
    [
        ("start_line", True),
        ("start_column", 1.5),
        ("end_line", "2"),
        ("end_column", False),
    ],
)
def test_source_ranges_require_integer_coordinates(field: str, value: object) -> None:
    with pytest.raises(TypeError, match="integer"):
        BuildSourceRange(**{field: value})  # type: ignore[arg-type]


def test_source_ranges_require_string_files() -> None:
    with pytest.raises(TypeError, match="file"):
        BuildSourceRange(file=Path("thesis.md"))  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["start_line", "start_column", "end_line", "end_column"])
@pytest.mark.parametrize("value", [0, -1])
def test_source_ranges_require_positive_coordinates(field: str, value: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        BuildSourceRange(**{field: value})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start_column": 1},
        {"end_line": 2},
        {"end_column": 2},
    ],
)
def test_source_ranges_reject_orphaned_coordinates(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError, match="requires"):
        BuildSourceRange(**kwargs)


def test_source_ranges_reject_reverse_line_and_column_order() -> None:
    with pytest.raises(ValueError, match="end_line"):
        BuildSourceRange(start_line=3, end_line=2)
    with pytest.raises(ValueError, match="end_column"):
        BuildSourceRange(
            start_line=3,
            start_column=4,
            end_line=3,
            end_column=2,
        )


def _diagnostic_kwargs() -> dict[str, object]:
    return {
        "id": "diag-typed",
        "severity": BuildDiagnosticSeverity.ERROR,
        "category": BuildDiagnosticCategory.SEMANTIC,
        "code": "TF-SEMANTIC-DUPLICATE-ID",
        "stage": BuildReportStage.VALIDATE,
        "message": "duplicate",
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", 1, "id"),
        ("code", 1, "code"),
        ("message", 1, "message"),
        ("severity", "error", "severity"),
        ("category", "semantic", "category"),
        ("stage", "validate", "stage"),
        ("source", object(), "source"),
        ("target", 7, "target"),
        ("suggestion", 7, "suggestion"),
    ],
)
def test_diagnostics_reject_wrong_runtime_field_types(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(TypeError, match=message):
        BuildDiagnostic(
            **_diagnostic_kwargs(),
            **{field: value},
        )  # type: ignore[arg-type]


def test_related_locations_reject_wrong_message_and_source_types() -> None:
    with pytest.raises(TypeError, match="message"):
        BuildRelatedLocation(message=1, source=BuildSourceRange())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="message"):
        BuildRelatedLocation(message="", source=BuildSourceRange())
    with pytest.raises(TypeError, match="source"):
        BuildRelatedLocation(message="related", source=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="related locations"):
        BuildDiagnostic(
            **_diagnostic_kwargs(),
            related_locations=(object(),),  # type: ignore[arg-type]
        )


def test_diagnostics_reject_non_mapping_and_non_string_detail_keys() -> None:
    with pytest.raises(TypeError, match="mapping"):
        BuildDiagnostic(
            **_diagnostic_kwargs(),
            details=[("count", 1)],  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="keys"):
        BuildDiagnostic(
            **_diagnostic_kwargs(),
            details={1: "bad"},  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_diagnostics_reject_non_finite_scalar_details(value: float) -> None:
    with pytest.raises(ValueError, match="finite scalar"):
        BuildDiagnostic(**_diagnostic_kwargs(), details={"value": value})


def test_diagnostic_contract_preserves_valid_related_locations() -> None:
    source = BuildSourceRange(start_line=2, end_line=2)
    related = BuildRelatedLocation(message="first definition", source=source)
    diagnostic = BuildDiagnostic(
        **_diagnostic_kwargs(),
        source=source,
        related_locations=(related,),
        details={"count": 2, "ratio": 0.5},
    )

    assert diagnostic.source is source
    assert diagnostic.related_locations == (related,)
    assert diagnostic.details == {"count": 2, "ratio": 0.5}


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
                "docforge.application.contracts",
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
