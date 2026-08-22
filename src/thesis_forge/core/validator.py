from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

from thesis_forge.bibliography import (
    BibliographyDatabase,
    BibliographyError,
    BibliographyLoader,
    BibliographyParseError,
    LocalBibTeXLoader,
    normalize_citation_style,
    supported_citation_styles,
)
from thesis_forge.project.loader import ProjectLoadError, load_project
from thesis_forge.project.model import ObjectLayoutOverride
from thesis_forge.project.paths import ProjectPathError, resolve_project_paths
from thesis_forge.templates import (
    TemplateAmbiguousError,
    TemplateLoadError,
    TemplateNotFoundError,
    TemplateSelectionError,
    ThesisTemplate,
    default_template_search_roots,
    resolve_template,
)

from .ids import is_valid_stable_id
from .index import DocumentIndex
from .math import MathConversionError, UnsupportedMathError, preflight_latex
from .model import (
    Algorithm,
    Emphasis,
    Equation,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    Heading,
    InlineMath,
    Listing,
    Strong,
    Table,
    ThesisDocument,
    ValidationIssue,
)

ValidationRule: TypeAlias = Callable[
    [ThesisDocument, "ValidationContext"],
    Iterable[ValidationIssue],
]

DEFAULT_REQUIRED_METADATA = ("thesis.title", "author.name")
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


@dataclass(slots=True)
class ValidationContext:
    template: ThesisTemplate | None = None
    template_path: Path | None = None
    template_error: TemplateSelectionError | TemplateLoadError | None = None
    resource_roots: tuple[Path, ...] = ()
    required_metadata: tuple[str, ...] = DEFAULT_REQUIRED_METADATA
    rules: Sequence[ValidationRule] | None = None
    bibliography_loader: BibliographyLoader = field(default_factory=LocalBibTeXLoader)
    bibliography_database: BibliographyDatabase | None = None
    manifest_bibliography_path: Path | None = None
    manifest_bibliography_reference: str | None = None
    manifest_citation_style: str | None = None
    manifest_layout_objects: dict[str, ObjectLayoutOverride] = field(default_factory=dict)
    project_error: ProjectLoadError | ProjectPathError | None = None

    @classmethod
    def from_document(
        cls,
        document: ThesisDocument,
        *,
        template_path: str | Path | None = None,
        template_roots: Iterable[Path] | None = None,
        resource_roots: Iterable[Path] | None = None,
        required_metadata: Iterable[str] = DEFAULT_REQUIRED_METADATA,
        rules: Sequence[ValidationRule] | None = None,
        bibliography_loader: BibliographyLoader | None = None,
    ) -> ValidationContext:
        project = None
        manifest_paths = None
        project_error = None
        try:
            project = _discover_project(document.source_path)
            manifest_paths = (
                resolve_project_paths(project)
                if project is not None
                else None
            )
        except (ProjectLoadError, ProjectPathError) as error:
            project_error = error
        render = document.metadata.get("render")
        template_id = render.get("template_id") if isinstance(render, dict) else None
        if not isinstance(template_id, str):
            template_id = None
        if project is not None:
            template_id = project.manifest.render.template_id

        active_template_roots = (
            tuple(template_roots)
            if template_roots is not None
            else default_template_search_roots(
                project.source_path if project is not None else document.source_path
            )
        )
        active_resource_roots = tuple(
            Path(root).expanduser().resolve()
            for root in (
                resource_roots
                if resource_roots is not None
                else (
                    (manifest_paths.project_root, manifest_paths.assets)
                    if manifest_paths is not None
                    else (document.source_path.parent,)
                )
            )
        )
        manifest_bibliography_path = (
            manifest_paths.bibliography
            if manifest_paths is not None
            else None
        )
        manifest_bibliography_reference = (
            str(project.manifest.resources.bibliography)
            if project is not None
            and project.manifest.resources.bibliography is not None
            else None
        )
        manifest_citation_style = (
            project.manifest.render.citation_style
            if project is not None
            else None
        )
        manifest_layout_objects = (
            dict(project.manifest.layout.objects)
            if project is not None
            else {}
        )

        try:
            resolved = resolve_template(
                explicit_path=template_path,
                template_id=template_id,
                search_roots=active_template_roots,
            )
        except (TemplateSelectionError, TemplateLoadError) as error:
            return cls(
                template_error=error,
                resource_roots=active_resource_roots,
                required_metadata=tuple(required_metadata),
                rules=rules,
                bibliography_loader=bibliography_loader or LocalBibTeXLoader(),
                manifest_bibliography_path=manifest_bibliography_path,
                manifest_bibliography_reference=manifest_bibliography_reference,
                manifest_citation_style=manifest_citation_style,
                manifest_layout_objects=manifest_layout_objects,
                project_error=project_error,
            )
        return cls(
            template=resolved.template,
            template_path=resolved.path,
            resource_roots=active_resource_roots,
            required_metadata=tuple(required_metadata),
            rules=rules,
            bibliography_loader=bibliography_loader or LocalBibTeXLoader(),
            manifest_bibliography_path=manifest_bibliography_path,
            manifest_bibliography_reference=manifest_bibliography_reference,
            manifest_citation_style=manifest_citation_style,
            manifest_layout_objects=manifest_layout_objects,
            project_error=project_error,
        )


