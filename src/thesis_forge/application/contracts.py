from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import ClassVar

from thesis_forge.core.model import ThesisDocument, ValidationIssue
from thesis_forge.core.render_plan import RenderPlan
from thesis_forge.core.validator import ValidationContext

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


@dataclass(frozen=True, slots=True)
class BuildSourceRange:
    file: str | None = None
    start_line: int | None = None
    start_column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    def __post_init__(self) -> None:
        for name in ("start_line", "start_column", "end_line", "end_column"):
            value = getattr(self, name)
            if value is not None and value < 1:
                raise ValueError(f"{name} must be positive when provided")
        if (
            self.start_line is not None
            and self.end_line is not None
            and self.end_line < self.start_line
        ):
            raise ValueError("end_line must not precede start_line")

    @property
    def line(self) -> int | None:
        return self.start_line


@dataclass(frozen=True, slots=True)
class BuildRelatedLocation:
    message: str
    source: BuildSourceRange


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
        if not self.id:
            raise ValueError("diagnostic id must not be empty")
        if not self.code:
            raise ValueError("diagnostic code must not be empty")
        if not self.message:
            raise ValueError("diagnostic message must not be empty")
        object.__setattr__(self, "details", dict(self.details))
        object.__setattr__(
            self,
            "related_locations",
            tuple(self.related_locations),
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
        source = (
            BuildSourceRange(
                file=source_file,
                start_line=issue.line,
                end_line=issue.line,
            )
            if issue.line is not None
            else None
        )
        return cls(
            id=f"validation-{sequence}",
            severity=BuildDiagnosticSeverity(issue.severity),
            category=BuildDiagnosticCategory.SEMANTIC,
            code=issue.code,
            stage=BuildReportStage.VALIDATE,
            message=issue.message,
            source=source,
            target=issue.target,
            details=dict(issue.details),
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
    document: ThesisDocument


@dataclass(frozen=True, slots=True)
class ValidationResult:
    document: ThesisDocument
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
    document: ThesisDocument
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
