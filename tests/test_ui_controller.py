from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path

import pytest

from thesis_forge import ui
from thesis_forge.application import (
    BuildResult,
    BuildStage,
    InspectionResult,
    ValidationResult,
)
from thesis_forge.core.model import ThesisDocument, ValidationIssue
from thesis_forge.core.validator import ValidationContext


@dataclass(slots=True)
class _PendingTask:
    operation: Callable[[], object]
    on_success: Callable[[object], None]
    on_error: Callable[[Exception], None]


class _DeferredTaskRunner:
    def __init__(self) -> None:
        self.tasks: list[_PendingTask] = []

    def submit(self, operation, *, on_success, on_error) -> None:
        self.tasks.append(_PendingTask(operation, on_success, on_error))

    def complete(self, index: int = -1) -> None:
        task = self.tasks[index]
        try:
            result = task.operation()
        except Exception as error:  # noqa: BLE001 - fake runner forwards task failures
            task.on_error(error)
            return
        task.on_success(result)

    def fail(self, error: Exception, index: int = -1) -> None:
        self.tasks[index].on_error(error)


class _UnusedFileSystem:
    def read_text(self, path: Path) -> str:
        raise AssertionError(f"Slice 002 must not read {path}")

    def write_text_atomic(self, path: Path, text: str) -> None:
        raise AssertionError(f"Slice 002 must not write {path}: {text}")


def _inspection(path: Path) -> InspectionResult:
    return InspectionResult(document=ThesisDocument(source_path=path))


def _validation(
    path: Path,
    issues: tuple[ValidationIssue, ...] = (),
) -> ValidationResult:
    return ValidationResult(
        document=ThesisDocument(source_path=path),
        context=ValidationContext(),
        issues=issues,
    )


def _loaded_controller(
    tmp_path: Path,
    *,
    validate: Callable[..., ValidationResult] | None = None,
    build: Callable[..., BuildResult] | None = None,
) -> tuple[ui.WorkspaceController, _DeferredTaskRunner, Path]:
    runner = _DeferredTaskRunner()
    source = tmp_path / "thesis.md"
    controller = ui.WorkspaceController(
        inspect=lambda path: _inspection(Path(path)),
        validate=validate or (lambda path, **_kwargs: _validation(Path(path))),
        build=build
        or (
            lambda _source, output, **_kwargs: BuildResult(
                output_path=Path(output),
                issues=(),
            )
        ),
        filesystem=_UnusedFileSystem(),
        task_runner=runner,
    )
    controller.load_snapshot(source, "# Saved\n")
    runner.complete()
    return controller, runner, source


def test_headless_workspace_public_contract_is_exported():
    expected = {
        "DiagnosticViewModel",
        "OperationKind",
        "OperationToken",
        "OutputViewModel",
        "ProgressViewModel",
        "SynchronousTaskRunner",
        "TaskRunner",
        "WorkspaceActions",
        "WorkspaceController",
        "WorkspaceFileSystem",
        "WorkspaceStatus",
        "WorkspaceViewModel",
    }

    assert expected <= set(ui.__all__)
    assert all(hasattr(ui, name) for name in expected)


def test_workspace_models_are_immutable_and_normalize_diagnostic_details():
    issue = ValidationIssue(
        code="missing-reference",
        severity="error",
        message="Reference target does not exist",
        line=12,
        target="fig:missing",
        details={"z": 2, "a": "first"},
    )
    diagnostic = ui.DiagnosticViewModel.from_issue(issue)
    state = ui.WorkspaceViewModel(diagnostics=(diagnostic,))

    assert diagnostic.details == (("a", "first"), ("z", 2))
    assert isinstance(state.diagnostics, tuple)
    with pytest.raises(FrozenInstanceError):
        state.status = ui.WorkspaceStatus.ERROR
    with pytest.raises(FrozenInstanceError):
        diagnostic.message = "mutated"


