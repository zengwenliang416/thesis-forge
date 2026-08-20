from __future__ import annotations

import re
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
from time import monotonic, time
from typing import Protocol
from uuid import uuid4

from thesis_forge.application import (
    ApplicationDependencies,
    ApplicationStageError,
    BuildCanceledError,
    BuildResult,
    BuildValidationError,
    InspectionResult,
    LibreOfficePdfPreviewExporter,
    PreviewResult,
    ValidationResult,
    build_service,
    inspect_service,
    preferred_pdf_preview_exporter,
    preview_service,
    validation_service,
)
from thesis_forge.application.contracts import (
    BuildDiagnostic,
    BuildDiagnosticCategory,
    BuildDiagnosticSeverity,
    BuildIntent,
    BuildLogEntry,
    BuildLogLevel,
    BuildOutcome,
    BuildReport,
    BuildReportStage,
    BuildStage,
)
from thesis_forge.core.model import Heading
from thesis_forge.presentation.preview import map_preview_result
from thesis_forge.templates import default_template_search_roots, resolve_template
from thesis_forge.ui.filesystem import LocalWorkspaceFileSystem

from .dto import PROTOCOL_VERSION, error_response, success_response

InspectService = Callable[..., InspectionResult]
ValidationService = Callable[..., ValidationResult]
BuildService = Callable[..., BuildResult]
PreviewService = Callable[..., PreviewResult]
BuildEventSink = Callable[[dict], None]
CancellationPredicate = Callable[[], bool]
LIVE_PREVIEW_STEM_RE = re.compile(
    r"^\.?thesisforge-live-preview-[0-9a-f]{32}$"
)
ABSOLUTE_PATH_RE = re.compile(r"(?<![\w])(?:/[^\s:]+|[A-Za-z]:\\[^\s:]+)")


def final_preview_build_service(
    source: str | Path,
    output: str | Path,
    **kwargs,
) -> BuildResult:
    return build_service(
        source,
        output,
        dependencies=ApplicationDependencies(
            pdf_preview_exporter=LibreOfficePdfPreviewExporter(),
        ),
        **kwargs,
    )


def desktop_final_preview_build_service(
    source: str | Path,
    output: str | Path,
    **kwargs,
) -> BuildResult:
    return build_service(
        source,
        output,
        dependencies=ApplicationDependencies(
            pdf_preview_exporter=preferred_pdf_preview_exporter(),
        ),
        **kwargs,
    )


class RuntimePaths(Protocol):
    def source_path(self, source: dict) -> Path: ...

    def output_path(self, output: dict) -> Path: ...

    def save_source(self, source: dict, text: str) -> Path: ...

    def present_source(self, source: dict, path: Path) -> dict: ...

    def present_output(
        self,
        output: dict,
        path: Path,
        final_preview: object | None = None,
    ) -> dict: ...

    def validate_live_preview_output(self, output: dict, path: Path) -> None: ...

    def release_live_preview_output(self, output: dict) -> None: ...


def _artifact_field(artifact: object, name: str) -> object:
    if isinstance(artifact, dict):
        return artifact.get(name)
    return getattr(artifact, name, None)


def _sanitize_log_message(message: str) -> str:
    return ABSOLUTE_PATH_RE.sub("<path>", message)


