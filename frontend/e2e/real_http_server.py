from __future__ import annotations

import argparse
import mimetypes
from pathlib import Path
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, make_server

from thesis_forge.adapters import (
    WebWorkspaceRuntime,
    WorkbenchCommandDispatcher,
    WorkbenchHttpApp,
)

FRONTEND_ROOT = Path(__file__).resolve().parents[1]
DIST_ROOT = (FRONTEND_ROOT / "dist").resolve()
WORKSPACE_ROOT = (
    FRONTEND_ROOT / "test-results" / "real-http-workspaces"
).resolve()


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class RealHttpAcceptanceApp:
    def __init__(self) -> None:
        runtime = WebWorkspaceRuntime(WORKSPACE_ROOT)
        self._api = WorkbenchHttpApp(
            WorkbenchCommandDispatcher(runtime=runtime),
            web_runtime=runtime,
        )

    def __call__(self, environ: dict, start_response):
        path = str(environ.get("PATH_INFO") or "/")
        if path.startswith("/api/v1/"):
            return self._api(environ, self._api_start_response(start_response))
        return self._serve_static(environ, start_response, path)

    @staticmethod
    def _api_start_response(start_response):
        def wrapped(status: str, headers: list[tuple[str, str]]):
            return start_response(
                status,
                [*headers, ("X-ThesisForge-Adapter", "python-wsgi")],
            )

        return wrapped

    @staticmethod
    def _serve_static(environ: dict, start_response, path: str):
        method = environ.get("REQUEST_METHOD")
        if method not in {"GET", "HEAD"}:
            return RealHttpAcceptanceApp._response(
                start_response,
                "405 Method Not Allowed",
                b"method not allowed",
                "text/plain; charset=utf-8",
                method,
            )

        relative = path.lstrip("/") or "index.html"
        candidate = (DIST_ROOT / relative).resolve()
        if not candidate.is_relative_to(DIST_ROOT) or not candidate.is_file():
            candidate = DIST_ROOT / "index.html"
        if not candidate.is_file():
            return RealHttpAcceptanceApp._response(
                start_response,
                "503 Service Unavailable",
                b"frontend build is missing",
                "text/plain; charset=utf-8",
                method,
            )

        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or (
            "application/octet-stream"
        )
        if content_type.startswith("text/") or content_type in {
            "application/javascript",
            "application/json",
        }:
            content_type = f"{content_type}; charset=utf-8"
        return RealHttpAcceptanceApp._response(
            start_response,
            "200 OK",
            body,
            content_type,
            method,
        )

    @staticmethod
    def _response(
        start_response,
        status: str,
        body: bytes,
        content_type: str,
        method: object,
    ):
        start_response(
            status,
            [
                ("Content-Type", content_type),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [] if method == "HEAD" else [body]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Serve the built workbench and real Python HTTP adapter."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4187)
    args = parser.parse_args()

    if not DIST_ROOT.is_dir():
        parser.error(f"frontend build is missing: {DIST_ROOT}")
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    with make_server(
        args.host,
        args.port,
        RealHttpAcceptanceApp(),
        server_class=ThreadingWSGIServer,
    ) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
