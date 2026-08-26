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


def _require_absolute_length(
    value: LengthSpec | None,
    *,
    positive: bool = False,
) -> LengthSpec | None:
    if value is None:
        return None
    if value.unit == "em":
        raise ValueError("物理尺寸必须使用绝对单位 mm / cm / pt")
    if positive and value.value <= 0:
        raise ValueError("物理尺寸必须大于 0")
    return value


class FontSpec(TemplateModel):
    east_asia: str = "宋体"
    latin: str = "Times New Roman"


class DocumentGridSpec(TemplateModel):
    type: Literal["default", "lines", "lines_and_chars", "snap_to_chars"] = "lines"
    line_pitch: LengthSpec | None = None
    char_space: int | None = None

    @field_validator("line_pitch")
    @classmethod
    def validate_line_pitch(
        cls,
        value: LengthSpec | None,
    ) -> LengthSpec | None:
        return _require_absolute_length(value, positive=True)

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

    @field_validator("top", "bottom", "left", "right")
    @classmethod
    def validate_physical_length(cls, value: LengthSpec) -> LengthSpec:
        validated = _require_absolute_length(value)
        assert validated is not None
        return validated


class PageSpec(TemplateModel):
    size: Literal["A3", "A4", "A5", "Letter", "Legal"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margin: MarginSpec
    header_distance: LengthSpec | None = None
    footer_distance: LengthSpec | None = None
    document_grid: DocumentGridSpec | None = None

    @field_validator("header_distance", "footer_distance")
    @classmethod
    def validate_header_footer_distance(
        cls,
        value: LengthSpec | None,
    ) -> LengthSpec | None:
        return _require_absolute_length(value)


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
    color: str | None = Field(
        default=None,
        pattern=r"^(?:auto|[0-9A-Fa-f]{6})$",
    )
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


CoverField = Literal[
    "university.name",
    "university.college",
    "thesis.title",
    "thesis.title_en",
    "thesis.major",
    "thesis.degree",
    "author.name",
    "author.student_id",
    "advisor.name",
    "advisor.title",
    "dates.completed",
]


OrderedListFormat = Literal[
    "decimal",
    "lower_letter",
    "upper_letter",
    "lower_roman",
    "upper_roman",
]
ListMarkerAlignment = Literal["left", "center", "right"]


def _absolute_length_points(value: LengthSpec) -> Decimal:
    if value.unit == "pt":
        return value.value
    if value.unit == "mm":
        return value.value * Decimal(72) / Decimal("25.4")
    if value.unit == "cm":
        return value.value * Decimal(72) / Decimal("2.54")
    raise ValueError("列表缩进必须使用绝对单位 mm / cm / pt")


class ListLevelGeometrySpec(TemplateModel):
    alignment: ListMarkerAlignment = "left"
    left_indent: LengthSpec = Field(
        default_factory=lambda: LengthSpec.model_validate("36pt")
    )
    hanging_indent: LengthSpec = Field(
        default_factory=lambda: LengthSpec.model_validate("18pt")
    )
    style: ParagraphStyleSpec = Field(default_factory=ParagraphStyleSpec)

    @field_validator("left_indent", "hanging_indent")
    @classmethod
    def validate_absolute_indent(cls, value: LengthSpec) -> LengthSpec:
        validated = _require_absolute_length(value)
        assert validated is not None
        return validated

    @model_validator(mode="after")
    def validate_indent_geometry(self) -> ListLevelGeometrySpec:
        if _absolute_length_points(self.hanging_indent) > _absolute_length_points(
            self.left_indent
        ):
            raise ValueError("hanging_indent 不能大于 left_indent")
        return self


class OrderedListLevelSpec(ListLevelGeometrySpec):
    format: OrderedListFormat = "decimal"
    prefix: str = ""
    suffix: str = "."


class UnorderedListLevelSpec(ListLevelGeometrySpec):
    marker: str = "•"

    @field_validator("marker")
    @classmethod
    def validate_marker(cls, value: str) -> str:
        marker = value.strip()
        if not marker:
            raise ValueError("unordered list marker 不能为空")
        return marker


def _default_ordered_list_levels() -> tuple[OrderedListLevelSpec, ...]:
    return tuple(
        OrderedListLevelSpec(left_indent=LengthSpec.model_validate(f"{36 * level}pt"))
        for level in range(1, 10)
    )


def _default_unordered_list_levels() -> tuple[UnorderedListLevelSpec, ...]:
    markers = ("•", "◦", "▪")
    return tuple(
        UnorderedListLevelSpec(
            marker=markers[(level - 1) % len(markers)],
            left_indent=LengthSpec.model_validate(f"{36 * level}pt"),
        )
        for level in range(1, 10)
    )


class OrderedListSpec(TemplateModel):
    levels: tuple[OrderedListLevelSpec, ...] = Field(
        default_factory=_default_ordered_list_levels,
        min_length=1,
        max_length=9,
    )

    def for_level(self, level: int) -> OrderedListLevelSpec:
        return self.levels[max(0, min(level, len(self.levels) - 1))]


class UnorderedListSpec(TemplateModel):
    levels: tuple[UnorderedListLevelSpec, ...] = Field(
        default_factory=_default_unordered_list_levels,
        min_length=1,
        max_length=9,
    )

    def for_level(self, level: int) -> UnorderedListLevelSpec:
        return self.levels[max(0, min(level, len(self.levels) - 1))]


class ListSpec(TemplateModel):
    ordered: OrderedListSpec = Field(default_factory=OrderedListSpec)
    unordered: UnorderedListSpec = Field(default_factory=UnorderedListSpec)


class CoverItemSpec(TemplateModel):
    field: CoverField | None = None
    text: str | None = None
    prefix: str = ""
    suffix: str = ""
    skip_if_empty: bool = True
    style: ParagraphStyleSpec = Field(
        default_factory=lambda: ParagraphStyleSpec(alignment="center")
    )

    @model_validator(mode="after")
    def validate_content_source(self) -> CoverItemSpec:
        if (self.field is None) == (self.text is None):
            raise ValueError("cover item 必须且只能配置 field 或 text")
        if self.text is not None:
            self.text = self.text.strip()
            if not self.text:
                raise ValueError("cover item text 不能为空")
        return self


def _default_cover_items() -> tuple[CoverItemSpec, ...]:
    fields: tuple[CoverField, ...] = (
        "university.name",
        "university.college",
        "thesis.title",
        "thesis.title_en",
        "thesis.major",
        "thesis.degree",
        "author.name",
        "author.student_id",
        "advisor.name",
        "advisor.title",
        "dates.completed",
    )
    return tuple(CoverItemSpec(field=field) for field in fields)


class CoverSpec(TemplateModel):
    items: tuple[CoverItemSpec, ...] = Field(
        default_factory=_default_cover_items,
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_unique_fields(self) -> CoverSpec:
        fields = [item.field for item in self.items if item.field is not None]
        duplicates = sorted({field for field in fields if fields.count(field) > 1})
        if duplicates:
            raise ValueError(
                f"cover.items 包含重复 field: {', '.join(duplicates)}"
            )
        return self


class BodySpec(ParagraphStyleSpec):
    font: FontSpec = Field(default_factory=FontSpec)
    size: LengthSpec
    alignment: Literal["left", "center", "right", "justify"] = "justify"
    first_line_indent: LengthSpec
    line_spacing: LineSpacingSpec

    @field_validator("size")
    @classmethod
    def validate_absolute_body_size(cls, value: LengthSpec) -> LengthSpec:
        if value.unit == "em":
            raise ValueError("body.size 必须使用绝对单位，不能使用 em")
        return value


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
    first_line_indent: LengthSpec | None = Field(
        default_factory=lambda: LengthSpec.model_validate("0pt")
    )
    page_number_tab: LengthSpec | None = None
    leader: Literal["none", "dots", "dashes", "line", "heavy", "middle_dot"] = (
        "dots"
    )

    @field_validator("page_number_tab")
    @classmethod
    def validate_page_number_tab(
        cls,
        value: LengthSpec | None,
    ) -> LengthSpec | None:
        if value is not None and value.value <= 0:
            raise ValueError("page_number_tab 必须大于 0")
        return value


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


class ThreeLineTableSpec(TemplateModel):
    top_width: LengthSpec = Field(
        default_factory=lambda: LengthSpec.model_validate("1.5pt")
    )
    header_width: LengthSpec = Field(
        default_factory=lambda: LengthSpec.model_validate("0.75pt")
    )
    bottom_width: LengthSpec = Field(
        default_factory=lambda: LengthSpec.model_validate("1.5pt")
    )

    @field_validator("top_width", "header_width", "bottom_width")
    @classmethod
    def validate_border_width(cls, value: LengthSpec) -> LengthSpec:
        validated = _require_absolute_length(value, positive=True)
        assert validated is not None
        points = _absolute_length_points(validated)
        if not Decimal("0.25") <= points <= Decimal(12):
            raise ValueError("Word 表格线宽必须在 0.25pt 到 12pt 之间")
        return validated


class TableSpec(TemplateModel):
    style: Literal["three_line", "grid", "plain"] = "three_line"
    three_line: ThreeLineTableSpec = Field(default_factory=ThreeLineTableSpec)
    numbering: NumberingSpec = Field(default_factory=NumberingSpec)
    caption: CaptionSpec


class EquationSpec(TemplateModel):
    numbering: NumberingSpec = Field(default_factory=NumberingSpec)
    alignment: Literal["left", "center", "right"] = "center"


class ListingSpec(TemplateModel):
    numbering: NumberingSpec = Field(default_factory=NumberingSpec)
    caption: CaptionSpec


class AlgorithmSpec(TemplateModel):
    numbering: NumberingSpec = Field(default_factory=NumberingSpec)
    caption: CaptionSpec


class ParagraphBorderSpec(TemplateModel):
    style: Literal["none", "single", "double", "dotted", "dashed"] = "single"
    width: LengthSpec | None = None
    color: str = Field(default="auto", pattern=r"^(?:auto|[0-9A-Fa-f]{6})$")
    space: LengthSpec | None = None

    @field_validator("width")
    @classmethod
    def validate_width(
        cls,
        value: LengthSpec | None,
    ) -> LengthSpec | None:
        return _require_absolute_length(value, positive=True)

    @field_validator("space")
    @classmethod
    def validate_space(
        cls,
        value: LengthSpec | None,
    ) -> LengthSpec | None:
        return _require_absolute_length(value)


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

    @model_validator(mode="after")
    def validate_restart(self) -> PageNumberSpec:
        if self.format == "none" and self.restart is not None:
            raise ValueError("page_number.format 为 none 时不能配置 restart")
        return self


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
    cover: CoverSpec = Field(default_factory=CoverSpec)
    list: ListSpec = Field(default_factory=ListSpec)
    body: BodySpec
    heading: HeadingSpec
    semantic_styles: SemanticStylesSpec = Field(default_factory=SemanticStylesSpec)
    toc: TocSpec | None = None
    bibliography: BibliographySpec | None = None
    figure: FigureSpec | None = None
    table: TableSpec | None = None
    equation: EquationSpec | None = None
    listing: ListingSpec | None = None
    algorithm: AlgorithmSpec | None = None
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
