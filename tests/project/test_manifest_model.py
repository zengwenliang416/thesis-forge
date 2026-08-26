from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from docforge.project import (
    DEFAULT_DOCX_PATH,
    DEFAULT_REVIEW_MAP_PATH,
    DEFAULT_REVIEW_MARKDOWN_PATH,
    DEFAULT_SOURCE_PATH,
    MANIFEST_FILENAME,
    PROJECT_SCHEMA,
    DocForgeProjectManifest,
    ProjectRelativePath,
)


def valid_manifest() -> dict:
    return {
        "schema": "docforge.project.v1",
        "project": {"id": "general-fixture", "language": "zh-CN"},
        "document": {},
        "metadata": {
            "title": {"zh": "季度项目报告", "en": "Quarterly Project Report"},
            "subtitle": {"zh": "研发进展与风险"},
            "authors": [{"name": "张三"}, {"name": "李四"}],
            "organization": "示例科技有限公司",
            "date": "2026-08-26",
            "version": "1.0",
            "keywords": ["项目管理", "研发"],
        },
        "resources": {
            "root": ".",
            "assets": "assets",
            "bibliography": "references.bib",
        },
        "render": {
            "template_id": "docforge-standard",
            "citation_style": "gbt7714-numeric",
        },
        "layout": {"objects": {"fig:model": {"width": "85%"}}},
    }


def academic_profile() -> dict:
    return {
        "student": {"name": "张三", "id": "20260001"},
        "institution": {"name": "示例大学", "department": "计算机学院"},
        "degree": {"name": "工学硕士", "major": "计算机科学与技术"},
        "advisor": {"name": "李教授", "title": "教授"},
        "completion": {"date": "2026-05"},
    }


def test_project_identity_constants_are_neutral_and_centralized() -> None:
    assert MANIFEST_FILENAME == "docforge.yaml"
    assert PROJECT_SCHEMA == "docforge.project.v1"
    assert DEFAULT_SOURCE_PATH == "document.md"
    assert DEFAULT_DOCX_PATH == "build/document.docx"
    assert DEFAULT_REVIEW_MARKDOWN_PATH == "review/document.review.md"
    assert DEFAULT_REVIEW_MAP_PATH == "review/document.review-map.json"


def test_manifest_resolves_general_document_defaults_and_metadata() -> None:
    manifest = DocForgeProjectManifest.model_validate(valid_manifest())

    assert manifest.schema == "docforge.project.v1"
    assert manifest.project.id == "general-fixture"
    assert manifest.document.type == "general"
    assert manifest.document.source.root == "document.md"
    assert isinstance(manifest.document.source, ProjectRelativePath)
    assert manifest.metadata.title is not None
    assert manifest.metadata.title.zh == "季度项目报告"
    assert manifest.metadata.subtitle is not None
    assert manifest.metadata.subtitle.zh == "研发进展与风险"
    assert [author.name for author in manifest.metadata.authors] == ["张三", "李四"]
    assert manifest.metadata.organization == "示例科技有限公司"
    assert manifest.metadata.date.isoformat() == "2026-08-26"
    assert manifest.metadata.version == "1.0"
    assert manifest.metadata.keywords == ("项目管理", "研发")
    assert manifest.render.template_id == "docforge-standard"
    assert manifest.resources.assets.root == "assets"
    assert manifest.layout.objects["fig:model"].width == "85%"
    assert manifest.output.directory.root == "build"
    assert manifest.output.docx.root == "document.docx"
    assert manifest.review.directory.root == "review"
    assert manifest.review.markdown.root == "document.review.md"
    assert manifest.review.source_map.root == "document.review-map.json"
    assert manifest.academic is None


def test_manifest_accepts_typed_optional_academic_profile() -> None:
    payload = valid_manifest()
    payload["document"]["type"] = "academic"
    payload["academic"] = academic_profile()

    manifest = DocForgeProjectManifest.model_validate(payload)

    assert manifest.document.type == "academic"
    assert manifest.academic is not None
    assert manifest.academic.student.name == "张三"
    assert manifest.academic.student.id == "20260001"
    assert manifest.academic.institution.name == "示例大学"
    assert manifest.academic.institution.department == "计算机学院"
    assert manifest.academic.degree.major == "计算机科学与技术"
    assert manifest.academic.advisor.title == "教授"
    assert manifest.academic.completion.date == "2026-05"


@pytest.mark.parametrize(
    ("section", "field"),
    [
        (None, "unexpected"),
        ("project", "unexpected"),
        ("document", "unexpected"),
        ("metadata", "university"),
        ("academic", "unexpected"),
        ("resources", "unexpected"),
        ("render", "unexpected"),
        ("layout", "unexpected"),
        ("output", "unexpected"),
        ("review", "unexpected"),
    ],
)
def test_manifest_rejects_unknown_fields(section: str | None, field: str) -> None:
    payload = valid_manifest()
    payload["academic"] = academic_profile()
    target = payload if section is None else payload.setdefault(section, {})
    target[field] = True

    with pytest.raises(ValidationError):
        DocForgeProjectManifest.model_validate(payload)


@pytest.mark.parametrize(
    "schema",
    ["thesisforge.project.v2", "docforge.project.v2", None],
)
def test_manifest_requires_exact_docforge_v1_schema(schema: object) -> None:
    payload = valid_manifest()
    payload["schema"] = schema

    with pytest.raises(ValidationError):
        DocForgeProjectManifest.model_validate(payload)


@pytest.mark.parametrize(
    "value",
    [
        "/tmp/document.md",
        "../document.md",
        "https://example.com/document.md",
        "C:\\document.md",
        "\\\\server\\share\\document.md",
        "safe\x00path",
        "",
    ],
)
@pytest.mark.parametrize(
    ("section", "field"),
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
    payload.setdefault(section, {})[field] = value

    with pytest.raises(ValidationError):
        DocForgeProjectManifest.model_validate(payload)


@pytest.mark.parametrize("source", ["notes.txt", "document.docx", "README"])
def test_manifest_rejects_non_markdown_source(source: str) -> None:
    payload = valid_manifest()
    payload["document"]["source"] = source

    with pytest.raises(ValidationError):
        DocForgeProjectManifest.model_validate(payload)


def test_project_relative_path_is_strict_and_immutable() -> None:
    path = ProjectRelativePath("safe/path")

    with pytest.raises(ValidationError):
        path.root = "../escape"

    with pytest.raises(ValidationError):
        ProjectRelativePath.model_validate(b"safe/path")


def test_manifest_rejects_malformed_generic_and_academic_metadata() -> None:
    payload = deepcopy(valid_manifest())
    payload["project"]["language"] = "not a language"
    with pytest.raises(ValidationError):
        DocForgeProjectManifest.model_validate(payload)

    payload = deepcopy(valid_manifest())
    payload["metadata"]["authors"] = [{"name": ""}]
    with pytest.raises(ValidationError):
        DocForgeProjectManifest.model_validate(payload)

    payload = deepcopy(valid_manifest())
    payload["academic"] = academic_profile()
    payload["academic"]["completion"]["date"] = "2026-13"
    with pytest.raises(ValidationError):
        DocForgeProjectManifest.model_validate(payload)

    payload = deepcopy(valid_manifest())
    payload["layout"]["objects"]["fig:model"] = {}
    with pytest.raises(ValidationError):
        DocForgeProjectManifest.model_validate(payload)
