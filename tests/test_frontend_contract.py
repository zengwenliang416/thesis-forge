from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from thesis_forge import ui
from thesis_forge.application import InspectionResult, ValidationResult
from thesis_forge.core.model import ForgeDocument
from thesis_forge.core.validator import ValidationContext

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "workspace-state-v1.json"


class _DeferredTaskRunner:
    def __init__(self) -> None:
        self.pending = []

    def submit(self, operation, *, on_success, on_error):
        self.pending.append((operation, on_success, on_error))

    def complete(self) -> None:
        operation, on_success, _on_error = self.pending.pop(0)
        on_success(operation())


def _snapshot(controller: ui.WorkspaceController) -> dict:
    state = controller.state
    actions = state.actions
    return {
        "status": state.status.value,
        "sourceKind": state.source_kind.value if state.source_kind else None,
        "sourceName": state.source_name,
        "savedText": state.saved_text,
        "editorText": state.editor_text,
        "dirty": state.dirty,
        "operation": (
            state.active_operation.kind.value if state.active_operation else None
        ),
        "actions": {
            "canOpen": actions.can_open,
            "canEdit": actions.can_edit,
            "canSave": actions.can_save,
            "canSaveAs": actions.can_save_as,
            "canDownload": actions.can_download,
            "canValidate": actions.can_validate,
            "canBuild": actions.can_build,
            "canCancel": actions.can_cancel,
        },
    }


def test_workspace_fixture_matches_python_reference_controller(tmp_path: Path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    steps = fixture["cases"][0]["steps"]
    source = tmp_path / "thesis.md"
    source.write_text("# Saved\n", encoding="utf-8")
    runner = _DeferredTaskRunner()
    controller = ui.WorkspaceController(
        inspect=lambda path: InspectionResult(ForgeDocument(Path(path))),
        validate=lambda path, **_kwargs: ValidationResult(
            ForgeDocument(Path(path)),
            ValidationContext(),
            (),
        ),
        task_runner=runner,
    )

    controller.open_source(source)
    runner.complete()
    assert _snapshot(controller) == steps[0]["expected"]
    controller.edit_text("# Changed\n")
    assert _snapshot(controller) == steps[1]["expected"]
    controller.save()
    assert _snapshot(controller) == steps[2]["expected"]
    runner.complete()
    assert controller.state.active_operation.kind is ui.OperationKind.REFRESH
    runner.complete()
    assert _snapshot(controller) == steps[3]["expected"]


def test_python_cli_runs_with_frontend_toolchain_and_network_unavailable():
    env = os.environ.copy()
    env["PATH"] = ""
    env.pop("NODE_PATH", None)
    env.pop("CARGO_HOME", None)
    script = """
import socket
socket.socket = lambda *args, **kwargs: (_ for _ in ()).throw(
    AssertionError("network must not be used")
)
import thesis_forge.cli
print("ok")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "ok"


def test_frontend_and_tauri_boundaries_exist_without_entering_python_core():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert package["scripts"]["frontend:test"] == "pnpm --dir frontend test"
    assert (ROOT / "frontend" / "src" / "transport" / "WorkbenchTransport.ts").is_file()
    assert (ROOT / "src-tauri" / "tauri.conf.json").is_file()

    forbidden = ("react", "vite", "tauri", "fastapi", "flask")
    for path in (ROOT / "src" / "thesis_forge" / "core").glob("*.py"):
        if path.name.startswith("._"):
            continue
        content = path.read_text(encoding="utf-8").lower()
        assert not any(f"import {name}" in content for name in forbidden)
