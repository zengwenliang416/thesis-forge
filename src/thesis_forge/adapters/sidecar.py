from __future__ import annotations

import argparse
import json
import sys

from .runtime import DesktopRuntime, WorkbenchCommandDispatcher


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    dispatcher = WorkbenchCommandDispatcher(runtime=DesktopRuntime())
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
