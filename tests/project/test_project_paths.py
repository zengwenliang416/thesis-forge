from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from thesis_forge.project.loader import load_project
from thesis_forge.project.paths import (
    ProjectPathError,
    resolve_project_path,
    resolve_project_paths,
)


def write_project(root: Path, *, assets: str = "assets") -> None:
    (root / assets).mkdir(parents=True, exist_ok=True)
    (root / "thesis.md").write_text("# 绪论\n", encoding="utf-8")
    (root / "references.bib").write_text(
        "@article{sample, author={张三}, title={测试}, year={2026}}\n",
        encoding="utf-8",
    )
    (root / "thesisforge.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "thesisforge.project.v2",
                "project": {"id": "paths-fixture", "language": "zh-CN"},
                "document": {"source": "thesis.md"},
                "resources": {
                    "root": ".",
                    "assets": assets,
                    "bibliography": "references.bib",
                },
                "render": {"template_id": "example-university-2026"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_resolve_project_paths_uses_one_project_root(tmp_path: Path) -> None:
    write_project(tmp_path)

    paths = resolve_project_paths(load_project(tmp_path))

    assert paths.project_root == tmp_path.resolve()
    assert paths.source == (tmp_path / "thesis.md").resolve()
    assert paths.assets == (tmp_path / "assets").resolve()
    assert paths.bibliography == (tmp_path / "references.bib").resolve()
    assert paths.output_directory == (tmp_path / "build").resolve()
    assert paths.docx == (tmp_path / "build/thesis.docx").resolve()
    assert paths.review_directory == (tmp_path / "review").resolve()
    assert paths.review_markdown == (tmp_path / "review/thesis.review.md").resolve()
    assert paths.source_map == (tmp_path / "review/thesis.review-map.json").resolve()


@pytest.mark.parametrize(
    "value, code",
    [
        ("../escape", "TF-PROJECT-PATH-TRAVERSAL"),
        ("/tmp/escape", "TF-PROJECT-PATH-ABSOLUTE"),
        ("C:\\escape", "TF-PROJECT-PATH-ABSOLUTE"),
        ("\\\\server\\share\\escape", "TF-PROJECT-PATH-ABSOLUTE"),
        ("https://example.com/asset", "TF-PROJECT-PATH-REMOTE"),
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


def test_resolve_project_path_rejects_symlink_escape(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    outside = tmp_path / "outside"
    project_root.mkdir()
    outside.mkdir()
    try:
        os.symlink(outside, project_root / "assets", target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")

    with pytest.raises(ProjectPathError) as captured:
        resolve_project_path(project_root, "assets", field="resources.assets")

    assert captured.value.code == "TF-PROJECT-PATH-SYMLINK-ESCAPE"


def test_resolve_project_paths_rejects_output_symlink_escape(tmp_path: Path) -> None:
    write_project(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    try:
        os.symlink(outside, tmp_path / "build", target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")

    with pytest.raises(ProjectPathError) as captured:
        resolve_project_paths(load_project(tmp_path))

    assert captured.value.code == "TF-PROJECT-PATH-SYMLINK-ESCAPE"
    assert captured.value.field == "output.directory"
