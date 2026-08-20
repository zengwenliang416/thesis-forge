from __future__ import annotations

import pytest

from thesis_forge.application.contracts import (
    BuildReportStage,
    BuildStage,
    BuildStageStatus,
)
from thesis_forge.application.services import BuildStageLifecycle


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


def test_invalid_transition_is_rejected() -> None:
    lifecycle = BuildStageLifecycle()

    with pytest.raises(ValueError, match="must be running"):
        lifecycle.succeed(BuildStage.VALIDATE)

    lifecycle.start(BuildStage.PARSE)
    with pytest.raises(ValueError, match="must be pending"):
        lifecycle.start(BuildStage.PARSE)
