from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Final

from thesis_forge.application.contracts import BuildReport, ProjectIdentity

PROTOCOL_VERSION: Final = "thesisforge.workbench.v1"
ABSOLUTE_PATH_RE = re.compile(r"(?<![\w])(?:/[^\s:]+|[A-Za-z]:\\[^\s:]+)")


@dataclass(frozen=True, slots=True)
class ProjectRequestPayload:
    project_id: str
    project_root: str
    manifest_path: str
    editor_snapshot: str | None
    output: dict[str, object] | None


def read_project_request_payload(payload: object) -> ProjectRequestPayload | None:
    if not isinstance(payload, dict):
        raise TypeError("payload must be an object")
    if "project" not in payload:
        raise TypeError("project is required")
    project = payload["project"]
    if not isinstance(project, dict):
        raise TypeError("project must be an object")
    project_id = project.get("id")
    project_root = project.get("root")
    manifest_path = project.get("manifestPath")
    if not isinstance(project_id, str) or not project_id:
        raise TypeError("project.id must be a non-empty string")
    if not isinstance(project_root, str) or not project_root:
        raise TypeError("project.root must be a non-empty string")
    if not isinstance(manifest_path, str) or not manifest_path:
        raise TypeError("project.manifestPath must be a non-empty string")
    try:
        ProjectIdentity(
            project_id=project_id,
            project_root=Path(project_root),
            manifest_path=Path(manifest_path),
        )
    except (TypeError, ValueError) as error:
        raise ValueError("project identity is invalid") from error
    editor_snapshot = payload.get("text")
    if editor_snapshot is not None and not isinstance(editor_snapshot, str):
        raise TypeError("text must be a string")
    output = payload.get("output")
    if output is not None and not isinstance(output, dict):
        raise TypeError("output must be an object")
    return ProjectRequestPayload(
        project_id=project_id,
        project_root=project_root,
        manifest_path=manifest_path,
        editor_snapshot=editor_snapshot,
        output=dict(output) if output is not None else None,
    )


def success_response(request_id: str, result: dict) -> dict:
    return {
        "protocol": PROTOCOL_VERSION,
        "requestId": request_id,
        "ok": True,
        "result": result,
    }


def error_response(
    request_id: str,
    *,
    kind: str,
    message: str,
    stage: str | None = None,
) -> dict:
    error = {"kind": kind, "message": message}
    if stage is not None:
        error["stage"] = stage
    return {
        "protocol": PROTOCOL_VERSION,
        "requestId": request_id,
        "ok": False,
        "error": error,
    }


def sanitize_build_report_text(message: str) -> str:
    return ABSOLUTE_PATH_RE.sub("<path>", message)


def _timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    serialized = value.isoformat()
    return (
        serialized.replace("+00:00", "Z")
        if value.utcoffset() == timedelta(0)
        else serialized
    )


def _source_range(source) -> dict | None:
    if source is None:
        return None
    return {
        "file": sanitize_build_report_text(source.file or "<source>"),
        "startLine": source.start_line,
        "startColumn": source.start_column,
        "endLine": source.end_line,
        "endColumn": source.end_column,
    }


def _details(details) -> dict:
    serialized: dict = {}
    for key, value in details.items():
        if not isinstance(key, str):
            raise TypeError("BuildReport detail keys must be strings")
        if isinstance(value, str):
            serialized[key] = sanitize_build_report_text(value)
        elif (
            value is None
            or isinstance(value, (bool, int))
            or (isinstance(value, float) and math.isfinite(value))
        ):
            serialized[key] = value
        else:
            raise ValueError(
                f"BuildReport detail {key!r} must be a finite scalar"
            )
    return serialized


def serialize_build_report(report: BuildReport) -> dict:
    def diagnostic(item) -> dict:
        return {
            "id": item.id,
            "severity": item.severity.value,
            "category": item.category.value,
            "code": item.code,
            "stage": item.stage.value,
            "message": sanitize_build_report_text(item.message),
            "source": _source_range(item.source),
            "target": (
                sanitize_build_report_text(item.target)
                if item.target is not None
                else None
            ),
            "suggestion": (
                sanitize_build_report_text(item.suggestion)
                if item.suggestion is not None
                else None
            ),
            "relatedLocations": [
                {
                    "message": sanitize_build_report_text(location.message),
                    "source": _source_range(location.source),
                }
                for location in item.related_locations
            ],
            "details": _details(item.details),
        }

    return {
        "schemaVersion": report.schema_version,
        "buildId": report.build_id,
        "intent": report.intent.value,
        "outcome": report.outcome.value,
        "startedAt": _timestamp(report.started_at),
        "completedAt": _timestamp(report.completed_at),
        "stages": [
            {
                "name": stage.name.value,
                "status": stage.status.value,
                "startedAt": _timestamp(stage.started_at),
                "completedAt": _timestamp(stage.completed_at),
            }
            for stage in report.stages
        ],
        "failedStage": report.failed_stage.value if report.failed_stage else None,
        "primaryDiagnosticId": report.primary_diagnostic_id,
        "diagnostics": [diagnostic(item) for item in report.diagnostics],
        "logs": [
            {
                "sequence": log.sequence,
                "stage": log.stage.value,
                "level": log.level.value,
                "message": sanitize_build_report_text(log.message),
            }
            for log in report.logs
        ],
        "output": (
            {
                "docxPath": (
                    sanitize_build_report_text(str(report.output.docx_path))
                    if report.output.docx_path is not None
                    else None
                ),
                "pdfPath": (
                    sanitize_build_report_text(str(report.output.pdf_path))
                    if report.output.pdf_path is not None
                    else None
                ),
                "previewStale": report.output.preview_stale,
                "successfulBuildId": report.output.successful_build_id,
            }
            if report.output is not None
            else None
        ),
    }