def _discover_project(source_path: Path):
    source = Path(source_path).expanduser().resolve()
    for ancestor in (source.parent, *source.parents):
        manifest_path = ancestor / "thesisforge.yaml"
        if manifest_path.is_file():
            return load_project(manifest_path)
    return None


def _metadata_value(document: ThesisDocument, dotted_path: str) -> object | None:
    value: object = document.metadata
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _validate_project_error(
    _document: ThesisDocument,
    context: ValidationContext,
) -> Iterable[ValidationIssue]:
    if context.project_error is None:
        return
    error = context.project_error
    yield ValidationIssue(
        code="project-path-boundary",
        severity="error",
        message="Project resource path could not be resolved safely",
        target=error.field,
        details={"error_code": error.code},
    )


def _expected_id_prefixes(block: object) -> tuple[str, ...] | None:
    if isinstance(block, Heading):
        return ("chap",) if block.level == 1 else ("sec",)
    if isinstance(block, Figure):
        return ("fig",)
    if isinstance(block, Table):
        return ("tbl",)
    if isinstance(block, Equation):
        return ("eq",)
    if isinstance(block, Algorithm):
        return ("alg",)
    if isinstance(block, Listing):
        return ("lst",)
    return None


def _validate_required_metadata(
    document: ThesisDocument,
    context: ValidationContext,
) -> Iterable[ValidationIssue]:
    for dotted_path in context.required_metadata:
        value = _metadata_value(document, dotted_path)
        if value is None or (isinstance(value, str) and not value.strip()):
            yield ValidationIssue(
                code="required-metadata",
                severity="error",
                message="Required metadata is missing",
                target=dotted_path,
                details={"path": dotted_path},
            )


def _validate_empty_document(
    document: ThesisDocument,
    _context: ValidationContext,
) -> Iterable[ValidationIssue]:
    if not document.blocks:
        yield ValidationIssue(
            code="empty-document",
            severity="error",
            message="Document body is empty",
        )


def _location_details(location: object, prefix: str) -> dict[str, str | int]:
    details: dict[str, str | int] = {}
    for detail_name, attribute in (
        ("file", "source_file"),
        ("line", "line"),
        ("column", "column"),
        ("end_line", "end_line"),
        ("end_column", "end_column"),
    ):
        value = getattr(location, attribute, None)
        if value is not None:
            details[f"{prefix}_{detail_name}"] = value
    return details


def _validate_ids(
    document: ThesisDocument,
    _context: ValidationContext,
) -> Iterable[ValidationIssue]:
    for block in document.blocks:
        if not block.id:
            continue

        expected_prefixes = _expected_id_prefixes(block)
        if expected_prefixes is not None and not is_valid_stable_id(
            block.id,
            expected_prefixes,
        ):
            expected = " / ".join(expected_prefixes)
            yield ValidationIssue(
                code="invalid-id-prefix",
                severity="error",
                message="Referencable object has an invalid ID prefix",
                line=block.location.line,
                target=block.id,
                details={"expected": expected},
            )

    for conflict in DocumentIndex.from_document(document).id_conflicts:
        duplicate = conflict.duplicate
        object_id = conflict.object_id
        details = {
            "object_id": object_id,
            "related_message": f"首次定义：{object_id}",
        }
        details.update(_location_details(duplicate.location, "source"))
        details.update(_location_details(conflict.first.location, "related"))
        yield ValidationIssue(
            code="duplicate-id",
            severity="error",
            message="Referencable object ID is duplicated",
            line=duplicate.location.line,
            target=object_id,
            details=details,
        )


