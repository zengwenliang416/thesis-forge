from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from thesis_forge.core.model import ThesisDocument, ValidationIssue
from thesis_forge.core.render_plan import RenderPlan
from thesis_forge.core.validator import ValidationContext


class BuildStage(StrEnum):
    PARSE = "parse"
    VALIDATE = "validate"
    COMPILE = "compile"
    RENDER = "render"
    FINALIZE = "finalize"


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
