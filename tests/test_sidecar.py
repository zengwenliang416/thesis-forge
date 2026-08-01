from __future__ import annotations

import json
from pathlib import Path

from thesis_forge.adapters import (
    PROTOCOL_VERSION,
    DesktopRuntime,
    WorkbenchCommandDispatcher,
    stream_json_lines,
)
from thesis_forge.application import BuildResult, BuildStage


def test_sidecar_build_stream_uses_the_shared_event_contract(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论\n", encoding="utf-8")
    output = tmp_path / "thesis.docx"

    def build(_source, output_path, *, on_progress=None, **_kwargs):
        on_progress(BuildStage.PARSE)
        on_progress(BuildStage.FINALIZE)
        Path(output_path).write_bytes(b"docx")
        return BuildResult(output_path=Path(output_path), issues=())

    dispatcher = WorkbenchCommandDispatcher(
        runtime=DesktopRuntime(),
        build=build,
    )
    request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "sidecar-build-1",
        "operation": "build",
        "payload": {
            "source": {
                "kind": "desktop",
                "path": str(source),
                "fileName": source.name,
            },
            "output": {
                "kind": "desktop",
                "path": str(output),
                "fileName": output.name,
            },
        },
    }

    events = [
        json.loads(line)
        for line in stream_json_lines(dispatcher, json.dumps(request))
    ]

    assert [event["type"] for event in events] == [
        "progress",
        "progress",
        "success",
    ]
    assert [event.get("stage") for event in events] == [
        "parse",
        "finalize",
        None,
    ]
    assert all(event["requestId"] == "sidecar-build-1" for event in events)


def test_sidecar_build_stream_passes_per_request_cancellation(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论\n", encoding="utf-8")
    output = tmp_path / "thesis.docx"
    observed: list[bool] = []

    def build(_source, _output, *, should_cancel=None, **_kwargs):
        observed.append(should_cancel())
        raise RuntimeError("stop")

    dispatcher = WorkbenchCommandDispatcher(
        runtime=DesktopRuntime(),
        build=build,
    )
    request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "sidecar-cancel-1",
        "operation": "build",
        "payload": {
            "source": {
                "kind": "desktop",
                "path": str(source),
                "fileName": source.name,
            },
            "output": {
                "kind": "desktop",
                "path": str(output),
                "fileName": output.name,
            },
        },
    }

    events = list(
        stream_json_lines(
            dispatcher,
            json.dumps(request),
            should_cancel=lambda: True,
        )
    )

    assert observed == [True]
    assert json.loads(events[-1])["type"] == "error"
