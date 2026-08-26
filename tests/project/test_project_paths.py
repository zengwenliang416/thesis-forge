from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from docforge.project.loader import load_project
from docforge.project.paths import (
    ProjectPathError,
    resolve_project_path,
    resolve_project_paths,
)


def write_project(
    root: Path,
    *,
    resources_root: str = ".",
    assets: str = "assets",
) -> None:
    resource_directory = root / resources_root
    (resource_directory / assets).mkdir(parents=True, exist_ok=True)
    (root / "document.md").write_text("# 概述\n", encoding="utf-8")
    (resource_directory / "references.bib").write_text(
        "@article{sample, author={张三}, title={测试}, year={2026}}\n",
        encoding="utf-8",
    )
    (root / "docforge.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "docforge.project.v1",
                "project": {"id": "paths-fixture", "language": "zh-CN"},
                "document": {},
                "resources": {
                    "root": resources_root,
                    "assets": assets,
                    "bibliography": "references.bib",
                },
                "render": {"template_id": "docforge-standard"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_resolve_project_paths_uses_one_project_root(tmp_path: Path) -> None:
    write_project(tmp_path)

    paths = resolve_project_paths(load_project(tmp_path))

    assert paths.project_root == tmp_path.resolve()
    assert paths.source == (tmp_path / "document.md").resolve()
    assert paths.resources_root == tmp_path.resolve()
    assert paths.assets == (tmp_path / "assets").resolve()
    assert paths.bibliography == (tmp_path / "references.bib").resolve()
    assert paths.output_directory == (tmp_path / "build").resolve()
    assert paths.docx == (tmp_path / "build/document.docx").resolve()
    assert paths.review_directory == (tmp_path / "review").resolve()
    assert paths.review_markdown == (tmp_path / "review/document.review.md").resolve()
    assert paths.source_map == (tmp_path / "review/document.review-map.json").resolve()


def test_resolve_project_paths_uses_declared_resource_root(tmp_path: Path) -> None:
    write_project(tmp_path, resources_root="resources")

    paths = resolve_project_paths(load_project(tmp_path))

    assert paths.resources_root == (tmp_path / "resources").resolve()
    assert paths.assets == (tmp_path / "resources/assets").resolve()
    assert paths.bibliography == (tmp_path / "resources/references.bib").resolve()


@pytest.mark.parametrize(
    "value, code",
    [
        ("../escape", "TF-PROJECT-PATH-TRAVERSAL"),
        ("/tmp/escape", "TF-PROJECT-PATH-ABSOLUTE"),
        ("C:\\escape", "TF-PROJECT-PATH-ABSOLUTE"),
        ("\\\\server\\share\\escape", "TF-PROJECT-PATH-ABSOLUTE"),
        ("https://example.com/asset", "TF-PROJECT-PATH-REMOTE"),
        ("safe\x00path", "TF-PROJECT-PATH-INVALID"),
        ("", "TF-PROJECT-PATH-INVALID"),
    ],
)
def test_resolve_project_path_rejects_unsafe_values(
    tmp_path: Path,
    value: str,
    code: str,
) -> None:
    tmp_path.mkdir(exist_ok=True)

    with pytest.raises(ProjectPathError) as captured:
        resolve_project_path(tmp_path, value, field="resources.assets")

    assert captured.value.code == code
    assert captured.value.field == "resources.assets"


@pytest.mark.parametrize(
    ("field", "link_path", "target_is_directory"),
    [
        ("document.source", "document.md", False),
        ("resources.assets", "resources/assets", True),
        ("resources.bibliography", "resources/references.bib", False),
        ("output.directory", "build", True),
        ("output.docx", "build/document.docx", False),
        ("review.directory", "review", True),
        ("review.markdown", "review/document.review.md", False),
        ("review.source_map", "review/document.review-map.json", False),
    ],
)
def test_resolve_project_paths_rejects_symlink_escape_for_every_path(
    tmp_path: Path,
    field: str,
    link_path: str,
    target_is_directory: bool,
) -> None:
    project_root = tmp_path / "project"
    write_project(project_root, resources_root="resources")
    link = project_root / link_path
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_dir():
        link.rmdir()
    elif link.exists():
        link.unlink()

    outside = tmp_path / f"outside-{field.replace('.', '-')}"
    if target_is_directory:
        outside.mkdir()
    else:
        outside.write_text("outside\n", encoding="utf-8")
    try:
        os.symlink(outside, link, target_is_directory=target_is_directory)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")

    with pytest.raises(ProjectPathError) as captured:
        load_project(project_root)

    assert captured.value.code == "TF-PROJECT-PATH-SYMLINK-ESCAPE"
    assert captured.value.field == field


def test_resolve_project_paths_rejects_resource_root_symlink_escape(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    outside = tmp_path / "outside"
    project_root.mkdir()
    outside.mkdir()
    (project_root / "document.md").write_text("# 概述\n", encoding="utf-8")
    (project_root / "docforge.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "docforge.project.v1",
                "project": {"id": "paths-fixture", "language": "zh-CN"},
                "document": {},
                "resources": {"root": "resources"},
                "render": {"template_id": "docforge-standard"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    try:
        os.symlink(outside, project_root / "resources", target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")

    with pytest.raises(ProjectPathError) as captured:
        load_project(project_root)

    assert captured.value.code == "TF-PROJECT-PATH-SYMLINK-ESCAPE"
    assert captured.value.field == "resources.root"
