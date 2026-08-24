from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from threading import Event, Lock
from typing import Protocol

from .dto import PROTOCOL_VERSION, read_project_request_payload


class Dispatcher(Protocol):
    def dispatch(self, request: dict) -> dict: ...


class WebRuntime(Protocol):
    def create_project_workspace(
        self,
        project: object,
        manifest: object,
        source: object,
    ) -> dict: ...

    def read_pdf(self, workspace_id: object, file_name: object) -> bytes: ...

    def prepare_live_preview_output(self, source: dict) -> dict: ...

    def release_live_preview_output(self, output: dict) -> None: ...

    def read_live_preview(
        self,
        workspace_id: object,
        live_preview_id: object,
    ) -> bytes: ...


StartResponse = Callable[[str, list[tuple[str, str]]], object]


class WorkbenchHttpApp:
    def __init__(
        self,
        dispatcher: Dispatcher,
        *,
        web_runtime: WebRuntime | None = None,
    ) -> None:
        self._dispatcher = dispatcher
        self._web_runtime = web_runtime
        self._build_cancellations: dict[str, Event] = {}
        self._cancellation_lock = Lock()

    def __call__(
        self,
        environ: dict,
        start_response: StartResponse,
    ) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD")
        path = environ.get("PATH_INFO")
        if method == "GET":
            return self._get(path, start_response)
        if method != "POST":
            payload = {"ok": False, "error": {"kind": "request", "message": "not found"}}
            status = "404 Not Found"
        else:
            try:
                length = int(environ.get("CONTENT_LENGTH") or 0)
                raw = environ["wsgi.input"].read(length)
                request = json.loads(raw.decode("utf-8"))
                if not isinstance(request, dict):
                    raise TypeError("request body must be an object")
                if path in {"/api/v1/dispatch", "/api/v1/build-stream"}:
                    request_payload = request.get("payload")
                    if isinstance(request_payload, dict) and "project" in request_payload:
                        read_project_request_payload(request_payload)
                if path == "/api/v1/build-stream":
                    request_id = request.get("requestId")
                    if not isinstance(request_id, str) or not request_id:
                        raise ValueError("requestId is required")
                    cancellation = Event()
                    with self._cancellation_lock:
                        self._build_cancellations[request_id] = cancellation
                    start_response(
                        "200 OK",
                        [
                            (
                                "Content-Type",
                                "application/x-ndjson; charset=utf-8",
                            ),
                            ("Cache-Control", "no-store"),
                        ],
                    )
                    return self._build_stream(request, request_id, cancellation)
                if path == "/api/v1/build-cancel":
                    request_id = request.get("requestId")
                    if not isinstance(request_id, str) or not request_id:
                        raise ValueError("requestId is required")
                    with self._cancellation_lock:
                        cancellation = self._build_cancellations.get(request_id)
                    if cancellation is not None:
                        cancellation.set()
                    payload = {
                        "protocol": PROTOCOL_VERSION,
                        "requestId": request_id,
                        "ok": True,
                    }
                    status = "202 Accepted"
                elif path == "/api/v1/dispatch":
                    payload = self._dispatcher.dispatch(request)
                    status = "200 OK"
                elif path == "/api/v1/workspaces" and self._web_runtime is not None:
                    if set(request) != {"project", "manifest", "source"}:
                        raise ValueError(
                            "project, manifest and source are required"
                        )
                    opened = self._web_runtime.create_project_workspace(
                        request["project"],
                        request["manifest"],
                        request["source"],
                    )
                    payload = {
                        "protocol": PROTOCOL_VERSION,
                        "ok": True,
                        **opened,
                    }
                    status = "201 Created"
                elif (
                    path == "/api/v1/live-previews"
                    and self._web_runtime is not None
                ):
                    source = request.get("source")
                    if not isinstance(source, dict):
                        raise ValueError("source is required")
                    output = self._web_runtime.prepare_live_preview_output(source)
                    payload = {
                        "protocol": PROTOCOL_VERSION,
                        "ok": True,
                        "output": output,
                    }
                    status = "201 Created"
                elif (
                    path == "/api/v1/live-previews/discard"
                    and self._web_runtime is not None
                ):
                    output = request.get("output")
                    if not isinstance(output, dict):
                        raise ValueError("output is required")
                    self._web_runtime.release_live_preview_output(output)
                    payload = {
                        "protocol": PROTOCOL_VERSION,
                        "ok": True,
                    }
                    status = "200 OK"
                else:
                    payload = {
                        "ok": False,
                        "error": {"kind": "request", "message": "not found"},
                    }
                    status = "404 Not Found"
            except (
                KeyError,
                TypeError,
                UnicodeDecodeError,
                ValueError,
                json.JSONDecodeError,
            ) as error:
                payload = {
                    "ok": False,
                    "error": {"kind": "request", "message": str(error)},
                }
                status = "400 Bad Request"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        start_response(
            status,
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [body]

    def _get(
        self,
        path: object,
        start_response: StartResponse,
    ) -> Iterable[bytes]:
        prefix = "/api/v1/workspaces/"
        if (
            self._web_runtime is None
            or not isinstance(path, str)
            or not path.startswith(prefix)
        ):
            return self._json_error(start_response, "404 Not Found", "not found")
        remainder = path[len(prefix) :]
        parts = remainder.split("/")
        if len(parts) != 3 or parts[1] not in {"files", "live-previews"}:
            return self._json_error(start_response, "404 Not Found", "not found")
        workspace_id, resource_kind, locator = parts
        try:
            content = (
                self._web_runtime.read_pdf(workspace_id, locator)
                if resource_kind == "files"
                else self._web_runtime.read_live_preview(workspace_id, locator)
            )
        except FileNotFoundError as error:
            return self._json_error(start_response, "404 Not Found", str(error))
        except (PermissionError, TypeError, ValueError) as error:
            return self._json_error(start_response, "400 Bad Request", str(error))
        start_response(
            "200 OK",
            [
                ("Content-Type", "application/pdf"),
                ("Content-Length", str(len(content))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
        return [content]

    @staticmethod
    def _json_error(
        start_response: StartResponse,
        status: str,
        message: str,
    ) -> Iterable[bytes]:
        body = json.dumps(
            {"ok": False, "error": {"kind": "request", "message": message}},
            ensure_ascii=False,
        ).encode("utf-8")
        start_response(
            status,
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
        return [body]

    def _build_stream(
        self,
        request: dict,
        request_id: str,
        cancellation: Event,
    ) -> Iterable[bytes]:
        from .runtime import iter_build_events

        def finished() -> None:
            with self._cancellation_lock:
                if self._build_cancellations.get(request_id) is cancellation:
                    self._build_cancellations.pop(request_id, None)

        try:
            for event in iter_build_events(
                self._dispatcher,
                request,
                should_cancel=cancellation.is_set,
                on_finished=finished,
            ):
                yield (
                    json.dumps(event, ensure_ascii=False).encode("utf-8") + b"\n"
                )
        finally:
            cancellation.set()
