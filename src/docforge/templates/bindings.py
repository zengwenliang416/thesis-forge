from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from docforge.project.model import DocForgeProjectManifest

from .model import (
    CoverItemSpec,
    MetadataBindingPath,
    ThesisTemplate,
    get_metadata_binding_descriptor,
)


class ManifestBindingData(dict[str, Any]):
    """Manifest groups plus the project language used by localized bindings."""

    __slots__ = ("locale",)

    def __init__(self, data: Mapping[str, Any], locale: str) -> None:
        super().__init__(data)
        self.locale = locale


@dataclass(frozen=True, slots=True)
class ResolvedMetadataBinding:
    path: MetadataBindingPath
    value: str
    required: bool
    required_group: str | None = None
    skip_if_empty: bool = True


def manifest_binding_data(manifest: DocForgeProjectManifest) -> dict[str, Any]:
    data: dict[str, Any] = {
        "metadata": manifest.metadata.model_dump(mode="json", exclude_none=True),
        "render": manifest.render.model_dump(mode="json", exclude_none=True),
    }
    if manifest.academic is not None:
        data["academic"] = manifest.academic.model_dump(
            mode="json",
            exclude_none=True,
        )
    return ManifestBindingData(data, manifest.project.language)


def _primary_locale(locale: str | None) -> str:
    if isinstance(locale, str):
        primary = locale.replace("_", "-").split("-", 1)[0].lower()
        if primary in {"zh", "en"}:
            return primary
    return "zh"


def _inferred_locale(data: Mapping[str, Any]) -> str:
    metadata = data.get("metadata")
    title = metadata.get("title") if isinstance(metadata, Mapping) else None
    if isinstance(title, Mapping) and title.get("en") and not title.get("zh"):
        return "en"
    return "zh"


def _binding_value(
    data: Mapping[str, Any],
    path: MetadataBindingPath,
    join_with: str,
) -> str:
    descriptor = get_metadata_binding_descriptor(path)
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return ""
        value = value[part]

    if descriptor.format_kind == "authors":
        if not isinstance(value, list):
            return ""
        names = [
            item["name"].strip()
            for item in value
            if isinstance(item, Mapping)
            and isinstance(item.get("name"), str)
            and item["name"].strip()
        ]
        return join_with.join(names)
    if descriptor.format_kind == "keywords":
        if not isinstance(value, list):
            return ""
        keywords = [
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]
        return join_with.join(keywords)
    if descriptor.format_kind != "scalar":
        raise ValueError(
            f"unsupported metadata binding format: {descriptor.format_kind}"
        )
    if value is None or isinstance(value, (Mapping, list)):
        return ""
    return str(value).strip()


def _group_binding(
    data: Mapping[str, Any],
    items: tuple[CoverItemSpec, ...],
    *,
    locale: str,
    required_group: str,
) -> ResolvedMetadataBinding:
    candidates = [
        (item, get_metadata_binding_descriptor(item.field or ""))
        for item in items
        if item.field is not None
    ]
    localized = [
        pair for pair in candidates if pair[1].localized_group == required_group
    ]
    if localized:
        candidates = [
            *[pair for pair in localized if pair[1].locale == locale],
            *[pair for pair in localized if pair[1].locale != locale],
        ]
    selected_item, _ = candidates[0]
    for item, _descriptor in candidates:
        if _binding_value(data, item.field or "", item.join_with):
            selected_item = item
            break
    value = _binding_value(data, selected_item.field or "", selected_item.join_with)
    return ResolvedMetadataBinding(
        path=selected_item.field,
        value=value,
        required=any(item.required for item in items),
        required_group=required_group,
        skip_if_empty=selected_item.skip_if_empty,
    )


def resolve_template_bindings(
    data: Mapping[str, Any],
    template: ThesisTemplate,
    *,
    locale: str | None = None,
) -> tuple[ResolvedMetadataBinding, ...]:
    active_locale = _primary_locale(
        locale or getattr(data, "locale", None) or _inferred_locale(data)
    )
    grouped: dict[str, list[CoverItemSpec]] = {}
    for item in template.cover.items:
        if item.field is not None and item.required_group is not None:
            grouped.setdefault(item.required_group, []).append(item)

    bindings: list[ResolvedMetadataBinding] = []
    emitted_groups: set[str] = set()
    for item in template.cover.items:
        if item.field is None:
            continue
        if item.required_group is not None:
            if item.required_group in emitted_groups:
                continue
            emitted_groups.add(item.required_group)
            bindings.append(
                _group_binding(
                    data,
                    tuple(grouped[item.required_group]),
                    locale=active_locale,
                    required_group=item.required_group,
                )
            )
            continue
        bindings.append(
            ResolvedMetadataBinding(
                path=item.field,
                value=_binding_value(data, item.field, item.join_with),
                required=item.required,
            )
        )
    return tuple(bindings)