def _timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _serialize_build_report(report: BuildReport) -> dict:
    def source_range(source) -> dict | None:
        if source is None:
            return None
        return {
            "file": source.file or "<source>",
            "startLine": source.start_line,
            "startColumn": source.start_column,
            "endLine": source.end_line,
            "endColumn": source.end_column,
        }

    def diagnostic(diagnostic: BuildDiagnostic) -> dict:
        return {
            "id": diagnostic.id,
            "severity": diagnostic.severity.value,
            "category": diagnostic.category.value,
            "code": diagnostic.code,
            "stage": diagnostic.stage.value,
            "message": _sanitize_log_message(diagnostic.message),
            "source": source_range(diagnostic.source),
            "target": diagnostic.target,
            "suggestion": diagnostic.suggestion,
            "relatedLocations": [
                {
                    "message": _sanitize_log_message(location.message),
                    "source": source_range(location.source),
                }
                for location in diagnostic.related_locations
            ],
            "details": dict(diagnostic.details),
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
                "message": _sanitize_log_message(log.message),
            }
            for log in report.logs
        ],
        "output": (
            {
                "docxPath": str(report.output.docx_path)
                if report.output.docx_path is not None
                else None,
                "pdfPath": str(report.output.pdf_path)
                if report.output.pdf_path is not None
                else None,
                "previewStale": report.output.preview_stale,
                "successfulBuildId": report.output.successful_build_id,
            }
            if report.output is not None
            else None
        ),
    }


def _build_report_stage(error: Exception, progressed: list[BuildStage]) -> BuildReportStage:
    if isinstance(error, ApplicationStageError):
        return BuildReportStage(error.stage.value)
    if progressed:
        return BuildReportStage(progressed[-1].value)
    return BuildReportStage.PARSE


def _build_report_logs(
    error: Exception,
    stage: BuildReportStage,
) -> tuple[BuildLogEntry, ...]:
    if isinstance(error, BuildValidationError):
        message = f"Validation failed with {len(error.issues)} issue(s)."
    elif isinstance(error, BuildCanceledError):
        message = "Build canceled."
    elif isinstance(error, PermissionError):
        message = "Build failed because output permission was denied."
    else:
        message = f"Build failed during {stage.value}."
    return (
        BuildLogEntry(
            sequence=0,
            stage=stage,
            level=BuildLogLevel.ERROR,
            message=message,
        ),
    )


def _transport_build_report(
    error: Exception,
    *,
    build_id: str,
    intent: BuildIntent,
    stage: BuildReportStage,
    logs: tuple[BuildLogEntry, ...],
) -> BuildReport:
    item = BuildDiagnostic(
        id="transport-error-1",
        severity=BuildDiagnosticSeverity.ERROR,
        category=BuildDiagnosticCategory.TRANSPORT,
        code="TF-TRANSPORT-BUILD-FAILED",
        stage=stage,
        message=_sanitize_log_message(str(error)),
        details={"exception": type(error).__name__},
    )
    return BuildReport(
        schema_version=BuildReport.SCHEMA_VERSION,
        build_id=build_id,
        intent=intent,
        outcome=BuildOutcome.FAILED,
        stages=BuildReport.default_stages(
            failed_stage=stage,
            outcome=BuildOutcome.FAILED,
        ),
        failed_stage=stage,
        primary_diagnostic_id=item.id,
        diagnostics=(item,),
        logs=logs,
        output=None,
    )


def _failed_build_report(
    error: Exception,
    *,
    build_id: str,
    intent: BuildIntent,
    progressed: list[BuildStage],
    source_file: str | None,
) -> BuildReport:
    stage = _build_report_stage(error, progressed)
    logs = _build_report_logs(error, stage)
    outcome = (
        BuildOutcome.CANCELED
        if isinstance(error, BuildCanceledError)
        else BuildOutcome.FAILED
    )
    stages = BuildReport.default_stages(
        failed_stage=stage,
        outcome=outcome,
    )
    if isinstance(error, BuildValidationError):
        return BuildReport.from_validation_error(
            error,
            build_id=build_id,
            intent=intent,
            source_file=source_file,
            stages=stages,
            logs=logs,
        )
    if isinstance(error, ApplicationStageError):
        return BuildReport.from_stage_error(
            error,
            build_id=build_id,
            intent=intent,
            stages=stages,
            logs=logs,
        )
    if isinstance(error, PermissionError):
        return BuildReport.from_permission_error(
            error,
            build_id=build_id,
            intent=intent,
            stage=stage,
            stages=stages,
            logs=logs,
        )
    return _transport_build_report(
        error,
        build_id=build_id,
        intent=intent,
        stage=stage,
        logs=logs,
    )


