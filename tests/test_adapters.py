from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from thesis_forge.adapters import (
    PROTOCOL_VERSION,
    DesktopRuntime,
    WebWorkspaceRuntime,
    WorkbenchCommandDispatcher,
    WorkbenchHttpApp,
    dispatch_json_line,
)
from thesis_forge.application import InspectionResult, ValidationResult
from thesis_forge.core.model import Heading, ThesisDocument, ValidationIssue
from thesis_forge.core.validator import ValidationContext


def _dispatcher(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论\n", encoding="utf-8")
    calls: list[tuple[str, Path]] = []

    def inspect(path):
        source_path = Path(path)
        calls.append(("inspect", source_path))
        return InspectionResult(
            ThesisDocument(
                source_path=source_path,
                metadata={"thesis": {"title": "共享工作台"}},
                blocks=[Heading(level=1, text="绪论")],
            )
        )

    def validate(path, **_kwargs):
        source_path = Path(path)
        calls.append(("validate", source_path))
        document = ThesisDocument(source_path=source_path)
        return ValidationResult(
            document=document,
            context=ValidationContext(),
            issues=(
                ValidationIssue(
                    code="heading-level-jump",
                    severity="warning",
                    message="jump",
                    line=3,
                    target="sec:method",
                ),
            ),
        )

    return (
        WorkbenchCommandDispatcher(
            runtime=DesktopRuntime(),
            inspect=inspect,
            validate=validate,
        ),
        source,
        calls,
    )


def _request(operation: str, source: Path) -> dict:
    return {
        "protocol": PROTOCOL_VERSION,
        "requestId": f"{operation}-1",
        "operation": operation,
        "payload": {
            "source": {
                "kind": "desktop",
                "path": str(source),
                "fileName": source.name,
            }
        },
    }


def _write_source(path: Path) -> None:
    path.write_text(
        """---
thesis:
  title: Template diagnostics
author:
  name: ThesisForge
---

# 绪论

## 背景
""",
        encoding="utf-8",
    )


def _write_template(path: Path, *, include_level2: bool) -> None:
    level2 = (
        """
  level2:
    size: 14pt
"""
        if include_level2
        else ""
    )
    path.write_text(
        f"""id: test-template
name: Test Template
year: 2026
page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  font:
    east_asia: 宋体
    latin: Times New Roman
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
{level2}""",
        encoding="utf-8",
    )


def test_dispatcher_serializes_inspection_and_validation_without_python_objects(
    tmp_path: Path,
):
    dispatcher, source, calls = _dispatcher(tmp_path)

    inspection = dispatcher.dispatch(_request("inspect", source))
    validation = dispatcher.dispatch(_request("validate", source))

    assert calls == [("inspect", source), ("validate", source)]
    assert inspection == {
        "protocol": PROTOCOL_VERSION,
        "requestId": "inspect-1",
        "ok": True,
        "result": {
            "source": {"kind": "desktop", "name": "thesis.md"},
            "metadata": {"thesis": {"title": "共享工作台"}},
            "outline": [
                {
                    "id": None,
                    "level": 1,
                    "text": "绪论",
                    "line": None,
                }
            ],
            "blockCount": 1,
        },
    }
    assert validation["result"]["diagnostics"] == [
        {
            "severity": "warning",
            "code": "heading-level-jump",
            "message": "jump",
            "line": 3,
            "target": "sec:method",
            "details": {},
        }
    ]
    json.dumps(inspection)
    json.dumps(validation)


def test_dispatcher_validates_with_a_selected_template_path(tmp_path: Path):
    source = tmp_path / "thesis.md"
    template = tmp_path / "school.yaml"
    _write_source(source)
    _write_template(template, include_level2=True)
    request = _request("validate", source)
    request["payload"]["templatePath"] = str(template)

    response = WorkbenchCommandDispatcher(runtime=DesktopRuntime()).dispatch(request)

    assert response["ok"] is True
    template_codes = {
        diagnostic["code"]
        for diagnostic in response["result"]["diagnostics"]
        if "template" in diagnostic["code"]
    }
    assert template_codes == set()


def test_dispatcher_resolves_a_stable_template_id_without_using_process_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    source = tmp_path / "thesis.md"
    _write_source(source)
    monkeypatch.chdir(tmp_path)
    request = _request("validate", source)
    request["payload"]["templateId"] = "bachelor-base"

    response = WorkbenchCommandDispatcher(runtime=DesktopRuntime()).dispatch(request)

    assert response["ok"] is True
    assert all(
        diagnostic["code"]
        not in {"missing-template", "ambiguous-template", "invalid-template"}
        for diagnostic in response["result"]["diagnostics"]
    )


def test_dispatcher_rejects_conflicting_template_selectors(tmp_path: Path):
    source = tmp_path / "thesis.md"
    template = tmp_path / "school.yaml"
    _write_source(source)
    _write_template(template, include_level2=True)
    request = _request("validate", source)
    request["payload"]["templateId"] = "bachelor-base"
    request["payload"]["templatePath"] = str(template)

    response = WorkbenchCommandDispatcher(runtime=DesktopRuntime()).dispatch(request)

    assert response["ok"] is False
    assert response["error"] == {
        "kind": "request",
        "message": "templateId and templatePath cannot be used together",
    }


@pytest.mark.parametrize(
    ("template_kind", "expected_code"),
    [
        ("missing", "missing-template"),
        ("malformed", "invalid-template"),
        ("incompatible", "missing-template-style"),
    ],
)
def test_dispatcher_surfaces_structured_selected_template_failures(
    tmp_path: Path,
    template_kind: str,
    expected_code: str,
):
    source = tmp_path / "thesis.md"
    template = tmp_path / "school.yaml"
    _write_source(source)
    if template_kind == "malformed":
        template.write_text("id: broken\npage: [\n", encoding="utf-8")
    elif template_kind == "incompatible":
        _write_template(template, include_level2=False)

    request = _request("validate", source)
    request["payload"]["templatePath"] = str(template)
    response = WorkbenchCommandDispatcher(runtime=DesktopRuntime()).dispatch(request)

    assert response["ok"] is True
    diagnostic = next(
        item
        for item in response["result"]["diagnostics"]
        if item["code"] == expected_code
    )
    assert diagnostic["severity"] == "error"
    assert diagnostic["target"]
    assert isinstance(diagnostic["details"], dict)
    if template_kind != "incompatible":
        assert diagnostic["details"]


def test_http_and_sidecar_use_the_same_versioned_command_contract(tmp_path: Path):
    dispatcher, source, _calls = _dispatcher(tmp_path)
    request = _request("inspect", source)
    app = WorkbenchHttpApp(dispatcher)
    status: list[str] = []
    headers: list[list[tuple[str, str]]] = []
    body = json.dumps(request).encode()
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/api/v1/dispatch",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }

    http_body = b"".join(
        app(
            environ,
            lambda value, items: (status.append(value), headers.append(items)),
        )
    )
    sidecar_body = dispatch_json_line(dispatcher, json.dumps(request))

    assert status == ["200 OK"]
    assert ("Content-Type", "application/json; charset=utf-8") in headers[0]
    assert json.loads(http_body) == json.loads(sidecar_body)


def test_adapter_rejects_wrong_protocol_and_unknown_operations(tmp_path: Path):
    dispatcher, source, _calls = _dispatcher(tmp_path)
    wrong = _request("inspect", source)
    wrong["protocol"] = "thesisforge.workbench.v0"

    response = dispatcher.dispatch(wrong)
    unknown = dispatcher.dispatch(_request("delete-everything", source))

    assert response["ok"] is False
    assert response["error"]["kind"] == "protocol"
    assert unknown["ok"] is False
    assert unknown["error"]["kind"] == "request"


def test_web_runtime_resolves_opaque_workspace_without_serializing_service_path(
    tmp_path: Path,
):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")
    handle = runtime.create_workspace("thesis.md", "# 绪论\n")
    calls: list[Path] = []

    def inspect(path):
        source_path = Path(path)
        calls.append(source_path)
        return InspectionResult(ThesisDocument(source_path=source_path))

    dispatcher = WorkbenchCommandDispatcher(runtime=runtime, inspect=inspect)
    request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "web-inspect-1",
        "operation": "inspect",
        "payload": {
            "source": {
                "kind": "web-workspace",
                "workspaceId": handle["workspaceId"],
                "fileName": "thesis.md",
            }
        },
    }

    response = dispatcher.dispatch(request)
    encoded = json.dumps(response)

    assert response["ok"] is True
    assert response["result"]["source"] == {
        "kind": "web-workspace",
        "name": "thesis.md",
    }
    assert calls == [runtime.root / handle["workspaceId"] / "thesis.md"]
    assert str(runtime.root) not in encoded


