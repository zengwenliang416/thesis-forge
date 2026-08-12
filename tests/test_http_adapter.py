from __future__ import annotations

import io
import json
import threading
from pathlib import Path

from thesis_forge.adapters import (
    PROTOCOL_VERSION,
    DesktopRuntime,
    WebWorkspaceRuntime,
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


def test_http_serves_only_workspace_bound_pdf_bytes_with_safe_headers(
    tmp_path: Path,
):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")
    source = runtime.create_workspace("thesis.md", "# 绪论\n")
    pdf = runtime.root / source["workspaceId"] / "thesis.preview.pdf"
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
    source = runtime.create_workspace("thesis.md", "# 绪论\n")
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
    source = runtime.create_workspace("thesis.md", "# 绪论\n")
    workspace = runtime.root / source["workspaceId"]
    token = "c" * 32
    docx = workspace / f".thesisforge-live-preview-{token}.docx"
    pdf = workspace / f".thesisforge-live-preview-{token}.preview.pdf"
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
    source = runtime.create_workspace("thesis.md", "# 绪论\n")
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
    source = runtime.create_workspace("thesis.md", "# 绪论\n")
    workspace = runtime.root / source["workspaceId"]
    (workspace / "not-pdf.pdf").write_bytes(b"not a pdf")
    other = runtime.create_workspace("other.md", "# 其他\n")
    (runtime.root / other["workspaceId"] / "other.pdf").write_bytes(b"%PDF-1.7\n")
    app = WorkbenchHttpApp(
        WorkbenchCommandDispatcher(runtime=runtime),
        web_runtime=runtime,
    )

    cases = [
        (f"/api/v1/workspaces/{source['workspaceId']}/files/thesis.docx", "400"),
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
