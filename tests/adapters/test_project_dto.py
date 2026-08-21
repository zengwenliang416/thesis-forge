from __future__ import annotations

from pathlib import Path

import pytest

from thesis_forge.adapters.dto import (
    ProjectRequestPayload,
    read_project_request_payload,
)


def valid_payload() -> dict:
    return {
        "project": {
            "id": "dto-fixture",
            "root": "/tmp/dto-fixture",
            "manifestPath": "/tmp/dto-fixture/thesisforge.yaml",
        },
        "text": "# 未保存\n",
        "output": {
            "kind": "desktop",
            "path": "/tmp/dto-fixture/build/thesis.docx",
            "fileName": "thesis.docx",
        },
    }


def test_project_payload_is_typed_and_preserves_snapshot_and_output() -> None:
    parsed = read_project_request_payload(valid_payload())

    assert isinstance(parsed, ProjectRequestPayload)
    assert parsed.project_id == "dto-fixture"
    assert parsed.project_root == "/tmp/dto-fixture"
    assert parsed.manifest_path.endswith("thesisforge.yaml")
    assert parsed.editor_snapshot == "# 未保存\n"
    assert parsed.output == valid_payload()["output"]


@pytest.mark.parametrize(
    "payload",
    [
        {"source": {"kind": "desktop", "path": "/tmp/thesis.md"}},
        {
            "project": {
                "id": "dto-fixture",
                "root": "relative",
                "manifestPath": "/tmp/thesisforge.yaml",
            }
        },
        {
            "project": {
                "id": "   ",
                "root": "/tmp/dto-fixture",
                "manifestPath": "/tmp/dto-fixture/thesisforge.yaml",
            }
        },
    ],
)
def test_project_payload_rejects_bare_or_invalid_identity(payload: dict) -> None:
    with pytest.raises((TypeError, ValueError)):
        read_project_request_payload(payload)


def test_project_payload_rejects_non_string_snapshot_and_non_object_output() -> None:
    payload = valid_payload()
    payload["text"] = Path("not-text")
    with pytest.raises(TypeError):
        read_project_request_payload(payload)

    payload = valid_payload()
    payload["output"] = "/tmp/output.docx"
    with pytest.raises(TypeError):
        read_project_request_payload(payload)
