from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from docforge.presentation import localized_issue_message

if TYPE_CHECKING:
    from docforge.application.contracts import BuildStage
    from docforge.core.model import ValidationIssue


class WorkspaceStatus(StrEnum):
    EMPTY = "empty"
    LOADING = "loading"
    POPULATED = "populated"
    DIRTY = "dirty"
    ERROR = "error"
    DISABLED = "disabled"
    PERMISSION = "permission"
    CANCELED = "canceled"


class WorkspaceSourceKind(StrEnum):
    DESKTOP = "desktop"
    WEB_WORKSPACE = "web-workspace"
    WEB_UPLOAD = "web-upload"


class OperationKind(StrEnum):
    OPEN = "open"
    INSPECT = "inspect"
    REFRESH = "refresh"
    SAVE = "save"
    DOWNLOAD = "download"
    VALIDATE = "validate"
    BUILD = "build"


@dataclass(frozen=True, slots=True)
class OperationToken:
    kind: OperationKind
    generation: int


@dataclass(frozen=True, slots=True)
class WebSourceHandle:
    file_name: str
    workspace_id: str | None = None
    writable: bool = False

    def __post_init__(self) -> None:
        if (
            not self.file_name
            or Path(self.file_name).name != self.file_name
            or "\\" in self.file_name
        ):
            raise ValueError("web source file_name must be a plain file name")
        if self.workspace_id is not None and not self.workspace_id.strip():
            raise ValueError("web workspace_id must not be blank")
        if self.writable and self.workspace_id is None:
            raise ValueError("writable web source requires a workspace_id")


@dataclass(frozen=True, slots=True)
class DiagnosticViewModel:
    severity: str
    code: str
    message: str
    line: int | None = None
    target: str | None = None
    details: tuple[tuple[str, str | int], ...] = ()

    @classmethod
    def from_issue(cls, issue: ValidationIssue) -> DiagnosticViewModel:
        return cls(
            severity=issue.severity,
            code=issue.code,
            message=localized_issue_message(issue),
            line=issue.line,
            target=issue.target,
            details=tuple(sorted(issue.details.items())),
        )


@dataclass(frozen=True, slots=True)
class ProgressViewModel:
    operation: OperationToken
    stage: BuildStage | None = None


@dataclass(frozen=True, slots=True)
class OutputViewModel:
    path: Path
    diagnostics: tuple[DiagnosticViewModel, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkspaceActions:
    can_open: bool = True
    can_edit: bool = False
    can_save: bool = False
    can_save_as: bool = False
    can_download: bool = False
    can_validate: bool = False
    can_build: bool = False
    can_cancel: bool = False
    can_recover: bool = False


@dataclass(frozen=True, slots=True)
class WorkspaceViewModel:
    status: WorkspaceStatus = WorkspaceStatus.EMPTY
    source_path: Path | None = None
    source_kind: WorkspaceSourceKind | None = None
    source_name: str | None = None
    web_source: WebSourceHandle | None = None
    template_path: Path | None = None
    saved_text: str = ""
    editor_text: str = ""
    dirty: bool = False
    diagnostics: tuple[DiagnosticViewModel, ...] = ()
    progress: ProgressViewModel | None = None
    output: OutputViewModel | None = None
    error_message: str | None = None
    disabled_reason: str | None = None
    active_operation: OperationToken | None = None
    actions: WorkspaceActions = WorkspaceActions()
