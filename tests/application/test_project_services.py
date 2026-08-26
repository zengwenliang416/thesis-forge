from __future__ import annotations

from pathlib import Path

import pytest

from thesis_forge.application.contracts import (
    ProjectIdentity,
    ProjectOutput,
    ProjectRequest,
    ProjectRequestIntent,
)
from thesis_forge.application.services import (
    ApplicationDependencies,
    ProjectApplicationService,
    ProjectServiceContext,
)
from thesis_forge.core.model import ThesisDocument
from thesis_forge.core.validator import ValidationContext

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
PROJECT_ROOT = FIXTURES / "docforge-general"
ACADEMIC_PROJECT_ROOT = FIXTURES / "docforge-academic"


def request(
    intent: ProjectRequestIntent,
    *,
    editor_snapshot: str | None = None,
    output: Path | None = None,
) -> ProjectRequest:
    return ProjectRequest(
        project=ProjectIdentity(
            project_id="general-fixture",
            project_root=PROJECT_ROOT.resolve(),
            manifest_path=(PROJECT_ROOT / "docforge.yaml").resolve(),
        ),
        intent=intent,
        output=ProjectOutput(output.resolve()) if output is not None else None,
        editor_snapshot=editor_snapshot,
    )


def service(calls: list[tuple[str, Path]]) -> ProjectApplicationService:
    def parse_file(path: str | Path) -> ThesisDocument:
        source = Path(path)
        calls.append(("file", source))
        return ThesisDocument(source_path=source)

    def parse_text(text: str, *, source_path: str | Path) -> ThesisDocument:
        source = Path(source_path)
        calls.append(("snapshot", source))
        return ThesisDocument(source_path=source)

    def context_factory(
        document: ThesisDocument,
        _template_path: str | Path | None,
    ) -> ValidationContext:
        calls.append(("context", document.source_path))
        return ValidationContext(template=object())

    def validator(
        document: ThesisDocument,
        _context: ValidationContext,
    ) -> list:
        calls.append(("validate", document.source_path))
        return []

    return ProjectApplicationService(
        ApplicationDependencies(
            parser=parse_file,
            snapshot_parser=parse_text,
            context_factory=context_factory,
            validator=validator,
            compiler=lambda *_args, **_kwargs: object(),
        )
    )


def test_load_returns_manifest_identity_and_all_resolved_project_paths() -> None:
    context = ProjectApplicationService().load(request(ProjectRequestIntent.INSPECT))

    assert isinstance(context, ProjectServiceContext)
    assert context.project.manifest.project.id == "general-fixture"
    assert context.project.manifest.academic is None
    assert context.paths.source == (PROJECT_ROOT / "document.md").resolve()
    assert context.paths.resources_root == PROJECT_ROOT.resolve()
    assert context.paths.assets == (PROJECT_ROOT / "assets").resolve()
    assert context.paths.bibliography is None
    assert context.paths.output_directory == (PROJECT_ROOT / "build").resolve()


def test_inspect_uses_manifest_source_before_parsing() -> None:
    calls: list[tuple[str, Path]] = []

    service(calls).inspect(request(ProjectRequestIntent.INSPECT))

    assert calls == [("file", (PROJECT_ROOT / "document.md").resolve())]


def test_validate_and_preview_use_editor_snapshot_and_project_source() -> None:
    calls: list[tuple[str, Path]] = []
    project_service = service(calls)

    project_service.validate(
        request(ProjectRequestIntent.VALIDATE, editor_snapshot="# unsaved\n")
    )
    project_service.preview(
        request(ProjectRequestIntent.REVIEW, editor_snapshot="# review\n")
    )

    assert calls == [
        ("snapshot", (PROJECT_ROOT / "document.md").resolve()),
        ("context", (PROJECT_ROOT / "document.md").resolve()),
        ("validate", (PROJECT_ROOT / "document.md").resolve()),
        ("snapshot", (PROJECT_ROOT / "document.md").resolve()),
        ("context", (PROJECT_ROOT / "document.md").resolve()),
        ("validate", (PROJECT_ROOT / "document.md").resolve()),
    ]


def test_build_requires_typed_output_after_loading_project() -> None:
    with pytest.raises(ValueError, match="requires output"):
        service([]).build(request(ProjectRequestIntent.BUILD))


def test_project_identity_mismatch_is_rejected_before_parsing() -> None:
    mismatched = ProjectRequest(
        project=ProjectIdentity(
            project_id="wrong-id",
            project_root=PROJECT_ROOT.resolve(),
            manifest_path=(PROJECT_ROOT / "docforge.yaml").resolve(),
        ),
        intent=ProjectRequestIntent.INSPECT,
    )

    with pytest.raises(ValueError, match="identity"):
        ProjectApplicationService().inspect(mismatched)


def test_load_academic_fixture_uses_same_project_service_pipeline() -> None:
    academic_request = ProjectRequest(
        project=ProjectIdentity(
            project_id="academic-fixture",
            project_root=ACADEMIC_PROJECT_ROOT.resolve(),
            manifest_path=(ACADEMIC_PROJECT_ROOT / "docforge.yaml").resolve(),
        ),
        intent=ProjectRequestIntent.INSPECT,
    )

    context = ProjectApplicationService().load(academic_request)

    assert context.paths.source == (ACADEMIC_PROJECT_ROOT / "document.md").resolve()
    assert context.project.manifest.document.type == "academic"
    assert context.project.manifest.academic is not None
    assert context.project.manifest.academic.student.id == "20260001"
