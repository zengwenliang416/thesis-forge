from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
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
        number = format(self.value, "f")
        if "." in number:
            number = number.rstrip("0").rstrip(".")
        return f"{number or '0'}{self.unit}"


class FontSpec(TemplateModel):
    east_asia: str = "宋体"
    latin: str = "Times New Roman"


class DocumentGridSpec(TemplateModel):
    type: Literal["default", "lines", "lines_and_chars", "snap_to_chars"] = "lines"
    line_pitch: LengthSpec | None = None
    char_space: int | None = None

    @model_validator(mode="after")
    def validate_grid(self) -> DocumentGridSpec:
        if self.type != "default" and self.line_pitch is None:
            raise ValueError("非 default 文档网格必须提供 line_pitch")
        return self


class MarginSpec(TemplateModel):
    top: LengthSpec
    bottom: LengthSpec
    left: LengthSpec
    right: LengthSpec


class PageSpec(TemplateModel):
    size: Literal["A3", "A4", "A5", "Letter", "Legal"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margin: MarginSpec
    header_distance: LengthSpec | None = None
    footer_distance: LengthSpec | None = None
    document_grid: DocumentGridSpec | None = None


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
        if self.type == "single" and self.value is not None:
            raise ValueError("single 行距不能提供 value")
        return self


class ParagraphStyleSpec(TemplateModel):
    font: FontSpec | None = None
    size: LengthSpec | None = None
    bold: bool | None = None
    italic: bool | None = None
    alignment: Literal["left", "center", "right", "justify"] | None = None
    left_indent: LengthSpec | None = None
    right_indent: LengthSpec | None = None
    first_line_indent: LengthSpec | None = None
    hanging_indent: LengthSpec | None = None
    space_before: LengthSpec | None = None
    space_after: LengthSpec | None = None
    line_spacing: LineSpacingSpec | None = None
    widow_control: bool | None = None
    keep_together: bool | None = None
    keep_with_next: bool | None = None
    page_break_before: bool | None = None
    outline_level: int | None = Field(default=None, ge=0, le=9)
    snap_to_grid: bool | None = None

    @field_validator("hanging_indent")
    @classmethod
    def validate_indentation(
        cls,
        value: LengthSpec | None,
        info: ValidationInfo,
    ) -> LengthSpec | None:
        first_line_indent = info.data.get("first_line_indent")
        if (
            isinstance(first_line_indent, LengthSpec)
            and first_line_indent.value > 0
            and value is not None
            and value.value > 0
        ):
            raise ValueError(
                "first_line_indent 与 hanging_indent 不能同时为正值"
            )
        return value


class BodySpec(ParagraphStyleSpec):
    font: FontSpec = Field(default_factory=FontSpec)
    size: LengthSpec
    alignment: Literal["left", "center", "right", "justify"] = "justify"
    first_line_indent: LengthSpec
    line_spacing: LineSpacingSpec


class HeadingLevelSpec(ParagraphStyleSpec):
    size: LengthSpec
    bold: bool = False
    italic: bool = False
    alignment: Literal["left", "center", "right", "justify"] = "left"
    page_break_before: bool = False


class HeadingSpec(TemplateModel):
    level1: HeadingLevelSpec
    level2: HeadingLevelSpec | None = None
    level3: HeadingLevelSpec | None = None

    def for_level(self, level: int) -> HeadingLevelSpec | None:
        return getattr(self, f"level{level}", None)


class AbstractStyleSpec(TemplateModel):
    title: ParagraphStyleSpec | None = None
    body: ParagraphStyleSpec | None = None
    keywords: ParagraphStyleSpec | None = None


class SemanticStylesSpec(TemplateModel):
    abstract_zh: AbstractStyleSpec | None = None
    abstract_en: AbstractStyleSpec | None = None
    acknowledgements: ParagraphStyleSpec | None = None
    achievements: ParagraphStyleSpec | None = None


class TocLevelSpec(ParagraphStyleSpec):
    page_number_tab: LengthSpec | None = None
    leader: Literal["none", "dots", "dashes", "line", "heavy", "middle_dot"] = (
        "dots"
    )


class TocSpec(TemplateModel):
    title: ParagraphStyleSpec | None = None
    level1: TocLevelSpec | None = None
    level2: TocLevelSpec | None = None
    level3: TocLevelSpec | None = None

    def for_level(self, level: int) -> TocLevelSpec | None:
        return getattr(self, f"level{level}", None)


class BibliographySpec(TemplateModel):
    title: ParagraphStyleSpec | None = None
    entry: ParagraphStyleSpec | None = None


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


class ParagraphBorderSpec(TemplateModel):
    style: Literal["none", "single", "double", "dotted", "dashed"] = "single"
    width: LengthSpec | None = None
    color: str = Field(default="auto", pattern=r"^(?:auto|[0-9A-Fa-f]{6})$")
    space: LengthSpec | None = None


class PageNumberDisplaySpec(TemplateModel):
    alignment: Literal["left", "center", "right"] = "center"
    page_prefix: str = "第 "
    page_suffix: str = " 页"
    include_total: bool = True
    separator: str = " / "
    total_prefix: str = "共 "
    total_suffix: str = " 页"


class HeaderFooterVariantSpec(TemplateModel):
    enabled: bool = True
    text: str | None = None
    style: ParagraphStyleSpec | None = None
    bottom_border: ParagraphBorderSpec | None = None
    page_number: PageNumberDisplaySpec | None = None


class HeaderFooterSpec(TemplateModel):
    enabled: bool = False
    text: str | None = None
    different_first_page: bool = False
    default: HeaderFooterVariantSpec | None = None
    first: HeaderFooterVariantSpec | None = None
    even: HeaderFooterVariantSpec | None = None

    @model_validator(mode="after")
    def normalize_legacy_fields(self) -> HeaderFooterSpec:
        fields_set = self.model_fields_set
        if "default" in fields_set and ({"enabled", "text"} & fields_set):
            raise ValueError(
                "default 变体不能与 legacy enabled/text 同时配置"
            )
        if "first" in fields_set and "different_first_page" in fields_set:
            raise ValueError(
                "first 变体不能与 legacy different_first_page 同时配置"
            )
        if self.default is None:
            self.default = HeaderFooterVariantSpec(
                enabled=self.enabled,
                text=self.text,
            )
        if self.first is None and self.different_first_page:
            self.first = HeaderFooterVariantSpec(enabled=False)
        return self


class PageNumberSpec(TemplateModel):
    format: Literal["none", "decimal", "roman-lower", "roman-upper"] = "decimal"
    restart: int | None = Field(default=None, ge=1)
    display: PageNumberDisplaySpec = Field(default_factory=PageNumberDisplaySpec)


class SectionSpec(TemplateModel):
    start: Literal["continuous", "new_page", "odd_page", "even_page"] = "new_page"
    header: HeaderFooterSpec = Field(default_factory=HeaderFooterSpec)
    footer: HeaderFooterSpec = Field(default_factory=HeaderFooterSpec)
    page_number: PageNumberSpec = Field(default_factory=PageNumberSpec)

    @model_validator(mode="after")
    def validate_page_number_variants(self) -> SectionSpec:
        if self.page_number.format != "none":
            return self

        errors = []
        for part_name, part in (("header", self.header), ("footer", self.footer)):
            for variant_name in ("default", "first", "even"):
                variant = getattr(part, variant_name)
                if (
                    variant is not None
                    and variant.enabled
                    and variant.page_number is not None
                ):
                    errors.append(
                        {
                            "type": "value_error",
                            "loc": (part_name, variant_name, "page_number"),
                            "input": variant.page_number,
                            "ctx": {
                                "error": ValueError(
                                    "page_number.format 为 none 时不能输出 PAGE/NUMPAGES"
                                )
                            },
                        }
                    )
        if errors:
            raise ValidationError.from_exception_data(type(self).__name__, errors)
        return self


class SectionsSpec(TemplateModel):
    cover: SectionSpec | None = None
    front_matter: SectionSpec | None = None
    main: SectionSpec | None = None


class CitationSpec(TemplateModel):
    style: str = Field(min_length=1)
    presentation: Literal["inline", "superscript"] = "inline"


class ThesisTemplate(TemplateModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    year: int | str
    page: PageSpec
    body: BodySpec
    heading: HeadingSpec
    semantic_styles: SemanticStylesSpec = Field(default_factory=SemanticStylesSpec)
    toc: TocSpec | None = None
    bibliography: BibliographySpec | None = None
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
