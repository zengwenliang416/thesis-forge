from __future__ import annotations

from pathlib import Path
from typing import get_type_hints

import pytest

from docforge.application.contracts import (
    ProjectIdentity,
    ProjectOutput,
    ProjectRequest,
    ProjectRequestIntent,
)
from docforge.project.constants import DEFAULT_DOCX_FILENAME, MANIFEST_FILENAME


def identity(tmp_path: Path) -> ProjectIdentity:
    root = tmp_path.resolve()
    return ProjectIdentity(
        project_id="request-fixture",
        project_root=root,
        manifest_path=root / MANIFEST_FILENAME,
    )


def test_project_request_preserves_identity_intent_output_and_editor_snapshot(
    tmp_path: Path,
) -> None:
    project = identity(tmp_path)
    output = ProjectOutput(tmp_path.resolve() / "build" / DEFAULT_DOCX_FILENAME)

    request = ProjectRequest(
        project=project,
        intent=ProjectRequestIntent.BUILD,
        output=output,
        editor_snapshot="# unsaved source\n",
    )

    assert request.project is project
    assert request.project.project_id == "request-fixture"
    assert request.project.root == tmp_path.resolve()
    assert request.intent is ProjectRequestIntent.BUILD
    assert request.output is output
    assert request.editor_snapshot == "# unsaved source\n"


@pytest.mark.parametrize("intent", list(ProjectRequestIntent))
def test_one_request_contract_represents_each_project_operation(
    tmp_path: Path,
    intent: ProjectRequestIntent,
) -> None:
    request = ProjectRequest(
        project=identity(tmp_path),
        intent=intent,
        editor_snapshot="",
    )

    assert request.intent is intent
    assert request.editor_snapshot == ""


def test_non_build_request_can_omit_output(tmp_path: Path) -> None:
    request = ProjectRequest(
        project=identity(tmp_path),
        intent=ProjectRequestIntent.REVIEW,
    )

    assert request.output is None
    assert request.editor_snapshot is None


def test_request_types_do_not_use_bare_path_or_compatibility_unions() -> None:
    hints = get_type_hints(ProjectRequest)

    assert hints["project"] is ProjectIdentity
    assert hints["intent"] is ProjectRequestIntent
    assert "Path" not in str(hints["project"])
    assert "str | pathlib.Path" not in str(hints["output"])


@pytest.mark.parametrize(
    "factory",
    [
        lambda tmp_path: ProjectIdentity(
            project_id="",
            project_root=tmp_path.resolve(),
            manifest_path=tmp_path.resolve() / MANIFEST_FILENAME,
        ),
        lambda tmp_path: ProjectIdentity(
            project_id="x",
            project_root=Path("relative"),
            manifest_path=tmp_path.resolve() / MANIFEST_FILENAME,
        ),
        lambda tmp_path: ProjectOutput(Path("relative-output.docx")),
    ],
)
def test_identity_and_output_reject_invalid_path_contracts(
    tmp_path: Path,
    factory,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        factory(tmp_path)


def test_request_rejects_untyped_compatibility_values(tmp_path: Path) -> None:
    project = identity(tmp_path)

    with pytest.raises(TypeError):
        ProjectRequest(project=project, intent="build")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ProjectRequest(
            project=project,
            intent=ProjectRequestIntent.BUILD,
            output=tmp_path / DEFAULT_DOCX_FILENAME,  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError):
        ProjectRequest(
            project=project,
            intent=ProjectRequestIntent.REVIEW,
            editor_snapshot=Path("wrong"),  # type: ignore[arg-type]
        )