def _validate_cross_references(
    document: ThesisDocument,
    _context: ValidationContext,
) -> Iterable[ValidationIssue]:
    doc_index = DocumentIndex.from_document(document)
    index = doc_index.by_id
    for reference in doc_index.cross_references:
        if reference.target not in index:
            yield ValidationIssue(
                code="missing-reference",
                severity="error",
                message="Cross-reference target does not exist",
                line=reference.location.line,
                target=reference.target,
            )


def _nested_footnote_references(
    inlines: Iterable[object],
) -> Iterable[FootnoteReference]:
    for inline in inlines:
        if isinstance(inline, FootnoteReference):
            yield inline
        elif isinstance(inline, (Strong, Emphasis)):
            yield from _nested_footnote_references(inline.children)


def _validate_footnotes(
    document: ThesisDocument,
    _context: ValidationContext,
) -> Iterable[ValidationIssue]:
    definitions: dict[str, FootnoteDefinition] = {}
    for block in document.blocks:
        if not isinstance(block, FootnoteDefinition):
            continue

        first = definitions.get(block.label)
        if first is not None:
            details = {
                "label": block.label,
                "related_message": f"首次定义：{block.label}",
            }
            details.update(_location_details(block.location, "source"))
            details.update(_location_details(first.location, "related"))
            yield ValidationIssue(
                code="duplicate-footnote",
                severity="error",
                message="Footnote definition label is duplicated",
                line=block.location.line,
                target=block.label,
                details=details,
            )
        else:
            definitions[block.label] = block

        for reference in _nested_footnote_references(block.inlines):
            details = {"definition_label": block.label}
            details.update(_location_details(reference.location, "source"))
            yield ValidationIssue(
                code="nested-footnote",
                severity="error",
                message="Nested footnote references are not supported",
                line=reference.location.line,
                target=reference.label,
                details=details,
            )

    for reference in DocumentIndex.from_document(document).footnote_references:
        if reference.label in definitions:
            continue
        details = {"label": reference.label}
        details.update(_location_details(reference.location, "source"))
        yield ValidationIssue(
            code="missing-footnote",
            severity="error",
            message="Footnote reference has no definition",
            line=reference.location.line,
            target=reference.label,
            details=details,
        )


def _validate_math_preflight(
    document: ThesisDocument,
    _context: ValidationContext,
) -> Iterable[ValidationIssue]:
    index = DocumentIndex.from_document(document)
    formulas = [
        (
            f"inline:{inline.node_id}",
            inline.latex,
            inline.location,
        )
        for inline in index.inlines
        if isinstance(inline, InlineMath)
    ]
    formulas.extend(
        (
            f"equation:{block.id or block.node_id}",
            block.latex,
            block.location,
        )
        for block in document.blocks
        if isinstance(block, Equation)
    )

    for target, latex, location in formulas:
        try:
            preflight_latex(latex)
        except MathConversionError as error:
            details: dict[str, str | int] = {
                "formula": latex,
                "error_type": type(error).__name__,
            }
            if isinstance(error, UnsupportedMathError):
                code = "unsupported-math"
                message = "Formula uses an unsupported LaTeX command"
                details["command"] = error.command
            else:
                code = "invalid-math"
                message = "Formula syntax is invalid"
            details.update(_location_details(location, "source"))
            yield ValidationIssue(
                code=code,
                severity="error",
                message=message,
                line=location.line,
                target=target,
                details=details,
            )


def _validate_heading_hierarchy(
    document: ThesisDocument,
    _context: ValidationContext,
) -> Iterable[ValidationIssue]:
    previous_level: int | None = None
    for block in document.blocks:
        if not isinstance(block, Heading):
            continue
        if previous_level is not None and block.level > previous_level + 1:
            yield ValidationIssue(
                code="heading-level-jump",
                severity="warning",
                message="Heading level jumps by more than one level",
                line=block.location.line,
                target=f"H{previous_level}->H{block.level}",
                details={
                    "previous_level": previous_level,
                    "current_level": block.level,
                },
            )
        previous_level = block.level


