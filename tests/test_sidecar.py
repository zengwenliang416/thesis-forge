from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from thesis_forge import application
from thesis_forge.adapters import (
    PROTOCOL_VERSION,
    DesktopRuntime,
    WorkbenchCommandDispatcher,
    stream_json_lines,
)
from thesis_forge.adapters.sidecar import (
    _configure_standard_streams,
    create_dispatcher,
)
from thesis_forge.application import BuildResult, BuildStage
from thesis_forge.application.contracts import ProjectRequestIntent


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

    def build(_source, _output, *, on_progress=None, should_cancel=None, **_kwargs):
        on_progress(BuildStage.PARSE)
        observed.append(should_cancel())
        raise application.BuildCanceledError(BuildStage.VALIDATE)

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
    report = json.loads(events[-1])["report"]
    assert json.loads(events[-1])["type"] == "completed"
    statuses = {stage["name"]: stage["status"] for stage in report["stages"]}
    assert statuses == {
        "parse": "succeeded",
        "validate": "skipped",
        "compile": "skipped",
        "render": "skipped",
        "finalize": "skipped",
        "postflight": "skipped",
        "preview": "skipped",
    }


def test_sidecar_renderer_failure_preserves_lifecycle_provenance(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论\n", encoding="utf-8")
    output = tmp_path / "thesis.docx"

    def build(_source, _output, *, on_progress=None, **_kwargs):
        for stage in (
            BuildStage.PARSE,
            BuildStage.VALIDATE,
            BuildStage.COMPILE,
            BuildStage.RENDER,
        ):
            on_progress(stage)
        raise application.ApplicationStageError(
            BuildStage.RENDER,
            RuntimeError("renderer exploded"),
        )

    dispatcher = WorkbenchCommandDispatcher(
        runtime=DesktopRuntime(),
        build=build,
    )
    request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "sidecar-render-failure-1",
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

    event = json.loads(
        list(stream_json_lines(dispatcher, json.dumps(request)))[-1]
    )
    assert event["type"] == "completed"
    statuses = {stage["name"]: stage["status"] for stage in event["report"]["stages"]}
    assert statuses == {
        "parse": "succeeded",
        "validate": "succeeded",
        "compile": "succeeded",
        "render": "failed",
        "finalize": "skipped",
        "postflight": "skipped",
        "preview": "skipped",
    }


def test_sidecar_build_event_exposes_only_the_strict_preview_descriptor(
    tmp_path: Path,
):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论\n", encoding="utf-8")
    output = tmp_path / "thesis.docx"

    def build(_source, output_path, **_kwargs):
        output_path = Path(output_path)
        preview_path = output_path.with_suffix(".preview.pdf")
        return SimpleNamespace(
            output_path=output_path,
            issues=(),
            final_preview=SimpleNamespace(
                path=preview_path,
                name=preview_path.name,
                engine="libreoffice",
                label="LibreOffice PDF",
            ),
        )

    dispatcher = WorkbenchCommandDispatcher(runtime=DesktopRuntime(), build=build)
    request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "sidecar-preview-1",
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

    event = json.loads(
        list(stream_json_lines(dispatcher, json.dumps(request)))[-1]
    )

    assert event["result"]["output"]["finalPreview"] == {
        "engine": "libreoffice",
        "label": "LibreOffice PDF",
        "fileName": "thesis.preview.pdf",
    }
    assert str(tmp_path) not in json.dumps(event)


def test_sidecar_project_request_preserves_identity_and_cancellation(
    tmp_path: Path,
) -> None:
    project_root = (tmp_path / "project").resolve()
    project_root.mkdir()
    source = project_root / "thesis.md"
    source.write_text("# 绪论\n", encoding="utf-8")
    manifest = project_root / "thesisforge.yaml"
    manifest.write_text("schema: thesisforge.project.v2\n", encoding="utf-8")
    output = project_root / "build" / "thesis.docx"
    observed = []

    class ProjectService:
        def build(self, request, *, on_progress=None, should_cancel=None):
            observed.append(request)
            on_progress(BuildStage.PARSE)
            assert should_cancel is not None and should_cancel()
            raise application.BuildCanceledError(BuildStage.VALIDATE)

    dispatcher = create_dispatcher()
    dispatcher._project_service = ProjectService()
    request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "sidecar-project-cancel-1",
        "operation": "build",
        "payload": {
            "project": {
                "id": "sidecar-fixture",
                "root": str(project_root),
                "manifestPath": str(manifest),
            },
            "source": {
                "kind": "desktop",
                "path": str(source),
                "fileName": source.name,
            },
            "text": "# 未保存\n",
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
    report = json.loads(events[-1])["report"]

    assert observed[0].project.project_id == "sidecar-fixture"
    assert observed[0].intent is ProjectRequestIntent.BUILD
    assert observed[0].editor_snapshot == "# 未保存\n"
    assert json.loads(events[-1])["type"] == "completed"
    assert report["outcome"] == "canceled"