def test_initial_workspace_is_empty_with_only_open_available():
    filesystem = _UnusedFileSystem()
    controller = ui.WorkspaceController(filesystem=filesystem)

    assert controller.filesystem is filesystem
    assert controller.state.status is ui.WorkspaceStatus.EMPTY
    assert controller.state.source_path is None
    assert controller.state.actions == ui.WorkspaceActions(can_open=True)


def test_load_snapshot_transitions_loading_to_populated_and_notifies_subscribers(
    tmp_path: Path,
):
    runner = _DeferredTaskRunner()
    snapshots: list[ui.WorkspaceViewModel] = []
    source = tmp_path / "thesis.md"
    controller = ui.WorkspaceController(
        inspect=lambda path: _inspection(Path(path)),
        task_runner=runner,
    )
    unsubscribe = controller.subscribe(snapshots.append)

    token = controller.load_snapshot(source, "# Saved\n")

    assert token == ui.OperationToken(ui.OperationKind.INSPECT, 1)
    assert controller.state.status is ui.WorkspaceStatus.LOADING
    assert controller.state.active_operation == token
    assert controller.state.actions.can_cancel is True
    assert snapshots[-1] == controller.state

    runner.complete()

    assert controller.state.status is ui.WorkspaceStatus.POPULATED
    assert controller.state.source_path == source
    assert controller.state.saved_text == "# Saved\n"
    assert controller.state.editor_text == "# Saved\n"
    assert controller.state.active_operation is None
    assert controller.state.actions.can_validate is True
    assert controller.state.actions.can_build is True

    unsubscribe()
    controller.edit_text("# Changed\n")
    assert snapshots[-1].status is ui.WorkspaceStatus.POPULATED


def test_dirty_edits_disable_validate_and_build_without_source_io(tmp_path: Path):
    controller, runner, _source = _loaded_controller(tmp_path)
    call_count = len(runner.tasks)

    assert controller.edit_text("# Unsaved\n") is True
    assert controller.state.status is ui.WorkspaceStatus.DIRTY
    assert controller.state.dirty is True
    assert controller.state.saved_text == "# Saved\n"
    assert controller.state.editor_text == "# Unsaved\n"
    assert controller.state.actions.can_save is True
    assert controller.state.actions.can_validate is False
    assert controller.state.actions.can_build is False
    assert controller.validate() is None
    assert controller.build(tmp_path / "dirty.docx") is None
    assert len(runner.tasks) == call_count

    assert controller.discard_edits() is True
    assert controller.state.status is ui.WorkspaceStatus.POPULATED
    assert controller.state.editor_text == "# Saved\n"
    assert controller.state.dirty is False


def test_validate_maps_diagnostics_and_passes_template_path(tmp_path: Path):
    calls: list[tuple[Path, Path | None]] = []
    issue = ValidationIssue(
        code="heading-level-jump",
        severity="warning",
        message="Heading level jumps",
        line=8,
        target="H1->H3",
    )

    def validate(source, *, template_path=None):
        calls.append((Path(source), Path(template_path) if template_path else None))
        return _validation(Path(source), (issue,))

    controller, runner, source = _loaded_controller(tmp_path, validate=validate)
    template = tmp_path / "school.yaml"
    controller.load_snapshot(source, "# Saved\n", template_path=template)
    runner.complete()

    token = controller.validate()
    assert token == ui.OperationToken(ui.OperationKind.VALIDATE, 3)
    assert controller.state.status is ui.WorkspaceStatus.LOADING
    runner.complete()

    assert calls == [(source, template)]
    assert controller.state.status is ui.WorkspaceStatus.POPULATED
    assert controller.state.diagnostics == (ui.DiagnosticViewModel.from_issue(issue),)


