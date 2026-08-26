from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from thesis_forge.project.loader import ProjectLoadError, load_project


def manifest_data() -> dict:
    return {
        "schema": "docforge.project.v1",
        "project": {"id": "loader-fixture", "language": "zh-CN"},
        "document": {},
        "metadata": {"title": {"zh": "测试文档"}, "authors": [{"name": "张三"}]},
        "render": {"template_id": "docforge-standard"},
    }


def write_project(root: Path, manifest: dict | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "document.md").write_text("# 概述\n", encoding="utf-8")
    manifest_path = root / "docforge.yaml"
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
        assert loaded.manifest.document.source.root == "document.md"
        assert loaded.manifest.project.id == "loader-fixture"


def test_loader_rejects_bare_markdown_input(tmp_path: Path) -> None:
    source = tmp_path / "document.md"
    source.write_text("# 概述\n", encoding="utf-8")

    with pytest.raises(ProjectLoadError) as captured:
        load_project(source)

    assert captured.value.code == "TF-PROJECT-BARE-MARKDOWN"
    assert "DocForge" in str(captured.value)


def test_loader_rejects_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-MANIFEST-MISSING"
    assert captured.value.path == tmp_path / "docforge.yaml"


def test_loader_rejects_obsolete_manifest_path(tmp_path: Path) -> None:
    obsolete = tmp_path / "thesisforge.yaml"
    obsolete.write_text("schema: thesisforge.project.v2\n", encoding="utf-8")

    with pytest.raises(ProjectLoadError) as captured:
        load_project(obsolete)

    assert captured.value.code == "TF-PROJECT-CONTRACT-OBSOLETE"
    assert "docforge.yaml" in str(captured.value)


def test_loader_rejects_obsolete_manifest_in_directory(tmp_path: Path) -> None:
    (tmp_path / "thesisforge.yaml").write_text(
        "schema: thesisforge.project.v2\n",
        encoding="utf-8",
    )

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-CONTRACT-OBSOLETE"


def test_loader_rejects_obsolete_schema_in_docforge_manifest(tmp_path: Path) -> None:
    payload = manifest_data()
    payload["schema"] = "thesisforge.project.v2"
    write_project(tmp_path, payload)

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-CONTRACT-OBSOLETE"
    assert captured.value.field == "schema"


def test_loader_rejects_duplicate_yaml_keys(tmp_path: Path) -> None:
    (tmp_path / "document.md").write_text("# 概述\n", encoding="utf-8")
    (tmp_path / "docforge.yaml").write_text(
        """
schema: docforge.project.v1
project:
  id: loader-fixture
  language: zh-CN
document: {}
project:
  id: duplicate
  language: zh-CN
render:
  template_id: docforge-standard
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-DUPLICATE-KEY"


def test_loader_rejects_nested_duplicate_yaml_keys(tmp_path: Path) -> None:
    (tmp_path / "document.md").write_text("# 概述\n", encoding="utf-8")
    (tmp_path / "docforge.yaml").write_text(
        """
schema: docforge.project.v1
project:
  id: loader-fixture
  language: zh-CN
document: {}
metadata:
  title:
    zh: first
    zh: second
render:
  template_id: docforge-standard
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-DUPLICATE-KEY"


def test_loader_rejects_existing_non_manifest_file(tmp_path: Path) -> None:
    notes = tmp_path / "notes.yaml"
    notes.write_text("not: a project\n", encoding="utf-8")

    with pytest.raises(ProjectLoadError) as captured:
        load_project(notes)

    assert captured.value.code == "TF-PROJECT-MANIFEST-REQUIRED"


def test_loader_rejects_missing_default_source_file(tmp_path: Path) -> None:
    (tmp_path / "docforge.yaml").write_text(
        yaml.safe_dump(manifest_data(), sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-SOURCE-MISSING"
    assert captured.value.path == tmp_path / "document.md"


def test_loader_wraps_invalid_manifest_with_stable_field(tmp_path: Path) -> None:
    manifest = manifest_data()
    manifest["metadata"]["university"] = "不属于通用元数据"
    write_project(tmp_path, manifest)

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-MANIFEST-INVALID"
    assert captured.value.field == "metadata.university"


def test_loader_sanitizes_manifest_validation_details(tmp_path: Path) -> None:
    manifest = manifest_data()
    manifest["document"]["source"] = "/Users/secret/document.md"
    write_project(tmp_path, manifest)

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-MANIFEST-INVALID"
    assert "/Users/secret" not in str(captured.value)
    assert "input_value" not in str(captured.value)


def test_loader_wraps_unhashable_yaml_mapping_keys(tmp_path: Path) -> None:
    (tmp_path / "docforge.yaml").write_text(
        """
? [unhashable]
: value
""".lstrip(),
        encoding="utf-8",
    )

    with pytest.raises(ProjectLoadError) as captured:
        load_project(tmp_path)

    assert captured.value.code == "TF-PROJECT-YAML-INVALID"
