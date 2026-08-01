from __future__ import annotations

from typing import Final

PROTOCOL_VERSION: Final = "thesisforge.workbench.v1"


def success_response(request_id: str, result: dict) -> dict:
    return {
        "protocol": PROTOCOL_VERSION,
        "requestId": request_id,
        "ok": True,
        "result": result,
    }


def error_response(
    request_id: str,
    *,
    kind: str,
    message: str,
    stage: str | None = None,
) -> dict:
    error = {"kind": kind, "message": message}
    if stage is not None:
        error["stage"] = stage
    return {
        "protocol": PROTOCOL_VERSION,
        "requestId": request_id,
        "ok": False,
        "error": error,
    }
