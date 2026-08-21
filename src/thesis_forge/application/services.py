from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import ThesisDocument, ValidationIssue
from thesis_forge.core.parser_backend import LegacyParserBackend, ParserBackend
from thesis_forge.core.render_plan import RenderPlan
from thesis_forge.core.validator import ValidationContext, validate_document
from thesis_forge.renderers.docx import DocxRenderer
from thesis_forge.renderers.docx.package import validate_docx_package

from .contracts import (
    ApplicationStageError,
    BuildReportStage,
    BuildResult,
    BuildStage,
    BuildStageState,
    BuildStageStatus,
    BuildValidationError,
    InspectionResult,
    PreviewResult,
    ValidationResult,
)
from .office_refresh import (
    DocumentRefresher,
    LibreOfficeDocumentRefresher,
    refresh_document_safely,
)
from .output import ReplaceFile, replace_output, temporary_output_path
from .pdf_preview import (
    PdfPreviewArtifact,
    PdfPreviewExporter,
    derived_pdf_preview_path,
)

Parser = Callable[[str | Path], ThesisDocument]
SnapshotParser = Callable[..., ThesisDocument]
ContextFactory = Callable[[ThesisDocument, str | Path | None], ValidationContext]
Validator = Callable[[ThesisDocument, ValidationContext], list[ValidationIssue]]
Compiler = Callable[..., RenderPlan]
PackageValidator = Callable[[str | Path], None]
ProgressCallback = Callable[[BuildStage], None]
CancellationPredicate = Callable[[], bool]
REPORT_STAGES = tuple(BuildReportStage)


class DocumentRenderer(Protocol):
    def render(self, plan: RenderPlan, output: str | Path) -> Path: ...


@dataclass(slots=True)
class BuildStageLifecycle:
    """Deterministic application-stage state machine for BuildReport emission."""

    _states: dict[BuildReportStage, BuildStageState] = field(
        default_factory=lambda: {
            stage: BuildStageState(
                name=stage,
                status=BuildStageStatus.PENDING,
            )
            for stage in REPORT_STAGES
        }
    )
    _history: list[BuildStageState] = field(default_factory=list)

    def state(self, stage: BuildStage | BuildReportStage) -> BuildStageState:
        return self._states[self._report_stage(stage)]

    def start(self, stage: BuildStage | BuildReportStage) -> BuildStageState:
        report_stage = self._report_stage(stage)
        self._require_status(report_stage, BuildStageStatus.PENDING)
        self._set(report_stage, BuildStageStatus.RUNNING)
        return self.state(report_stage)

    def succeed(self, stage: BuildStage | BuildReportStage) -> BuildStageState:
        report_stage = self._report_stage(stage)
        self._require_status(report_stage, BuildStageStatus.RUNNING)
        self._set(report_stage, BuildStageStatus.SUCCEEDED)
        return self.state(report_stage)

    def fail(self, stage: BuildStage | BuildReportStage) -> BuildStageState:
        report_stage = self._report_stage(stage)
        self._require_status(report_stage, BuildStageStatus.RUNNING)
        self._set(report_stage, BuildStageStatus.FAILED)
        return self.state(report_stage)

    def terminalize(
        self,
        stage: BuildStage | BuildReportStage,
        *,
        canceled: bool = False,
    ) -> tuple[BuildStageState, ...]:
        """Close the active boundary and make the whole snapshot terminal."""
        report_stage = self._report_stage(stage)
        self._require_upstream_terminal(report_stage)
        current = self.state(report_stage)
        if canceled:
            if current.status not in {
                BuildStageStatus.PENDING,
                BuildStageStatus.RUNNING,
            }:
                raise ValueError(
                    f"{report_stage.value} must be pending or running, "
                    f"got {current.status.value}"
                )
            self._set(report_stage, BuildStageStatus.SKIPPED)
        else:
            self._require_status(report_stage, BuildStageStatus.RUNNING)
            self._set(report_stage, BuildStageStatus.FAILED)
        self.skip_downstream(report_stage)
        return self.snapshot()

    def _require_upstream_terminal(self, stage: BuildReportStage) -> None:
        stage_index = REPORT_STAGES.index(stage)
        for upstream in REPORT_STAGES[:stage_index]:
            status = self.state(upstream).status
            if status in {BuildStageStatus.PENDING, BuildStageStatus.RUNNING}:
                raise ValueError(
                    f"{upstream.value} must be terminal before {stage.value}, "
                    f"got {status.value}"
                )

    def skip_downstream(
        self,
        stage: BuildStage | BuildReportStage,
    ) -> tuple[BuildStageState, ...]:
        report_stage = self._report_stage(stage)
        start = REPORT_STAGES.index(report_stage) + 1
        skipped: list[BuildStageState] = []
        for downstream in REPORT_STAGES[start:]:
            if self.state(downstream).status in {
                BuildStageStatus.PENDING,
                BuildStageStatus.RUNNING,
            }:
                self._set(downstream, BuildStageStatus.SKIPPED)
                skipped.append(self.state(downstream))
        return tuple(skipped)

    def snapshot(self) -> tuple[BuildStageState, ...]:
        return tuple(self._states[stage] for stage in REPORT_STAGES)

    def history(self) -> tuple[BuildStageState, ...]:
        return tuple(self._history)

    @staticmethod
    def _report_stage(stage: BuildStage | BuildReportStage) -> BuildReportStage:
        return (
            stage
            if isinstance(stage, BuildReportStage)
            else BuildReportStage(stage.value)
        )

    def _require_status(
        self,
        stage: BuildReportStage,
        expected: BuildStageStatus,
    ) -> None:
        actual = self.state(stage).status
        if actual is not expected:
            raise ValueError(
                f"{stage.value} must be {expected.value}, got {actual.value}"
            )

    def _set(self, stage: BuildReportStage, status: BuildStageStatus) -> None:
        updated = BuildStageState(name=stage, status=status)
        self._states[stage] = updated
        self._history.append(updated)


