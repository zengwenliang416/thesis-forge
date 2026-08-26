from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import ClassVar

from docforge.core.model import ForgeDocument, ValidationIssue
from docforge.core.render_plan import RenderPlan
from docforge.core.validator import ValidationContext

from .pdf_preview import PdfPreviewArtifact


class BuildStage(StrEnum):
    PARSE = "parse"
    VALIDATE = "validate"
    COMPILE = "compile"
    RENDER = "render"
    FINALIZE = "finalize"


class BuildIntent(StrEnum):
    PUBLISH = "publish"
    LIVE_PREVIEW = "live-preview"


class ProjectRequestIntent(StrEnum):
    INSPECT = "inspect"
    VALIDATE = "validate"
    REVIEW = "review"
    BUILD = "build"


@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    project_id: str
    project_root: Path
    manifest_path: Path

    @property
    def root(self) -> Path:
        return self.project_root

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id must not be blank")
        for name in ("project_root", "manifest_path"):
            value = getattr(self, name)
            if not isinstance(value, Path):
                raise TypeError(f"{name} must be a Path")
            if not value.is_absolute():
                raise ValueError(f"{name} must be absolute")


@dataclass(frozen=True, slots=True)
class ProjectOutput:
    path: Path

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("project output path must be a Path")
        if not self.path.is_absolute():
            raise ValueError("project output path must be absolute")


@dataclass(frozen=True, slots=True)
class ProjectRequest:
    project: ProjectIdentity
    intent: ProjectRequestIntent
    output: ProjectOutput | None = None
    editor_snapshot: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.project, ProjectIdentity):
            raise TypeError("project must be a ProjectIdentity")
        if not isinstance(self.intent, ProjectRequestIntent):
            raise TypeError("intent must be a ProjectRequestIntent")
        if self.output is not None and not isinstance(self.output, ProjectOutput):
            raise TypeError("output must be a ProjectOutput or None")
        if self.editor_snapshot is not None and not isinstance(self.editor_snapshot, str):
            raise TypeError("editor_snapshot must be a string or None")


class BuildOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class BuildReportStage(StrEnum):
    PARSE = "parse"
    VALIDATE = "validate"
    COMPILE = "compile"
    RENDER = "render"
    FINALIZE = "finalize"
    POSTFLIGHT = "postflight"
    PREVIEW = "preview"


class BuildStageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class BuildDiagnosticSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class BuildDiagnosticCategory(StrEnum):
    PROJECT = "project"
    SOURCE = "source"
    SEMANTIC = "semantic"
    REFERENCE = "reference"
    RESOURCE = "resource"
    TEMPLATE = "template"
    COMPILE = "compile"
    DOCX = "docx"
    OFFICE = "office"
    PERMISSION = "permission"
    TRANSPORT = "transport"
    INTERNAL = "internal"


class BuildLogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


BuildDetailValue = str | int | float | bool | None
_DUPLICATE_ID_CODE = "TF-SEMANTIC-DUPLICATE-ID"


@dataclass(frozen=True, slots=True)
class BuildSourceRange:
    file: str | None = None
    start_line: int | None = None
    start_column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        if self.file is not None and not isinstance(self.file, str):
            raise TypeError("source range file must be a string or None")
        for name in ("start_line", "start_column", "end_line", "end_column"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int)
            ):
                raise TypeError(f"{name} must be an integer or None")
            if value is not None and value < 1:
                raise ValueError(f"{name} must be positive when provided")
        if self.start_column is not None and self.start_line is None:
            raise ValueError("start_column requires start_line")
        if self.end_line is not None and self.start_line is None:
            raise ValueError("end_line requires start_line")
        if self.end_column is not None and self.end_line is None:
            raise ValueError("end_column requires end_line")
        if (
            self.start_line is not None
            and self.end_line is not None
            and self.end_line < self.start_line
        ):
            raise ValueError("end_line must not precede start_line")
        if (
            self.start_line is not None
            and self.end_line == self.start_line
            and self.start_column is not None
            and self.end_column is not None
            and self.end_column < self.start_column
        ):
            raise ValueError("end_column must not precede start_column")

    @property
    def line(self) -> int | None:
        return self.start_line


