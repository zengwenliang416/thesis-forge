from __future__ import annotations

import json
import sys
from pathlib import Path

from thesis_forge.adapters import (
    PROTOCOL_VERSION,
    DesktopRuntime,
    WorkbenchCommandDispatcher,
    stream_json_lines,
)
from thesis_forge.adapters.sidecar import _configure_standard_streams
from thesis_forge.application import BuildResult, BuildStage


def test_sidecar_forces_utf8_standard_streams(monkeypatch):
    class ReconfigurableStream:
        def __init__(self):
            self.encoding = "cp1252"
            self.errors = "replace"

        def reconfigure(self, *, encoding, errors):
            self.encoding = encoding
            self.errors = errors

        def write(self, value):
            return len(value.encode(self.encoding, errors=self.errors))

    streams = [ReconfigurableStream() for _ in range(3)]
    monkeypatch.setattr(sys, "stdin", streams[0])
    monkeypatch.setattr(sys, "stdout", streams[1])
    monkeypatch.setattr(sys, "stderr", streams[2])

    _configure_standard_streams()

    assert [(stream.encoding, stream.errors) for stream in streams] == [
        ("utf-8", "strict"),
        ("utf-8", "strict"),
        ("utf-8", "strict"),
    ]
    assert streams[1].write("绪论") == len("绪论".encode())


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