def _create_validation_context(
    document: ThesisDocument,
    template_path: str | Path | None,
) -> ValidationContext:
    return ValidationContext.from_document(document, template_path=template_path)


@dataclass(frozen=True, slots=True)
class ApplicationDependencies:
    # 解析默认经 ParserBackend（ADR-0001，默认 legacy）；parser/snapshot_parser
    # 保留为细粒度覆盖通道，为 None 时回落到 parser_backend 的对应方法。
    parser_backend: ParserBackend = field(default_factory=LegacyParserBackend)
    parser: Parser | None = None
    snapshot_parser: SnapshotParser | None = None
    context_factory: ContextFactory = _create_validation_context
    validator: Validator = validate_document
    compiler: Compiler = compile_document
    renderer: DocumentRenderer = field(default_factory=DocxRenderer)
    document_refresher: DocumentRefresher = field(
        default_factory=LibreOfficeDocumentRefresher
    )
    pdf_preview_exporter: PdfPreviewExporter | None = None
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
    source_text: str | None = None,
    dependencies: ApplicationDependencies | None = None,
) -> InspectionResult:
    active = _dependencies(dependencies)
    parse_file = active.parser or active.parser_backend.parse_file
    parse_text = active.snapshot_parser or active.parser_backend.parse_text
    try:
        document = (
            parse_file(source)
            if source_text is None
            else parse_text(source_text, source_path=source)
        )
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
    source_text: str | None = None,
    template_path: str | Path | None = None,
    dependencies: ApplicationDependencies | None = None,
) -> ValidationResult:
    active = _dependencies(dependencies)
    inspection = inspect_service(
        source,
        source_text=source_text,
        dependencies=active,
    )
    return _validate_inspection(inspection, template_path, active)


def preview_service(
    source: str | Path,
    *,
    source_text: str | None = None,
    template_path: str | Path | None = None,
    dependencies: ApplicationDependencies | None = None,
) -> PreviewResult:
    active = _dependencies(dependencies)
    inspection = inspect_service(
        source,
        source_text=source_text,
        dependencies=active,
    )
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
    source_text: str | None = None,
    template_path: str | Path | None = None,
    on_progress: ProgressCallback | None = None,
    should_cancel: CancellationPredicate | None = None,
    dependencies: ApplicationDependencies | None = None,
) -> BuildResult:
    active = _dependencies(dependencies)
    output_path = Path(output)
    final_preview: PdfPreviewArtifact | None = None

    _check_canceled(should_cancel, BuildStage.PARSE)
    _notify(on_progress, BuildStage.PARSE)
    inspection = inspect_service(
        source,
        source_text=source_text,
        dependencies=active,
    )

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
                refresh_document_safely(
                    active.document_refresher,
                    temporary_path,
                )
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

    if active.pdf_preview_exporter is not None:
        try:
            final_preview = active.pdf_preview_exporter.export(
                output_path,
                derived_pdf_preview_path(output_path),
            )
        # A third-party exporter must never downgrade a published DOCX build.
        except Exception:  # noqa: BLE001
            final_preview = None

    return BuildResult(
        output_path=output_path,
        issues=validation.issues,
        final_preview=final_preview,
    )