def _source_range_from_issue_details(
    details: Mapping[str, BuildDetailValue],
    *,
    prefix: str,
    fallback_file: str | None,
    fallback_line: int | None,
    force: bool = False,
) -> BuildSourceRange | None:
    location_keys = (
        f"{prefix}_file",
        f"{prefix}_line",
        f"{prefix}_column",
        f"{prefix}_end_line",
        f"{prefix}_end_column",
    )
    has_location = any(details.get(key) is not None for key in location_keys)
    if not force and not has_location and fallback_file is None and fallback_line is None:
        return None

    file_name = details.get(f"{prefix}_file")
    start_line = details.get(f"{prefix}_line")
    start_column = details.get(f"{prefix}_column")
    end_line = details.get(f"{prefix}_end_line")
    end_column = details.get(f"{prefix}_end_column")

    if file_name is None:
        file_name = fallback_file
    if start_line is None:
        start_line = fallback_line

    # BuildSourceRange intentionally rejects orphaned coordinates. Location
    # details originate in a permissive core model, so drop unusable suffixes.
    if start_line is None:
        start_column = None
        end_line = None
        end_column = None
    elif end_line is None:
        end_line = start_line
    elif end_line < start_line:
        end_line = None
        end_column = None
    elif (
        end_line == start_line
        and start_column is not None
        and end_column is not None
        and end_column < start_column
    ):
        end_column = None

    return BuildSourceRange(
        file=file_name,
        start_line=start_line,
        start_column=start_column,
        end_line=end_line,
        end_column=end_column,
    )


@dataclass(frozen=True, slots=True)
class BuildRelatedLocation:
    message: str
    source: BuildSourceRange

    def __post_init__(self) -> None:
        if not isinstance(self.message, str):
            raise TypeError("related location message must be a string")
        if not self.message:
            raise ValueError("related location message must not be empty")
        if not isinstance(self.source, BuildSourceRange):
            raise TypeError("related location source must be a BuildSourceRange")


@dataclass(frozen=True, slots=True)
class BuildStageState:
    name: BuildReportStage
    status: BuildStageStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class BuildDiagnostic:
    id: str
    severity: BuildDiagnosticSeverity
    category: BuildDiagnosticCategory
    code: str
    stage: BuildReportStage
    message: str
    source: BuildSourceRange | None = None
    target: str | None = None
    suggestion: str | None = None
    related_locations: tuple[BuildRelatedLocation, ...] = ()
    details: Mapping[str, BuildDetailValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("id", "code", "message"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"diagnostic {name} must be a string")
            if not value:
                raise ValueError(f"diagnostic {name} must not be empty")
        if not isinstance(self.severity, BuildDiagnosticSeverity):
            raise TypeError("diagnostic severity must be a BuildDiagnosticSeverity")
        if not isinstance(self.category, BuildDiagnosticCategory):
            raise TypeError("diagnostic category must be a BuildDiagnosticCategory")
        if not isinstance(self.stage, BuildReportStage):
            raise TypeError("diagnostic stage must be a BuildReportStage")
        if self.source is not None and not isinstance(self.source, BuildSourceRange):
            raise TypeError("diagnostic source must be a BuildSourceRange or None")
        for name in ("target", "suggestion"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"diagnostic {name} must be a string or None")
        related_locations = tuple(self.related_locations)
        if not all(
            isinstance(location, BuildRelatedLocation)
            for location in related_locations
        ):
            raise TypeError(
                "diagnostic related locations must be BuildRelatedLocation values"
            )
        if not isinstance(self.details, Mapping):
            raise TypeError("diagnostic details must be a mapping")
        details = dict(self.details)
        for key, value in details.items():
            if not isinstance(key, str):
                raise TypeError("diagnostic detail keys must be strings")
            if value is None or isinstance(value, (bool, int, str)):
                continue
            if isinstance(value, float) and math.isfinite(value):
                continue
            raise ValueError(
                f"diagnostic detail {key!r} must be a finite scalar"
            )
        object.__setattr__(self, "details", details)
        object.__setattr__(
            self,
            "related_locations",
            related_locations,
        )

    @property
    def line(self) -> int | None:
        return self.source.line if self.source is not None else None

    @classmethod
    def from_validation_issue(
        cls,
        issue: ValidationIssue,
        *,
        sequence: int,
        source_file: str | None = None,
    ) -> BuildDiagnostic:
        if sequence < 1:
            raise ValueError("diagnostic sequence must be positive")
        is_duplicate = issue.code == "duplicate-id"
        details = dict(issue.details)
        if is_duplicate:
            source = _source_range_from_issue_details(
                details,
                prefix="source",
                fallback_file=source_file,
                fallback_line=issue.line,
                force=True,
            )
            related_source = _source_range_from_issue_details(
                details,
                prefix="related",
                fallback_file=source_file,
                fallback_line=None,
                force=True,
            )
            related_locations = (
                BuildRelatedLocation(
                    message=str(
                        details.get(
                            "related_message",
                            f"首次定义：{issue.target or ''}",
                        )
                    ),
                    source=related_source,
                ),
            )
        else:
            source = (
                BuildSourceRange(
                    file=source_file,
                    start_line=issue.line,
                    end_line=issue.line,
                )
                if issue.line is not None
                else None
            )
            related_locations = ()
        return cls(
            id=f"validation-{sequence}",
            severity=BuildDiagnosticSeverity(issue.severity),
            category=BuildDiagnosticCategory.SEMANTIC,
            code=_DUPLICATE_ID_CODE if is_duplicate else issue.code,
            stage=BuildReportStage.VALIDATE,
            message=issue.message,
            source=source,
            target=issue.target,
            related_locations=related_locations,
            details=details,
        )


@dataclass(frozen=True, slots=True)
class BuildLogEntry:
    sequence: int
    stage: BuildReportStage
    level: BuildLogLevel
    message: str

    MAX_MESSAGE_LENGTH: ClassVar[int] = 4_000

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("log sequence must not be negative")
        if len(self.message) > self.MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"log message must be at most {self.MAX_MESSAGE_LENGTH} characters"
            )


