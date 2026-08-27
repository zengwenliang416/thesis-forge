from __future__ import annotations

import io
import json
import threading
from pathlib import Path

import pytest

from docforge.adapters import (
    PROTOCOL_VERSION,
    DesktopRuntime,
    WebWorkspaceRuntime,
    WorkbenchCommandDispatcher,
    WorkbenchHttpApp,
)
from docforge.application import BuildCanceledError, BuildResult, BuildStage


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


def _get_environ(path: str) -> dict:
    return {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "CONTENT_LENGTH": "0",
        "wsgi.input": io.BytesIO(),
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
    assert len(remaining) == 1
    assert remaining[0]["protocol"] == PROTOCOL_VERSION
    assert remaining[0]["requestId"] == "build-stream-1"
    assert remaining[0]["type"] == "completed"
    assert "error" not in remaining[0]
    report = remaining[0]["report"]
    assert report["schemaVersion"] == "docforge.build-report.v2"
    assert report["outcome"] == "canceled"
    assert report["failedStage"] == "validate"
    assert report["primaryDiagnosticId"] == "build-error-1"
    assert report["diagnostics"][0]["code"] == "TF-BUILD-CANCELED"
    assert all(event["type"] != "error" for event in remaining)
    assert not output.exists()


def test_http_dispatch_preserves_project_identity_snapshot_and_output(
    tmp_path: Path,
):
    class EchoDispatcher:
        def dispatch(self, request: dict) -> dict:
            return {
                "protocol": PROTOCOL_VERSION,
                "requestId": request["requestId"],
                "ok": True,
                "result": request["payload"],
            }

    project_root = (tmp_path / "project").resolve()
    project_root.mkdir()
    manifest = project_root / "docforge.yaml"
    payload = {
        "project": {
            "id": "http-fixture",
            "root": str(project_root),
            "manifestPath": str(manifest),
        },
        "text": "# 未保存\n",
        "output": {
            "kind": "web-download",
            "workspaceId": "a" * 32,
            "fileName": "document.docx",
            "downloadId": "a" * 32,
        },
    }
    app = WorkbenchHttpApp(EchoDispatcher())

    body = b"".join(
        app(
            _environ(
                "/api/v1/dispatch",
                {
                    "protocol": PROTOCOL_VERSION,
                    "requestId": "http-project-1",
                    "operation": "build",
                    "payload": payload,
                },
            ),
            lambda _status, _headers: None,
        )
    )

    response = json.loads(body)
    assert response["ok"] is True
    assert response["result"]["project"] == payload["project"]
    assert response["result"]["text"] == "# 未保存\n"
    assert response["result"]["output"] == payload["output"]


def test_http_rejects_malformed_project_payload(tmp_path: Path):
    app = WorkbenchHttpApp(WorkbenchCommandDispatcher(runtime=DesktopRuntime()))

    body = b"".join(
        app(
            _environ(
                "/api/v1/dispatch",
                {
                    "protocol": PROTOCOL_VERSION,
                    "requestId": "http-project-invalid",
                    "operation": "inspect",
                    "payload": {
                        "project": {
                            "id": "http-fixture",
                            "root": 42,
                            "manifestPath": str(tmp_path / "docforge.yaml"),
                        }
                    },
                },
            ),
            lambda _status, _headers: None,
        )
    )

    response = json.loads(body)
    assert response["ok"] is False
    assert response["error"]["kind"] == "request"


@pytest.mark.parametrize(
    "project",
    [
        {
            "id": "   ",
            "root": "/tmp/project",
            "manifestPath": "/tmp/project/docforge.yaml",
        },
        {
            "id": "http-fixture",
            "root": "relative/project",
            "manifestPath": "relative/project/docforge.yaml",
        },
    ],
)
@pytest.mark.parametrize("path", ["/api/v1/dispatch", "/api/v1/build-stream"])
def test_http_rejects_semantically_invalid_project_identity_before_dispatch(
    tmp_path: Path,
    project: dict,
    path: str,
):
    class RecordingDispatcher:
        def __init__(self):
            self.calls = 0

        def dispatch(self, _request):
            self.calls += 1
            return {"protocol": PROTOCOL_VERSION, "ok": True}

    dispatcher = RecordingDispatcher()
    app = WorkbenchHttpApp(dispatcher)
    request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "invalid-project-identity",
        "operation": "build" if path.endswith("build-stream") else "inspect",
        "payload": {
            "project": project,
            "text": "# 未保存\n",
            "output": {
                "kind": "desktop",
                "path": str(tmp_path / "document.docx"),
                "fileName": "document.docx",
            },
        },
    }

    if path.endswith("build-stream"):
        response = b"".join(
            app(
                _environ(path, request),
                lambda _status, _headers: None,
            )
        )
        assert json.loads(response)["error"]["kind"] == "request"
    else:
        response = b"".join(
            app(
                _environ(path, request),
                lambda _status, _headers: None,
            )
        )
        assert json.loads(response)["error"]["kind"] == "request"
    assert dispatcher.calls == 0


