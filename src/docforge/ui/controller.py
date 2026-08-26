from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from docforge.application import ProjectApplicationService
from docforge.application.contracts import (
    ProjectIdentity,
    ProjectOutput,
    ProjectRequest,
    ProjectRequestIntent,
)
from docforge.project.loader import load_project

from .filesystem import LocalWorkspaceFileSystem
from .models import (
    DiagnosticViewModel,
    OperationKind,
    OperationToken,
    OutputViewModel,
    ProgressViewModel,
    WebSourceHandle,
    WorkspaceActions,
    WorkspaceSourceKind,
    WorkspaceStatus,
    WorkspaceViewModel,
)
from .tasks import (
    SynchronousTaskRunner,
    TaskRunner,
    WebWorkspacePersistence,
    WorkspaceFileSystem,
)

if TYPE_CHECKING:
    from docforge.application.contracts import (
        BuildResult,
        InspectionResult,
        ValidationResult,
    )

InspectService = Callable[..., "InspectionResult"]
ValidationService = Callable[..., "ValidationResult"]
BuildService = Callable[..., "BuildResult"]
StateListener = Callable[[WorkspaceViewModel], None]
PersistenceOperation = Callable[[], Path]


@dataclass(frozen=True, slots=True)
class _WorkspaceAnalysis:
    inspection: InspectionResult
    validation: ValidationResult


@dataclass(frozen=True, slots=True)
class _OpenedWorkspace:
    source_path: Path
    source_kind: WorkspaceSourceKind
    source_name: str
    web_source: WebSourceHandle | None
    template_path: Path | None
    saved_text: str
    analysis: _WorkspaceAnalysis
    project_identity: ProjectIdentity | None = None


def _default_inspect(*args, **kwargs):
    from docforge.application.services import inspect_service

    return inspect_service(*args, **kwargs)


def _default_validate(*args, **kwargs):
    from docforge.application.services import validation_service

    return validation_service(*args, **kwargs)


def _default_build(*args, **kwargs):
    from docforge.application.services import build_service

    return build_service(*args, **kwargs)


