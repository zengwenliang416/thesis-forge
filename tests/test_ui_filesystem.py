from __future__ import annotations

from pathlib import Path

import pytest

from thesis_forge.ui import LocalWorkspaceFileSystem


def _temporary_sources(path: Path) -> list[Path]:
    return sorted(path.parent.glob(f".{path.name}.*.tmp"))


def test_local_workspace_filesystem_reads_and_atomically_writes_utf8(tmp_path: Path):
    source = tmp_path / "thesis.md"
    filesystem = LocalWorkspaceFileSystem()

    filesystem.write_text_atomic(source, "# 绪论\n")

    assert filesystem.read_text(source) == "# 绪论\n"
    assert _temporary_sources(source) == []


def test_atomic_write_replaces_existing_source_and_cleans_temporary_file(
    tmp_path: Path,
):
    source = tmp_path / "thesis.md"
    source.write_text("# Old\n", encoding="utf-8")
    filesystem = LocalWorkspaceFileSystem()

    filesystem.write_text_atomic(source, "# New\n")

    assert source.read_text(encoding="utf-8") == "# New\n"
    assert _temporary_sources(source) == []


def test_atomic_write_failure_preserves_existing_source_and_cleans_temporary_file(
    tmp_path: Path,
):
    source = tmp_path / "thesis.md"
    source.write_text("# Previous\n", encoding="utf-8")

    def fail_replace(_temporary: Path, _target: Path) -> None:
        raise PermissionError("replace denied")

    filesystem = LocalWorkspaceFileSystem(replace_file=fail_replace)

    with pytest.raises(PermissionError, match="replace denied"):
        filesystem.write_text_atomic(source, "# Unsaved\n")

    assert source.read_text(encoding="utf-8") == "# Previous\n"
    assert _temporary_sources(source) == []


def test_local_workspace_filesystem_surfaces_missing_and_invalid_utf8_sources(
    tmp_path: Path,
):
    filesystem = LocalWorkspaceFileSystem()
    invalid = tmp_path / "invalid.md"
    invalid.write_bytes(b"\xff")

    with pytest.raises(FileNotFoundError):
        filesystem.read_text(tmp_path / "missing.md")
    with pytest.raises(UnicodeDecodeError):
        filesystem.read_text(invalid)
