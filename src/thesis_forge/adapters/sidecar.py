from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path

from thesis_forge.application.services import ProjectApplicationService

from .runtime import (
    DesktopRuntime,
    WorkbenchCommandDispatcher,
    desktop_final_preview_build_service,
    iter_build_events,
)


def create_dispatcher() -> WorkbenchCommandDispatcher:
    return WorkbenchCommandDispatcher(
        runtime=DesktopRuntime(),
        build=desktop_final_preview_build_service,
        project_service=ProjectApplicationService(),
    )


def _configure_standard_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="strict")


def dispatch_json_line(
    dispatcher: WorkbenchCommandDispatcher,
    line: str,
) -> str:
    try:
        request = json.loads(line)
        if not isinstance(request, dict):
            raise TypeError("request must be an object")
        response = dispatcher.dispatch(request)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        response = {
            "protocol": "thesisforge.workbench.v1",
            "requestId": "invalid-request",
            "ok": False,
            "error": {"kind": "request", "message": str(error)},
        }
    return json.dumps(response, ensure_ascii=False)


def stream_json_lines(
    dispatcher: WorkbenchCommandDispatcher,
    line: str,
    *,
    should_cancel: Callable[[], bool] | None = None,
):
    try:
        request = json.loads(line)
        if not isinstance(request, dict):
            raise TypeError("request must be an object")
        for event in iter_build_events(
            dispatcher,
            request,
            should_cancel=should_cancel,
        ):
            yield json.dumps(event, ensure_ascii=False)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        yield json.dumps(
            {
                "protocol": "thesisforge.workbench.v1",
                "requestId": "invalid-request",
                "type": "error",
                "error": {"kind": "transport", "message": str(error)},
            },
            ensure_ascii=False,
        )


def main(argv: list[str] | None = None) -> int:
    _configure_standard_streams()
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args(argv)
    dispatcher = create_dispatcher()
    if args.stream:
        cancel_file = os.environ.get("THESISFORGE_CANCEL_FILE")
        should_cancel = (
            (lambda: Path(cancel_file).exists())
            if cancel_file is not None
            else None
        )
        line = sys.stdin.readline()
        if line:
            for event in stream_json_lines(
                dispatcher,
                line,
                should_cancel=should_cancel,
            ):
                print(event, flush=True)
        return 0
    if args.once:
        line = sys.stdin.readline()
        if line:
            print(dispatch_json_line(dispatcher, line))
        return 0
    for line in sys.stdin:
        print(dispatch_json_line(dispatcher, line), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
