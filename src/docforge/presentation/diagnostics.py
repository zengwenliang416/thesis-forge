from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from docforge.application.contracts import BuildDiagnostic
    from docforge.core.model import ValidationIssue


class _DiagnosticLike(Protocol):
    code: str
    message: str
    target: str | None
    details: Mapping[str, object]


DiagnosticFormatter = Callable[[_DiagnosticLike], str]


def _format_required_metadata(diagnostic: _DiagnosticLike) -> str:
    return f"缺少必填元数据：{diagnostic.details.get('path', diagnostic.target or '')}"


def _format_empty_document(_diagnostic: _DiagnosticLike) -> str:
    return "论文正文为空"


def _format_invalid_id_prefix(diagnostic: _DiagnosticLike) -> str:
    return (
        f"ID 前缀无效：{diagnostic.target or ''}，"
        f"期望 {diagnostic.details.get('expected', '')}"
    )


def _format_duplicate_id(diagnostic: _DiagnosticLike) -> str:
    return f"重复 ID：{diagnostic.target or ''}"


def _format_canonical_duplicate_id(diagnostic: _DiagnosticLike) -> str:
    return f"重复 ID：{diagnostic.target or diagnostic.details.get('object_id', '')}"


def _format_missing_reference(diagnostic: _DiagnosticLike) -> str:
    return f"引用目标不存在：{diagnostic.target or ''}"


def _format_heading_level_jump(diagnostic: _DiagnosticLike) -> str:
    return (
        f"标题层级从 H{diagnostic.details.get('previous_level', '?')} "
        f"跳到 H{diagnostic.details.get('current_level', '?')}"
    )


def _format_resource_path_escape(diagnostic: _DiagnosticLike) -> str:
    kind = "图片" if diagnostic.details.get("resource_type") == "image" else "参考文献"
    return f"{kind}路径越出论文资源目录：{diagnostic.target or ''}"


def _format_missing_image(diagnostic: _DiagnosticLike) -> str:
    return f"图片不存在：{diagnostic.target or ''}"


def _format_missing_bibliography(diagnostic: _DiagnosticLike) -> str:
    if diagnostic.target:
        return f"参考文献文件不存在：{diagnostic.target}"
    return "文档包含引用，但未配置本地 bibliography 路径"


def _format_invalid_bibliography(diagnostic: _DiagnosticLike) -> str:
    return (
        f"参考文献数据无效：{diagnostic.target or ''}："
        f"{diagnostic.details.get('problem', diagnostic.message)}"
    )


def _format_missing_citation(diagnostic: _DiagnosticLike) -> str:
    return f"本地参考文献中不存在 citation key：{diagnostic.target or ''}"


def _format_missing_template(diagnostic: _DiagnosticLike) -> str:
    return f"找不到模板：{diagnostic.details.get('selector', diagnostic.target or 'template')}"


def _format_ambiguous_template(diagnostic: _DiagnosticLike) -> str:
    return (
        f"模板 ID 不唯一：{diagnostic.details.get('template_id', diagnostic.target or '')}："
        f"{diagnostic.details.get('paths', '')}"
    )


def _format_invalid_template(diagnostic: _DiagnosticLike) -> str:
    return (
        f"模板无效：{diagnostic.details.get('path', '')}："
        f"{diagnostic.details.get('field', diagnostic.target or '')}："
        f"{diagnostic.details.get('problem', '')}"
    )


def _format_missing_template_style(diagnostic: _DiagnosticLike) -> str:
    return f"模板未定义所需样式：{diagnostic.target or ''}"


def _format_fallback(diagnostic: _DiagnosticLike) -> str:
    return diagnostic.message


