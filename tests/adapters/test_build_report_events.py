from __future__ import annotations

from pathlib import Path

import pytest

from docforge import application
from docforge.adapters import (
    PROTOCOL_VERSION,
    DesktopRuntime,
    WorkbenchCommandDispatcher,
)
from docforge.adapters.runtime import _serialize_build_report
from docforge.application import BuildStage
from docforge.application.contracts import (
    BuildIntent,
    BuildOutcome,
    BuildReport,
    BuildReportStage,
    BuildStageState,
    BuildStageStatus,
)
from docforge.core.model import ValidationIssue
from docforge.project.constants import DEFAULT_DOCX_FILENAME, DEFAULT_SOURCE_PATH, MANIFEST_FILENAME


def _request(source: Path, output: Path) -> dict:
    return {
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-events-1",
        "operation": "build",
        "payload": {
            "source": {
                "kind": "desktop",
                "path": str(source),
                "fileName": source.name,
            },
            "output": {
                "kind": "desktop",
                "path": str(output),
                "fileName": output.name,
            },
        },
    }


def _dispatcher(tmp_path: Path, build) -> tuple[WorkbenchCommandDispatcher, dict]:
    source = tmp_path / DEFAULT_SOURCE_PATH
    source.write_text("# 绪论\n", encoding="utf-8")
    output = tmp_path / DEFAULT_DOCX_FILENAME
    return (
        WorkbenchCommandDispatcher(
            runtime=DesktopRuntime(),
            build=build,
        ),
        _request(source, output),
    )


def _completed_report(
    dispatcher: WorkbenchCommandDispatcher,
    request: dict,
) -> tuple[list[dict], dict]:
    events: list[dict] = []
    dispatcher.stream_build(request, events.append)
    assert sum(event["type"] == "completed" for event in events) == 1
    assert all(event["type"] != "error" for event in events)
    assert events[-1]["type"] == "completed"
    return events, events[-1]["report"]


def _assert_report_shape(report: dict) -> None:
    assert set(report) == {
        "schemaVersion",
        "buildId",
        "intent",
        "outcome",
        "startedAt",
        "completedAt",
        "stages",
        "failedStage",
        "primaryDiagnosticId",
        "diagnostics",
        "logs",
        "output",
    }
    assert report["schemaVersion"] == BuildReport.SCHEMA_VERSION
    assert report["buildId"]
    assert report["intent"] in {"publish", "live-preview"}
    assert report["failedStage"] in {
        "parse",
        "validate",
        "compile",
        "render",
        "finalize",
        "postflight",
        "preview",
    }
    assert report["primaryDiagnosticId"]
    assert report["diagnostics"]
    assert report["output"] is None
    assert len(report["logs"]) <= 500
    assert all(len(log["message"]) <= 4000 for log in report["logs"])
    assert all(
        stage["status"]
        in {"pending", "running", "succeeded", "failed", "skipped"}
        for stage in report["stages"]
    )


def test_validation_failure_preserves_all_issue_fields_and_order(
    tmp_path: Path,
) -> None:
    issues = (
        ValidationIssue(
            code="missing-image",
            severity="error",
            message="missing image",
            line=14,
            target="fig:model",
            details={"asset": "assets/missing.png"},
        ),
        ValidationIssue(
            code="heading-level-jump",
            severity="warning",
            message="heading jump",
            line=22,
            target="sec:method",
            details={"expected": 2},
        ),
    )

    def build(_source, _output, **_kwargs):
        raise application.BuildValidationError(issues)

    dispatcher, request = _dispatcher(tmp_path, build)
    _events, report = _completed_report(dispatcher, request)

    _assert_report_shape(report)
    assert report["outcome"] == "failed"
    assert report["failedStage"] == "validate"
    assert report["primaryDiagnosticId"] == "validation-1"
    assert [item["code"] for item in report["diagnostics"]] == [
        "missing-image",
        "heading-level-jump",
    ]
    assert [item["severity"] for item in report["diagnostics"]] == [
        "error",
        "warning",
    ]
    assert [item["source"]["startLine"] for item in report["diagnostics"]] == [14, 22]
    assert [item["target"] for item in report["diagnostics"]] == [
        "fig:model",
        "sec:method",
    ]
    assert [item["details"] for item in report["diagnostics"]] == [
        {"asset": "assets/missing.png"},
        {"expected": 2},
    ]
    assert report["logs"][0]["stage"] == "validate"


