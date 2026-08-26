from __future__ import annotations

import re
import shutil
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, replace
from pathlib import Path, PurePosixPath
from queue import Queue
from threading import Lock, Thread
from time import monotonic, time
from typing import Protocol
from urllib.parse import urlsplit
from uuid import uuid4

from docforge.application import (
    ApplicationDependencies,
    ApplicationStageError,
    BuildCanceledError,
    BuildResult,
    BuildValidationError,
    InspectionResult,
    LibreOfficePdfPreviewExporter,
    MicrosoftWordPdfPreviewExporter,
    PreviewResult,
    ValidationResult,
    build_service,
    inspect_service,
    preview_service,
    validation_service,
)
from docforge.application.contracts import (
    BuildDiagnostic,
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
    ProjectIdentity,
    ProjectOutput,
    ProjectRequest,
    ProjectRequestIntent,
)
from docforge.application.services import (
    BuildStageLifecycle,
    ProjectApplicationService,
)
from docforge.core.model import Heading, ValidationIssue, inline_plain_text
from docforge.presentation.preview import map_preview_result
from docforge.project.loader import load_project
from docforge.project.model import ProjectRelativePath
from docforge.project.paths import resolve_project_paths
from docforge.templates import default_template_search_roots, resolve_template
from docforge.ui.filesystem import LocalWorkspaceFileSystem

from .dto import (
    PROTOCOL_VERSION,
    error_response,
    sanitize_build_report_text,
    serialize_build_report,
    success_response,
)

InspectService = Callable[..., InspectionResult]
ValidationService = Callable[..., ValidationResult]
BuildService = Callable[..., BuildResult]
PreviewService = Callable[..., PreviewResult]
BuildEventSink = Callable[[dict], None]
CancellationPredicate = Callable[[], bool]
LIVE_PREVIEW_STEM_RE = re.compile(
    r"^\.?thesisforge-live-preview-[0-9a-f]{32}$"
)
BUILD_REPORT_CODE_RE = re.compile(r"^TF-[A-Z0-9-]+$")
_serialize_build_report = serialize_build_report


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


def desktop_application_dependencies() -> ApplicationDependencies:
    return ApplicationDependencies(
        pdf_preview_exporter=MicrosoftWordPdfPreviewExporter(),
    )


def desktop_final_preview_build_service(
    source: str | Path,
    output: str | Path,
    **kwargs,
) -> BuildResult:
    return build_service(
        source,
        output,
        dependencies=desktop_application_dependencies(),
        **kwargs,
    )


class RuntimePaths(Protocol):
    def source_path(self, source: dict) -> Path: ...

    def project_identity(self, source: dict, project: object) -> ProjectIdentity: ...

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
        message = (
            "Build failed because output permission was denied: "
            f"{sanitize_build_report_text(str(error))}"
        )
    else:
        message = (
            f"Build failed during {stage.value}: "
            f"{sanitize_build_report_text(str(error))}"
        )
    return (
        BuildLogEntry(
            sequence=0,
            stage=stage,
            level=BuildLogLevel.ERROR,
            message=message[: BuildLogEntry.MAX_MESSAGE_LENGTH],
        ),
    )


def _transport_build_report(
    error: Exception,
    *,
    build_id: str,
    intent: BuildIntent,
    stage: BuildReportStage,
    stages: tuple[BuildStageState, ...],
    logs: tuple[BuildLogEntry, ...],
) -> BuildReport:
    item = BuildDiagnostic(
        id="transport-error-1",
        severity=BuildDiagnosticSeverity.ERROR,
        category=BuildDiagnosticCategory.TRANSPORT,
        code="TF-TRANSPORT-BUILD-FAILED",
        stage=stage,
        message=sanitize_build_report_text(str(error)),
        details={"exception": type(error).__name__},
    )
    return BuildReport(
        schema_version=BuildReport.SCHEMA_VERSION,
        build_id=build_id,
        intent=intent,
        outcome=BuildOutcome.FAILED,
        stages=stages,
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
    lifecycle: BuildStageLifecycle,
    source_file: str | None,
) -> BuildReport:
    stage = _build_report_stage(error, progressed)
    logs = _build_report_logs(error, stage)
    outcome = (
        BuildOutcome.CANCELED
        if isinstance(error, BuildCanceledError)
        else BuildOutcome.FAILED
    )
    report_stage = BuildReportStage(stage.value)
    target_index = tuple(BuildReportStage).index(report_stage)
    for upstream in tuple(BuildReportStage)[:target_index]:
        if lifecycle.state(upstream).status is BuildStageStatus.RUNNING:
            lifecycle.succeed(upstream)
    if lifecycle.state(report_stage).status is BuildStageStatus.PENDING:
        lifecycle.start(report_stage)
    stages = lifecycle.terminalize(
        report_stage,
        canceled=outcome is BuildOutcome.CANCELED,
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
        stages=stages,
        logs=logs,
    )