_FORMATTER_REGISTRY: dict[str, DiagnosticFormatter] = {
    "required-metadata": _format_required_metadata,
    "empty-document": _format_empty_document,
    "invalid-id-prefix": _format_invalid_id_prefix,
    "duplicate-id": _format_duplicate_id,
    "TF-SEMANTIC-DUPLICATE-ID": _format_canonical_duplicate_id,
    "missing-reference": _format_missing_reference,
    "heading-level-jump": _format_heading_level_jump,
    "resource-path-escape": _format_resource_path_escape,
    "missing-image": _format_missing_image,
    "missing-bibliography": _format_missing_bibliography,
    "invalid-bibliography": _format_invalid_bibliography,
    "missing-citation": _format_missing_citation,
    "missing-template": _format_missing_template,
    "ambiguous-template": _format_ambiguous_template,
    "invalid-template": _format_invalid_template,
    "missing-template-style": _format_missing_template_style,
}


def format_diagnostic(diagnostic: _DiagnosticLike) -> str:
    formatter = _FORMATTER_REGISTRY.get(diagnostic.code, _format_fallback)
    return formatter(diagnostic)


def localized_issue_message(issue: ValidationIssue) -> str:
    return format_diagnostic(issue)


def localized_build_diagnostic_message(diagnostic: BuildDiagnostic) -> str:
    return format_diagnostic(diagnostic)


def localized_diagnostic_message(diagnostic: _DiagnosticLike) -> str:
    return format_diagnostic(diagnostic)


def _build_source_range(
    location: object,
    source_file: str | None,
    source_range_type: type,
):
    line = getattr(location, "line", None)
    start_column = getattr(location, "column", None)
    end_line = getattr(location, "end_line", None)
    end_column = getattr(location, "end_column", None)
    if line is None:
        start_column = None
        end_line = None
        end_column = None
    elif end_line is None:
        end_column = None
    location_file = getattr(location, "source_file", None) or source_file
    return source_range_type(
        file=str(location_file) if location_file is not None else None,
        start_line=line,
        start_column=start_column,
        end_line=end_line,
        end_column=end_column,
    )


def duplicate_id_diagnostics(
    index: object,
    *,
    source_file: str | None = None,
) -> tuple[BuildDiagnostic, ...]:
    """Convert derived duplicate-ID conflicts into canonical diagnostics.

    Application and core models are imported only when this conversion is
    requested. Importing presentation or the headless UI therefore remains
    independent from the compiler and rendering stack.
    """

    from docforge.application.contracts import (
        BuildDiagnostic,
        BuildDiagnosticCategory,
        BuildDiagnosticSeverity,
        BuildRelatedLocation,
        BuildReportStage,
        BuildSourceRange,
    )

    conflicts = getattr(index, "id_conflicts", None)
    if conflicts is None:
        from docforge.core.index import DocumentIndex

        conflicts = DocumentIndex.from_document(index).id_conflicts

    ordinals: dict[str, int] = {}
    diagnostics: list[BuildDiagnostic] = []
    for conflict in conflicts:
        object_id = conflict.object_id
        ordinal = ordinals.get(object_id, 0) + 1
        ordinals[object_id] = ordinal
        duplicate_source = _build_source_range(
            conflict.duplicate.location,
            source_file,
            BuildSourceRange,
        )
        first_source = _build_source_range(
            conflict.first.location,
            source_file,
            BuildSourceRange,
        )
        diagnostics.append(
            BuildDiagnostic(
                id=f"duplicate-id:{object_id}:{ordinal}",
                severity=BuildDiagnosticSeverity.ERROR,
                category=BuildDiagnosticCategory.SEMANTIC,
                code="TF-SEMANTIC-DUPLICATE-ID",
                stage=BuildReportStage.VALIDATE,
                message=f"重复 ID：{object_id}",
                source=duplicate_source,
                target=object_id,
                related_locations=(
                    BuildRelatedLocation(
                        message=f"首次定义：{object_id}",
                        source=first_source,
                    ),
                ),
                details={
                    "object_id": object_id,
                    "duplicate_ordinal": ordinal,
                },
            )
        )
    return tuple(diagnostics)


__all__ = [
    "duplicate_id_diagnostics",
    "format_diagnostic",
    "localized_build_diagnostic_message",
    "localized_diagnostic_message",
    "localized_issue_message",
]