def test_repeated_actions_are_suppressed_until_current_operation_finishes(
    tmp_path: Path,
):
    controller, runner, _source = _loaded_controller(tmp_path)

    token = controller.validate()

    assert token is not None
    assert controller.validate() is None
    assert controller.build(tmp_path / "thesis.docx") is None
    assert len(runner.tasks) == 2

    runner.complete()
    assert controller.build(tmp_path / "thesis.docx") is not None
    assert len(runner.tasks) == 3


def test_build_progress_and_output_are_published_in_application_stage_order(
    tmp_path: Path,
):
    calls: list[tuple[Path, Path, Path | None]] = []

    def build(source, output, *, template_path=None, on_progress=None):
        calls.append(
            (
                Path(source),
                Path(output),
                Path(template_path) if template_path else None,
            )
        )
        for stage in (BuildStage.PARSE, BuildStage.VALIDATE, BuildStage.FINALIZE):
            on_progress(stage)
        return BuildResult(output_path=Path(output), issues=())

    controller, runner, source = _loaded_controller(tmp_path, build=build)
    snapshots: list[ui.WorkspaceViewModel] = []
    controller.subscribe(snapshots.append)
    output = tmp_path / "thesis.docx"

    token = controller.build(output)
    runner.complete()

    assert token == ui.OperationToken(ui.OperationKind.BUILD, 2)
    assert calls == [(source, output, None)]
    assert [
        snapshot.progress.stage
        for snapshot in snapshots
        if snapshot.progress is not None and snapshot.progress.stage is not None
    ] == [BuildStage.PARSE, BuildStage.VALIDATE, BuildStage.FINALIZE]
    assert controller.state.status is ui.WorkspaceStatus.POPULATED
    assert controller.state.output == ui.OutputViewModel(path=output)


def test_generic_failure_enters_error_and_recovery_preserves_workspace(tmp_path: Path):
    controller, runner, source = _loaded_controller(tmp_path)

    controller.validate()
    runner.fail(RuntimeError("validator exploded"))

    assert controller.state.status is ui.WorkspaceStatus.ERROR
    assert controller.state.error_message == "validator exploded"
    assert controller.state.source_path == source
    assert controller.state.actions.can_recover is True
    assert controller.edit_text("# bypass\n") is False
    assert controller.discard_edits() is False
    assert controller.state.status is ui.WorkspaceStatus.ERROR
    assert controller.state.error_message == "validator exploded"

    assert controller.recover() is True
    assert controller.state.status is ui.WorkspaceStatus.POPULATED
    assert controller.state.error_message is None


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (RuntimeError("inspect failed"), ui.WorkspaceStatus.ERROR),
        (PermissionError("permission denied"), ui.WorkspaceStatus.PERMISSION),
    ],
)
def test_initial_inspect_failure_recovery_retries_before_populating(
    tmp_path: Path,
    error: Exception,
    expected_status: ui.WorkspaceStatus,
):
    runner = _DeferredTaskRunner()
    controller = ui.WorkspaceController(
        inspect=lambda path: _inspection(Path(path)),
        task_runner=runner,
    )

    controller.load_snapshot(tmp_path / "protected.md", "# Saved\n")
    runner.fail(error)

    assert controller.state.status is expected_status
    assert controller.state.error_message == str(error)
    assert controller.state.actions.can_recover is True
    assert controller.recover() is True
    assert controller.state.status is ui.WorkspaceStatus.LOADING
    assert controller.state.actions.can_validate is False
    assert controller.state.actions.can_build is False

    runner.complete(1)
    assert controller.state.status is ui.WorkspaceStatus.POPULATED


