from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from threading import Event, Lock
from typing import Protocol

from .dto import PROTOCOL_VERSION


class Dispatcher(Protocol):
    def dispatch(self, request: dict) -> dict: ...


class WebRuntime(Protocol):
    def create_workspace(self, file_name: str, text: str) -> dict: ...


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
                    file_name = request.get("fileName")
                    text = request.get("text")
                    if not isinstance(file_name, str) or not isinstance(text, str):
                        raise ValueError("fileName and text are required")
                    source = self._web_runtime.create_workspace(file_name, text)
                    payload = {
                        "protocol": PROTOCOL_VERSION,
                        "ok": True,
                        "source": source,
                        "text": text,
                    }
                    status = "201 Created"
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
