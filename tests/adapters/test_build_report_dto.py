from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest

from thesis_forge.adapters.dto import serialize_build_report
from thesis_forge.application.contracts import (
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
    BuildStageState,
    BuildStageStatus,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = PROJECT_ROOT / "protocol" / "examples"


def _timestamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value is not None else None


def _source(value: dict | None) -> BuildSourceRange | None:
    if value is None:
        return None
    return BuildSourceRange(
        file=value["file"],
        start_line=value["startLine"],
        start_column=value["startColumn"],
        end_line=value["endLine"],
        end_column=value["endColumn"],
    )


def _report(payload: dict) -> BuildReport:
    output = payload["output"]
    return BuildReport(
        schema_version=payload["schemaVersion"],
        build_id=payload["buildId"],
        intent=BuildIntent(payload["intent"]),
        outcome=BuildOutcome(payload["outcome"]),
        started_at=_timestamp(payload.get("startedAt")),
        completed_at=_timestamp(payload.get("completedAt")),
        stages=tuple(
            BuildStageState(
                name=BuildReportStage(stage["name"]),
                status=BuildStageStatus(stage["status"]),
                started_at=_timestamp(stage.get("startedAt")),
                completed_at=_timestamp(stage.get("completedAt")),
            )
            for stage in payload["stages"]
        ),
        failed_stage=(
            BuildReportStage(payload["failedStage"])
            if payload["failedStage"] is not None
            else None
        ),
        primary_diagnostic_id=payload["primaryDiagnosticId"],
        diagnostics=tuple(
            BuildDiagnostic(
                id=item["id"],
                severity=BuildDiagnosticSeverity(item["severity"]),
                category=BuildDiagnosticCategory(item["category"]),
                code=item["code"],
                stage=BuildReportStage(item["stage"]),
                message=item["message"],
                source=_source(item["source"]),
                target=item["target"],
                suggestion=item["suggestion"],
                related_locations=tuple(
                    BuildRelatedLocation(
                        message=location["message"],
                        source=_source(location["source"]),
                    )
                    for location in item["relatedLocations"]
                ),
                details=item["details"],
            )
            for item in payload["diagnostics"]
        ),
        logs=tuple(
            BuildLogEntry(
                sequence=log["sequence"],
                stage=BuildReportStage(log["stage"]),
                level=BuildLogLevel(log["level"]),
                message=log["message"],
            )
            for log in payload["logs"]
        ),
        output=(
            BuildOutput(
                docx_path=(
                    Path(output["docxPath"])
                    if output["docxPath"] is not None
                    else None
                ),
                pdf_path=(
                    Path(output["pdfPath"]) if output["pdfPath"] is not None else None
                ),
                preview_stale=output["previewStale"],
                successful_build_id=output["successfulBuildId"],
            )
            if output is not None
            else None
        ),
    )


@pytest.mark.parametrize(
    "filename",
    [
        "build-success.json",
        "build-failed-validation.json",
        "build-failed-render.json",
    ],
)
def test_protocol_examples_round_trip_without_dropping_fields(filename: str) -> None:
    expected = json.loads((EXAMPLES / filename).read_text(encoding="utf-8"))

    assert serialize_build_report(_report(expected)) == expected


def test_cancellation_preserves_nullable_output_and_diagnostics() -> None:
    payload = json.loads(
        (EXAMPLES / "build-failed-validation.json").read_text(encoding="utf-8")
    )
    report = replace(_report(payload), outcome=BuildOutcome.CANCELED)

    serialized = serialize_build_report(report)

    assert serialized["outcome"] == "canceled"
    assert serialized["primaryDiagnosticId"] == "diag-asset-1"
    assert serialized["output"]["previewStale"] is True
    assert serialized["diagnostics"][0]["details"] == {"figureId": "fig:model"}


def test_missing_source_file_uses_safe_placeholder() -> None:
    payload = json.loads(
        (EXAMPLES / "build-failed-validation.json").read_text(encoding="utf-8")
    )
    report = _report(payload)
    report = replace(
        report,
        diagnostics=(
            replace(
                report.diagnostics[0],
                source=BuildSourceRange(
                    file=None,
                    start_line=14,
                    start_column=1,
                    end_line=14,
                    end_column=52,
                ),
            ),
        ),
    )

    serialized = serialize_build_report(report)

    assert serialized["diagnostics"][0]["source"]["file"] == "<source>"


def test_path_bearing_report_fields_are_sanitized() -> None:
    payload = json.loads(
        (EXAMPLES / "build-failed-validation.json").read_text(encoding="utf-8")
    )
    report = _report(payload)
    source = BuildSourceRange(
        file="/Users/alice/thesis.md",
        start_line=14,
        start_column=1,
        end_line=14,
        end_column=52,
    )
    diagnostic = replace(
        report.diagnostics[0],
        source=source,
        target="/Users/alice/assets/missing.png",
        suggestion="Fix /Users/alice/assets/missing.png",
        related_locations=(
            BuildRelatedLocation(
                message="See /Users/alice/thesis.md",
                source=source,
            ),
        ),
        details={"path": "/Users/alice/assets/missing.png"},
    )
    output = replace(
        report.output,
        docx_path=Path("/Users/alice/build/thesis.docx"),
        pdf_path=Path("/Users/alice/build/thesis.pdf"),
    )
    report = replace(report, diagnostics=(diagnostic,), output=output)

    serialized = serialize_build_report(report)
    encoded = json.dumps(serialized, ensure_ascii=False)

    assert "/Users/alice" not in encoded
    assert "<path>" in encoded


@pytest.mark.parametrize(
    "details",
    [
        {"nested": {"value": float("nan")}},
        {"nested": [float("inf")]},
        {"nested": {"path": "/Users/alice/secret"}},
    ],
)
def test_nested_or_non_finite_details_are_rejected(details: dict) -> None:
    payload = json.loads(
        (EXAMPLES / "build-failed-validation.json").read_text(encoding="utf-8")
    )
    report = _report(payload)

    with pytest.raises(ValueError, match="finite scalar"):
        replace(report.diagnostics[0], details=details)