def test_initial_inspect_cancellation_recovery_retries_before_populating(
    tmp_path: Path,
):
    runner = _DeferredTaskRunner()
    controller = ui.WorkspaceController(
        inspect=lambda path: _inspection(Path(path)),
        task_runner=runner,
    )
    source = tmp_path / "thesis.md"
    controller.load_snapshot(source, "# Saved\n")

    assert controller.cancel_current() is True
    assert controller.state.status is ui.WorkspaceStatus.CANCELED
    assert controller.recover() is True
    assert controller.state.status is ui.WorkspaceStatus.LOADING

    runner.complete(0)
    assert controller.state.status is ui.WorkspaceStatus.LOADING
    runner.complete(1)
    assert controller.state.status is ui.WorkspaceStatus.POPULATED
    assert controller.state.source_path == source


def test_disable_during_initial_inspect_recovery_retries_before_populating(
    tmp_path: Path,
):
    runner = _DeferredTaskRunner()
    controller = ui.WorkspaceController(
        inspect=lambda path: _inspection(Path(path)),
        task_runner=runner,
    )
    controller.load_snapshot(tmp_path / "thesis.md", "# Saved\n")

    controller.disable("temporarily unavailable")
    assert controller.state.status is ui.WorkspaceStatus.DISABLED
    assert controller.recover() is True
    assert controller.state.status is ui.WorkspaceStatus.LOADING

    runner.complete(0)
    assert controller.state.status is ui.WorkspaceStatus.LOADING
    runner.complete(1)
    assert controller.state.status is ui.WorkspaceStatus.POPULATED


def test_disable_invalidates_active_operation_and_recovers_prior_state(tmp_path: Path):
    controller, runner, _source = _loaded_controller(tmp_path)
    controller.validate()

    controller.disable("feature unavailable")

    assert controller.state.status is ui.WorkspaceStatus.DISABLED
    assert controller.state.disabled_reason == "feature unavailable"
    assert controller.state.active_operation is None
    assert controller.state.actions.can_recover is True

    runner.complete()
    assert controller.state.status is ui.WorkspaceStatus.DISABLED
    assert controller.recover() is True
    assert controller.state.status is ui.WorkspaceStatus.POPULATED


def test_cancel_invalidates_late_success_error_and_progress_callbacks(tmp_path: Path):
    progress_calls: list[BuildStage] = []

    def build(_source, output, *, on_progress=None, **_kwargs):
        for stage in (BuildStage.PARSE, BuildStage.FINALIZE):
            progress_calls.append(stage)
            on_progress(stage)
        return BuildResult(output_path=Path(output), issues=())

    controller, runner, _source = _loaded_controller(tmp_path, build=build)
    output = tmp_path / "canceled.docx"
    controller.build(output)

    assert controller.cancel_current() is True
    assert controller.state.status is ui.WorkspaceStatus.CANCELED
    assert controller.state.active_operation is None
    assert controller.state.actions.can_recover is True

    runner.complete()
    runner.fail(RuntimeError("late failure"))

    assert progress_calls == [BuildStage.PARSE, BuildStage.FINALIZE]
    assert controller.state.status is ui.WorkspaceStatus.CANCELED
    assert controller.state.progress is None
    assert controller.state.output is None
    assert controller.state.error_message is None
    assert controller.cancel_current() is False

    assert controller.recover() is True
    assert controller.state.status is ui.WorkspaceStatus.POPULATED


def test_newer_snapshot_generation_wins_over_stale_success_and_error(tmp_path: Path):
    runner = _DeferredTaskRunner()
    controller = ui.WorkspaceController(
        inspect=lambda path: _inspection(Path(path)),
        task_runner=runner,
    )
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"

    first_token = controller.load_snapshot(first, "# First\n")
    second_token = controller.load_snapshot(second, "# Second\n")

    assert first_token.generation == 1
    assert second_token.generation == 2
    runner.complete(1)
    assert controller.state.status is ui.WorkspaceStatus.POPULATED
    assert controller.state.source_path == second

    runner.complete(0)
    runner.fail(RuntimeError("stale failure"), 0)
    assert controller.state.status is ui.WorkspaceStatus.POPULATED
    assert controller.state.source_path == second
    assert controller.state.editor_text == "# Second\n"
    assert controller.state.error_message is None


