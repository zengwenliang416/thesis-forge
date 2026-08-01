from __future__ import annotations

import io
import json
import threading
from pathlib import Path

from thesis_forge.adapters import (
    PROTOCOL_VERSION,
    DesktopRuntime,
    WorkbenchCommandDispatcher,
    WorkbenchHttpApp,
)
from thesis_forge.application import BuildCanceledError, BuildResult, BuildStage


def _request(source: Path, output: Path) -> dict:
    return {
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-stream-1",
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


def _environ(path: str, body: dict) -> dict:
    encoded = json.dumps(body).encode()
    return {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(encoded)),
        "wsgi.input": io.BytesIO(encoded),
    }


def test_http_build_stream_is_incremental_and_cancelable(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论\n", encoding="utf-8")
    output = tmp_path / "thesis.docx"
    continue_build = threading.Event()

    def build(_source, output_path, *, on_progress=None, should_cancel=None, **_kwargs):
        on_progress(BuildStage.PARSE)
        continue_build.wait(timeout=2)
        if should_cancel():
            raise BuildCanceledError(BuildStage.VALIDATE)
        Path(output_path).write_bytes(b"docx")
        return BuildResult(output_path=Path(output_path), issues=())

    app = WorkbenchHttpApp(
        WorkbenchCommandDispatcher(runtime=DesktopRuntime(), build=build)
    )
    statuses: list[str] = []
    headers: list[list[tuple[str, str]]] = []
    stream = iter(
        app(
            _environ("/api/v1/build-stream", _request(source, output)),
            lambda status, values: (statuses.append(status), headers.append(values)),
        )
    )

    first = json.loads(next(stream))
    assert first == {
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-stream-1",
        "type": "progress",
        "stage": "parse",
    }

    cancel_statuses: list[str] = []
    cancel_body = b"".join(
        app(
            _environ(
                "/api/v1/build-cancel",
                {"requestId": "build-stream-1"},
            ),
            lambda status, _headers: cancel_statuses.append(status),
        )
    )
    continue_build.set()
    remaining = [json.loads(line) for line in stream]

    assert statuses == ["200 OK"]
    assert (
        "Content-Type",
        "application/x-ndjson; charset=utf-8",
    ) in headers[0]
    assert cancel_statuses == ["202 Accepted"]
    assert json.loads(cancel_body)["ok"] is True
    assert remaining == [
        {
            "protocol": PROTOCOL_VERSION,
            "requestId": "build-stream-1",
            "type": "error",
            "error": {
                "kind": "canceled",
                "message": "构建已取消",
                "stage": "validate",
            },
        }
    ]
    assert not output.exists()
