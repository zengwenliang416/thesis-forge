from __future__ import annotations

import os
from pathlib import Path

import pytest

from thesis_forge.core.compiler import compile_document
from thesis_forge.core.model import (
    BibliographyConfig,
    Citation,
    Figure,
    ForgeDocument,
    Paragraph,
    Text,
)
from thesis_forge.core.parser_backend import create_parser_backend
from thesis_forge.core.render_plan import CoverInstruction
from thesis_forge.core.validator import ValidationContext, validate_document

REFERENCE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "v2-project" / "references.bib"
)


def write_project(
    tmp_path: Path,
    *,
    bibliography: str | None = None,
    metadata: bool = False,
) -> Path:
    root = tmp_path / "project"
    (root / "assets").mkdir(parents=True)
    (root / "thesis.md").write_text("# 绪论\n", encoding="utf-8")
    (root / "assets" / "model.png").write_bytes(b"png")
    (root / "references.bib").write_text(
        bibliography or REFERENCE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    metadata_block = (
        """
metadata:
  title:
    zh: 测试论文
    en: Test Thesis
  author:
    name: 张三
    student_id: "20260001"
  institution:
    university: 示例大学
    college: 计算机学院
  degree:
    name: 工学硕士
    major: 计算机科学与技术
  advisor:
    name: 李教授
    title: 教授
  dates:
    completed: "2026-05"
"""
        if metadata
        else ""
    )
    (root / "thesisforge.yaml").write_text(
        f"""
schema: thesisforge.project.v2
project:
  id: validation-fixture
  language: zh-CN
document:
  source: thesis.md
{metadata_block}
resources:
  root: .
  assets: assets
  bibliography: references.bib
render:
  template_id: example-university-2026
  citation_style: GB-T-7714-2025
""".lstrip(),
        encoding="utf-8",
    )
    return root


def test_project_manifest_controls_template_and_resource_roots(
    tmp_path: Path,
) -> None:
    project_root = write_project(tmp_path)
    citation = Citation(keys=["smith2025"])
    document = ForgeDocument(
        source_path=(project_root / "thesis.md").resolve(),
        blocks=[
            Paragraph(inlines=[citation]),
            Figure(
                src="assets/model.png",
                caption_inlines=(Text(value="模型"),),
            ),
        ],
    )

    context = ValidationContext.from_document(document)
    issues = validate_document(document, context)

    assert context.template is not None
    assert context.template.id == "example-university-2026"
    assert context.manifest_bibliography_path == (project_root / "references.bib").resolve()
    assert context.resource_roots == (
        project_root.resolve(),
        (project_root / "assets").resolve(),
    )
    assert context.bibliography_database is not None
    assert "smith2025" in context.bibliography_database.records
    assert not any(issue.code == "missing-bibliography" for issue in issues)
    assert not any(issue.code == "missing-image" for issue in issues)
    assert {
        issue.target
        for issue in issues
        if issue.code == "required-metadata"
    } == {"thesis.title", "author.name"}


def test_manifest_metadata_drives_validation_and_cover_compilation(
    tmp_path: Path,
) -> None:
    project_root = write_project(tmp_path, metadata=True)
    document = create_parser_backend().parse_file(project_root / "thesis.md")
    document.metadata = {
        "thesis": {"title": "旧标题"},
        "author": {"name": "旧作者"},
    }

    context = ValidationContext.from_document(document)
    issues = validate_document(document, context)

    assert not any(issue.code == "required-metadata" for issue in issues)
    assert document.metadata == {
        "thesis": {
            "title": "测试论文",
            "title_en": "Test Thesis",
            "degree": "工学硕士",
            "major": "计算机科学与技术",
        },
        "university": {"name": "示例大学", "college": "计算机学院"},
        "author": {"name": "张三", "student_id": "20260001"},
        "advisor": {"name": "李教授", "title": "教授"},
        "dates": {"completed": "2026-05"},
    }

    plan = compile_document(
        document,
        template=context.template,
        template_path=context.template_path,
        bibliography_database=context.bibliography_database,
    )
    cover = next(node for node in plan.nodes if isinstance(node, CoverInstruction))
    expected_cover = {
        "university.name": "示例大学",
        "university.college": "计算机学院",
        "thesis.title": "测试论文",
        "thesis.title_en": "Test Thesis",
        "thesis.major": "计算机科学与技术",
        "thesis.degree": "工学硕士",
        "author.name": "张三",
        "author.student_id": "20260001",
        "advisor.name": "李教授",
        "advisor.title": "教授",
        "dates.completed": "2026-05",
    }
    assert {
        field: cover.value_for(field) for field in expected_cover
    } == expected_cover


def test_manifest_bibliography_overrides_document_front_matter_path(
    tmp_path: Path,
) -> None:
    project_root = write_project(tmp_path)
    citation = Citation(keys=["smith2025"])
    document = ForgeDocument(
        source_path=(project_root / "thesis.md").resolve(),
        bibliography=BibliographyConfig(
            path="does-not-exist.bib",
            citation_style="unsupported-style",
        ),
        blocks=[Paragraph(inlines=[citation])],
    )

    context = ValidationContext.from_document(document)
    issues = validate_document(document, context)
    codes = {issue.code for issue in issues}

    assert context.manifest_bibliography_reference == "references.bib"
    assert context.bibliography_database is not None
    assert "smith2025" in context.bibliography_database.records
    assert "missing-bibliography" not in codes
    assert "unsupported-citation-style" not in codes


def test_manifest_path_escape_becomes_structured_validation_issue(
    tmp_path: Path,
) -> None:
    project_root = write_project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (project_root / "assets" / "model.png").unlink()
    (project_root / "assets").rmdir()
    try:
        os.symlink(outside, project_root / "assets", target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")

    document = ForgeDocument(source_path=(project_root / "thesis.md").resolve())
    context = ValidationContext.from_document(document)
    issues = validate_document(document, context)

    project_issues = [issue for issue in issues if issue.code == "project-path-boundary"]
    assert len(project_issues) == 1
    assert project_issues[0].target == "resources.assets"
    assert project_issues[0].details == {
        "error_code": "TF-PROJECT-PATH-SYMLINK-ESCAPE"
    }


def test_invalid_manifest_bibliography_details_do_not_leak_absolute_path(
    tmp_path: Path,
) -> None:
    project_root = write_project(
        tmp_path,
        bibliography="@article{broken,\n  title={missing brace}\n",
    )
    citation = Citation(keys=["broken"])
    document = ForgeDocument(
        source_path=(project_root / "thesis.md").resolve(),
        blocks=[Paragraph(inlines=[citation])],
    )

    context = ValidationContext.from_document(document)
    issues = validate_document(document, context)
    invalid = next(issue for issue in issues if issue.code == "invalid-bibliography")

    assert str(project_root) not in str(invalid.details)