def test_scheduled_validation_freezes_source_and_template_inputs(tmp_path: Path):
    calls: list[tuple[Path, Path | None]] = []

    def validate(source, *, template_path=None):
        calls.append((Path(source), Path(template_path) if template_path else None))
        return _validation(Path(source))

    controller, runner, first_source = _loaded_controller(tmp_path, validate=validate)
    first_template = tmp_path / "first.yaml"
    second_source = tmp_path / "second.md"
    second_template = tmp_path / "second.yaml"
    controller.load_snapshot(first_source, "# First\n", template_path=first_template)
    runner.complete()
    controller.validate()
    controller.load_snapshot(second_source, "# Second\n", template_path=second_template)

    runner.complete(2)
    runner.complete(3)

    assert calls == [(first_source, first_template)]
    assert controller.state.source_path == second_source
    assert controller.state.template_path == second_template


def test_scheduled_build_freezes_source_template_and_output_inputs(tmp_path: Path):
    calls: list[tuple[Path, Path, Path | None]] = []

    def build(source, output, *, template_path=None, **_kwargs):
        calls.append(
            (
                Path(source),
                Path(output),
                Path(template_path) if template_path else None,
            )
        )
        return BuildResult(output_path=Path(output), issues=())

    controller, runner, first_source = _loaded_controller(tmp_path, build=build)
    first_template = tmp_path / "first.yaml"
    first_output = tmp_path / "first.docx"
    controller.load_snapshot(first_source, "# First\n", template_path=first_template)
    runner.complete()
    controller.build(first_output)
    controller.load_snapshot(
        tmp_path / "second.md",
        "# Second\n",
        template_path=tmp_path / "second.yaml",
    )

    runner.complete(2)
    assert controller.state.status is ui.WorkspaceStatus.LOADING
    assert controller.state.progress is not None
    assert controller.state.progress.operation.kind is ui.OperationKind.INSPECT
    assert controller.state.progress.stage is None
    runner.complete(3)

    assert calls == [(first_source, first_output, first_template)]
    assert controller.state.output is None


def test_editing_during_operation_invalidates_result_and_becomes_dirty(tmp_path: Path):
    controller, runner, _source = _loaded_controller(tmp_path)
    controller.validate()

    assert controller.edit_text("# Changed while validating\n") is True
    assert controller.state.status is ui.WorkspaceStatus.DIRTY
    assert controller.state.active_operation is None

    runner.complete()
    assert controller.state.status is ui.WorkspaceStatus.DIRTY
    assert controller.state.editor_text == "# Changed while validating\n"
    assert controller.state.diagnostics == ()


def test_failed_rebuild_preserves_previous_output_view_model(tmp_path: Path):
    controller, runner, _source = _loaded_controller(tmp_path)
    first_output = tmp_path / "first.docx"
    controller.build(first_output)
    runner.complete()
    assert controller.state.output == ui.OutputViewModel(first_output)

    controller.build(tmp_path / "second.docx")
    runner.fail(RuntimeError("render failed"))

    assert controller.state.status is ui.WorkspaceStatus.ERROR
    assert controller.state.output == ui.OutputViewModel(first_output)


def test_reset_invalidates_pending_work_and_restores_empty_state(tmp_path: Path):
    controller, runner, _source = _loaded_controller(tmp_path)
    controller.validate()

    controller.reset()
    runner.complete()

    assert controller.state == ui.WorkspaceViewModel()


def test_synchronous_task_runner_reports_success_and_failure():
    runner = ui.SynchronousTaskRunner()
    results: list[object] = []
    errors: list[Exception] = []

    runner.submit(lambda: 42, on_success=results.append, on_error=errors.append)
    runner.submit(
        lambda: (_ for _ in ()).throw(ValueError("boom")),
        on_success=results.append,
        on_error=errors.append,
    )

    assert results == [42]
    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)
