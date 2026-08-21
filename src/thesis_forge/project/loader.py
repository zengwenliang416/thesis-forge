"""Load and validate a ThesisForge v2 project manifest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .model import ProjectManifestV2


class ProjectLoadError(ValueError):
    """A stable, user-facing project loading failure."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        path: Path | None = None,
        field: str | None = None,
    ) -> None:
        self.code = code
        self.path = path
        self.field = field
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class LoadedProject:
    project_root: Path
    manifest_path: Path
    manifest: ProjectManifestV2

    @property
    def root(self) -> Path:
        return self.project_root

    @property
    def source_path(self) -> Path:
        return self.project_root / self.manifest.document.source.root


class _DuplicateKeyError(yaml.YAMLError):
    def __init__(self, key: object, line: int) -> None:
        self.key = key
        self.line = line
        super().__init__(f"duplicate YAML key {key!r} at line {line}")


class _UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(
        self,
        node: yaml.MappingNode,
        deep: bool = False,
    ) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise _DuplicateKeyError(key, key_node.start_mark.line + 1)
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def _resolve_manifest_input(input_path: str | Path) -> tuple[Path, Path]:
    candidate = Path(input_path).expanduser()
    if candidate.suffix.lower() == ".md":
        raise ProjectLoadError(
            "TF-PROJECT-BARE-MARKDOWN",
            "a project directory or thesisforge.yaml is required",
            path=candidate,
        )

    if candidate.is_dir():
        project_root = candidate.resolve()
        manifest_path = project_root / "thesisforge.yaml"
        if not manifest_path.is_file():
            raise ProjectLoadError(
                "TF-PROJECT-MANIFEST-MISSING",
                "project directory does not contain thesisforge.yaml",
                path=manifest_path,
            )
        return project_root, manifest_path.resolve()

    if not candidate.exists():
        raise ProjectLoadError(
            "TF-PROJECT-INPUT-MISSING",
            "project input does not exist",
            path=candidate,
        )
    if not candidate.is_file() or candidate.name != "thesisforge.yaml":
        raise ProjectLoadError(
            "TF-PROJECT-MANIFEST-REQUIRED",
            "project input must be a directory or thesisforge.yaml",
            path=candidate,
        )

    manifest_path = candidate.resolve()
    return manifest_path.parent, manifest_path


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ProjectLoadError(
            "TF-PROJECT-MANIFEST-READ",
            error.strerror or str(error),
            path=path,
        ) from error

    try:
        raw = yaml.load(text, Loader=_UniqueKeyLoader)
    except _DuplicateKeyError as error:
        raise ProjectLoadError(
            "TF-PROJECT-DUPLICATE-KEY",
            str(error),
            path=path,
        ) from error
    except yaml.YAMLError as error:
        raise ProjectLoadError(
            "TF-PROJECT-YAML-INVALID",
            str(error),
            path=path,
        ) from error

    if not isinstance(raw, dict):
        raise ProjectLoadError(
            "TF-PROJECT-MANIFEST-INVALID",
            "manifest root must be a mapping",
            path=path,
        )
    return raw


def load_project(input_path: str | Path) -> LoadedProject:
    """Load a project directory or explicit ``thesisforge.yaml`` path."""

    project_root, manifest_path = _resolve_manifest_input(input_path)
    raw = _read_manifest(manifest_path)
    document = raw.get("document")
    if not isinstance(document, dict) or not document.get("source"):
        raise ProjectLoadError(
            "TF-PROJECT-SOURCE-DECLARATION",
            "manifest must declare document.source",
            path=manifest_path,
            field="document.source",
        )

    try:
        manifest = ProjectManifestV2.model_validate(raw)
    except Exception as error:
        raise ProjectLoadError(
            "TF-PROJECT-MANIFEST-INVALID",
            str(error),
            path=manifest_path,
        ) from error

    loaded = LoadedProject(
        project_root=project_root,
        manifest_path=manifest_path,
        manifest=manifest,
    )
    if not loaded.source_path.is_file():
        raise ProjectLoadError(
            "TF-PROJECT-SOURCE-MISSING",
            "declared document source does not exist",
            path=loaded.source_path,
            field="document.source",
        )
    return loaded


__all__ = ["LoadedProject", "ProjectLoadError", "load_project"]