def _active_resource_roots(
    document: ThesisDocument,
    context: ValidationContext,
) -> tuple[Path, ...]:
    if context.resource_roots:
        return context.resource_roots
    return (document.source_path.parent.resolve(),)


def _resolve_local_resource(
    document: ThesisDocument,
    context: ValidationContext,
    value: str | Path,
) -> tuple[Path, bool]:
    path = (
        value.resolve()
        if isinstance(value, Path)
        else (document.source_path.parent / value).resolve()
    )
    escaped = not any(
        path.is_relative_to(root)
        for root in _active_resource_roots(document, context)
    )
    return path, escaped


def _validate_images(
    document: ThesisDocument,
    context: ValidationContext,
) -> Iterable[ValidationIssue]:
    for block in document.blocks:
        if isinstance(block, Figure) and block.src:
            image_path, escaped = _resolve_local_resource(
                document,
                context,
                block.src,
            )
            if escaped:
                yield ValidationIssue(
                    code="resource-path-escape",
                    severity="error",
                    message="Local resource path escapes the configured resource root",
                    line=block.location.line,
                    target=block.src,
                    details={"resource_type": "image"},
                )
                continue
            if not image_path.is_file():
                yield ValidationIssue(
                    code="missing-image",
                    severity="error",
                    message="Local image does not exist",
                    line=block.location.line,
                    target=block.src,
                    details={"object_id": block.id or ""},
                )


def _validate_bibliography(
    document: ThesisDocument,
    context: ValidationContext,
) -> Iterable[ValidationIssue]:
    context.bibliography_database = None
    bibliography_path = (
        context.manifest_bibliography_path
        if context.manifest_bibliography_path is not None
        else document.bibliography.path
        if document.bibliography
        else None
    )
    bibliography_target = (
        context.manifest_bibliography_reference
        if context.manifest_bibliography_reference is not None
        else str(bibliography_path)
        if bibliography_path is not None
        else None
    )
    citations = DocumentIndex.from_document(document).citations
    first_citation = citations[0] if citations else None
    if not bibliography_path:
        if first_citation is not None:
            yield ValidationIssue(
                code="missing-bibliography",
                severity="error",
                message="Document contains citations without a bibliography path",
                line=first_citation.location.line,
            )
        return

    resolved_path, escaped = _resolve_local_resource(
        document,
        context,
        bibliography_path,
    )
    line = first_citation.location.line if first_citation is not None else None

    # D-07：citation_style / 模板 citation.style 必须真正可解析；不支持的
    # 样式给结构化诊断，而不是静默回落默认 GB/T 引擎。
    style = context.manifest_citation_style
    if style is None and document.bibliography:
        style = document.bibliography.citation_style
    if (
        style is None
        and context.template is not None
        and context.template.citation is not None
    ):
        style = context.template.citation.style
    if style is not None and normalize_citation_style(style) is None:
        yield ValidationIssue(
            code="unsupported-citation-style",
            severity="error",
            message="Configured citation style is not supported",
            line=line,
            target=style,
            details={"supported_styles": ", ".join(supported_citation_styles())},
        )
        return

    if escaped:
        yield ValidationIssue(
            code="resource-path-escape",
            severity="error",
            message="Local resource path escapes the configured resource root",
            line=line,
            target=bibliography_target,
            details={"resource_type": "bibliography"},
        )
        return
    if not resolved_path.is_file():
        yield ValidationIssue(
            code="missing-bibliography",
            severity="error",
            message="Configured bibliography file does not exist",
            line=line,
            target=bibliography_target,
        )
        return

    try:
        database = context.bibliography_loader.load(resolved_path)
    except (BibliographyError, OSError) as error:
        details: dict[str, str | int] = {
            "error_type": type(error).__name__,
            "problem": str(
                getattr(error, "detail", str(error))
            ).replace(str(resolved_path), "<path>"),
        }
        if isinstance(error, BibliographyParseError):
            details["bibliography_line"] = error.line
        yield ValidationIssue(
            code="invalid-bibliography",
            severity="error",
            message="Configured bibliography data is invalid",
            line=line,
            target=bibliography_target,
            details=details,
        )
        return

    context.bibliography_database = database
    for citation in citations:
        for key in citation.keys:
            if key not in database.records:
                yield ValidationIssue(
                    code="missing-citation",
                    severity="error",
                    message="Citation key does not exist in the local bibliography",
                    line=citation.location.line,
                    target=key,
                    details={"bibliography": bibliography_target or ""},
                )


