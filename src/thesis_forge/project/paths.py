"""Project-root path resolution and boundary enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from .model import ProjectRelativePath

if TYPE_CHECKING:
    from .loader import LoadedProject


class ProjectPathError(ValueError):
    """A stable failure while resolving a path inside a project root."""

    def __init__(self, code: str, message: str, *, field: str) -> None:
        self.code = code
        self.field = field
        super().__init__(f"{code}: {field}: {message}")


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    project_root: Path
    source: Path
    resources_root: Path
    assets: Path
    bibliography: Path | None
    output_directory: Path
    docx: Path
    review_directory: Path
    review_markdown: Path
    source_map: Path

    @property
    def root(self) -> Path:
        return self.project_root


def _invalid_path_code(raw: str) -> str:
    normalized = raw.strip().replace("\\", "/")
    if normalized.startswith("/") or PureWindowsPath(raw).is_absolute():
        return "TF-PROJECT-PATH-ABSOLUTE"
    if any(part == ".." for part in PurePosixPath(normalized).parts):
        return "TF-PROJECT-PATH-TRAVERSAL"
    if urlsplit(normalized).scheme:
        return "TF-PROJECT-PATH-REMOTE"
    return "TF-PROJECT-PATH-INVALID"


def _coerce_relative(value: ProjectRelativePath | str, *, field: str) -> ProjectRelativePath:
    if isinstance(value, ProjectRelativePath):
        raw = value.root
    elif isinstance(value, str):
        raw = value
    else:
        raise ProjectPathError(
            "TF-PROJECT-PATH-INVALID",
            "path must be a project-relative string",
            field=field,
        )

    try:
        return ProjectRelativePath.model_validate(raw)
    except (TypeError, ValueError) as error:
        raise ProjectPathError(
            _invalid_path_code(raw),
            "path is not a valid project-relative value",
            field=field,
        ) from error


def _resolve_under(root: Path, value: ProjectRelativePath | str, *, field: str) -> Path:
    relative = _coerce_relative(value, field=field)
    lexical = root / relative.root
    try:
        resolved = lexical.resolve(strict=False)
        resolved.relative_to(root)
    except ValueError as error:
        raise ProjectPathError(
            "TF-PROJECT-PATH-SYMLINK-ESCAPE",
            "resolved path leaves the project root",
            field=field,
        ) from error
    except (OSError, RuntimeError) as error:
        raise ProjectPathError(
            "TF-PROJECT-PATH-RESOLUTION",
            "path could not be resolved",
            field=field,
        ) from error
    return resolved


def _project_root(root: str | Path) -> Path:
    resolved = Path(root).expanduser().resolve()
    if not resolved.is_dir():
        raise ProjectPathError(
            "TF-PROJECT-ROOT-MISSING",
            "project root is not a directory",
            field="project.root",
        )
    return resolved


def resolve_project_path(
    project_root: str | Path,
    value: ProjectRelativePath | str,
    *,
    field: str,
) -> Path:
    """Resolve one project-relative value and enforce the root boundary."""

    return _resolve_under(_project_root(project_root), value, field=field)


def resolve_project_paths(project: LoadedProject) -> ProjectPaths:
    """Resolve all manifest paths against one normalized project root."""

    root = _project_root(project.project_root)
    manifest = project.manifest
    source = _resolve_under(root, manifest.document.source, field="document.source")
    resources_root = _resolve_under(
        root,
        manifest.resources.root,
        field="resources.root",
    )
    assets = _resolve_under(
        resources_root,
        manifest.resources.assets,
        field="resources.assets",
    )
    bibliography = (
        _resolve_under(
            resources_root,
            manifest.resources.bibliography,
            field="resources.bibliography",
        )
        if manifest.resources.bibliography is not None
        else None
    )
    output_directory = _resolve_under(
        root,
        manifest.output.directory,
        field="output.directory",
    )
    docx = _resolve_under(output_directory, manifest.output.docx, field="output.docx")
    review_directory = _resolve_under(
        root,
        manifest.review.directory,
        field="review.directory",
    )
    review_markdown = _resolve_under(
        review_directory,
        manifest.review.markdown,
        field="review.markdown",
    )
    source_map = _resolve_under(
        review_directory,
        manifest.review.source_map,
        field="review.source_map",
    )
    return ProjectPaths(
        project_root=root,
        source=source,
        resources_root=resources_root,
        assets=assets,
        bibliography=bibliography,
        output_directory=output_directory,
        docx=docx,
        review_directory=review_directory,
        review_markdown=review_markdown,
        source_map=source_map,
    )


__all__ = [
    "ProjectPathError",
    "ProjectPaths",
    "resolve_project_path",
    "resolve_project_paths",
]
