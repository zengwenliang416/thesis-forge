from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from thesis_forge.project import ProjectManifestV2, ProjectRelativePath


def valid_manifest() -> dict:
    return {
        "schema": "thesisforge.project.v2",
        "project": {"id": "goal-fixture", "language": "zh-CN"},
        "document": {"source": "thesis.md"},
        "metadata": {
            "title": {"zh": "测试论文", "en": "Test Thesis"},
            "author": {"name": "张三", "student_id": "20260001"},
            "institution": {"university": "示例大学", "college": "计算机学院"},
            "degree": {"name": "工学硕士", "major": "计算机科学与技术"},
            "advisor": {"name": "李教授", "title": "教授"},
            "dates": {"completed": "2026-05"},
        },
        "resources": {
            "root": ".",
            "assets": "assets",
            "bibliography": "references.bib",
        },
        "render": {
            "template_id": "example-university-2026",
            "citation_style": "gbt7714-numeric",
        },
        "layout": {"objects": {"fig:model": {"width": "85%"}}},
        "output": {
            "directory": "build",
            "docx": "thesis.docx",
            "retain_last_successful_preview": True,
        },
        "review": {
            "directory": "review",
            "markdown": "thesis.review.md",
            "source_map": "thesis.review-map.json",
        },
    }


def test_manifest_models_all_v2_sections_and_typed_paths() -> None:
    manifest = ProjectManifestV2.model_validate(valid_manifest())

    assert manifest.schema == "thesisforge.project.v2"
    assert manifest.project.id == "goal-fixture"
    assert str(manifest.document.source) == "thesis.md"
    assert isinstance(manifest.document.source, ProjectRelativePath)
    assert manifest.metadata.title is not None
    assert manifest.metadata.title.zh == "测试论文"
    assert manifest.render.template_id == "example-university-2026"
    assert manifest.resources.assets.root == "assets"
    assert manifest.layout.objects["fig:model"].width == "85%"
    assert manifest.output.docx.root == "thesis.docx"
    assert manifest.review.source_map.root == "thesis.review-map.json"


@pytest.mark.parametrize(
    "section",
    [
        "project",
        "document",
        "metadata",
        "resources",
        "render",
        "layout",
        "output",
        "review",
    ],
)
def test_manifest_rejects_unknown_fields_at_root_and_nested_sections(
    section: str,
) -> None:
    root_extra = valid_manifest()
    root_extra["unexpected"] = True
    with pytest.raises(ValidationError):
        ProjectManifestV2.model_validate(root_extra)

    nested_extra = valid_manifest()
    nested_extra[section]["unexpected"] = True
    with pytest.raises(ValidationError):
        ProjectManifestV2.model_validate(nested_extra)


@pytest.mark.parametrize(
    "schema",
    ["thesisforge.project.v1", "thesisforge.project.v2.1", None],
)
def test_manifest_requires_exact_v2_schema(schema: object) -> None:
    payload = valid_manifest()
    payload["schema"] = schema

    with pytest.raises(ValidationError):
        ProjectManifestV2.model_validate(payload)


@pytest.mark.parametrize(
    "value",
    [
        "/tmp/thesis.md",
        "../thesis.md",
        "https://example.com/thesis.md",
        "C:\\thesis.md",
        "\\\\server\\share\\thesis.md",
        "safe\x00path",
        "",
    ],
)
@pytest.mark.parametrize(
    "section, field",
    [
        ("document", "source"),
        ("resources", "root"),
        ("resources", "assets"),
        ("resources", "bibliography"),
        ("output", "directory"),
        ("output", "docx"),
        ("review", "directory"),
        ("review", "markdown"),
        ("review", "source_map"),
    ],
)
def test_manifest_path_fields_reject_non_project_relative_values(
    value: str,
    section: str,
    field: str,
) -> None:
    payload = valid_manifest()
    payload[section][field] = value

    with pytest.raises(ValidationError):
        ProjectManifestV2.model_validate(payload)


def test_project_relative_path_is_strict_and_immutable() -> None:
    path = ProjectRelativePath("safe/path")

    with pytest.raises(ValidationError):
        path.root = "../escape"

    with pytest.raises(ValidationError):
        ProjectRelativePath.model_validate(b"safe/path")


def test_manifest_rejects_malformed_sections() -> None:
    payload = deepcopy(valid_manifest())
    payload["project"]["language"] = "not a language"
    with pytest.raises(ValidationError):
        ProjectManifestV2.model_validate(payload)

    payload = deepcopy(valid_manifest())
    payload["metadata"]["dates"]["completed"] = "2026-13"
    with pytest.raises(ValidationError):
        ProjectManifestV2.model_validate(payload)

    payload = deepcopy(valid_manifest())
    payload["layout"]["objects"]["fig:model"] = {}
    with pytest.raises(ValidationError):
        ProjectManifestV2.model_validate(payload)