def _plain_file_name(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value in {".", ".."}
        or Path(value).name != value
        or "/" in value
        or "\\" in value
    ):
        raise ValueError(f"{label} must be a plain file name")
    return value


def _canonical_build_report_code(code: str) -> str:
    if BUILD_REPORT_CODE_RE.fullmatch(code):
        return code
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", code).strip("-").upper()
    normalized = normalized.removeprefix("TF-")
    if not normalized:
        raise ValueError("build result diagnostic code is required")
    return f"TF-VALIDATION-{normalized}"


def _successful_build_stages(
    progressed: tuple[BuildStage, ...],
    *,
    has_final_preview: bool,
) -> tuple[BuildStageState, ...]:
    succeeded = {BuildReportStage(stage.value) for stage in progressed}
    if has_final_preview:
        succeeded.add(BuildReportStage.PREVIEW)
    return tuple(
        BuildStageState(
            name=stage,
            status=(
                BuildStageStatus.SUCCEEDED
                if stage in succeeded
                else BuildStageStatus.SKIPPED
            ),
        )
        for stage in BuildReportStage
    )


def _build_report_diagnostic(
    item: dict,
    *,
    sequence: int,
    source_file: str | None,
) -> BuildDiagnostic:
    diagnostic = BuildDiagnostic.from_validation_issue(
        ValidationIssue(
            code=item["code"],
            severity=item["severity"],
            message=item["message"],
            line=item.get("line"),
            target=item.get("target"),
            details=item.get("details", {}),
        ),
        sequence=sequence,
        source_file=source_file,
    )
    return replace(
        diagnostic,
        code=_canonical_build_report_code(diagnostic.code),
    )


def _serialize_success_build_report(
    result: dict,
    *,
    build_id: str,
    intent: BuildIntent,
    source_file: str | None,
    progressed: tuple[BuildStage, ...],
) -> dict:
    output = result.get("output")
    if not isinstance(output, dict):
        raise TypeError("build result output must be an object")
    output_name = _plain_file_name(
        output.get("name"),
        label="build result output name",
    )

    final_preview = output.get("finalPreview")
    if final_preview is not None and not isinstance(final_preview, dict):
        raise TypeError("build result final preview must be an object")
    preview_name = (
        _plain_file_name(
            final_preview.get("fileName"),
            label="build result final preview file name",
        )
        if final_preview is not None
        else None
    )
    if preview_name is not None and not preview_name.lower().endswith(".pdf"):
        raise ValueError("build result final preview file name must be a PDF")

    diagnostics = tuple(
        _build_report_diagnostic(
            item,
            sequence=sequence,
            source_file=source_file,
        )
        for sequence, item in enumerate(result.get("diagnostics", ()), start=1)
    )
    primary = next(
        (
            diagnostic.id
            for diagnostic in diagnostics
            if diagnostic.severity is BuildDiagnosticSeverity.ERROR
        ),
        None,
    )
    report = BuildReport(
        schema_version=BuildReport.SCHEMA_VERSION,
        build_id=build_id,
        intent=intent,
        outcome=BuildOutcome.SUCCEEDED,
        stages=_successful_build_stages(
            progressed,
            has_final_preview=final_preview is not None,
        ),
        failed_stage=None,
        primary_diagnostic_id=primary,
        diagnostics=diagnostics,
        logs=(),
        output=BuildOutput(
            docx_path=Path(output_name),
            pdf_path=Path(preview_name) if preview_name is not None else None,
            preview_stale=False,
            successful_build_id=build_id,
        ),
    )
    serialized = serialize_build_report(report)
    if final_preview is not None:
        serialized_output = serialized.get("output")
        if not isinstance(serialized_output, dict):
            raise ValueError("successful build report output is missing")
        serialized_output["finalPreview"] = final_preview
    return serialized


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

    def project_identity(self, source: dict, project: object) -> ProjectIdentity:
        return _project_identity_from_payload(project)

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