def test_web_runtime_rejects_path_like_names(tmp_path: Path):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")

    for file_name in ("../thesis.md", "folder/thesis.md", r"folder\thesis.md"):
        with pytest.raises(ValueError, match="plain file name"):
            runtime.create_workspace(file_name, "# 绪论\n")


def test_http_workspace_creation_returns_opaque_handle(tmp_path: Path):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")
    dispatcher = WorkbenchCommandDispatcher(runtime=runtime)
    app = WorkbenchHttpApp(dispatcher, web_runtime=runtime)
    body = json.dumps({"fileName": "thesis.md", "text": "# 绪论\n"}).encode()
    status: list[str] = []
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/api/v1/workspaces",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    }

    payload = json.loads(
        b"".join(app(environ, lambda value, _headers: status.append(value)))
    )

    assert status == ["201 Created"]
    assert payload["protocol"] == PROTOCOL_VERSION
    assert payload["ok"] is True
    assert payload["source"]["kind"] == "web-workspace"
    assert payload["source"]["fileName"] == "thesis.md"
    assert payload["text"] == "# 绪论\n"
    assert str(runtime.root) not in json.dumps(payload)


def test_desktop_save_uses_atomic_source_persistence(tmp_path: Path):
    dispatcher, source, _calls = _dispatcher(tmp_path)
    request = _request("save", source)
    request["payload"]["text"] = "# 已保存\n"

    response = dispatcher.dispatch(request)

    assert response == {
        "protocol": PROTOCOL_VERSION,
        "requestId": "save-1",
        "ok": True,
        "result": {
            "source": {"kind": "desktop", "name": "thesis.md"},
        },
    }
    assert source.read_text(encoding="utf-8") == "# 已保存\n"


