from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from pydantic_core import PydanticCustomError

SUPPORTED_LENGTH_UNITS = ("mm", "cm", "pt", "em")
LENGTH_RE = re.compile(r"^(?P<value>\d+(?:\.\d+)?)(?P<unit>mm|cm|pt|em)$")


class TemplateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LengthSpec(TemplateModel):
    value: Decimal
    unit: Literal["mm", "cm", "pt", "em"]

    @model_validator(mode="before")
    @classmethod
    def parse_explicit_length(cls, value: Any) -> Any:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise PydanticCustomError(
                "explicit_length_type",
                "长度必须是带单位的字符串，支持 mm / cm / pt / em",
            )
        match = LENGTH_RE.fullmatch(value.strip())
        if match is None:
            raise ValueError("长度必须显式带单位，支持 mm / cm / pt / em")
        return {
            "value": Decimal(match.group("value")),
            "unit": match.group("unit"),
        }

    def __str__(self) -> str:
        number = format(self.value, "f").rstrip("0").rstrip(".")
        return f"{number or '0'}{self.unit}"


class FontSpec(TemplateModel):
    east_asia: str = "宋体"
    latin: str = "Times New Roman"


class MarginSpec(TemplateModel):
    top: LengthSpec
    bottom: LengthSpec
    left: LengthSpec
    right: LengthSpec


class PageSpec(TemplateModel):
    size: Literal["A3", "A4", "A5", "Letter", "Legal"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margin: MarginSpec


class LineSpacingSpec(TemplateModel):
    type: Literal["single", "multiple", "fixed"] = "fixed"
    value: LengthSpec | float | None = None

    @model_validator(mode="after")
    def validate_spacing_value(self) -> LineSpacingSpec:
        if self.type == "fixed" and not isinstance(self.value, LengthSpec):
            raise ValueError("fixed 行距必须提供带单位的 value")
        if self.type == "multiple" and (
            not isinstance(self.value, float) or self.value <= 0
        ):
            raise ValueError("multiple 行距必须提供正数 value")
        return self


class BodySpec(TemplateModel):
    font: FontSpec = Field(default_factory=FontSpec)
    size: LengthSpec
    alignment: Literal["left", "center", "right", "justify"] = "justify"
    first_line_indent: LengthSpec
    line_spacing: LineSpacingSpec


class HeadingLevelSpec(TemplateModel):
    font: FontSpec | None = None
    size: LengthSpec
    bold: bool = False
    italic: bool = False
    alignment: Literal["left", "center", "right", "justify"] = "left"
    space_before: LengthSpec | None = None
    space_after: LengthSpec | None = None
    page_break_before: bool = False


class HeadingSpec(TemplateModel):
    level1: HeadingLevelSpec
    level2: HeadingLevelSpec | None = None
    level3: HeadingLevelSpec | None = None

    def for_level(self, level: int) -> HeadingLevelSpec | None:
        return getattr(self, f"level{level}", None)


class NumberingSpec(TemplateModel):
    mode: Literal["chapter", "continuous", "none"] = "chapter"
    separator: str = "-"

    @model_validator(mode="before")
    @classmethod
    def parse_short_form(cls, value: Any) -> Any:
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return {"mode": value}
        return value


class CaptionSpec(TemplateModel):
    position: Literal["top", "bottom"]
    prefix: str
    font: FontSpec | None = None
    size: LengthSpec | None = None
    alignment: Literal["left", "center", "right", "justify"] = "center"


class FigureSpec(TemplateModel):
    numbering: NumberingSpec = Field(default_factory=NumberingSpec)
    caption: CaptionSpec
    default_width: LengthSpec | None = None


class TableSpec(TemplateModel):
    style: Literal["three_line", "grid", "plain"] = "three_line"
    numbering: NumberingSpec = Field(default_factory=NumberingSpec)
    caption: CaptionSpec


class EquationSpec(TemplateModel):
    numbering: NumberingSpec = Field(default_factory=NumberingSpec)
    alignment: Literal["left", "center", "right"] = "center"


class HeaderFooterSpec(TemplateModel):
    enabled: bool = False
    text: str | None = None
    different_first_page: bool = False


class PageNumberSpec(TemplateModel):
    format: Literal["none", "decimal", "roman-lower", "roman-upper"] = "decimal"
    restart: int | None = Field(default=None, ge=1)


class SectionSpec(TemplateModel):
    start: Literal["continuous", "new_page", "odd_page", "even_page"] = "new_page"
    header: HeaderFooterSpec = Field(default_factory=HeaderFooterSpec)
    footer: HeaderFooterSpec = Field(default_factory=HeaderFooterSpec)
    page_number: PageNumberSpec = Field(default_factory=PageNumberSpec)


class SectionsSpec(TemplateModel):
    cover: SectionSpec | None = None
    front_matter: SectionSpec | None = None
    main: SectionSpec | None = None


class CitationSpec(TemplateModel):
    style: str = Field(min_length=1)


class ThesisTemplate(TemplateModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    year: int | str
    page: PageSpec
    body: BodySpec
    heading: HeadingSpec
    figure: FigureSpec | None = None
    table: TableSpec | None = None
    equation: EquationSpec | None = None
    sections: SectionsSpec = Field(default_factory=SectionsSpec)
    citation: CitationSpec | None = None


class TemplateLoadError(ValueError):
    def __init__(self, path: Path, field_errors: tuple[tuple[str, str], ...]):
        self.path = path
        self.field_errors = field_errors
        detail = "; ".join(f"{field}: {message}" for field, message in field_errors)
        super().__init__(f"模板无效: {path}: {detail}")


def load_template(path: str | Path) -> ThesisTemplate:
    template_path = Path(path)
    try:
        data = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    except OSError as error:
        detail = error.strerror or str(error)
        raise TemplateLoadError(template_path, (("$file", detail),)) from error
    except yaml.YAMLError as error:
        raise TemplateLoadError(template_path, (("$yaml", str(error)),)) from error

    try:
        return ThesisTemplate.model_validate(data)
    except ValidationError as error:
        field_errors = tuple(
            (
                ".".join(str(part) for part in item["loc"]) or "$root",
                item["msg"],
            )
            for item in error.errors()
        )
        raise TemplateLoadError(template_path, field_errors) from error