def _project_identity_from_payload(project: object) -> ProjectIdentity:
    if not isinstance(project, dict):
        raise TypeError("project must be an object")
    if set(project) != {"id", "root", "manifestPath"}:
        raise ValueError("project identity must contain only id, root and manifestPath")
    project_id = project.get("id")
    project_root = project.get("root")
    manifest_path = project.get("manifestPath")
    if not isinstance(project_id, str):
        raise TypeError("project.id must be a string")
    if not isinstance(project_root, str):
        raise TypeError("project.root must be a string")
    if not isinstance(manifest_path, str):
        raise TypeError("project.manifestPath must be a string")
    return ProjectIdentity(
        project_id=project_id,
        project_root=Path(project_root),
        manifest_path=Path(manifest_path),
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

    @staticmethod
    def _relative_file_name(file_name: object) -> str:
        if not isinstance(file_name, str) or not file_name.strip():
            raise ValueError("web workspace fileName must be a project-relative file path")
        normalized = file_name.strip().replace("\\", "/")
        if urlsplit(normalized).scheme:
            raise ValueError("web workspace fileName must be a project-relative file path")
        try:
            relative = ProjectRelativePath.model_validate(normalized).root
        except (TypeError, ValueError) as error:
            raise ValueError(
                "web workspace fileName must be a project-relative file path"
            ) from error
        if relative == ".":
            raise ValueError("web workspace fileName must identify a file")
        return PurePosixPath(relative).as_posix()

    def _workspace_directory(self, workspace_id: object) -> Path:
        safe_workspace_id = self._workspace_id(workspace_id)
        workspace = self.root / safe_workspace_id
        if workspace.is_symlink() or not workspace.is_dir():
            raise ValueError("web workspace does not exist")
        return workspace

    @staticmethod
    def _opaque_project_snapshot(workspace_id: str, project_id: str) -> dict:
        root = Path("/thesisforge-web") / workspace_id
        return {
            "id": project_id,
            "root": str(root),
            "manifestPath": str(root / "thesisforge.yaml"),
        }

    def _write_workspace_file(
        self,
        workspace: Path,
        file_name: str,
        text: str,
    ) -> Path:
        path = workspace / file_name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._filesystem.write_text_atomic(path, text)
        return path

    def create_project_workspace(
        self,
        manifest: object,
        source: object,
    ) -> dict:
        if not isinstance(manifest, dict) or set(manifest) != {"fileName", "text"}:
            raise TypeError("manifest must contain only fileName and text")
        if not isinstance(source, dict) or set(source) != {"fileName", "text"}:
            raise TypeError("source must contain only fileName and text")

        manifest_name = manifest.get("fileName")
        manifest_text = manifest.get("text")
        source_name = self._relative_file_name(source.get("fileName"))
        source_text = source.get("text")
        if manifest_name != "thesisforge.yaml":
            raise ValueError("manifest fileName must be thesisforge.yaml")
        if not isinstance(manifest_text, str):
            raise TypeError("manifest.text must be a string")
        if not isinstance(source_text, str):
            raise TypeError("source.text must be a string")
        if source_name == manifest_name or not source_name.lower().endswith(".md"):
            raise ValueError("source.fileName must identify a Markdown source")

        workspace_id = uuid4().hex
        workspace = self.root / workspace_id
        workspace.mkdir(mode=0o700)
        try:
            self._write_workspace_file(workspace, manifest_name, manifest_text)
            self._write_workspace_file(workspace, source_name, source_text)
            loaded = load_project(workspace)
            resolve_project_paths(loaded)
            declared_source = self._relative_file_name(
                loaded.manifest.document.source.root
            )
            if declared_source != source_name:
                raise ValueError(
                    "uploaded source does not match manifest document.source"
                )
        except Exception:
            shutil.rmtree(workspace, ignore_errors=True)
            raise

        return {
            "project": self._opaque_project_snapshot(
                workspace_id,
                loaded.manifest.project.id,
            ),
            "source": {
                "kind": "web-workspace",
                "workspaceId": workspace_id,
                "fileName": source_name,
            },
            "text": source_text,
        }

    def project_identity(self, source: dict, project: object) -> ProjectIdentity:
        if source.get("kind") != "web-workspace":
            raise ValueError("manifest-backed Web projects require a web workspace")
        requested = _project_identity_from_payload(project)
        workspace_id = self._workspace_id(source.get("workspaceId"))
        workspace = self._workspace_directory(workspace_id)
        loaded = load_project(workspace)
        resolve_project_paths(loaded)
        source_path = self.source_path(source)
        expected = self._opaque_project_snapshot(
            workspace_id,
            loaded.manifest.project.id,
        )
        if (
            requested.project_id != expected["id"]
            or str(requested.project_root) != expected["root"]
            or str(requested.manifest_path) != expected["manifestPath"]
            or source_path.resolve() != loaded.source_path.resolve()
        ):
            raise ValueError("Web project identity does not match workspace manifest")
        return ProjectIdentity(
            project_id=loaded.manifest.project.id,
            project_root=loaded.project_root,
            manifest_path=loaded.manifest_path,
        )

    def create_workspace(self, file_name: str, text: str) -> dict:
        """Allocate a raw source workspace for non-project artifact tests."""
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
        if source.get("kind") != "web-workspace":
            raise ValueError("web workspace source is required")
        workspace = self._workspace_directory(source.get("workspaceId"))
        file_name = self._relative_file_name(source.get("fileName"))
        path = workspace / file_name
        try:
            path.resolve().relative_to(workspace.resolve())
        except ValueError as error:
            raise ValueError("web workspace source escapes its workspace") from error
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
        project_service: ProjectApplicationService | None = None,
    ) -> None:
        self._runtime = runtime
        self._inspect = inspect
        self._validate = validate
        self._preview = preview
        self._build = build
        self._project_service = project_service or ProjectApplicationService()

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
        lifecycle = BuildStageLifecycle()
        active_stage: BuildStage | None = None

        def progress(stage) -> None:
            nonlocal active_stage
            if active_stage is not None:
                lifecycle.succeed(active_stage)
            lifecycle.start(stage)
            active_stage = stage
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
                    "type": "completed",
                    "report": _serialize_success_build_report(
                        result,
                        build_id=build_id,
                        intent=intent,
                        source_file=source_file,
                        progressed=tuple(progressed),
                    ),
                }
            )
        except Exception as error:  # noqa: BLE001 - terminal report boundary
            report = _failed_build_report(
                error,
                build_id=build_id,
                intent=intent,
                progressed=progressed,
                lifecycle=lifecycle,
                source_file=source_file,
            )
            emit(
                {
                    "protocol": PROTOCOL_VERSION,
                    "requestId": request_id,
                    "type": "completed",
                    "report": serialize_build_report(report),
                }
            )

    def _source(self, payload: dict) -> tuple[dict, Path]:
        source = payload.get("source")
        if not isinstance(source, dict):
            raise TypeError("source must be an object")
        return source, self._runtime.source_path(source)

    def _project_request(
        self,
        payload: dict,
        intent: ProjectRequestIntent,
        *,
        output_path: Path | None = None,
    ) -> ProjectRequest:
        project = payload.get("project")
        source = payload.get("source")
        if not isinstance(source, dict):
            raise TypeError("project source is required")
        if source.get("kind") == "web-workspace":
            project_identity = self._runtime.project_identity(source, project)
        elif source.get("kind") == "desktop":
            project_identity = _project_identity_from_payload(project)
        else:
            raise ValueError("project source must be a desktop or web workspace")
        text = payload.get("text")
        if text is not None and not isinstance(text, str):
            raise TypeError("text must be a string")
        return ProjectRequest(
            project=project_identity,
            intent=intent,
            output=ProjectOutput(output_path) if output_path is not None else None,
            editor_snapshot=text,
        )

    def _project_source(self, payload: dict, path: Path) -> dict:
        source = payload.get("source")
        if not isinstance(source, dict):
            source = {"kind": "desktop", "fileName": path.name}
        return self._runtime.present_source(source, path)

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
        if "project" in payload:
            result = self._project_service.inspect(
                self._project_request(payload, ProjectRequestIntent.INSPECT)
            )
            return {
                "source": self._project_source(payload, result.document.source_path),
                "metadata": result.document.metadata,
                "outline": [
                    {
                        "id": block.id,
                        "level": block.level,
                        "text": inline_plain_text(block.inlines),
                        "line": block.location.line,
                    }
                    for block in result.document.blocks
                    if isinstance(block, Heading)
                ],
                "blockCount": len(result.document.blocks),
            }
        source, source_path = self._source(payload)
        result = self._inspect(source_path)
        outline = [
            {
                "id": block.id,
                "level": block.level,
                "text": inline_plain_text(block.inlines),
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
        if "project" in payload:
            result = self._project_service.validate(
                self._project_request(payload, ProjectRequestIntent.VALIDATE)
            )
            return {
                "source": self._project_source(payload, result.document.source_path),
                "diagnostics": [asdict(issue) for issue in result.issues],
            }
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
        if "project" in payload:
            result = self._project_service.preview(
                self._project_request(payload, ProjectRequestIntent.REVIEW)
            )
            return {
                "source": self._project_source(payload, result.document.source_path),
                "diagnostics": [asdict(issue) for issue in result.issues],
                **map_preview_result(result),
            }
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
        if "project" in payload:
            return self._project_build_result(
                payload,
                on_progress=on_progress,
                should_cancel=should_cancel,
            )
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

    def _project_build_result(
        self,
        payload: dict,
        *,
        on_progress: Callable | None = None,
        should_cancel: CancellationPredicate | None = None,
    ) -> dict:
        source = payload.get("source")
        if not isinstance(source, dict):
            raise TypeError("source must be an object")
        source_path = self._runtime.source_path(source)
        source_text = payload.get("text")
        if source_text is not None and not isinstance(source_text, str):
            raise TypeError("text must be a string")
        intent = payload.get("intent", BuildIntent.PUBLISH.value)
        if intent not in {BuildIntent.PUBLISH.value, BuildIntent.LIVE_PREVIEW.value}:
            raise ValueError("intent must be publish or live-preview")
        if intent == BuildIntent.LIVE_PREVIEW.value and source_text is None:
            raise ValueError("live-preview requires text")
        output = payload.get("output")
        if not isinstance(output, dict):
            raise TypeError("output must be an object")
        output_path = self._runtime.output_path(output)
        if intent == BuildIntent.LIVE_PREVIEW.value:
            self._runtime.validate_live_preview_output(output, output_path)
        stages: list[str] = []
        progress = on_progress or (lambda stage: stages.append(stage.value))
        try:
            result = self._project_service.build(
                self._project_request(
                    payload,
                    ProjectRequestIntent.BUILD,
                    output_path=output_path,
                ),
                on_progress=progress,
                should_cancel=should_cancel,
            )
            final_preview = getattr(result, "final_preview", None)
            presented_output = self._runtime.present_output(
                output,
                result.output_path,
                final_preview,
            )
            return {
                "source": self._project_source(payload, source_path),
                "output": presented_output,
                "diagnostics": [asdict(issue) for issue in result.issues],
                "progress": stages,
            }
        except Exception:
            if intent == BuildIntent.LIVE_PREVIEW.value:
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