def test_web_workspace_save_and_build_share_one_opaque_workspace(tmp_path: Path):
    runtime = WebWorkspaceRuntime(tmp_path / "workspaces")
    source = runtime.create_workspace("thesis.md", "# Before\n")
    output = {
        "kind": "web-download",
        "workspaceId": source["workspaceId"],
        "fileName": "thesis.docx",
    }
    build_calls: list[tuple[Path, Path]] = []

    def build(source_path, output_path, **kwargs):
        source_path = Path(source_path)
        output_path = Path(output_path)
        build_calls.append((source_path, output_path))
        output_path.write_bytes(b"docx")
        kwargs["on_progress"](type("Stage", (), {"value": "finalize"})())
        return type("Result", (), {"output_path": output_path, "issues": ()})()

    dispatcher = WorkbenchCommandDispatcher(runtime=runtime, build=build)
    save_request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "save-web-1",
        "operation": "save",
        "payload": {"source": source, "text": "# After\n"},
    }
    build_request = {
        "protocol": PROTOCOL_VERSION,
        "requestId": "build-web-1",
        "operation": "build",
        "payload": {"source": source, "output": output},
    }

    save_response = dispatcher.dispatch(save_request)
    build_response = dispatcher.dispatch(build_request)
    source_path = runtime.root / source["workspaceId"] / "thesis.md"

    assert save_response["ok"] is True
    assert source_path.read_text(encoding="utf-8") == "# After\n"
    assert build_response["ok"] is True
    assert build_response["result"]["output"] == {
        "kind": "web-download",
        "name": "thesis.docx",
        "downloadId": source["workspaceId"],
    }
    assert build_calls == [
        (source_path, runtime.root / source["workspaceId"] / "thesis.docx")
    ]


def test_save_rejects_missing_text_without_mutating_source(tmp_path: Path):
    dispatcher, source, _calls = _dispatcher(tmp_path)
    request = _request("save", source)

    response = dispatcher.dispatch(request)

    assert response["ok"] is False
    assert response["error"]["kind"] == "request"
    assert source.read_text(encoding="utf-8") == "# 绪论\n"


def test_unexpected_application_failure_is_normalized_as_transport_error(
    tmp_path: Path,
):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论\n", encoding="utf-8")

    def inspect(_path):
        raise RuntimeError("adapter exploded")

    dispatcher = WorkbenchCommandDispatcher(
        runtime=DesktopRuntime(),
        inspect=inspect,
    )

    response = dispatcher.dispatch(_request("inspect", source))

    assert response == {
        "protocol": PROTOCOL_VERSION,
        "requestId": "inspect-1",
        "ok": False,
        "error": {
            "kind": "transport",
            "message": "adapter exploded",
        },
    }
