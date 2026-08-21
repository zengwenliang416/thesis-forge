from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from thesis_forge.project.loader import ProjectLoadError, load_project


def manifest_data() -> dict:
    return {
        "schema": "thesisforge.project.v2",
        "project": {"id": "loader-fixture", "language": "zh-CN"},
        "document": {"source": "thesis.md"},
        "render": {"template_id": "example-university-2026"},
    }


def write_project(root: Path, manifest: dict | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "thesis.md").write_text("# 绪论\n", encoding="utf-8")
    manifest_path = root / "thesisforge.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest or manifest_data(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return manifest_path


def test_load_project_directory_and_manifest_path_returns_normalized_paths(
    tmp_path: Path,
) -> None:
    manifest_path = write_project(tmp_path)

    loaded_from_directory = load_project(tmp_path)
    loaded_from_manifest = load_project(manifest_path)

    for loaded in (loaded_from_directory, loaded_from_manifest):
        assert loaded.project_root == tmp_path.resolve()
        assert loaded.root == tmp_path.resolve()
        assert loaded.manifest_path == manifest_path.resolve()
        assert loaded.source_path == (tmp_path / "thesis.md").resolve()
        assert loaded.manifest.project.id == "loader-fixture"


def test_loader_rejects_bare_markdown_input(tmp_path: Path) -> None:
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论\n", encoding="utf-8")

    with pytest.raises(ProjectLoadError) as captured:
        load_project(source)

    assert captured.value.code == "TF-PROJECT-BARE-MARKDOWN"


def test_loader_rejects_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-MANIFEST-MISSING"


def test_loader_rejects_duplicate_yaml_keys(tmp_path: Path) -> None:
    (tmp_path / "thesis.md").write_text("# 绪论\n", encoding="utf-8")
    (tmp_path / "thesisforge.yaml").write_text(
        """
schema: thesisforge.project.v2
project:
  id: loader-fixture
  language: zh-CN
document:
  source: thesis.md
project:
  id: duplicate
  language: zh-CN
render:
  template_id: example-university-2026
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-DUPLICATE-KEY"


def test_loader_rejects_missing_source_declaration(tmp_path: Path) -> None:
    manifest = manifest_data()
    del manifest["document"]["source"]
    write_project(tmp_path, manifest)

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-SOURCE-DECLARATION"


def test_loader_rejects_missing_source_file(tmp_path: Path) -> None:
    manifest = manifest_data()
    manifest["document"]["source"] = "missing.md"
    manifest_path = tmp_path / "thesisforge.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-SOURCE-MISSING"


def test_loader_wraps_invalid_manifest_with_stable_code(tmp_path: Path) -> None:
    manifest = manifest_data()
    manifest["unknown"] = True
    write_project(tmp_path, manifest)

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-MANIFEST-INVALID"
