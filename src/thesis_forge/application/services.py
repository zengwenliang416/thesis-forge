from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import ThesisDocument, ValidationIssue
from thesis_forge.core.parser import parse_markdown
from thesis_forge.core.render_plan import RenderPlan
from thesis_forge.core.validator import ValidationContext, validate_document
from thesis_forge.renderers.docx import DocxRenderer
from thesis_forge.renderers.docx.package import validate_docx_package

from .contracts import (
    ApplicationStageError,
    BuildResult,
    BuildStage,
    BuildValidationError,
    InspectionResult,
    PreviewResult,
    ValidationResult,
)
from .output import ReplaceFile, replace_output, temporary_output_path

Parser = Callable[[str | Path], ThesisDocument]
ContextFactory = Callable[[ThesisDocument, str | Path | None], ValidationContext]
Validator = Callable[[ThesisDocument, ValidationContext], list[ValidationIssue]]
Compiler = Callable[..., RenderPlan]
PackageValidator = Callable[[str | Path], None]
ProgressCallback = Callable[[BuildStage], None]
CancellationPredicate = Callable[[], bool]


class DocumentRenderer(Protocol):
    def render(self, plan: RenderPlan, output: str | Path) -> Path: ...


def _create_validation_context(
    document: ThesisDocument,
    template_path: str | Path | None,
) -> ValidationContext:
    return ValidationContext.from_document(document, template_path=template_path)


@dataclass(frozen=True, slots=True)
class ApplicationDependencies:
    parser: Parser = parse_markdown
    context_factory: ContextFactory = _create_validation_context
    validator: Validator = validate_document
    compiler: Compiler = compile_document
    renderer: DocumentRenderer = field(default_factory=DocxRenderer)
    package_validator: PackageValidator = validate_docx_package
    replace_file: ReplaceFile = os.replace


def _dependencies(
    dependencies: ApplicationDependencies | None,
) -> ApplicationDependencies:
    return dependencies or ApplicationDependencies()


def _notify(
    callback: ProgressCallback | None,
    stage: BuildStage,
) -> None:
    if callback is None:
        return
    try:
        callback(stage)
    except Exception as error:
        raise ApplicationStageError(stage, error) from error


def _check_canceled(
    should_cancel: CancellationPredicate | None,
    stage: BuildStage,
) -> None:
    if should_cancel is not None and should_cancel():
        from .contracts import BuildCanceledError

        raise BuildCanceledError(stage)


def inspect_service(
    source: str | Path,
    *,
    dependencies: ApplicationDependencies | None = None,
) -> InspectionResult:
    active = _dependencies(dependencies)
    try:
        document = active.parser(source)
    except ApplicationStageError:
        raise
    except Exception as error:
        raise ApplicationStageError(BuildStage.PARSE, error) from error
    return InspectionResult(document=document)


def _validate_inspection(
    inspection: InspectionResult,
    template_path: str | Path | None,
    dependencies: ApplicationDependencies,
) -> ValidationResult:
    try:
        context = dependencies.context_factory(inspection.document, template_path)
        issues = tuple(dependencies.validator(inspection.document, context))
    except ApplicationStageError:
        raise
    except Exception as error:
        raise ApplicationStageError(BuildStage.VALIDATE, error) from error
    return ValidationResult(
        document=inspection.document,
        context=context,
        issues=issues,
    )


def validation_service(
    source: str | Path,
    *,
    template_path: str | Path | None = None,
    dependencies: ApplicationDependencies | None = None,
) -> ValidationResult:
    active = _dependencies(dependencies)
    inspection = inspect_service(source, dependencies=active)
    return _validate_inspection(inspection, template_path, active)


def preview_service(
    source: str | Path,
    *,
    template_path: str | Path | None = None,
    dependencies: ApplicationDependencies | None = None,
) -> PreviewResult:
    active = _dependencies(dependencies)
    inspection = inspect_service(source, dependencies=active)
    validation = _validate_inspection(inspection, template_path, active)
    if validation.errors or validation.context.template is None:
        return PreviewResult(
            document=validation.document,
            context=validation.context,
            issues=validation.issues,
            plan=None,
        )

    try:
        plan = active.compiler(
            validation.document,
            template=validation.context.template,
            template_path=validation.context.template_path,
            bibliography_database=validation.context.bibliography_database,
        )
    except ApplicationStageError:
        raise
    except Exception as error:
        raise ApplicationStageError(BuildStage.COMPILE, error) from error

    return PreviewResult(
        document=validation.document,
        context=validation.context,
        issues=validation.issues,
        plan=plan,
    )


def build_service(
    source: str | Path,
    output: str | Path,
    *,
    template_path: str | Path | None = None,
    on_progress: ProgressCallback | None = None,
    should_cancel: CancellationPredicate | None = None,
    dependencies: ApplicationDependencies | None = None,
) -> BuildResult:
    active = _dependencies(dependencies)
    output_path = Path(output)

    _check_canceled(should_cancel, BuildStage.PARSE)
    _notify(on_progress, BuildStage.PARSE)
    inspection = inspect_service(source, dependencies=active)

    _check_canceled(should_cancel, BuildStage.VALIDATE)
    _notify(on_progress, BuildStage.VALIDATE)
    validation = _validate_inspection(inspection, template_path, active)

    if validation.errors:
        raise BuildValidationError(validation.issues)
    if validation.context.template is None:
        raise ApplicationStageError(
            BuildStage.VALIDATE,
            ValueError("模板未成功解析"),
        )

    _check_canceled(should_cancel, BuildStage.COMPILE)
    _notify(on_progress, BuildStage.COMPILE)
    try:
        plan = active.compiler(
            inspection.document,
            template=validation.context.template,
            template_path=validation.context.template_path,
            bibliography_database=validation.context.bibliography_database,
        )
    except Exception as error:
        raise ApplicationStageError(BuildStage.COMPILE, error) from error

    _check_canceled(should_cancel, BuildStage.RENDER)
    _notify(on_progress, BuildStage.RENDER)
    try:
        with temporary_output_path(output_path) as temporary_path:
            active.renderer.render(plan, temporary_path)

            _check_canceled(should_cancel, BuildStage.FINALIZE)
            _notify(on_progress, BuildStage.FINALIZE)
            try:
                active.package_validator(temporary_path)
                _check_canceled(should_cancel, BuildStage.FINALIZE)
                replace_output(
                    temporary_path,
                    output_path,
                    replace_file=active.replace_file,
                )
            except ApplicationStageError:
                raise
            except Exception as error:
                raise ApplicationStageError(BuildStage.FINALIZE, error) from error
    except ApplicationStageError:
        raise
    except Exception as error:
        raise ApplicationStageError(BuildStage.RENDER, error) from error

    return BuildResult(output_path=output_path, issues=validation.issues)
