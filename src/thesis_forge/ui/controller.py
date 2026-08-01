from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from .models import (
    DiagnosticViewModel,
    OperationKind,
    OperationToken,
    OutputViewModel,
    ProgressViewModel,
    WorkspaceActions,
    WorkspaceStatus,
    WorkspaceViewModel,
)
from .tasks import SynchronousTaskRunner, TaskRunner, WorkspaceFileSystem

if TYPE_CHECKING:
    from thesis_forge.application.contracts import (
        BuildResult,
        InspectionResult,
        ValidationResult,
    )

InspectService = Callable[..., "InspectionResult"]
ValidationService = Callable[..., "ValidationResult"]
BuildService = Callable[..., "BuildResult"]
StateListener = Callable[[WorkspaceViewModel], None]


def _default_inspect(*args, **kwargs):
    from thesis_forge.application.services import inspect_service

    return inspect_service(*args, **kwargs)


def _default_validate(*args, **kwargs):
    from thesis_forge.application.services import validation_service

    return validation_service(*args, **kwargs)


def _default_build(*args, **kwargs):
    from thesis_forge.application.services import build_service

    return build_service(*args, **kwargs)


class WorkspaceController:
    def __init__(
        self,
        *,
        inspect: InspectService = _default_inspect,
        validate: ValidationService = _default_validate,
        build: BuildService = _default_build,
        filesystem: WorkspaceFileSystem | None = None,
        task_runner: TaskRunner | None = None,
    ) -> None:
        self._inspect = inspect
        self._validate = validate
        self._build = build
        self.filesystem = filesystem
        self._task_runner = task_runner or SynchronousTaskRunner()
        self._state = WorkspaceViewModel()
        self._listeners: list[StateListener] = []
        self._generation = 0
        self._inspection: InspectionResult | None = None

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

    def load_snapshot(
        self,
        source_path: str | Path,
        saved_text: str,
        *,
        template_path: str | Path | None = None,
    ) -> OperationToken | None:
        if self._state.status is WorkspaceStatus.DISABLED:
            return None

        source = Path(source_path)
        template = Path(template_path) if template_path is not None else None
        token = self._next_token(OperationKind.INSPECT)
        self._inspection = None
        self._update_state(
            status=WorkspaceStatus.LOADING,
            source_path=source,
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
        if not self._state.actions.can_save:
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
        self._task_runner.submit(
            lambda: self._build(
                source,
                output,
                template_path=template,
                on_progress=lambda stage: self._report_progress(token, stage),
            ),
            on_success=lambda result: self._complete_build(token, result),
            on_error=lambda error: self._fail_operation(token, error),
        )
        return token

    def cancel_current(self) -> bool:
        if self._state.active_operation is None:
            return False
        self._update_state(
            status=WorkspaceStatus.CANCELED,
            progress=None,
            error_message=None,
            active_operation=None,
        )
        return True

    def disable(self, reason: str) -> None:
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
        self._inspection = None
        self._state = WorkspaceViewModel()
        self._publish()

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
            return WorkspaceActions(
                can_open=True,
                can_edit=self._inspection is not None,
                can_cancel=True,
            )
        if state.status is WorkspaceStatus.DIRTY:
            return WorkspaceActions(
                can_open=True,
                can_edit=True,
                can_save=True,
            )
        if state.status is WorkspaceStatus.POPULATED:
            return WorkspaceActions(
                can_open=True,
                can_edit=True,
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
