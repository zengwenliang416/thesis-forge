from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from thesis_forge.application.contracts import BuildStage
    from thesis_forge.core.model import ValidationIssue


class WorkspaceStatus(StrEnum):
    EMPTY = "empty"
    LOADING = "loading"
    POPULATED = "populated"
    DIRTY = "dirty"
    ERROR = "error"
    DISABLED = "disabled"
    PERMISSION = "permission"
    CANCELED = "canceled"


class OperationKind(StrEnum):
    INSPECT = "inspect"
    VALIDATE = "validate"
    BUILD = "build"


@dataclass(frozen=True, slots=True)
class OperationToken:
    kind: OperationKind
    generation: int


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
            message=issue.message,
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
    can_validate: bool = False
    can_build: bool = False
    can_cancel: bool = False
    can_recover: bool = False


@dataclass(frozen=True, slots=True)
class WorkspaceViewModel:
    status: WorkspaceStatus = WorkspaceStatus.EMPTY
    source_path: Path | None = None
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