class WorkspaceController:
    def __init__(
        self,
        *,
        inspect: InspectService = _default_inspect,
        validate: ValidationService = _default_validate,
        build: BuildService = _default_build,
        filesystem: WorkspaceFileSystem | None = None,
        web_persistence: WebWorkspacePersistence | None = None,
        task_runner: TaskRunner | None = None,
        project_service: ProjectApplicationService | None = None,
    ) -> None:
        self._inspect = inspect
        self._validate = validate
        self._build = build
        self.filesystem = (
            filesystem
            if filesystem is not None
            else LocalWorkspaceFileSystem()
        )
        self.web_persistence = web_persistence
        self._task_runner = task_runner or SynchronousTaskRunner()
        self._project_service = project_service or ProjectApplicationService()
        self._state = WorkspaceViewModel()
        self._listeners: list[StateListener] = []
        self._generation = 0
        self._inspection: InspectionResult | None = None
        self._project_identity: ProjectIdentity | None = None
        self._refresh_validation = False

    @property
    def state(self) -> WorkspaceViewModel:
        return self._state

    def subscribe(self, listener: StateListener) -> Callable[[], None]:
        self._listeners.append(listener)
        listener(self._state)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    def open_source(
        self,
        source_path: str | Path,
        *,
        template_path: str | Path | None = None,
    ) -> OperationToken | None:
        if not self._state.actions.can_open:
            return None

        source = Path(source_path)
        template = Path(template_path) if template_path is not None else None
        token = self._begin_operation(OperationKind.OPEN)
        open_operation = (
            self._open_desktop_project
            if source.is_dir() or source.name == "thesisforge.yaml"
            else self._open_desktop_workspace
        )
        self._task_runner.submit(
            lambda: open_operation(source, template),
            on_success=lambda result: self._complete_open(token, result),
            on_error=lambda error: self._fail_operation(token, error),
        )
        return token

    def open_web_snapshot(
        self,
        service_path: str | Path,
        saved_text: str,
        handle: WebSourceHandle,
        *,
        template_path: str | Path | None = None,
    ) -> OperationToken | None:
        if not self._state.actions.can_open:
            return None

        source = Path(service_path)
        template = Path(template_path) if template_path is not None else None
        source_kind = (
            WorkspaceSourceKind.WEB_WORKSPACE
            if handle.workspace_id is not None
            else WorkspaceSourceKind.WEB_UPLOAD
        )
        token = self._begin_operation(OperationKind.OPEN)
        self._task_runner.submit(
            lambda: _OpenedWorkspace(
                source_path=source,
                source_kind=source_kind,
                source_name=handle.file_name,
                web_source=handle,
                template_path=template,
                saved_text=saved_text,
                analysis=self._analyze_workspace(source, template),
            ),
            on_success=lambda result: self._complete_open(token, result),
            on_error=lambda error: self._fail_operation(token, error),
        )
        return token

    def load_snapshot(
        self,
        source_path: str | Path,
        saved_text: str,
        *,
        template_path: str | Path | None = None,
    ) -> OperationToken | None:
        if not self._state.actions.can_open:
            return None

        source = Path(source_path)
        template = Path(template_path) if template_path is not None else None
        token = self._next_token(OperationKind.INSPECT)
        self._inspection = None
        self._refresh_validation = False
        self._update_state(
            status=WorkspaceStatus.LOADING,
            source_path=source,
            source_kind=WorkspaceSourceKind.DESKTOP,
            source_name=source.name,
            web_source=None,
            template_path=template,
            saved_text=saved_text,
            editor_text=saved_text,
            dirty=False,
            diagnostics=(),
            progress=ProgressViewModel(operation=token),
            output=None,
            error_message=None,
            disabled_reason=None,
            active_operation=token,
        )
        self._task_runner.submit(
            lambda: self._inspect(source),
            on_success=lambda result: self._complete_inspection(token, result),
            on_error=lambda error: self._fail_operation(token, error),
        )
        return token

    def save(self) -> OperationToken | None:
        if not self._state.actions.can_save:
            return None

        source = self._require_source()
        text = self._state.editor_text
        if self._state.source_kind is WorkspaceSourceKind.DESKTOP:

            def persist() -> Path:
                self.filesystem.write_text_atomic(source, text)
                return source

        else:
            handle = self._state.web_source
            persistence = self.web_persistence
            if (
                handle is None
                or persistence is None
                or not handle.writable
                or handle.workspace_id is None
            ):
                return None

            def persist() -> Path:
                return Path(persistence.save_workspace(handle, source, text))

        return self._start_persistence(
            OperationKind.SAVE,
            persist,
            text=text,
            source_kind=self._state.source_kind,
            source_name=self._state.source_name or source.name,
            web_source=self._state.web_source,
        )

    def save_as(self, target_path: str | Path) -> OperationToken | None:
        if not self._state.actions.can_save_as:
            return None
        if self._project_identity is not None:
            return None

        target = Path(target_path)
        text = self._state.editor_text

        def persist() -> Path:
            self.filesystem.write_text_atomic(target, text)
            return target

        return self._start_persistence(
            OperationKind.SAVE,
            persist,
            text=text,
            source_kind=WorkspaceSourceKind.DESKTOP,
            source_name=target.name,
            web_source=None,
        )

    def download_source(self) -> OperationToken | None:
        if not self._state.actions.can_download:
            return None

        source = self._require_source()
        handle = self._state.web_source
        persistence = self.web_persistence
        if handle is None or persistence is None:
            return None
        text = self._state.editor_text

        def persist() -> Path:
            return Path(persistence.download(handle, source, text))

        return self._start_persistence(
            OperationKind.DOWNLOAD,
            persist,
            text=text,
            source_kind=self._state.source_kind,
            source_name=handle.file_name,
            web_source=handle,
        )

    def edit_text(self, text: str) -> bool:
        if not self._state.actions.can_edit:
            return False
        if text == self._state.editor_text and self._state.active_operation is None:
            return False

        status = (
            WorkspaceStatus.DIRTY
            if text != self._state.saved_text
            else WorkspaceStatus.POPULATED
        )
        self._update_state(
            status=status,
            editor_text=text,
            dirty=text != self._state.saved_text,
            progress=None,
            error_message=None,
            disabled_reason=None,
            active_operation=None,
        )
        return True

    def discard_edits(self) -> bool:
        if self._state.status is not WorkspaceStatus.DIRTY:
            return False

        self._update_state(
            status=WorkspaceStatus.POPULATED,
            editor_text=self._state.saved_text,
            dirty=False,
            progress=None,
            error_message=None,
            active_operation=None,
        )
        return True

    def validate(self) -> OperationToken | None:
        if not self._state.actions.can_validate:
            return None
        source = self._require_source()
        template = self._state.template_path
        token = self._begin_operation(OperationKind.VALIDATE)
        if self._project_identity is not None:
            request = ProjectRequest(
                project=self._project_identity,
                intent=ProjectRequestIntent.VALIDATE,
                editor_snapshot=self._state.editor_text,
            )
            self._task_runner.submit(
                lambda: self._project_service.validate(request),
                on_success=lambda result: self._complete_validation(token, result),
                on_error=lambda error: self._fail_operation(token, error),
            )
            return token
        self._task_runner.submit(
            lambda: self._validate(
                source,
                template_path=template,
            ),
            on_success=lambda result: self._complete_validation(token, result),
            on_error=lambda error: self._fail_operation(token, error),
        )
        return token

    def build(self, output_path: str | Path) -> OperationToken | None:
        if not self._state.actions.can_build:
            return None
        source = self._require_source()
        template = self._state.template_path
        output = Path(output_path)
        token = self._begin_operation(OperationKind.BUILD)
        if self._project_identity is not None:
            request = ProjectRequest(
                project=self._project_identity,
                intent=ProjectRequestIntent.BUILD,
                output=ProjectOutput(output),
                editor_snapshot=self._state.editor_text,
            )
            self._task_runner.submit(
                lambda: self._project_service.build(
                    request,
                    on_progress=lambda stage: self._report_progress(token, stage),
                    should_cancel=lambda: not self._is_current(token),
                ),
                on_success=lambda result: self._complete_build(token, result),
                on_error=lambda error: self._fail_operation(token, error),
            )
            return token
        self._task_runner.submit(
            lambda: self._build(
                source,
                output,
                template_path=template,
                on_progress=lambda stage: self._report_progress(token, stage),
                should_cancel=lambda: not self._is_current(token),
            ),
            on_success=lambda result: self._complete_build(token, result),
            on_error=lambda error: self._fail_operation(token, error),
        )
        return token

    def cancel_current(self) -> bool:
        if (
            self._state.active_operation is None
            or not self._state.actions.can_cancel
        ):
            return False
        self._update_state(
            status=WorkspaceStatus.CANCELED,
            progress=None,
            error_message=None,
            active_operation=None,
        )
        return True

    def disable(self, reason: str) -> None:
        if self._persistence_in_progress():
            return
        self._update_state(
            status=WorkspaceStatus.DISABLED,
            progress=None,
            error_message=None,
            disabled_reason=reason,
            active_operation=None,
        )

    def recover(self) -> bool:
        if self._state.status not in {
            WorkspaceStatus.ERROR,
            WorkspaceStatus.DISABLED,
            WorkspaceStatus.PERMISSION,
            WorkspaceStatus.CANCELED,
        }:
            return False
        if self._inspection is None and self._state.source_path is not None:
            if self._refresh_validation:
                self._start_refresh()
                return True
            token = self._next_token(OperationKind.INSPECT)
            source = self._state.source_path
            self._update_state(
                status=WorkspaceStatus.LOADING,
                progress=ProgressViewModel(operation=token),
                error_message=None,
                disabled_reason=None,
                active_operation=token,
            )
            self._task_runner.submit(
                lambda: self._inspect(source),
                on_success=lambda result: self._complete_inspection(token, result),
                on_error=lambda error: self._fail_operation(token, error),
            )
            return True
        self._update_state(
            status=self._resting_status(),
            progress=None,
            error_message=None,
            disabled_reason=None,
            active_operation=None,
        )
        return True

    def reset(self) -> None:
        if self._persistence_in_progress():
            return
        self._inspection = None
        self._project_identity = None
        self._refresh_validation = False
        self._state = WorkspaceViewModel()
        self._publish()

    def _open_desktop_workspace(
        self,
        source: Path,
        template: Path | None,
    ) -> _OpenedWorkspace:
        saved_text = self.filesystem.read_text(source)
        return _OpenedWorkspace(
            source_path=source,
            source_kind=WorkspaceSourceKind.DESKTOP,
            source_name=source.name,
            web_source=None,
            template_path=template,
            saved_text=saved_text,
            analysis=self._analyze_workspace(source, template),
        )

    def _open_desktop_project(
        self,
        project_path: Path,
        _template: Path | None,
    ) -> _OpenedWorkspace:
        project = load_project(project_path)
        source = project.source_path
        saved_text = self.filesystem.read_text(source)
        identity = ProjectIdentity(
            project_id=project.manifest.project.id,
            project_root=project.project_root,
            manifest_path=project.manifest_path,
        )
        inspection = self._project_service.inspect(
            ProjectRequest(
                project=identity,
                intent=ProjectRequestIntent.INSPECT,
            )
        )
        validation = self._project_service.validate(
            ProjectRequest(
                project=identity,
                intent=ProjectRequestIntent.VALIDATE,
                editor_snapshot=saved_text,
            )
        )
        return _OpenedWorkspace(
            source_path=source,
            source_kind=WorkspaceSourceKind.DESKTOP,
            source_name=source.name,
            web_source=None,
            template_path=None,
            saved_text=saved_text,
            analysis=_WorkspaceAnalysis(
                inspection=inspection,
                validation=validation,
            ),
            project_identity=identity,
        )

    def _analyze_workspace(
        self,
        source: Path,
        template: Path | None,
    ) -> _WorkspaceAnalysis:
        return _WorkspaceAnalysis(
            inspection=self._inspect(source),
            validation=self._validate(
                source,
                template_path=template,
            ),
        )

    def _complete_open(
        self,
        token: OperationToken,
        result: _OpenedWorkspace,
    ) -> None:
        if not self._is_current(token):
            return
        self._inspection = result.analysis.inspection
        self._project_identity = result.project_identity
        self._refresh_validation = True
        self._update_state(
            status=WorkspaceStatus.POPULATED,
            source_path=result.source_path,
            source_kind=result.source_kind,
            source_name=result.source_name,
            web_source=result.web_source,
            template_path=result.template_path,
            saved_text=result.saved_text,
            editor_text=result.saved_text,
            dirty=False,
            diagnostics=self._diagnostics(result.analysis.validation.issues),
            progress=None,
            output=None,
            error_message=None,
            disabled_reason=None,
            active_operation=None,
        )

    def _start_persistence(
        self,
        kind: OperationKind,
        operation: PersistenceOperation,
        *,
        text: str,
        source_kind: WorkspaceSourceKind | None,
        source_name: str,
        web_source: WebSourceHandle | None,
    ) -> OperationToken:
        token = self._begin_operation(kind)
        self._task_runner.submit(
            operation,
            on_success=lambda source: self._complete_persistence(
                token,
                Path(source),
                text=text,
                source_kind=source_kind,
                source_name=source_name,
                web_source=web_source,
            ),
            on_error=lambda error: self._fail_operation(token, error),
        )
        return token

    def _complete_persistence(
        self,
        token: OperationToken,
        source: Path,
        *,
        text: str,
        source_kind: WorkspaceSourceKind | None,
        source_name: str,
        web_source: WebSourceHandle | None,
    ) -> None:
        if not self._is_current(token):
            return
        self._inspection = None
        self._refresh_validation = True
        self._update_state(
            source_path=source,
            source_kind=source_kind,
            source_name=source_name,
            web_source=web_source,
            saved_text=text,
            editor_text=text,
            dirty=False,
            progress=None,
            error_message=None,
            active_operation=None,
        )
        self._start_refresh()

    def _start_refresh(self) -> OperationToken:
        source = self._require_source()
        template = self._state.template_path
        token = self._begin_operation(OperationKind.REFRESH)
        if self._project_identity is not None:
            identity = self._project_identity
            snapshot = self._state.editor_text
            self._task_runner.submit(
                lambda: _WorkspaceAnalysis(
                    inspection=self._project_service.inspect(
                        ProjectRequest(
                            project=identity,
                            intent=ProjectRequestIntent.INSPECT,
                            editor_snapshot=snapshot,
                        )
                    ),
                    validation=self._project_service.validate(
                        ProjectRequest(
                            project=identity,
                            intent=ProjectRequestIntent.VALIDATE,
                            editor_snapshot=snapshot,
                        )
                    ),
                ),
                on_success=lambda result: self._complete_refresh(token, result),
                on_error=lambda error: self._fail_operation(token, error),
            )
            return token
        self._task_runner.submit(
            lambda: self._analyze_workspace(source, template),
            on_success=lambda result: self._complete_refresh(token, result),
            on_error=lambda error: self._fail_operation(token, error),
        )
        return token

    def _complete_refresh(
        self,
        token: OperationToken,
        result: _WorkspaceAnalysis,
    ) -> None:
        if not self._is_current(token):
            return
        self._inspection = result.inspection
        self._update_state(
            status=self._resting_status(),
            diagnostics=self._diagnostics(result.validation.issues),
            progress=None,
            error_message=None,
            active_operation=None,
        )

    def _next_token(self, kind: OperationKind) -> OperationToken:
        self._generation += 1
        return OperationToken(kind=kind, generation=self._generation)

    def _begin_operation(self, kind: OperationKind) -> OperationToken:
        token = self._next_token(kind)
        self._update_state(
            status=WorkspaceStatus.LOADING,
            progress=ProgressViewModel(operation=token),
            error_message=None,
            disabled_reason=None,
            active_operation=token,
        )
        return token

    def _complete_inspection(
        self,
        token: OperationToken,
        result: InspectionResult,
    ) -> None:
        if not self._is_current(token):
            return
        self._inspection = result
        self._update_state(
            status=self._resting_status(),
            progress=None,
            error_message=None,
            active_operation=None,
        )

    def _complete_validation(
        self,
        token: OperationToken,
        result: ValidationResult,
    ) -> None:
        if not self._is_current(token):
            return
        self._update_state(
            status=self._resting_status(),
            diagnostics=self._diagnostics(result.issues),
            progress=None,
            error_message=None,
            active_operation=None,
        )

    def _complete_build(
        self,
        token: OperationToken,
        result: BuildResult,
    ) -> None:
        if not self._is_current(token):
            return
        diagnostics = self._diagnostics(result.issues)
        self._update_state(
            status=self._resting_status(),
            diagnostics=diagnostics,
            progress=None,
            output=OutputViewModel(
                path=Path(result.output_path),
                diagnostics=diagnostics,
            ),
            error_message=None,
            active_operation=None,
        )

    def _report_progress(self, token: OperationToken, stage) -> None:
        if not self._is_current(token):
            return
        self._update_state(progress=ProgressViewModel(operation=token, stage=stage))

    def _fail_operation(self, token: OperationToken, error: Exception) -> None:
        if not self._is_current(token):
            return
        status = (
            WorkspaceStatus.PERMISSION
            if self._is_permission_error(error)
            else WorkspaceStatus.ERROR
        )
        issues = getattr(error, "issues", ())
        self._update_state(
            status=status,
            diagnostics=(
                self._diagnostics(tuple(issues))
                if issues
                else self._state.diagnostics
            ),
            progress=None,
            error_message=str(error),
            active_operation=None,
        )

    def _is_current(self, token: OperationToken) -> bool:
        return self._state.active_operation == token

    def _persistence_in_progress(self) -> bool:
        return (
            self._state.active_operation is not None
            and self._state.active_operation.kind
            in {OperationKind.SAVE, OperationKind.DOWNLOAD}
        )

    def _resting_status(self) -> WorkspaceStatus:
        if self._state.source_path is None:
            return WorkspaceStatus.EMPTY
        if self._state.editor_text != self._state.saved_text:
            return WorkspaceStatus.DIRTY
        return WorkspaceStatus.POPULATED

    def _require_source(self) -> Path:
        if self._state.source_path is None:
            raise RuntimeError("workspace source is not loaded")
        return self._state.source_path

    def _update_state(self, **changes) -> None:
        candidate = replace(self._state, **changes)
        candidate = replace(candidate, actions=self._actions_for(candidate))
        self._state = candidate
        self._publish()

    def _publish(self) -> None:
        for listener in tuple(self._listeners):
            listener(self._state)

    @staticmethod
    def _diagnostics(issues) -> tuple[DiagnosticViewModel, ...]:
        return tuple(DiagnosticViewModel.from_issue(issue) for issue in issues)

    @staticmethod
    def _is_permission_error(error: Exception) -> bool:
        current: BaseException | None = error
        visited: set[int] = set()
        while current is not None and id(current) not in visited:
            if isinstance(current, PermissionError):
                return True
            visited.add(id(current))
            cause = getattr(current, "cause", None)
            if isinstance(cause, BaseException):
                current = cause
            else:
                current = current.__cause__ or current.__context__
        return False

    def _actions_for(self, state: WorkspaceViewModel) -> WorkspaceActions:
        if state.status is WorkspaceStatus.DISABLED:
            return WorkspaceActions(can_open=False, can_recover=True)
        if state.status is WorkspaceStatus.LOADING:
            operation = (
                state.active_operation.kind
                if state.active_operation is not None
                else None
            )
            persistence_active = operation in {
                OperationKind.SAVE,
                OperationKind.DOWNLOAD,
                OperationKind.REFRESH,
            }
            return WorkspaceActions(
                can_open=not persistence_active,
                can_edit=(
                    self._inspection is not None
                    and operation in {
                        OperationKind.INSPECT,
                        OperationKind.VALIDATE,
                        OperationKind.BUILD,
                    }
                ),
                can_cancel=operation not in {
                    OperationKind.SAVE,
                    OperationKind.DOWNLOAD,
                    OperationKind.REFRESH,
                },
            )
        if state.status is WorkspaceStatus.DIRTY:
            if state.source_kind is WorkspaceSourceKind.DESKTOP:
                return WorkspaceActions(
                    can_open=True,
                    can_edit=True,
                    can_save=True,
                    can_save_as=True,
                )
            web_available = (
                state.web_source is not None
                and self.web_persistence is not None
            )
            return WorkspaceActions(
                can_open=True,
                can_edit=True,
                can_save=(
                    web_available
                    and state.web_source is not None
                    and state.web_source.workspace_id is not None
                    and state.web_source.writable
                ),
                can_download=web_available,
            )
        if state.status is WorkspaceStatus.POPULATED:
            desktop = state.source_kind is WorkspaceSourceKind.DESKTOP
            web_available = (
                state.web_source is not None
                and self.web_persistence is not None
            )
            return WorkspaceActions(
                can_open=True,
                can_edit=True,
                can_save_as=desktop and self._project_identity is None,
                can_download=web_available,
                can_validate=True,
                can_build=True,
            )
        if state.status in {
            WorkspaceStatus.ERROR,
            WorkspaceStatus.PERMISSION,
            WorkspaceStatus.CANCELED,
        }:
            return WorkspaceActions(can_open=True, can_recover=True)
        return WorkspaceActions(can_open=True)