@dataclass(frozen=True, slots=True)
class BuildOutput:
    docx_path: Path | None = None
    pdf_path: Path | None = None
    preview_stale: bool = False
    successful_build_id: str | None = None


@dataclass(frozen=True, slots=True)
class BuildReport:
    schema_version: str
    build_id: str
    intent: BuildIntent
    outcome: BuildOutcome
    stages: tuple[BuildStageState, ...]
    failed_stage: BuildReportStage | None
    primary_diagnostic_id: str | None
    diagnostics: tuple[BuildDiagnostic, ...]
    logs: tuple[BuildLogEntry, ...]
    output: BuildOutput | None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    SCHEMA_VERSION: ClassVar[str] = "thesisforge.build-report.v2"
    MAX_LOG_ENTRIES: ClassVar[int] = 500

    def __post_init__(self) -> None:
        if self.schema_version != self.SCHEMA_VERSION:
            raise ValueError(f"unsupported BuildReport schema: {self.schema_version}")
        if not self.build_id:
            raise ValueError("build id must not be empty")

        stages = tuple(self.stages)
        stage_names = tuple(stage.name for stage in stages)
        if not stages:
            raise ValueError("BuildReport must contain at least one stage")
        if len(set(stage_names)) != len(stage_names):
            raise ValueError("BuildReport stages must have unique names")
        if self.failed_stage is not None and self.failed_stage not in stage_names:
            raise ValueError("failed_stage must refer to a reported stage")
        object.__setattr__(self, "stages", stages)

        diagnostics = tuple(self.diagnostics)
        diagnostic_ids = tuple(diagnostic.id for diagnostic in diagnostics)
        if len(set(diagnostic_ids)) != len(diagnostic_ids):
            raise ValueError("BuildReport diagnostic ids must be unique")
        if (
            self.primary_diagnostic_id is not None
            and self.primary_diagnostic_id not in diagnostic_ids
        ):
            raise ValueError("primary_diagnostic_id must refer to a diagnostic")
        object.__setattr__(self, "diagnostics", diagnostics)

        logs = tuple(self.logs)
        if len(logs) > self.MAX_LOG_ENTRIES:
            raise ValueError(
                f"BuildReport logs must contain at most {self.MAX_LOG_ENTRIES} entries"
            )
        sequences = tuple(log.sequence for log in logs)
        if sequences != tuple(sorted(sequences)):
            raise ValueError("BuildReport logs must be ordered by sequence")
        object.__setattr__(self, "logs", logs)

    @classmethod
    def from_validation_error(
        cls,
        error: BuildValidationError,
        *,
        build_id: str,
        intent: BuildIntent | str,
        source_file: str | None = None,
        stages: tuple[BuildStageState, ...] | None = None,
        logs: tuple[BuildLogEntry, ...] = (),
        output: BuildOutput | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> BuildReport:
        diagnostics = tuple(
            BuildDiagnostic.from_validation_issue(
                issue,
                sequence=sequence,
                source_file=source_file,
            )
            for sequence, issue in enumerate(error.issues, start=1)
        )
        primary = next(
            (
                diagnostic.id
                for diagnostic in diagnostics
                if diagnostic.severity is BuildDiagnosticSeverity.ERROR
            ),
            None,
        )
        return cls(
            schema_version=cls.SCHEMA_VERSION,
            build_id=build_id,
            intent=BuildIntent(intent),
            outcome=BuildOutcome.FAILED,
            stages=stages
            or cls.default_stages(
                failed_stage=BuildReportStage.VALIDATE,
                outcome=BuildOutcome.FAILED,
            ),
            failed_stage=BuildReportStage.VALIDATE,
            primary_diagnostic_id=primary,
            diagnostics=diagnostics,
            logs=logs,
            output=output,
            started_at=started_at,
            completed_at=completed_at,
        )

    @classmethod
    def from_stage_error(
        cls,
        error: ApplicationStageError,
        *,
        build_id: str,
        intent: BuildIntent | str,
        stages: tuple[BuildStageState, ...] | None = None,
        logs: tuple[BuildLogEntry, ...] = (),
        output: BuildOutput | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> BuildReport:
        if isinstance(error, BuildValidationError):
            return cls.from_validation_error(
                error,
                build_id=build_id,
                intent=intent,
                stages=stages,
                logs=logs,
                output=output,
                started_at=started_at,
                completed_at=completed_at,
            )

        stage = BuildReportStage(error.stage.value)
        canceled = isinstance(error, BuildCanceledError)
        cause = error.cause
        category = (
            BuildDiagnosticCategory.PERMISSION
            if isinstance(cause, PermissionError)
            else BuildDiagnosticCategory.INTERNAL
        )
        code = (
            "TF-BUILD-CANCELED"
            if canceled
            else "TF-PERMISSION-DENIED"
            if category is BuildDiagnosticCategory.PERMISSION
            else f"TF-BUILD-{stage.value.upper()}-FAILED"
        )
        diagnostic = BuildDiagnostic(
            id="build-error-1",
            severity=BuildDiagnosticSeverity.ERROR,
            category=category,
            code=code,
            stage=stage,
            message=str(cause),
            details={"exception": type(cause).__name__},
        )
        outcome = BuildOutcome.CANCELED if canceled else BuildOutcome.FAILED
        return cls(
            schema_version=cls.SCHEMA_VERSION,
            build_id=build_id,
            intent=BuildIntent(intent),
            outcome=outcome,
            stages=stages
            or cls.default_stages(
                failed_stage=stage,
                outcome=outcome,
            ),
            failed_stage=stage,
            primary_diagnostic_id=diagnostic.id,
            diagnostics=(diagnostic,),
            logs=logs,
            output=output,
            started_at=started_at,
            completed_at=completed_at,
        )

    @classmethod
    def from_permission_error(
        cls,
        error: PermissionError,
        *,
        build_id: str,
        intent: BuildIntent | str,
        stage: BuildReportStage | BuildStage | str = BuildReportStage.FINALIZE,
        stages: tuple[BuildStageState, ...] | None = None,
        logs: tuple[BuildLogEntry, ...] = (),
        output: BuildOutput | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> BuildReport:
        report_stage = BuildReportStage(stage.value if isinstance(stage, StrEnum) else stage)
        diagnostic = BuildDiagnostic(
            id="permission-error-1",
            severity=BuildDiagnosticSeverity.ERROR,
            category=BuildDiagnosticCategory.PERMISSION,
            code="TF-PERMISSION-DENIED",
            stage=report_stage,
            message=str(error),
            details={"exception": type(error).__name__},
        )
        return cls(
            schema_version=cls.SCHEMA_VERSION,
            build_id=build_id,
            intent=BuildIntent(intent),
            outcome=BuildOutcome.FAILED,
            stages=stages
            or cls.default_stages(
                failed_stage=report_stage,
                outcome=BuildOutcome.FAILED,
            ),
            failed_stage=report_stage,
            primary_diagnostic_id=diagnostic.id,
            diagnostics=(diagnostic,),
            logs=logs,
            output=output,
            started_at=started_at,
            completed_at=completed_at,
        )

    @classmethod
    def from_error(
        cls,
        error: Exception,
        *,
        build_id: str,
        intent: BuildIntent | str,
        stage: BuildReportStage | BuildStage | str = BuildReportStage.FINALIZE,
        **kwargs,
    ) -> BuildReport:
        if isinstance(error, BuildValidationError):
            return cls.from_validation_error(
                error,
                build_id=build_id,
                intent=intent,
                **kwargs,
            )
        if isinstance(error, ApplicationStageError):
            return cls.from_stage_error(
                error,
                build_id=build_id,
                intent=intent,
                **kwargs,
            )
        if isinstance(error, PermissionError):
            return cls.from_permission_error(
                error,
                build_id=build_id,
                intent=intent,
                stage=stage,
                **kwargs,
            )
        raise TypeError(f"unsupported build error: {type(error).__name__}")

    @classmethod
    def default_stages(
        cls,
        *,
        failed_stage: BuildReportStage | None,
        outcome: BuildOutcome,
    ) -> tuple[BuildStageState, ...]:
        failed_index = (
            tuple(BuildReportStage).index(failed_stage)
            if failed_stage is not None
            else None
        )
        states: list[BuildStageState] = []
        for index, stage in enumerate(BuildReportStage):
            if failed_index is None:
                status = (
                    BuildStageStatus.SUCCEEDED
                    if outcome is BuildOutcome.SUCCEEDED
                    else BuildStageStatus.SKIPPED
                )
            elif index < failed_index:
                status = BuildStageStatus.SUCCEEDED
            elif index == failed_index:
                status = (
                    BuildStageStatus.SKIPPED
                    if outcome is BuildOutcome.CANCELED
                    else BuildStageStatus.FAILED
                )
            else:
                status = BuildStageStatus.SKIPPED
            states.append(BuildStageState(name=stage, status=status))
        return tuple(states)


@dataclass(frozen=True, slots=True)
class InspectionResult:
    document: ForgeDocument


@dataclass(frozen=True, slots=True)
class ValidationResult:
    document: ForgeDocument
    context: ValidationContext
    issues: tuple[ValidationIssue, ...]

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")


@dataclass(frozen=True, slots=True)
class BuildResult:
    output_path: Path
    issues: tuple[ValidationIssue, ...]
    final_preview: PdfPreviewArtifact | None = None


@dataclass(frozen=True, slots=True)
class PreviewResult:
    document: ForgeDocument
    context: ValidationContext
    issues: tuple[ValidationIssue, ...]
    plan: RenderPlan | None

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity == "error")


class ApplicationStageError(RuntimeError):
    def __init__(self, stage: BuildStage, cause: Exception):
        self.stage = stage
        self.cause = cause
        super().__init__(str(cause))


class BuildValidationError(ApplicationStageError):
    def __init__(self, issues: tuple[ValidationIssue, ...]):
        self.issues = issues
        error_count = sum(issue.severity == "error" for issue in issues)
        super().__init__(
            BuildStage.VALIDATE,
            ValueError(f"存在 {error_count} 个验证错误"),
        )

    def to_report(
        self,
        *,
        build_id: str,
        intent: BuildIntent | str,
        **kwargs,
    ) -> BuildReport:
        return BuildReport.from_validation_error(
            self,
            build_id=build_id,
            intent=intent,
            **kwargs,
        )


class BuildCanceledError(ApplicationStageError):
    def __init__(self, stage: BuildStage):
        super().__init__(stage, RuntimeError("构建已取消"))