def _final_preview_descriptor(
    artifact: object | None,
    *,
    output_path: Path,
    download_id: str | None = None,
) -> dict | None:
    if artifact is None:
        return None
    artifact_path_value = _artifact_field(artifact, "path")
    if artifact_path_value is None:
        raise ValueError("final preview artifact path is required")
    artifact_path = Path(artifact_path_value)
    expected_path = output_path.with_suffix(".preview.pdf")
    if artifact_path != expected_path:
        raise ValueError("final preview must be the derived PDF output")

    name_value = _artifact_field(artifact, "name")
    file_name = name_value if isinstance(name_value, str) else artifact_path.name
    if (
        not file_name
        or Path(file_name).name != file_name
        or "/" in file_name
        or "\\" in file_name
        or not file_name.lower().endswith(".pdf")
        or artifact_path.name != file_name
    ):
        raise ValueError("final preview fileName must be a plain PDF file name")

    engine_value = _artifact_field(artifact, "engine")
    engine = getattr(engine_value, "value", engine_value)
    label = _artifact_field(artifact, "label")
    supported = {
        "microsoft-word": "Microsoft Word PDF",
        "libreoffice": "LibreOffice PDF",
    }
    if engine not in supported or label != supported[engine]:
        raise ValueError("automatic final preview metadata is invalid")

    descriptor = {
        "engine": engine,
        "label": label,
        "fileName": file_name,
    }
    if download_id is not None:
        descriptor["downloadId"] = download_id
    return descriptor


def _cleanup_live_preview_artifacts(output_path: Path) -> None:
    if LIVE_PREVIEW_STEM_RE.fullmatch(output_path.stem) is None:
        return
    output_path.unlink(missing_ok=True)
    output_path.with_suffix(".preview.pdf").unlink(missing_ok=True)
    parent = output_path.parent
    if LIVE_PREVIEW_STEM_RE.fullmatch(parent.name):
        try:
            parent.rmdir()
        except OSError:
            pass


def _is_live_preview_artifact(path: Path) -> bool:
    name = path.name
    if name.endswith(".preview.pdf"):
        stem = name.removesuffix(".preview.pdf")
    elif name.endswith(".docx"):
        stem = name.removesuffix(".docx")
    else:
        return False
    return LIVE_PREVIEW_STEM_RE.fullmatch(stem) is not None


class DesktopRuntime:
    def __init__(self) -> None:
        self._filesystem = LocalWorkspaceFileSystem()

    def source_path(self, source: dict) -> Path:
        if source.get("kind") != "desktop" or not source.get("path"):
            raise ValueError("desktop source path is required")
        return Path(source["path"])

    def output_path(self, output: dict) -> Path:
        if output.get("kind") != "desktop" or not output.get("path"):
            raise ValueError("desktop output path is required")
        return Path(output["path"])

    def save_source(self, source: dict, text: str) -> Path:
        path = self.source_path(source)
        self._filesystem.write_text_atomic(path, text)
        return path

    def present_source(self, source: dict, path: Path) -> dict:
        return {"kind": "desktop", "name": source.get("fileName") or path.name}

    def present_output(
        self,
        output: dict,
        path: Path,
        final_preview: object | None = None,
    ) -> dict:
        presented = {"kind": "desktop", "name": output.get("fileName") or path.name}
        descriptor = _final_preview_descriptor(
            final_preview,
            output_path=path,
        )
        if descriptor is not None:
            presented["finalPreview"] = descriptor
        return presented

    def validate_live_preview_output(self, output: dict, path: Path) -> None:
        stem = path.stem
        parent = path.parent
        if (
            output.get("kind") != "desktop"
            or LIVE_PREVIEW_STEM_RE.fullmatch(stem) is None
            or parent.name != stem
            or output.get("fileName") != path.name
            or parent.is_symlink()
            or not parent.is_dir()
            or parent.resolve().parent != Path(tempfile.gettempdir()).resolve()
            or not _is_token(output.get("livePreviewId"))
        ):
            raise ValueError("desktop live-preview output must use an authorized temporary path")

    def release_live_preview_output(self, output: dict) -> None:
        path = self.output_path(output)
        _cleanup_live_preview_artifacts(path)