def _template_error_issue(
    error: TemplateSelectionError | TemplateLoadError,
) -> ValidationIssue:
    if isinstance(error, TemplateNotFoundError):
        code = "missing-template"
        target = error.selector
        details = {"selector": error.selector}
    elif isinstance(error, TemplateAmbiguousError):
        code = "ambiguous-template"
        target = error.template_id
        details = {
            "template_id": error.template_id,
            "paths": ", ".join(str(path) for path in error.paths),
        }
    else:
        code = "invalid-template"
        field, problem = error.field_errors[0] if error.field_errors else ("$root", "")
        target = field
        details = {
            "path": str(error.path),
            "field": field,
            "problem": problem,
        }
    return ValidationIssue(
        code=code,
        severity="error",
        message="Template selection or validation failed",
        target=target,
        details=details,
    )


def _validate_template(
    document: ThesisDocument,
    context: ValidationContext,
) -> Iterable[ValidationIssue]:
    if context.template_error is not None:
        yield _template_error_issue(context.template_error)
        return
    if context.template is None:
        yield ValidationIssue(
            code="missing-template",
            severity="error",
            message="No thesis template was resolved",
            target="template",
        )
        return

    template = context.template
    missing_styles: dict[str, int | None] = {}
    for block in document.blocks:
        if isinstance(block, Heading) and template.heading.for_level(block.level) is None:
            missing_styles.setdefault(f"heading.level{block.level}", block.location.line)
        elif isinstance(block, Figure) and template.figure is None:
            missing_styles.setdefault("figure", block.location.line)
        elif isinstance(block, Table) and template.table is None:
            missing_styles.setdefault("table", block.location.line)
        elif isinstance(block, Equation) and template.equation is None:
            missing_styles.setdefault("equation", block.location.line)

    citations = DocumentIndex.from_document(document).citations
    if citations and template.citation is None:
        missing_styles.setdefault("citation", citations[0].location.line)

    for target, line in missing_styles.items():
        yield ValidationIssue(
            code="missing-template-style",
            severity="error",
            message="Template does not define a required semantic style",
            line=line,
            target=target,
        )


def _validate_layout_overrides(
    document: ThesisDocument,
    context: ValidationContext,
) -> Iterable[ValidationIssue]:
    if not context.manifest_layout_objects:
        return
    index = DocumentIndex.from_document(document).by_id
    for object_id in sorted(context.manifest_layout_objects):
        block = index.get(object_id)
        if block is None:
            yield ValidationIssue(
                code="orphan-layout-override",
                severity="error",
                message="Layout override targets an object that does not exist",
                target=object_id,
                details={"field": "width"},
            )
            continue
        if not isinstance(block, Figure):
            prefixes = _expected_id_prefixes(block)
            actual = prefixes[0] if prefixes else type(block).__name__.lower()
            yield ValidationIssue(
                code="layout-override-type-mismatch",
                severity="error",
                message="Layout override field does not apply to this object type",
                target=object_id,
                details={"field": "width", "expected": "fig", "actual": actual},
            )


DEFAULT_VALIDATION_RULES: tuple[ValidationRule, ...] = (
    _validate_project_error,
    _validate_required_metadata,
    _validate_empty_document,
    _validate_ids,
    _validate_cross_references,
    _validate_footnotes,
    _validate_math_preflight,
    _validate_heading_hierarchy,
    _validate_images,
    _validate_bibliography,
    _validate_template,
    _validate_layout_overrides,
)


def validation_issue_sort_key(issue: ValidationIssue) -> tuple[object, ...]:
    return (
        -1 if issue.line is None else issue.line,
        SEVERITY_ORDER[issue.severity],
        issue.code,
        issue.target or "",
        issue.message,
    )


def validate_document(
    document: ThesisDocument,
    context: ValidationContext | None = None,
) -> list[ValidationIssue]:
    active_context = context or ValidationContext.from_document(document)
    active_context.bibliography_database = None
    rules = (
        DEFAULT_VALIDATION_RULES
        if active_context.rules is None
        else tuple(active_context.rules)
    )
    issues = [
        issue
        for rule in rules
        for issue in rule(document, active_context)
    ]
    return sorted(issues, key=validation_issue_sort_key)