def test_http_serves_only_workspace_bound_pdf_bytes_with_safe_headers(
    tmp_path: Path,
):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")
    source = runtime.create_workspace("document.md", "# 绪论\n")
    pdf = runtime.root / source["workspaceId"] / "document.preview.pdf"
    content = b"%PDF-1.7\npreview"
    pdf.write_bytes(content)
    app = WorkbenchHttpApp(
        WorkbenchCommandDispatcher(runtime=runtime),
        web_runtime=runtime,
    )
    statuses: list[str] = []
    headers: list[list[tuple[str, str]]] = []

    body = b"".join(
        app(
            _get_environ(
                f"/api/v1/workspaces/{source['workspaceId']}/files/{pdf.name}"
            ),
            lambda status, values: (statuses.append(status), headers.append(values)),
        )
    )

    assert statuses == ["200 OK"]
    assert body == content
    assert ("Content-Type", "application/pdf") in headers[0]
    assert ("Content-Length", str(len(content))) in headers[0]
    assert ("Cache-Control", "no-store") in headers[0]
    assert ("X-Content-Type-Options", "nosniff") in headers[0]


def test_http_live_preview_pdf_is_consumed_and_cleans_its_docx(tmp_path: Path):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")
    source = runtime.create_workspace("document.md", "# 绪论\n")
    output = runtime.prepare_live_preview_output(source)
    docx = runtime.output_path(output)
    pdf = docx.with_suffix(".preview.pdf")
    docx.write_bytes(b"docx")
    pdf.write_bytes(b"%PDF-1.7\npreview")
    app = WorkbenchHttpApp(
        WorkbenchCommandDispatcher(runtime=runtime),
        web_runtime=runtime,
    )

    body = b"".join(
        app(
            _get_environ(
                f"/api/v1/workspaces/{source['workspaceId']}/live-previews/"
                f"{output['livePreviewId']}"
            ),
            lambda _status, _headers: None,
        )
    )

    assert body == b"%PDF-1.7\npreview"
    assert not pdf.exists()
    assert not docx.exists()


def test_http_named_like_live_preview_regular_pdf_is_not_consumed(tmp_path: Path):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")
    source = runtime.create_workspace("document.md", "# 绪论\n")
    workspace = runtime.root / source["workspaceId"]
    token = "c" * 32
    docx = workspace / f".docforge-live-preview-{token}.docx"
    pdf = workspace / f".docforge-live-preview-{token}.preview.pdf"
    docx.write_bytes(b"formal docx")
    pdf.write_bytes(b"%PDF-1.7\nformal")
    app = WorkbenchHttpApp(
        WorkbenchCommandDispatcher(runtime=runtime),
        web_runtime=runtime,
    )

    body = b"".join(
        app(
            _get_environ(
                f"/api/v1/workspaces/{source['workspaceId']}/files/{pdf.name}"
            ),
            lambda _status, _headers: None,
        )
    )

    assert body == b"%PDF-1.7\nformal"
    assert pdf.exists()
    assert docx.exists()


def test_http_can_discard_unread_live_preview_idempotently(tmp_path: Path):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")
    source = runtime.create_workspace("document.md", "# 绪论\n")
    output = runtime.prepare_live_preview_output(source)
    docx = runtime.output_path(output)
    pdf = docx.with_suffix(".preview.pdf")
    docx.write_bytes(b"docx")
    pdf.write_bytes(b"%PDF-1.7\npreview")
    app = WorkbenchHttpApp(
        WorkbenchCommandDispatcher(runtime=runtime),
        web_runtime=runtime,
    )

    for _ in range(2):
        statuses: list[str] = []
        body = b"".join(
            app(
                _environ(
                    "/api/v1/live-previews/discard",
                    {"output": output},
                ),
                lambda status, _headers, statuses=statuses: statuses.append(status),
            )
        )
        assert statuses == ["200 OK"]
        assert json.loads(body)["ok"] is True

    assert not pdf.exists()
    assert not docx.exists()


def test_http_rejects_invalid_workspace_pdf_requests(tmp_path: Path):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")
    source = runtime.create_workspace("document.md", "# 绪论\n")
    workspace = runtime.root / source["workspaceId"]
    (workspace / "not-pdf.pdf").write_bytes(b"not a pdf")
    other = runtime.create_workspace("other.md", "# 其他\n")
    (runtime.root / other["workspaceId"] / "other.pdf").write_bytes(b"%PDF-1.7\n")
    app = WorkbenchHttpApp(
        WorkbenchCommandDispatcher(runtime=runtime),
        web_runtime=runtime,
    )

    cases = [
        (f"/api/v1/workspaces/{source['workspaceId']}/files/document.docx", "400"),
        (f"/api/v1/workspaces/{source['workspaceId']}/files/not-pdf.pdf", "400"),
        (f"/api/v1/workspaces/{source['workspaceId']}/files/missing.pdf", "404"),
        (f"/api/v1/workspaces/{'g' * 32}/files/missing.pdf", "400"),
        (f"/api/v1/workspaces/{source['workspaceId']}/files/../other.pdf", "404"),
        (
            f"/api/v1/workspaces/{source['workspaceId']}/files/other.pdf",
            "404",
        ),
    ]

    for path, expected_status in cases:
        statuses: list[str] = []
        headers: list[list[tuple[str, str]]] = []
        b"".join(
            app(
                _get_environ(path),
                lambda status, values, statuses=statuses, headers=headers: (
                    statuses.append(status),
                    headers.append(values),
                ),
            )
        )
        assert statuses[0].startswith(expected_status)
        assert ("Cache-Control", "no-store") in headers[0]
        assert ("X-Content-Type-Options", "nosniff") in headers[0]
