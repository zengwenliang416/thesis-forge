from __future__ import annotations

import pytest

from docforge.application.contracts import (
    BuildReportStage,
    BuildStage,
    BuildStageStatus,
)
from docforge.application.services import BuildStageLifecycle


def test_validation_failure_keeps_started_stage_running_then_skips_downstream() -> None:
    lifecycle = BuildStageLifecycle()

    assert all(
        state.status is BuildStageStatus.PENDING
        for state in lifecycle.snapshot()
    )

    lifecycle.start(BuildStage.PARSE)
    assert lifecycle.state(BuildStage.PARSE).status is BuildStageStatus.RUNNING
    lifecycle.succeed(BuildStage.PARSE)

    lifecycle.start(BuildStage.VALIDATE)
    assert lifecycle.state(BuildStage.VALIDATE).status is BuildStageStatus.RUNNING
    lifecycle.fail(BuildStage.VALIDATE)
    skipped = lifecycle.skip_downstream(BuildStage.VALIDATE)

    assert lifecycle.state(BuildStage.VALIDATE).status is BuildStageStatus.FAILED
    assert [state.name for state in skipped] == [
        BuildReportStage.COMPILE,
        BuildReportStage.RENDER,
        BuildReportStage.FINALIZE,
        BuildReportStage.POSTFLIGHT,
        BuildReportStage.PREVIEW,
    ]
    assert all(
        state.status is BuildStageStatus.SKIPPED
        for state in lifecycle.snapshot()[2:]
    )


def test_transition_history_is_ordered_and_does_not_skip_started_state() -> None:
    lifecycle = BuildStageLifecycle()

    lifecycle.start(BuildStage.PARSE)
    lifecycle.succeed(BuildStage.PARSE)
    lifecycle.start(BuildStage.VALIDATE)

    assert [(state.name, state.status) for state in lifecycle.history()] == [
        (BuildReportStage.PARSE, BuildStageStatus.RUNNING),
        (BuildReportStage.PARSE, BuildStageStatus.SUCCEEDED),
        (BuildReportStage.VALIDATE, BuildStageStatus.RUNNING),
    ]
    assert lifecycle.state(BuildStage.VALIDATE).status is not BuildStageStatus.SUCCEEDED


def test_terminalize_failure_marks_current_failed_and_downstream_skipped() -> None:
    lifecycle = BuildStageLifecycle()

    lifecycle.start(BuildStage.PARSE)
    lifecycle.succeed(BuildStage.PARSE)
    lifecycle.start(BuildStage.VALIDATE)

    snapshot = lifecycle.terminalize(BuildStage.VALIDATE)

    assert [(state.name, state.status) for state in snapshot] == [
        (BuildReportStage.PARSE, BuildStageStatus.SUCCEEDED),
        (BuildReportStage.VALIDATE, BuildStageStatus.FAILED),
        (BuildReportStage.COMPILE, BuildStageStatus.SKIPPED),
        (BuildReportStage.RENDER, BuildStageStatus.SKIPPED),
        (BuildReportStage.FINALIZE, BuildStageStatus.SKIPPED),
        (BuildReportStage.POSTFLIGHT, BuildStageStatus.SKIPPED),
        (BuildReportStage.PREVIEW, BuildStageStatus.SKIPPED),
    ]
    assert all(
        state.status
        not in {BuildStageStatus.PENDING, BuildStageStatus.RUNNING}
        for state in snapshot
    )


def test_terminalize_cancellation_closes_pending_checkpoint_and_downstream() -> None:
    lifecycle = BuildStageLifecycle()

    lifecycle.start(BuildStage.PARSE)
    lifecycle.succeed(BuildStage.PARSE)

    snapshot = lifecycle.terminalize(BuildStage.VALIDATE, canceled=True)

    assert lifecycle.state(BuildStage.VALIDATE).status is BuildStageStatus.SKIPPED
    assert all(
        state.status is BuildStageStatus.SKIPPED
        for state in snapshot[2:]
    )
    assert all(
        state.status
        not in {BuildStageStatus.PENDING, BuildStageStatus.RUNNING}
        for state in snapshot
    )


def test_terminalize_rejects_non_active_failure_and_cancellation() -> None:
    lifecycle = BuildStageLifecycle()

    lifecycle.start(BuildStage.PARSE)
    lifecycle.succeed(BuildStage.PARSE)
    with pytest.raises(ValueError, match="must be running"):
        lifecycle.terminalize(BuildStage.VALIDATE)

    lifecycle.start(BuildStage.VALIDATE)
    lifecycle.succeed(BuildStage.VALIDATE)
    with pytest.raises(ValueError, match="must be pending or running"):
        lifecycle.terminalize(BuildStage.VALIDATE, canceled=True)


def test_terminalize_rejects_an_unfinished_upstream_stage() -> None:
    lifecycle = BuildStageLifecycle()
    lifecycle.start(BuildStage.PARSE)

    with pytest.raises(ValueError, match="must be terminal before validate"):
        lifecycle.terminalize(BuildStage.VALIDATE, canceled=True)


def test_terminalize_closes_unstarted_upstream_as_skipped() -> None:
    lifecycle = BuildStageLifecycle()

    snapshot = lifecycle.terminalize(BuildStage.COMPILE, canceled=True)

    assert [(state.name, state.status) for state in snapshot[:3]] == [
        (BuildReportStage.PARSE, BuildStageStatus.SKIPPED),
        (BuildReportStage.VALIDATE, BuildStageStatus.SKIPPED),
        (BuildReportStage.COMPILE, BuildStageStatus.SKIPPED),
    ]
    assert all(
        state.status
        not in {BuildStageStatus.PENDING, BuildStageStatus.RUNNING}
        for state in snapshot
    )


def test_terminalize_rejection_does_not_mutate_state_or_history() -> None:
    lifecycle = BuildStageLifecycle()

    with pytest.raises(ValueError, match="must be running"):
        lifecycle.terminalize(BuildStage.COMPILE)
    assert all(
        state.status is BuildStageStatus.PENDING
        for state in lifecycle.snapshot()
    )
    assert lifecycle.history() == ()

    lifecycle.start(BuildStage.PARSE)
    with pytest.raises(ValueError, match="must be terminal before compile"):
        lifecycle.terminalize(BuildStage.COMPILE, canceled=True)
    assert lifecycle.state(BuildStage.PARSE).status is BuildStageStatus.RUNNING
    assert all(
        state.status is BuildStageStatus.PENDING
        for state in lifecycle.snapshot()[1:]
    )
    assert [(state.name, state.status) for state in lifecycle.history()] == [
        (BuildReportStage.PARSE, BuildStageStatus.RUNNING),
    ]


def test_invalid_transition_is_rejected() -> None:
    lifecycle = BuildStageLifecycle()

    with pytest.raises(ValueError, match="must be running"):
        lifecycle.succeed(BuildStage.VALIDATE)

    lifecycle.start(BuildStage.PARSE)
    with pytest.raises(ValueError, match="must be pending"):
        lifecycle.start(BuildStage.PARSE)
