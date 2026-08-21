from __future__ import annotations

import os
from pathlib import Path

import pytest

from thesis_forge.core.model import (
    BibliographyConfig,
    Citation,
    Figure,
    Paragraph,
    ThesisDocument,
)
from thesis_forge.core.validator import ValidationContext, validate_document

REFERENCE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "v2-project" / "references.bib"
)


def write_project(
    tmp_path: Path,
    *,
    bibliography: str | None = None,
) -> Path:
    root = tmp_path / "project"
    (root / "assets").mkdir(parents=True)
    (root / "thesis.md").write_text("# 绪论\n", encoding="utf-8")
    (root / "assets" / "model.png").write_bytes(b"png")
    (root / "references.bib").write_text(
        bibliography or REFERENCE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / "thesisforge.yaml").write_text(
        """
schema: thesisforge.project.v2
project:
  id: validation-fixture
  language: zh-CN
document:
  source: thesis.md
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
    document = ThesisDocument(
        source_path=(project_root / "thesis.md").resolve(),
        blocks=[
            Paragraph(text="引用 [@smith2025]", inlines=[]),
            Figure(src="assets/model.png", caption="模型"),
        ],
        citations=[Citation(keys=["smith2025"])],
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


def test_manifest_bibliography_overrides_document_front_matter_path(
    tmp_path: Path,
) -> None:
    project_root = write_project(tmp_path)
    document = ThesisDocument(
        source_path=(project_root / "thesis.md").resolve(),
        bibliography=BibliographyConfig(
            path="does-not-exist.bib",
            citation_style="unsupported-style",
        ),
        blocks=[Paragraph(text="引用", inlines=[])],
        citations=[Citation(keys=["smith2025"])],
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

    document = ThesisDocument(source_path=(project_root / "thesis.md").resolve())
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
    document = ThesisDocument(
        source_path=(project_root / "thesis.md").resolve(),
        citations=[Citation(keys=["broken"])],
    )

    context = ValidationContext.from_document(document)
    issues = validate_document(document, context)
    invalid = next(issue for issue in issues if issue.code == "invalid-bibliography")

    assert str(project_root) not in str(invalid.details)
