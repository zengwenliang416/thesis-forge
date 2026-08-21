"""Strict ThesisForge v2 project manifest models."""

from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath
from typing import Literal
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)

PROJECT_SCHEMA = "thesisforge.project.v2"


class ProjectRelativePath(RootModel[str]):
    """A normalized path that is relative to the loaded project root."""

    model_config = ConfigDict(frozen=True, strict=True)
    root: str

    @field_validator("root")
    @classmethod
    def validate_root(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("project-relative path must be a string")
        normalized = value.strip().replace("\\", "/")
        if not normalized:
            raise ValueError("project-relative path must not be empty")
        if (
            normalized.startswith("/")
            or PureWindowsPath(value).is_absolute()
            or urlsplit(normalized).scheme
        ):
            raise ValueError("project-relative path must not be absolute or remote")
        if any(part == ".." for part in PurePosixPath(normalized).parts):
            raise ValueError("project-relative path must not contain '..'")
        if "\x00" in normalized:
            raise ValueError("project-relative path must not contain NUL")
        return normalized

    def __str__(self) -> str:
        return self.root

    def __fspath__(self) -> str:
        return self.root


class ManifestModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ProjectSpec(ManifestModel):
    id: str = Field(
        min_length=1,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    language: str = Field(
        min_length=2,
        pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$",
    )


class DocumentSpec(ManifestModel):
    source: ProjectRelativePath


class LocalizedText(ManifestModel):
    zh: str | None = Field(default=None, min_length=1)
    en: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_one_language(self) -> LocalizedText:
        if self.zh is None and self.en is None:
            raise ValueError("title must provide at least one localized value")
        return self


class AuthorSpec(ManifestModel):
    name: str = Field(min_length=1)
    student_id: str | None = Field(default=None, min_length=1)


class InstitutionSpec(ManifestModel):
    university: str = Field(min_length=1)
    college: str | None = Field(default=None, min_length=1)


class DegreeSpec(ManifestModel):
    name: str = Field(min_length=1)
    major: str | None = Field(default=None, min_length=1)


class AdvisorSpec(ManifestModel):
    name: str = Field(min_length=1)
    title: str | None = Field(default=None, min_length=1)


class DatesSpec(ManifestModel):
    completed: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(?:0[1-9]|1[0-2])$",
    )


class MetadataSpec(ManifestModel):
    title: LocalizedText | None = None
    author: AuthorSpec | None = None
    institution: InstitutionSpec | None = None
    degree: DegreeSpec | None = None
    advisor: AdvisorSpec | None = None
    dates: DatesSpec | None = None


class ResourcesSpec(ManifestModel):
    root: ProjectRelativePath = Field(
        default_factory=lambda: ProjectRelativePath("."),
    )
    assets: ProjectRelativePath = Field(
        default_factory=lambda: ProjectRelativePath("assets"),
    )
    bibliography: ProjectRelativePath | None = None


class RenderSpec(ManifestModel):
    template_id: str = Field(min_length=1)
    citation_style: str | None = Field(default=None, min_length=1)


class ObjectLayoutOverride(ManifestModel):
    width: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_override(self) -> ObjectLayoutOverride:
        if self.width is None:
            raise ValueError("layout object override must define a value")
        return self


class LayoutSpec(ManifestModel):
    objects: dict[str, ObjectLayoutOverride] = Field(default_factory=dict)

    @field_validator("objects")
    @classmethod
    def validate_object_ids(
        cls,
        value: dict[str, ObjectLayoutOverride],
    ) -> dict[str, ObjectLayoutOverride]:
        if any(not key.strip() for key in value):
            raise ValueError("layout object ids must not be empty")
        return value


class OutputSpec(ManifestModel):
    directory: ProjectRelativePath = Field(
        default_factory=lambda: ProjectRelativePath("build"),
    )
    docx: ProjectRelativePath = Field(
        default_factory=lambda: ProjectRelativePath("thesis.docx"),
    )
    retain_last_successful_preview: bool = True


class ReviewSpec(ManifestModel):
    directory: ProjectRelativePath = Field(
        default_factory=lambda: ProjectRelativePath("review"),
    )
    markdown: ProjectRelativePath = Field(
        default_factory=lambda: ProjectRelativePath("thesis.review.md"),
    )
    source_map: ProjectRelativePath = Field(
        default_factory=lambda: ProjectRelativePath("thesis.review-map.json"),
    )


class ProjectManifestV2(ManifestModel):
    """The complete strict ``thesisforge.yaml`` v2 contract."""

    schema_version: Literal[PROJECT_SCHEMA] = Field(
        alias="schema",
        serialization_alias="schema",
    )
    project: ProjectSpec
    document: DocumentSpec
    metadata: MetadataSpec = Field(default_factory=MetadataSpec)
    resources: ResourcesSpec = Field(default_factory=ResourcesSpec)
    render: RenderSpec
    layout: LayoutSpec = Field(default_factory=LayoutSpec)
    output: OutputSpec = Field(default_factory=OutputSpec)
    review: ReviewSpec = Field(default_factory=ReviewSpec)

    @property
    def schema(self) -> str:
        return self.schema_version


__all__ = [
    "PROJECT_SCHEMA",
    "AdvisorSpec",
    "AuthorSpec",
    "DatesSpec",
    "DegreeSpec",
    "DocumentSpec",
    "InstitutionSpec",
    "LayoutSpec",
    "LocalizedText",
    "MetadataSpec",
    "ObjectLayoutOverride",
    "OutputSpec",
    "ProjectManifestV2",
    "ProjectRelativePath",
    "ProjectSpec",
    "RenderSpec",
    "ResourcesSpec",
    "ReviewSpec",
]
