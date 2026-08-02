from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import yaml

from .model import TemplateLoadError, ThesisTemplate, load_template

TEMPLATE_ID_LINE_RE = re.compile(r"(?m)^id:\s*(?P<value>[^#\r\n]+)")


class TemplateSelectionError(ValueError):
    pass


class TemplateNotFoundError(TemplateSelectionError):
    def __init__(self, selector: str):
        self.selector = selector
        super().__init__(f"找不到模板: {selector}")


class TemplateAmbiguousError(TemplateSelectionError):
    def __init__(self, template_id: str, paths: tuple[Path, ...]):
        self.template_id = template_id
        self.paths = paths
        joined = ", ".join(str(path) for path in paths)
        super().__init__(f"模板 ID 不唯一: {template_id}: {joined}")


@dataclass(frozen=True, slots=True)
class ResolvedTemplate:
    path: Path
    template: ThesisTemplate


def default_template_search_roots(source_path: Path | None = None) -> tuple[Path, ...]:
    if source_path is not None:
        source = Path(source_path).expanduser().resolve()
        for ancestor in (source.parent, *source.parents):
            template_dir = ancestor / "templates"
            if template_dir.is_dir() and _candidate_paths((template_dir,)):
                return (template_dir,)

    package_templates = Path(str(resources.files("thesis_forge").joinpath("template_data")))
    if package_templates.is_dir():
        return (package_templates,)

    checkout_templates = Path(__file__).resolve().parents[3] / "templates"
    if checkout_templates.is_dir():
        return (checkout_templates,)

    return ()


def _candidate_paths(search_roots: Iterable[Path]) -> list[Path]:
    candidates: set[Path] = set()
    for raw_root in search_roots:
        root = Path(raw_root).expanduser()
        if not root.is_absolute():
            root = Path.cwd() / root
        if root.is_file() and root.suffix in {".yaml", ".yml"}:
            candidates.add(root.resolve())
        elif root.is_dir():
            candidates.update(
                path.resolve()
                for pattern in ("*.yaml", "*.yml")
                for path in root.rglob(pattern)
                if not path.name.startswith("._")
            )
    return sorted(candidates)


def _read_template_id(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        match = TEMPLATE_ID_LINE_RE.search(text)
        if match is None:
            return None
        return match.group("value").strip().strip("'\"") or None
    if not isinstance(data, dict):
        return None
    value = data.get("id")
    return value if isinstance(value, str) else None


def resolve_template(
    *,
    explicit_path: str | Path | None,
    template_id: str | None,
    search_roots: Iterable[Path] | None = None,
) -> ResolvedTemplate:
    if explicit_path is not None:
        path = Path(explicit_path).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        if path.suffix.lower() not in {".yaml", ".yml"}:
            raise TemplateLoadError(
                path,
                (("$file", "Template path must use a .yaml or .yml extension"),),
            )
        if not path.is_file():
            raise TemplateNotFoundError(str(explicit_path))
        return ResolvedTemplate(path=path, template=load_template(path))

    if not template_id:
        raise TemplateNotFoundError("未选择模板")

    active_roots = (
        default_template_search_roots()
        if search_roots is None
        else tuple(search_roots)
    )
    matches = tuple(
        path
        for path in _candidate_paths(active_roots)
        if _read_template_id(path) == template_id
    )
    if not matches:
        raise TemplateNotFoundError(template_id)
    if len(matches) > 1:
        raise TemplateAmbiguousError(template_id, matches)

    path = matches[0]
    return ResolvedTemplate(path=path, template=load_template(path))