@pytest.mark.parametrize(
    ("error", "failed_stage", "outcome", "category", "code"),
    [
        (
            application.ApplicationStageError(
                BuildStage.COMPILE,
                RuntimeError("compile exploded"),
            ),
            "compile",
            "failed",
            "internal",
            "TF-BUILD-COMPILE-FAILED",
        ),
        (
            application.ApplicationStageError(
                BuildStage.RENDER,
                RuntimeError("/private/build/secret.docx was rejected"),
            ),
            "render",
            "failed",
            "internal",
            "TF-BUILD-RENDER-FAILED",
        ),
        (
            application.ApplicationStageError(
                BuildStage.FINALIZE,
                RuntimeError("finalize exploded"),
            ),
            "finalize",
            "failed",
            "internal",
            "TF-BUILD-FINALIZE-FAILED",
        ),
        (
            application.BuildCanceledError(BuildStage.VALIDATE),
            "validate",
            "canceled",
            "internal",
            "TF-BUILD-CANCELED",
        ),
        (
            PermissionError("/private/output/document.docx is not writable"),
            "parse",
            "failed",
            "permission",
            "TF-PERMISSION-DENIED",
        ),
        (
            RuntimeError("unexpected transport failure"),
            "parse",
            "failed",
            "transport",
            "TF-TRANSPORT-BUILD-FAILED",
        ),
    ],
)
def test_terminal_failure_matrix_emits_typed_reports(
    tmp_path: Path,
    error: Exception,
    failed_stage: str,
    outcome: str,
    category: str,
    code: str,
) -> None:
    def build(_source, _output, **_kwargs):
        raise error

    dispatcher, request = _dispatcher(tmp_path, build)
    _events, report = _completed_report(dispatcher, request)

    _assert_report_shape(report)
    assert report["outcome"] == outcome
    assert report["failedStage"] == failed_stage
    assert report["diagnostics"][0]["category"] == category
    assert report["diagnostics"][0]["code"] == code
    assert report["primaryDiagnosticId"] == report["diagnostics"][0]["id"]
    assert len(report["logs"][0]["message"]) <= 4000
    assert "/private/" not in str(report["logs"])
    if failed_stage == "render":
        assert "<path>" in report["diagnostics"][0]["message"]
        assert "<path>" in report["logs"][0]["message"]


def test_render_failure_reports_prior_success_and_downstream_skips(
    tmp_path: Path,
) -> None:
    def build(_source, _output, *, on_progress=None, **_kwargs):
        for stage in (
            BuildStage.PARSE,
            BuildStage.VALIDATE,
            BuildStage.COMPILE,
            BuildStage.RENDER,
        ):
            on_progress(stage)
        raise application.ApplicationStageError(
            BuildStage.RENDER,
            RuntimeError("renderer exploded"),
        )

    dispatcher, request = _dispatcher(tmp_path, build)
    _events, report = _completed_report(dispatcher, request)
    statuses = {stage["name"]: stage["status"] for stage in report["stages"]}

    _assert_report_shape(report)
    assert statuses == {
        "parse": "succeeded",
        "validate": "succeeded",
        "compile": "succeeded",
        "render": "failed",
        "finalize": "skipped",
        "postflight": "skipped",
        "preview": "skipped",
    }


def test_report_serializer_preserves_pending_and_running_stage_statuses() -> None:
    report = BuildReport(
        schema_version=BuildReport.SCHEMA_VERSION,
        build_id="build-stage-statuses",
        intent=BuildIntent.PUBLISH,
        outcome=BuildOutcome.SUCCEEDED,
        stages=(
            BuildStageState(
                name=BuildReportStage.PARSE,
                status=BuildStageStatus.PENDING,
            ),
            BuildStageState(
                name=BuildReportStage.VALIDATE,
                status=BuildStageStatus.RUNNING,
            ),
        ),
        failed_stage=None,
        primary_diagnostic_id=None,
        diagnostics=(),
        logs=(),
        output=None,
    )

    serialized = _serialize_build_report(report)

    assert [stage["status"] for stage in serialized["stages"]] == [
        "pending",
        "running",
    ]


def test_failure_logs_are_truncated_after_path_sanitization(tmp_path: Path) -> None:
    raw_message = "secret-" * 1000

    def build(_source, _output, **_kwargs):
        raise application.ApplicationStageError(
            BuildStage.RENDER,
            RuntimeError(raw_message),
        )

    dispatcher, request = _dispatcher(tmp_path, build)
    _events, report = _completed_report(dispatcher, request)

    assert len(report["logs"][0]["message"]) == 4000


def test_project_stream_failure_emits_one_canonical_completed_report(
    tmp_path: Path,
) -> None:
    project_root = (tmp_path / "project").resolve()
    project_root.mkdir()
    source = project_root / DEFAULT_SOURCE_PATH
    source.write_text("# 绪论\n", encoding="utf-8")
    manifest = project_root / MANIFEST_FILENAME
    manifest.write_text("schema: docforge.project.v1\n", encoding="utf-8")
    output = project_root / "build" / DEFAULT_DOCX_FILENAME

    class ProjectService:
        def build(self, request, *, on_progress=None, should_cancel=None):
            on_progress(BuildStage.PARSE)
            raise application.ApplicationStageError(
                BuildStage.RENDER,
                RuntimeError("project renderer exploded"),
            )

    dispatcher = WorkbenchCommandDispatcher(
        runtime=DesktopRuntime(),
        project_service=ProjectService(),
    )
    request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "project-failure-1",
        "operation": "build",
        "payload": {
            "project": {
                "id": "report-fixture",
                "root": str(project_root),
                "manifestPath": str(manifest),
            },
            "source": {
                "kind": "desktop",
                "path": str(source),
                "fileName": source.name,
            },
            "text": "# 未保存\n",
            "output": {
                "kind": "desktop",
                "path": str(output),
                "fileName": output.name,
            },
        },
    }

    events: list[dict] = []
    dispatcher.stream_build(request, events.append)

    assert [event["type"] for event in events] == ["progress", "completed"]
    report = events[-1]["report"]
    assert report["outcome"] == "failed"
    assert report["failedStage"] == "render"
    assert all(event["type"] != "error" for event in events)