def _is_token(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 32
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True, slots=True)
class _WebLivePreviewGrant:
    workspace_id: str
    output_path: Path
    created_at: float


class WebWorkspaceRuntime:
    def __init__(
        self,
        root: Path,
        *,
        live_preview_ttl_seconds: float = 3600.0,
        clock: Callable[[], float] = monotonic,
        wall_clock: Callable[[], float] = time,
    ) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._filesystem = LocalWorkspaceFileSystem()
        self._live_preview_ttl_seconds = live_preview_ttl_seconds
        self._clock = clock
        self._wall_clock = wall_clock
        self._live_previews: dict[str, _WebLivePreviewGrant] = {}
        self._live_preview_lock = Lock()
        self._sweep_orphaned_live_preview_files()

    @staticmethod
    def _plain_file_name(file_name: object) -> str:
        if (
            not isinstance(file_name, str)
            or not file_name
            or Path(file_name).name != file_name
            or "/" in file_name
            or "\\" in file_name
        ):
            raise ValueError("web workspace fileName must be a plain file name")
        return file_name

    @staticmethod
    def _workspace_id(value: object) -> str:
        if (
            not isinstance(value, str)
            or len(value) != 32
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError("invalid web workspace ID")
        return value

    def create_workspace(self, file_name: str, text: str) -> dict:
        safe_name = self._plain_file_name(file_name)
        workspace_id = uuid4().hex
        workspace = self.root / workspace_id
        workspace.mkdir(mode=0o700)
        self._filesystem.write_text_atomic(workspace / safe_name, text)
        return {
            "kind": "web-workspace",
            "workspaceId": workspace_id,
            "fileName": safe_name,
        }

    def _cleanup_live_preview_grant(self, grant: _WebLivePreviewGrant) -> None:
        _cleanup_live_preview_artifacts(grant.output_path)

    def _sweep_expired_live_previews(self) -> None:
        cutoff = self._clock() - self._live_preview_ttl_seconds
        expired: list[_WebLivePreviewGrant] = []
        with self._live_preview_lock:
            for live_preview_id, grant in tuple(self._live_previews.items()):
                if grant.created_at <= cutoff:
                    expired.append(self._live_previews.pop(live_preview_id))
        for grant in expired:
            self._cleanup_live_preview_grant(grant)
        self._sweep_orphaned_live_preview_files()

    def _sweep_orphaned_live_preview_files(self) -> None:
        cutoff = self._wall_clock() - self._live_preview_ttl_seconds
        with self._live_preview_lock:
            active_paths = {
                grant.output_path
                for grant in self._live_previews.values()
            }
        active_artifacts = active_paths | {
            path.with_suffix(".preview.pdf")
            for path in active_paths
        }
        active_directories = {path.parent for path in active_paths}
        for directory in self.root.glob("*/.thesisforge-live-previews"):
            if directory.is_symlink() or not directory.is_dir():
                continue
            for artifact in directory.iterdir():
                if (
                    artifact in active_artifacts
                    or
                    artifact.is_symlink()
                    or not artifact.is_file()
                    or not _is_live_preview_artifact(artifact)
                ):
                    continue
                try:
                    if artifact.stat().st_mtime <= cutoff:
                        artifact.unlink(missing_ok=True)
                except OSError:
                    continue
            if directory not in active_directories:
                try:
                    directory.rmdir()
                except OSError:
                    pass

    def prepare_live_preview_output(self, source: dict) -> dict:
        source_path = self.source_path(source)
        workspace_id = self._workspace_id(source.get("workspaceId"))
        self._sweep_expired_live_previews()
        live_preview_id = uuid4().hex
        file_name = f".thesisforge-live-preview-{live_preview_id}.docx"
        output_directory = source_path.parent / ".thesisforge-live-previews"
        output_directory.mkdir(mode=0o700, exist_ok=True)
        output_path = output_directory / file_name
        grant = _WebLivePreviewGrant(
            workspace_id=workspace_id,
            output_path=output_path,
            created_at=self._clock(),
        )
        with self._live_preview_lock:
            self._live_previews[live_preview_id] = grant
        return {
            "kind": "web-download",
            "workspaceId": workspace_id,
            "fileName": file_name,
            "livePreviewId": live_preview_id,
        }

    def _live_preview_grant(
        self,
        live_preview_id: object,
        *,
        workspace_id: object | None = None,
    ) -> _WebLivePreviewGrant:
        if not _is_token(live_preview_id):
            raise ValueError("invalid live preview ID")
        self._sweep_expired_live_previews()
        with self._live_preview_lock:
            grant = self._live_previews.get(live_preview_id)
        if grant is None:
            raise ValueError("live preview is not authorized")
        if workspace_id is not None and grant.workspace_id != self._workspace_id(workspace_id):
            raise ValueError("live preview workspace does not match")
        return grant

    def source_path(self, source: dict) -> Path:
        if source.get("kind") not in {"web-workspace", "web-upload"}:
            raise ValueError("web workspace source is required")
        workspace_id = self._workspace_id(
            source.get("workspaceId") or source.get("uploadId")
        )
        file_name = self._plain_file_name(source.get("fileName"))
        path = self.root / workspace_id / file_name
        if not path.is_file():
            raise ValueError("web workspace source does not exist")
        return path

    def output_path(self, output: dict) -> Path:
        workspace_id = self._workspace_id(output.get("workspaceId"))
        file_name = self._plain_file_name(output.get("fileName") or "thesis.docx")
        workspace = self.root / workspace_id
        if not workspace.is_dir():
            raise ValueError("web workspace does not exist")
        live_preview_id = output.get("livePreviewId")
        if live_preview_id is not None:
            grant = self._live_preview_grant(
                live_preview_id,
                workspace_id=workspace_id,
            )
            if grant.output_path.name != file_name:
                raise ValueError("live preview output does not match authorization")
            return grant.output_path
        return workspace / file_name

    def save_source(self, source: dict, text: str) -> Path:
        path = self.source_path(source)
        self._filesystem.write_text_atomic(path, text)
        return path

    def present_source(self, source: dict, path: Path) -> dict:
        return {"kind": source["kind"], "name": source.get("fileName") or path.name}

    def present_output(
        self,
        output: dict,
        path: Path,
        final_preview: object | None = None,
    ) -> dict:
        workspace_id = self._workspace_id(output.get("workspaceId"))
        presented = {
            "kind": "web-download",
            "name": output.get("fileName") or path.name,
            "downloadId": workspace_id,
        }
        descriptor = _final_preview_descriptor(
            final_preview,
            output_path=path,
            download_id=workspace_id,
        )
        if descriptor is not None:
            if descriptor["engine"] != "libreoffice":
                raise ValueError("web automatic preview must use LibreOffice")
            live_preview_id = output.get("livePreviewId")
            if live_preview_id is not None:
                grant = self._live_preview_grant(
                    live_preview_id,
                    workspace_id=workspace_id,
                )
                if grant.output_path != path:
                    raise ValueError("live preview output does not match authorization")
                descriptor["livePreviewId"] = live_preview_id
            presented["finalPreview"] = descriptor
        return presented

    def validate_live_preview_output(self, output: dict, path: Path) -> None:
        workspace_id = self._workspace_id(output.get("workspaceId"))
        grant = self._live_preview_grant(
            output.get("livePreviewId"),
            workspace_id=workspace_id,
        )
        if (
            output.get("kind") != "web-download"
            or output.get("fileName") != path.name
            or path != grant.output_path
        ):
            raise ValueError("web live-preview output does not match authorization")

    def release_live_preview_output(self, output: dict) -> None:
        live_preview_id = output.get("livePreviewId")
        if not _is_token(live_preview_id):
            raise ValueError("invalid live preview ID")
        workspace_id = self._workspace_id(output.get("workspaceId"))
        with self._live_preview_lock:
            grant = self._live_previews.get(live_preview_id)
            if grant is None:
                return
            if grant.workspace_id != workspace_id:
                raise ValueError("live preview workspace does not match")
            if output.get("fileName") != grant.output_path.name:
                raise ValueError("live preview output does not match authorization")
            self._live_previews.pop(live_preview_id)
        self._cleanup_live_preview_grant(grant)

    def read_live_preview(
        self,
        workspace_id: object,
        live_preview_id: object,
    ) -> bytes:
        grant = self._live_preview_grant(
            live_preview_id,
            workspace_id=workspace_id,
        )
        pdf_path = grant.output_path.with_suffix(".preview.pdf")
        try:
            content = self._read_pdf_path(pdf_path, grant.output_path.parent)
            return content
        finally:
            self.release_live_preview_output(
                {
                    "workspaceId": grant.workspace_id,
                    "fileName": grant.output_path.name,
                    "livePreviewId": live_preview_id,
                }
            )

    def read_pdf(self, workspace_id: object, file_name: object) -> bytes:
        safe_workspace_id = self._workspace_id(workspace_id)
        safe_name = self._plain_file_name(file_name)
        if not safe_name.lower().endswith(".pdf"):
            raise ValueError("web workspace artifact must be a PDF")
        workspace = self.root / safe_workspace_id
        if not workspace.is_dir():
            raise FileNotFoundError("web workspace does not exist")
        path = workspace / safe_name
        if not path.exists():
            raise FileNotFoundError("web workspace PDF does not exist")
        if path.is_symlink() or path.resolve().parent != workspace.resolve():
            raise ValueError("web workspace PDF escapes its workspace")
        if not path.is_file():
            raise FileNotFoundError("web workspace PDF does not exist")
        return self._read_pdf_path(path, workspace)

    @staticmethod
    def _read_pdf_path(path: Path, workspace: Path) -> bytes:
        if not path.exists():
            raise FileNotFoundError("web workspace PDF does not exist")
        if path.is_symlink() or path.resolve().parent != workspace.resolve():
            raise ValueError("web workspace PDF escapes its workspace")
        if not path.is_file():
            raise FileNotFoundError("web workspace PDF does not exist")
        content = path.read_bytes()
        if not content.startswith(b"%PDF-"):
            raise ValueError("web workspace artifact is not a valid PDF")
        return content


class WorkbenchCommandDispatcher:
    def __init__(
        self,
        *,
        runtime: RuntimePaths,
        inspect: InspectService = inspect_service,
        validate: ValidationService = validation_service,
        preview: PreviewService = preview_service,
        build: BuildService = build_service,
    ) -> None:
        self._runtime = runtime
        self._inspect = inspect
        self._validate = validate
        self._preview = preview
        self._build = build

    def dispatch(self, request: dict) -> dict:
        request_id = request.get("requestId")
        if not isinstance(request_id, str) or not request_id:
            request_id = "invalid-request"
        if request.get("protocol") != PROTOCOL_VERSION:
            return error_response(
                request_id,
                kind="protocol",
                message="unsupported protocol",
            )
        operation = request.get("operation")
        payload = request.get("payload")
        if not isinstance(payload, dict):
            return error_response(
                request_id,
                kind="request",
                message="payload must be an object",
            )

        try:
            if operation == "inspect":
                return success_response(
                    request_id,
                    self._inspect_result(payload),
                )
            if operation == "validate":
                return success_response(
                    request_id,
                    self._validation_result(payload),
                )
            if operation == "preview":
                return success_response(
                    request_id,
                    self._preview_result(payload),
                )
            if operation == "build":
                return success_response(
                    request_id,
                    self._build_result(payload),
                )
            if operation == "save":
                return success_response(
                    request_id,
                    self._save_result(payload),
                )
            return error_response(
                request_id,
                kind="request",
                message=f"unsupported operation: {operation}",
            )
        except ApplicationStageError as error:
            return error_response(
                request_id,
                kind="domain",
                message=str(error),
                stage=error.stage.value,
            )
        except PermissionError as error:
            return error_response(
                request_id,
                kind="permission",
                message=str(error),
            )
        except (KeyError, TypeError, ValueError) as error:
            return error_response(
                request_id,
                kind="request",
                message=str(error),
            )
        except Exception as error:  # noqa: BLE001 - exceptions cross transport boundary
            return error_response(
                request_id,
                kind="transport",
                message=str(error),
            )

    def stream_build(
        self,
        request: dict,
        emit: BuildEventSink,
        *,
        should_cancel: CancellationPredicate | None = None,
    ) -> None:
        request_id = request.get("requestId")
        if not isinstance(request_id, str) or not request_id:
            request_id = "invalid-request"
        build_id = f"build-{uuid4().hex}"
        intent = BuildIntent.PUBLISH
        source_file: str | None = None
        progressed: list[BuildStage] = []

        def progress(stage) -> None:
            progressed.append(stage)
            emit(
                {
                    "protocol": PROTOCOL_VERSION,
                    "requestId": request_id,
                    "type": "progress",
                    "stage": stage.value,
                }
            )

        try:
            if request.get("protocol") != PROTOCOL_VERSION:
                raise ValueError("unsupported protocol")
            if request.get("operation") != "build":
                raise ValueError("build stream requires a build operation")
            payload = request.get("payload")
            if not isinstance(payload, dict):
                raise TypeError("payload must be an object")
            requested_intent = payload.get("intent", BuildIntent.PUBLISH.value)
            if requested_intent in {
                BuildIntent.PUBLISH.value,
                BuildIntent.LIVE_PREVIEW.value,
            }:
                intent = BuildIntent(requested_intent)
            source = payload.get("source")
            if isinstance(source, dict):
                file_name = source.get("fileName")
                if isinstance(file_name, str) and file_name:
                    source_file = file_name
            result = self._build_result(
                payload,
                on_progress=progress,
                should_cancel=should_cancel or (lambda: False),
            )
            emit(
                {
                    "protocol": PROTOCOL_VERSION,
                    "requestId": request_id,
                    "type": "success",
                    "result": result,
                }
            )
        except Exception as error:  # noqa: BLE001 - terminal report boundary
            report = _failed_build_report(
                error,
                build_id=build_id,
                intent=intent,
                progressed=progressed,
                source_file=source_file,
            )
            emit(
                {
                    "protocol": PROTOCOL_VERSION,
                    "requestId": request_id,
                    "type": "completed",
                    "report": _serialize_build_report(report),
                }
            )

    def _source(self, payload: dict) -> tuple[dict, Path]:
        source = payload.get("source")
        if not isinstance(source, dict):
            raise TypeError("source must be an object")
        return source, self._runtime.source_path(source)

    @staticmethod
    def _template_path(payload: dict, source_path: Path) -> str | Path | None:
        template_id = payload.get("templateId")
        template_path = payload.get("templatePath")
        if template_id is not None and template_path is not None:
            raise ValueError("templateId and templatePath cannot be used together")
        if template_id is not None:
            if not isinstance(template_id, str) or not template_id:
                raise TypeError("templateId must be a non-empty string or null")
            return resolve_template(
                explicit_path=None,
                template_id=template_id,
                search_roots=default_template_search_roots(source_path),
            ).path
        if template_path is not None and not isinstance(template_path, str):
            raise TypeError("templatePath must be a string or null")
        return template_path

    def _inspect_result(self, payload: dict) -> dict:
        source, source_path = self._source(payload)
        result = self._inspect(source_path)
        outline = [
            {
                "id": block.id,
                "level": block.level,
                "text": block.text,
                "line": block.location.line,
            }
            for block in result.document.blocks
            if isinstance(block, Heading)
        ]
        return {
            "source": self._runtime.present_source(source, source_path),
            "metadata": result.document.metadata,
            "outline": outline,
            "blockCount": len(result.document.blocks),
        }

    def _validation_result(self, payload: dict) -> dict:
        source, source_path = self._source(payload)
        result = self._validate(
            source_path,
            template_path=self._template_path(payload, source_path),
        )
        return {
            "source": self._runtime.present_source(source, source_path),
            "diagnostics": [asdict(issue) for issue in result.issues],
        }

    def _preview_result(self, payload: dict) -> dict:
        source, source_path = self._source(payload)
        source_text = payload.get("text")
        if source_text is not None and not isinstance(source_text, str):
            raise TypeError("text must be a string")
        snapshot_options = (
            {"source_text": source_text}
            if source_text is not None
            else {}
        )
        result = self._preview(
            source_path,
            template_path=self._template_path(payload, source_path),
            **snapshot_options,
        )
        return {
            "source": self._runtime.present_source(source, source_path),
            "diagnostics": [asdict(issue) for issue in result.issues],
            **map_preview_result(result),
        }

    def _save_result(self, payload: dict) -> dict:
        source = payload.get("source")
        text = payload.get("text")
        if not isinstance(source, dict):
            raise TypeError("source must be an object")
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        source_path = self._runtime.save_source(source, text)
        return {
            "source": self._runtime.present_source(source, source_path),
        }

    def _build_result(
        self,
        payload: dict,
        *,
        on_progress: Callable | None = None,
        should_cancel: CancellationPredicate | None = None,
    ) -> dict:
        source, source_path = self._source(payload)
        source_text = payload.get("text")
        if source_text is not None and not isinstance(source_text, str):
            raise TypeError("text must be a string")
        intent = payload.get("intent", "publish")
        if intent not in {"publish", "live-preview"}:
            raise ValueError("intent must be publish or live-preview")
        if intent == "live-preview" and source_text is None:
            raise ValueError("live-preview requires text")
        snapshot_options = (
            {"source_text": source_text}
            if source_text is not None
            else {}
        )
        output = payload.get("output")
        if not isinstance(output, dict):
            raise TypeError("output must be an object")
        output_path = self._runtime.output_path(output)
        if intent == "live-preview":
            self._runtime.validate_live_preview_output(output, output_path)
        stages: list[str] = []
        progress = on_progress or (lambda stage: stages.append(stage.value))
        try:
            result = self._build(
                source_path,
                output_path,
                template_path=self._template_path(payload, source_path),
                on_progress=progress,
                should_cancel=should_cancel,
                **snapshot_options,
            )
            final_preview = getattr(result, "final_preview", None)
            presented_output = self._runtime.present_output(
                output,
                result.output_path,
                final_preview,
            )
            if intent == "live-preview" and final_preview is None:
                self._runtime.release_live_preview_output(output)
            return {
                "source": self._runtime.present_source(source, source_path),
                "output": presented_output,
                "diagnostics": [asdict(issue) for issue in result.issues],
                "progress": stages,
            }
        except Exception:
            if intent == "live-preview":
                self._runtime.release_live_preview_output(output)
            raise


def iter_build_events(
    dispatcher: WorkbenchCommandDispatcher,
    request: dict,
    *,
    should_cancel: CancellationPredicate | None = None,
    on_finished: Callable[[], None] | None = None,
) -> Iterator[dict]:
    queue: Queue[dict | None] = Queue()

    def run() -> None:
        try:
            dispatcher.stream_build(
                request,
                queue.put,
                should_cancel=should_cancel,
            )
        finally:
            if on_finished is not None:
                on_finished()
            queue.put(None)

    Thread(target=run, name="thesisforge-build-stream", daemon=True).start()
    while True:
        event = queue.get()
        if event is None:
            return
        yield event
