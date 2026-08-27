from pathlib import Path
from typing import get_args

from docforge.core.model import ForgeDocument, Heading, Text
from docforge.core.validator import ValidationContext, validate_document
from docforge.presentation.metadata import cover_binding_label
from docforge.project.loader import load_project
from docforge.templates import (
    METADATA_BINDING_REGISTRY,
    CoverSpec,
    MetadataBindingPath,
    ResolvedMetadataBinding,
    load_template,
    manifest_binding_data,
    resolve_template,
    resolve_template_bindings,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"


def test_docforge_standard_is_resolvable_and_declares_only_common_bindings() -> None:
    resolved = resolve_template(
        explicit_path=None,
        template_id="docforge-standard",
        search_roots=(ROOT / "templates",),
    )

    assert resolved.template.id == "docforge-standard"
    fields = {
        item.field
        for item in resolved.template.cover.items
        if item.field is not None
    }
    assert fields == {
        "metadata.title.zh",
        "metadata.title.en",
        "metadata.subtitle.zh",
        "metadata.organization",
        "metadata.authors",
        "metadata.version",
        "metadata.date",
        "metadata.keywords",
    }
    assert not any(field.startswith("academic.") for field in fields)
    assert {
        item.required_group
        for item in resolved.template.cover.items
        if item.required_group is not None
    } == {"metadata.title"}


def test_metadata_binding_registry_has_complete_presentation_parity() -> None:
    paths = set(get_args(MetadataBindingPath))

    assert set(METADATA_BINDING_REGISTRY) == paths
    assert all(
        descriptor.label and descriptor.format_kind
        for descriptor in METADATA_BINDING_REGISTRY.values()
    )
    assert all(
        cover_binding_label(path) == METADATA_BINDING_REGISTRY[path].label
        for path in paths
    )


def test_common_and_academic_manifest_values_resolve_without_flattening() -> None:
    general = load_project(FIXTURES / "docforge-general")
    academic = load_project(FIXTURES / "docforge-academic")
    general_template = load_template(ROOT / "templates" / "base" / "docforge-standard.yaml")
    academic_template = load_template(
        ROOT / "templates" / "schools" / "example-university" / "2026.yaml"
    )

    general_values = {
        binding.path: binding.value
        for binding in resolve_template_bindings(
            manifest_binding_data(general.manifest),
            general_template,
        )
    }
    academic_values = {
        binding.path: binding.value
        for binding in resolve_template_bindings(
            manifest_binding_data(academic.manifest),
            academic_template,
        )
    }

    assert general_values["metadata.title.zh"] == "DocForge 通用文档"
    assert general_values["metadata.authors"] == "张三"
    assert general_values["metadata.keywords"] == "项目报告、Markdown"
    assert academic_values["academic.student.id"] == "20260001"
    assert academic_values["academic.institution.name"] == "示例大学"
    assert academic_values["academic.advisor.name"] == "李教授"


def test_academic_template_reports_template_scoped_missing_profile_fields() -> None:
    template = load_template(
        ROOT / "templates" / "schools" / "example-university" / "2026.yaml"
    )
    document = ForgeDocument(
        source_path=Path("/tmp/document.md"),
        metadata={
            "metadata": {
                "title": {"zh": "普通报告"},
                "authors": [{"name": "Alice"}],
            },
            "render": {"template_id": template.id},
        },
        blocks=[
            Heading(
                id="chap:introduction",
                level=1,
                inlines=[Text(value="绪论")],
            )
        ],
    )

    issues = validate_document(
        document,
        ValidationContext(template=template, required_metadata=()),
    )
    missing = {
        issue.target: issue.details
        for issue in issues
        if issue.code == "required-metadata"
    }

    assert "academic.student.id" in missing
    assert "academic.institution.name" in missing
    assert "academic.advisor.name" in missing
    assert all(details["template_id"] == template.id for details in missing.values())


def test_multiple_authors_honor_template_join_with() -> None:
    template = load_template(ROOT / "templates" / "base" / "docforge-standard.yaml")
    template.cover = CoverSpec.model_validate(
        {"items": [{"field": "metadata.authors", "join_with": " & "}]}
    )

    bindings = resolve_template_bindings(
        {
            "metadata": {
                "authors": [{"name": "Alice"}, {"name": "Bob"}],
            }
        },
        template,
    )

    assert bindings == (
        ResolvedMetadataBinding(
            path="metadata.authors",
            value="Alice & Bob",
            required=False,
        ),
    )


def test_docforge_standard_selects_one_title_for_project_locale() -> None:
    template = load_template(ROOT / "templates" / "base" / "docforge-standard.yaml")
    project = load_project(FIXTURES / "docforge-general").manifest.model_copy(
        deep=True
    )

    project.project.language = "en-US"
    project.metadata.title = type(project.metadata.title).model_validate(
        {"zh": "中文标题", "en": "English title"}
    )
    bindings = resolve_template_bindings(manifest_binding_data(project), template)

    assert [
        (binding.path, binding.value)
        for binding in bindings
        if binding.required_group == "metadata.title"
    ] == [
        ("metadata.title.en", "English title"),
    ]


def test_docforge_standard_accepts_english_only_title() -> None:
    template = load_template(ROOT / "templates" / "base" / "docforge-standard.yaml")
    project = load_project(FIXTURES / "docforge-general").manifest.model_copy(
        deep=True
    )
    project.project.language = "en-GB"
    project.metadata.title = type(project.metadata.title).model_validate(
        {"en": "English-only title"}
    )

    document = ForgeDocument(
        source_path=Path("/tmp/document.md"),
        metadata=manifest_binding_data(project),
        blocks=[Heading(level=1, inlines=[Text(value="Body")])],
    )
    context = ValidationContext(template=template)

    assert [
        issue
        for issue in validate_document(document, context)
        if issue.code == "required-metadata"
    ] == []


def test_docforge_standard_reports_one_missing_title_group() -> None:
    template = load_template(ROOT / "templates" / "base" / "docforge-standard.yaml")
    document = ForgeDocument(
        source_path=Path("/tmp/document.md"),
        metadata={"metadata": {}},
        blocks=[Heading(level=1, inlines=[Text(value="Body")])],
    )

    issues = [
        issue
        for issue in validate_document(document, ValidationContext(template=template))
        if issue.code == "required-metadata"
    ]

    assert len(issues) == 1
    assert issues[0].target == "metadata.title"
    assert issues[0].details == {
        "path": "metadata.title.zh",
        "required_group": "metadata.title",
        "template_id": template.id,
    }


def test_validator_without_project_has_no_legacy_required_metadata() -> None:
    document = ForgeDocument(
        source_path=Path("/tmp/document.md"),
        blocks=[Heading(level=1, inlines=[Text(value="Body")])],
    )

    issues = validate_document(document, ValidationContext())

    assert not any(issue.code == "required-metadata" for issue in issues)
