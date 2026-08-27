"""Template Package v2 `template.yaml` / `provenance.yaml` 的 pydantic 模型（SCHEMA §3）。

全部模型 `extra=forbid`（§2.1）：未知字段由 pydantic 拒绝，lint 层映射为
`invalid-template`（error）并保留完整字段路径。长度字段经 `units.parse_length`
按 §2.3 上下文矩阵校验。本节只做单包 schema 表达；extends 合并（§4.3 D-2）
在 `package.py` 完成后再对本模型校验。
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .units import (
    CTX_BORDER_WIDTH,
    CTX_COLUMN_SPACING,
    CTX_FIXED_LINE_SPACING,
    CTX_IMAGE_HEIGHT,
    CTX_INDENT,
    CTX_OVERFLOW_THRESHOLD,
    CTX_PAGE_GEOMETRY,
    CTX_PARENT_WIDTH,
    Length,
    LengthContext,
    LengthParseError,
    parse_length,
)

SCHEMA_VERSION = 2

TEMPLATE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")
BCP47_RE = re.compile(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
SHA256_REF_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ANCHOR_NAME_RE = re.compile(r"^tf_[a-z0-9_]+$")
SEQUENCE_NAME_RE = re.compile(r"^TF_[A-Z][A-Z0-9_]*$")
PLACEHOLDER_RE = re.compile(r"\{([a-z_]+)\}")

REGION_IDS = (
    "cover",
    "originality_statement",
    "authorization_statement",
    "abstract_zh",
    "abstract_en",
    "toc",
    "main",
    "bibliography",
    "acknowledgements",
    "appendices",
    "achievements",
)
SECTION_KEYS = ("cover", "front_matter", "main", "back_matter")
DEFAULT_REGION_SECTION = {
    "cover": "cover",
    "originality_statement": "front_matter",
    "authorization_statement": "front_matter",
    "abstract_zh": "front_matter",
    "abstract_en": "front_matter",
    "toc": "front_matter",
    "main": "main",
    "bibliography": "back_matter",
    "acknowledgements": "back_matter",
    "appendices": "back_matter",
    "achievements": "back_matter",
}
PARAGRAPH_TOKENS = (
    "body",
    "body_first",
    "abstract",
    "bibliography",
    "caption_figure",
    "caption_table",
    "equation",
    "listing",
    "footnote",
)
CHARACTER_TOKENS = ("emphasis", "strong", "code", "hyperlink", "equation_inline")
KNOWN_FONT_ROLES = ("body", "code", "heading", "caption")
HEADING_PLACEHOLDERS = frozenset({"chapter", "chapter_zh", "section", "subsection"})
CAPTION_PLACEHOLDERS = frozenset({"prefix", "number", "caption"})

RegionId = Literal[
    "cover",
    "originality_statement",
    "authorization_statement",
    "abstract_zh",
    "abstract_en",
    "toc",
    "main",
    "bibliography",
    "acknowledgements",
    "appendices",
    "achievements",
]
SectionKey = Literal["cover", "front_matter", "main", "back_matter"]


class TemplateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _length_type(ctx: LengthContext) -> Any:
    def _parse(value: Any, info: Any = None) -> Length | None:
        if value is None:
            return None  # 字段类型为 Length | None；validate_default 下默认值 None 必须放行
        field_path = ""
        if info is not None and getattr(info, "field_name", None):
            field_path = str(info.field_name)
        try:
            return parse_length(value, ctx, field_path=field_path)
        except LengthParseError as error:
            raise ValueError(str(error)) from None

    return Annotated[Length | None, BeforeValidator(_parse)]


PageLength = _length_type(CTX_PAGE_GEOMETRY)
BorderLength = _length_type(CTX_BORDER_WIDTH)
IndentLength = _length_type(CTX_INDENT)
FixedSpacingLength = _length_type(CTX_FIXED_LINE_SPACING)
ParentWidthLength = _length_type(CTX_PARENT_WIDTH)
OverflowThresholdLength = _length_type(CTX_OVERFLOW_THRESHOLD)
ImageHeightLength = _length_type(CTX_IMAGE_HEIGHT)
ColumnSpacingLength = _length_type(CTX_COLUMN_SPACING)


# ---------------------------------------------------------------------------
# §2.4 Semver / SemverRange
# ---------------------------------------------------------------------------

_RANGE_CLAUSE_RE = re.compile(
    r"^(>=|<=|>|<|==|!=|\^)\s*(\d+)\.(\d+)(?:\.(\d+))?(?:-([0-9A-Za-z.-]+))?$"
)


def parse_semver(raw: str) -> tuple[int, int, int]:
    """解析 Semver（允许省略 patch）；非字符串抛 TypeError，格式无效抛 ValueError。"""
    if not isinstance(raw, str):
        raise TypeError(f"版本号必须是字符串：{raw!r}")
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?(?:-[0-9A-Za-z.-]+)?", raw.strip())
    if match is None:
        raise ValueError(f"版本号格式无效：{raw!r}")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3) or 0))


def _parse_range(range_str: str) -> list[tuple[str, tuple[int, int, int]]]:
    if not isinstance(range_str, str) or not range_str.strip():
        raise ValueError(f"SemverRange 不能为空：{range_str!r}")
    clauses: list[tuple[str, tuple[int, int, int]]] = []
    for part in range_str.split(","):
        match = _RANGE_CLAUSE_RE.fullmatch(part.strip())
        if match is None:
            raise ValueError(f"SemverRange 子句无效：{part!r}（语法见 SCHEMA §2.4）")
        op, major, minor, patch, _prerelease = match.groups()
        clauses.append((op, (int(major), int(minor), int(patch or 0))))
    return clauses


def validate_semver_range(raw: str) -> str:
    """校验 SemverRange 语法（§2.4）；失败抛 ValueError，成功返回原串。"""
    _parse_range(raw)
    return raw


def version_satisfies(range_str: str, version: str) -> bool:
    """判断 version（Semver）是否满足 range（SemverRange）。"""
    target = parse_semver(version)
    for op, clause_version in _parse_range(range_str):
        if op == ">=" and not target >= clause_version:
            return False
        if op == ">" and not target > clause_version:
            return False
        if op == "<=" and not target <= clause_version:
            return False
        if op == "<" and not target < clause_version:
            return False
        if op == "==" and target != clause_version:
            return False
        if op == "!=" and target == clause_version:
            return False
        if op == "^":
            upper = (clause_version[0] + 1, 0, 0)
            if not (target >= clause_version and target < upper):
                return False
    return True


def _check_placeholders(pattern: str, allowed: frozenset[str], field: str) -> None:
    for name in PLACEHOLDER_RE.findall(pattern):
        if name not in allowed:
            raise ValueError(
                f"{field} 含未知占位符 {{{name}}}（允许：{', '.join(sorted(allowed))}）"
            )


def _optional_pattern(value: str | None, allowed: frozenset[str], field: str) -> str | None:
    if value is not None:
        _check_placeholders(value, allowed, field)
    return value


# ---------------------------------------------------------------------------
# §3.1 header / §3.2 compatibility / §3.3 extends
# ---------------------------------------------------------------------------


class CompatibilitySpec(TemplateModel):
    docforge: str
    document_types: list[
        Literal[
            "bachelor_thesis",
            "master_thesis",
            "phd_thesis",
            "course_paper",
            "report",
        ]
    ] = Field(min_length=1)
    target_apps: dict[
        Literal["word", "wps", "libreoffice"],
        Literal["primary", "compatible", "preview", "unsupported"],
    ] = Field(default_factory=lambda: {"word": "primary"})

    @field_validator("docforge")
    @classmethod
    def validate_range(cls, value: str) -> str:
        try:
            return validate_semver_range(value)
        except ValueError as error:
            raise ValueError(str(error)) from None

    @model_validator(mode="after")
    def validate_single_primary(self) -> CompatibilitySpec:
        primaries = [app for app, level in self.target_apps.items() if level == "primary"]
        if len(primaries) > 1:
            raise ValueError(f"target_apps 只允许一个 primary：{', '.join(primaries)}")
        return self


class ExtendsSpec(TemplateModel):
    id: str = Field(min_length=1)
    version: str
    sha256: str | None = None

    @field_validator("version")
    @classmethod
    def validate_range(cls, value: str) -> str:
        try:
            return validate_semver_range(value)
        except ValueError as error:
            raise ValueError(str(error)) from None

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str | None) -> str | None:
        if value is not None and SHA256_REF_RE.fullmatch(value) is None:
            raise ValueError("sha256 必须是 sha256: + 64 位小写十六进制")
        return value


# ---------------------------------------------------------------------------
# §3.4 word / §3.5 page
# ---------------------------------------------------------------------------


class WordSpec(TemplateModel):
    reference_docx: str = "reference.docx"
    shell_docx: str | None = None
    macro_policy: Literal["forbid"] = "forbid"
    external_relationships: Literal["forbid", "allowlist"] = "forbid"
    external_relationship_allowlist: list[str] = Field(default_factory=list)
    anchors: dict[Literal["body", "toc", "bibliography"], str] = Field(
        default_factory=lambda: {
            "body": "tf_body",
            "toc": "tf_toc",
            "bibliography": "tf_bibliography",
        }
    )

    @model_validator(mode="after")
    def validate_word(self) -> WordSpec:
        if (
            self.external_relationships == "allowlist"
            and not self.external_relationship_allowlist
        ):
            raise ValueError(
                "external_relationships 为 allowlist 时必须给出 "
                "external_relationship_allowlist"
            )
        defaults = {"body": "tf_body", "toc": "tf_toc", "bibliography": "tf_bibliography"}
        resolved = {**defaults, **self.anchors}
        for key, anchor in resolved.items():
            if ANCHOR_NAME_RE.fullmatch(anchor) is None:
                raise ValueError(
                    f"anchors.{key} 必须匹配 ^tf_[a-z0-9_]+$：{anchor!r}"
                )
        values = list(resolved.values())
        if len(set(values)) != len(values):
            raise ValueError("anchors 三键值必须互不相同")
        return self


class DocumentGridSpec(TemplateModel):
    type: Literal["default", "lines", "lines_and_chars", "snap_to_chars"] = "lines"
    line_pitch: PageLength = None
    char_space: int | None = None

    @model_validator(mode="after")
    def validate_grid(self) -> DocumentGridSpec:
        if self.type != "default" and self.line_pitch is None:
            raise ValueError("非 default 文档网格必须提供 line_pitch")
        if self.line_pitch is not None and self.line_pitch.value <= 0:
            raise ValueError("document_grid.line_pitch 必须大于 0")
        return self


class MarginSpec(TemplateModel):
    top: PageLength
    bottom: PageLength
    inner: PageLength
    outer: PageLength

    @model_validator(mode="after")
    def validate_required(self) -> MarginSpec:
        for name in ("top", "bottom", "inner", "outer"):
            if getattr(self, name) is None:
                raise ValueError(f"page.margin.{name} 为必需字段")
        return self


class PageSpec(TemplateModel):
    size: Literal["A3", "A4", "A5", "Letter", "Legal"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margin: MarginSpec
    gutter: PageLength = None
    mirror_margins: bool = False
    header_distance: PageLength = None
    footer_distance: PageLength = None
    document_grid: DocumentGridSpec | None = None


# ---------------------------------------------------------------------------
# §3.6 fonts / font_policy；§3.7 styles
# ---------------------------------------------------------------------------


class FontRoleSpec(TemplateModel):
    east_asia: str = Field(min_length=1)
    latin: str = Field(min_length=1)
    high_ansi: str | None = None
    complex_script: str | None = None
    fallback: dict[
        Literal["east_asia", "latin", "high_ansi", "complex_script"], list[str]
    ] = Field(default_factory=dict)

    @model_validator(mode="after")
    def fill_slot_defaults(self) -> FontRoleSpec:
        if self.high_ansi is None:
            self.high_ansi = self.latin
        if self.complex_script is None:
            self.complex_script = self.latin
        return self


class FontPolicySpec(TemplateModel):
    missing_primary: Literal["error", "warning"] = "error"
    missing_fallback: Literal["error", "warning"] = "warning"
    embed_fonts: bool = False


class ParagraphTokenMap(TemplateModel):
    body: str = Field(min_length=1)
    body_first: str | None = Field(default=None, min_length=1)
    abstract: str | None = Field(default=None, min_length=1)
    bibliography: str | None = Field(default=None, min_length=1)
    caption_figure: str | None = Field(default=None, min_length=1)
    caption_table: str | None = Field(default=None, min_length=1)
    equation: str | None = Field(default=None, min_length=1)
    listing: str | None = Field(default=None, min_length=1)
    footnote: str | None = Field(default=None, min_length=1)

    def declared(self) -> dict[str, str]:
        return {
            token: getattr(self, token)
            for token in PARAGRAPH_TOKENS
            if getattr(self, token) is not None
        }


class HeadingTokenMap(TemplateModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    level1: str = Field(alias="1", min_length=1)
    level2: str | None = Field(default=None, alias="2", min_length=1)
    level3: str | None = Field(default=None, alias="3", min_length=1)
    level4: str | None = Field(default=None, alias="4", min_length=1)

    @model_validator(mode="before")
    @classmethod
    def stringify_keys(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): item for key, item in value.items()}
        return value

    def declared(self) -> dict[int, str]:
        result = {1: self.level1}
        for level, attr in ((2, "level2"), (3, "level3"), (4, "level4")):
            name = getattr(self, attr)
            if name is not None:
                result[level] = name
        return result


class CharacterTokenMap(TemplateModel):
    emphasis: str | None = Field(default=None, min_length=1)
    strong: str | None = Field(default=None, min_length=1)
    code: str | None = Field(default=None, min_length=1)
    hyperlink: str | None = Field(default=None, min_length=1)
    equation_inline: str | None = Field(default=None, min_length=1)

    def declared(self) -> dict[str, str]:
        return {
            token: getattr(self, token)
            for token in CHARACTER_TOKENS
            if getattr(self, token) is not None
        }


class StylesSpec(TemplateModel):
    paragraph: ParagraphTokenMap
    heading: HeadingTokenMap
    character: CharacterTokenMap = Field(default_factory=CharacterTokenMap)

    @model_validator(mode="after")
    def validate_cross_category_duplicates(self) -> StylesSpec:
        paragraph_names = set(self.paragraph.declared().values())
        character_names = set(self.character.declared().values())
        duplicates = paragraph_names & character_names
        if duplicates:
            raise ValueError(
                "token 值跨类别重复（同一样式名不得同时作 paragraph 与 "
                f"character token）：{', '.join(sorted(duplicates))}"
            )
        return self


# ---------------------------------------------------------------------------
# §3.8 body / §3.9 headings
# ---------------------------------------------------------------------------


class LineSpacingSpec(TemplateModel):
    type: Literal["single", "multiple", "fixed"] = "fixed"
    value: FixedSpacingLength | float | None = None

    @model_validator(mode="after")
    def validate_value(self) -> LineSpacingSpec:
        if self.type == "fixed":
            if not isinstance(self.value, Length):
                raise ValueError("line_spacing.type 为 fixed 时必须提供带单位 Length value")
            if self.value.value <= 0:
                raise ValueError("fixed 行距必须大于 0")
        elif self.type == "multiple":
            if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
                raise ValueError("line_spacing.type 为 multiple 时 value 必须为正浮点数")
            if self.value <= 0:
                raise ValueError("multiple 行距倍数必须大于 0")
        elif self.value is not None:
            raise ValueError("line_spacing.type 为 single 时不得带 value")
        return self


class SpacingSpec(TemplateModel):
    before: IndentLength = None
    after: IndentLength = None


class BodySpec(TemplateModel):
    style: str = "body"
    alignment: Literal["left", "center", "right", "justify"] = "justify"
    first_line_indent: IndentLength = None
    # §4.1 B 类：未声明 line_spacing 时由 reference.docx 样式生效，不得默认出
    # type=fixed 的无值 LineSpacingSpec（§3.8 中 fixed 的 value 为条件必需）。
    line_spacing: LineSpacingSpec | None = None
    spacing: SpacingSpec = Field(default_factory=SpacingSpec)
    widow_control: bool | None = None


class HeadingNumberingSpec(TemplateModel):
    enabled: bool | None = None
    pattern: str | None = None

    @model_validator(mode="after")
    def validate_pattern(self) -> HeadingNumberingSpec:
        if self.enabled is False and self.pattern is not None:
            raise ValueError("numbering.enabled 为 false 时不得设置 pattern")
        _optional_pattern(self.pattern, HEADING_PLACEHOLDERS, "numbering.pattern")
        return self


class HeadingLevelSpec(TemplateModel):
    style: Literal[1, 2, 3, 4] | None = None
    page_break_before: bool | None = None
    keep_with_next: bool | None = None
    numbering: HeadingNumberingSpec = Field(default_factory=HeadingNumberingSpec)


class HeadingsSpec(TemplateModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    level1: HeadingLevelSpec = Field(default_factory=HeadingLevelSpec, alias="1")
    level2: HeadingLevelSpec = Field(default_factory=HeadingLevelSpec, alias="2")
    level3: HeadingLevelSpec = Field(default_factory=HeadingLevelSpec, alias="3")
    level4: HeadingLevelSpec = Field(default_factory=HeadingLevelSpec, alias="4")

    @model_validator(mode="before")
    @classmethod
    def stringify_keys(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): item for key, item in value.items()}
        return value

    def levels(self) -> dict[int, HeadingLevelSpec]:
        return {
            1: self.level1,
            2: self.level2,
            3: self.level3,
            4: self.level4,
        }


# ---------------------------------------------------------------------------
# §3.10 regions / §3.11 sections
# ---------------------------------------------------------------------------


class RegionSpec(TemplateModel):
    required: bool = False
    section: SectionKey | None = None
    title: str | None = None
    title_style: Literal[1, 2, 3, 4] = 1
    heading_numbering: bool = False
    anchor: str | None = None

    @field_validator("anchor")
    @classmethod
    def validate_anchor(cls, value: str | None) -> str | None:
        if value is not None and ANCHOR_NAME_RE.fullmatch(value) is None:
            raise ValueError(f"region anchor 必须匹配 ^tf_[a-z0-9_]+$：{value!r}")
        return value


class RegionsSpec(TemplateModel):
    order: list[RegionId] = Field(min_length=1)
    cover: RegionSpec | None = None
    originality_statement: RegionSpec | None = None
    authorization_statement: RegionSpec | None = None
    abstract_zh: RegionSpec | None = None
    abstract_en: RegionSpec | None = None
    toc: RegionSpec | None = None
    main: RegionSpec | None = None
    bibliography: RegionSpec | None = None
    acknowledgements: RegionSpec | None = None
    appendices: RegionSpec | None = None
    achievements: RegionSpec | None = None

    @model_validator(mode="after")
    def validate_order(self) -> RegionsSpec:
        if len(set(self.order)) != len(self.order):
            raise ValueError("regions.order 元素必须唯一")
        if self.order.count("main") != 1:
            raise ValueError("regions.order 必须含且仅含一个 main")
        return self

    def configs(self) -> dict[str, RegionSpec]:
        return {
            region: getattr(self, region)
            for region in REGION_IDS
            if getattr(self, region) is not None
        }


class PageNumberSpec(TemplateModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    display: bool = True
    format: Literal["decimal", "roman-lower", "roman-upper"] | None = None
    restart: int | None = Field(default=None, ge=1)
    continue_: bool = Field(default=False, alias="continue")

    @model_validator(mode="after")
    def validate_consistency(self) -> PageNumberSpec:
        if not self.display and (self.format is not None or self.restart is not None):
            raise ValueError("page_number.display 为 false 时不得设置 format/restart")
        if self.restart is not None and self.continue_:
            raise ValueError("page_number.restart 与 continue 互斥")
        return self

    @property
    def effective_format(self) -> str:
        return self.format or "decimal"


class HeaderFooterRefs(TemplateModel):
    default: str = "none"
    first: str = "none"
    even: str = "none"


class SectionPageOverride(TemplateModel):
    size: Literal["A3", "A4", "A5", "Letter", "Legal"] | None = None
    orientation: Literal["portrait", "landscape"] | None = None


class ColumnsSpec(TemplateModel):
    count: int = Field(default=1, ge=1, le=4)
    spacing: ColumnSpacingLength = None

    @model_validator(mode="after")
    def validate_spacing(self) -> ColumnsSpec:
        if self.count > 1 and self.spacing is None:
            raise ValueError("columns.count 大于 1 时 spacing 必需")
        return self


class SectionSpec(TemplateModel):
    start: Literal["continuous", "new_page", "odd_page", "even_page"] = "new_page"
    title_page: bool = False
    page_number: PageNumberSpec = Field(default_factory=PageNumberSpec)
    header_footer: HeaderFooterRefs = Field(default_factory=HeaderFooterRefs)
    page: SectionPageOverride | None = None
    columns: ColumnsSpec = Field(default_factory=ColumnsSpec)
    vertical_alignment: Literal["top", "center", "both", "bottom"] = "top"
    footnote_restart: Literal["continuous", "each_section", "each_page"] = "continuous"

    @field_validator("start", mode="before")
    @classmethod
    def normalize_start_alias(cls, value: Any) -> Any:
        # 偏差记录 C-5：next_page 为 new_page 的别名（lint 层补 info 提示）
        if value == "next_page":
            return "new_page"
        return value

    @model_validator(mode="after")
    def validate_first_page(self) -> SectionSpec:
        if self.header_footer.first != "none" and not self.title_page:
            raise ValueError("声明 header_footer.first 要求 title_page: true")
        return self


class SectionsSpec(TemplateModel):
    cover: SectionSpec = Field(default_factory=SectionSpec)
    front_matter: SectionSpec = Field(default_factory=SectionSpec)
    main: SectionSpec = Field(default_factory=SectionSpec)
    back_matter: SectionSpec = Field(default_factory=SectionSpec)

    def keys(self) -> tuple[str, ...]:
        return SECTION_KEYS


# ---------------------------------------------------------------------------
# §3.12 numbering
# ---------------------------------------------------------------------------


class ChapterNumberingSpec(TemplateModel):
    source: Literal["heading_1", "heading_2", "heading_3", "heading_4"] = "heading_1"
    format: Literal[
        "decimal",
        "lower_letter",
        "upper_letter",
        "lower_roman",
        "upper_roman",
        "chinese_counting",
    ] = "decimal"
    display: str = "第{n}章"

    @field_validator("display")
    @classmethod
    def validate_display(cls, value: str) -> str:
        _check_placeholders(value, frozenset({"n"}), "chapter.display")
        return value


class ReferenceFormsSpec(TemplateModel):
    number: str = "{number}"
    label_number: str = "{prefix} {number}"
    full: str = "{prefix} {number} {caption}"

    @model_validator(mode="after")
    def validate_placeholders(self) -> ReferenceFormsSpec:
        _check_placeholders(self.number, frozenset({"number"}), "reference_forms.number")
        _check_placeholders(
            self.label_number,
            frozenset({"prefix", "number"}),
            "reference_forms.label_number",
        )
        _check_placeholders(self.full, CAPTION_PLACEHOLDERS, "reference_forms.full")
        return self


class AppendixNumberingSpec(TemplateModel):
    prefix: str | None = None
    continue_numbering: bool = False


class CaptionNumberingSpec(TemplateModel):
    enabled: bool = True
    scope: Literal["chapter", "continuous"] = "chapter"
    sequence_name: str = "TF_FIGURE"
    separator: str = "-"
    caption_prefix: str = "图"
    caption_pattern: str = "{prefix} {number}  {caption}"
    reference_forms: ReferenceFormsSpec = Field(default_factory=ReferenceFormsSpec)
    appendix: AppendixNumberingSpec = Field(default_factory=AppendixNumberingSpec)

    @field_validator("sequence_name")
    @classmethod
    def validate_sequence_name(cls, value: str) -> str:
        if SEQUENCE_NAME_RE.fullmatch(value) is None:
            raise ValueError(
                f"sequence_name 必须匹配 ^TF_[A-Z][A-Z0-9_]*$：{value!r}"
            )
        return value

    @field_validator("caption_pattern")
    @classmethod
    def validate_caption_pattern(cls, value: str) -> str:
        _check_placeholders(value, CAPTION_PLACEHOLDERS, "caption_pattern")
        return value


class EquationNumberingSpec(TemplateModel):
    enabled: bool = True
    scope: Literal["chapter", "continuous"] = "chapter"
    sequence_name: str = "TF_EQUATION"
    display: str = "（{number}）"

    @field_validator("sequence_name")
    @classmethod
    def validate_sequence_name(cls, value: str) -> str:
        if SEQUENCE_NAME_RE.fullmatch(value) is None:
            raise ValueError(
                f"sequence_name 必须匹配 ^TF_[A-Z][A-Z0-9_]*$：{value!r}"
            )
        return value

    @field_validator("display")
    @classmethod
    def validate_display(cls, value: str) -> str:
        _check_placeholders(value, frozenset({"number"}), "equation.display")
        return value


class NumberingSpec(TemplateModel):
    chapter: ChapterNumberingSpec = Field(default_factory=ChapterNumberingSpec)
    figure: CaptionNumberingSpec = Field(default_factory=CaptionNumberingSpec)
    table: CaptionNumberingSpec = Field(
        default_factory=lambda: CaptionNumberingSpec(
            sequence_name="TF_TABLE", caption_prefix="表"
        )
    )
    equation: EquationNumberingSpec = Field(default_factory=EquationNumberingSpec)

    @model_validator(mode="after")
    def validate_sequence_uniqueness(self) -> NumberingSpec:
        names = [
            self.figure.sequence_name,
            self.table.sequence_name,
            self.equation.sequence_name,
        ]
        if len(set(names)) != len(names):
            raise ValueError("sequence_name 必须在全模板唯一")
        return self


# ---------------------------------------------------------------------------
# §3.13 figures / §3.14 tables / §3.15 equations
# ---------------------------------------------------------------------------


class FigureCaptionSpec(TemplateModel):
    position: Literal["top", "bottom"] = "bottom"
    style: str = "caption_figure"


class SourceNoteSpec(TemplateModel):
    policy: Literal["required", "optional", "forbidden"] = "optional"
    style: str = "body"


class FiguresSpec(TemplateModel):
    model_config = ConfigDict(validate_default=True)

    placement: Literal["inline", "floating"] = "inline"
    alignment: Literal["left", "center", "right"] = "center"
    max_width: ParentWidthLength = "100%"
    max_height: ImageHeightLength = "220mm"
    default_width: ParentWidthLength = None
    keep_with_caption: bool = True
    caption: FigureCaptionSpec = Field(default_factory=FigureCaptionSpec)
    source_note: SourceNoteSpec = Field(default_factory=SourceNoteSpec)
    format_allowlist: list[Literal["png", "jpg", "jpeg", "gif", "emf", "svg"]] = Field(
        default_factory=lambda: ["png", "jpg", "jpeg", "emf"]
    )
    dpi_warning: int = 150
    max_bytes: int | None = Field(default=None, gt=0)
    alt_text: Literal["required", "optional"] = "optional"
    subfigure_support: Literal["none", "basic", "full"] = "none"
    crop_policy: Literal["forbid", "allow"] = "forbid"


class TableBordersSpec(TemplateModel):
    model_config = ConfigDict(validate_default=True)

    top: BorderLength = "1.5pt"
    header_bottom: BorderLength = "0.75pt"
    bottom: BorderLength = "1.5pt"
    inside_vertical: BorderLength = "none"
    inside_horizontal: BorderLength = "none"


class TableCellPaddingSpec(TemplateModel):
    model_config = ConfigDict(validate_default=True)

    top: PageLength = "1mm"
    bottom: PageLength = "1mm"
    left: PageLength = "1mm"
    right: PageLength = "1mm"


class TableCellSpec(TemplateModel):
    vertical_alignment: Literal["top", "center", "bottom"] = "center"
    padding: TableCellPaddingSpec = Field(default_factory=TableCellPaddingSpec)


class TableStyleSpec(TemplateModel):
    borders: TableBordersSpec = Field(default_factory=TableBordersSpec)
    cell: TableCellSpec = Field(default_factory=TableCellSpec)


class TableOverflowSpec(TemplateModel):
    model_config = ConfigDict(validate_default=True)

    strategy: Literal["diagnose", "scale", "landscape_section"] = "diagnose"
    threshold: OverflowThresholdLength = "100%"
    min_scale: float = Field(default=0.6, gt=0, le=1)


class TableCaptionSpec(TemplateModel):
    position: Literal["top", "bottom"] = "top"
    style: str = "caption_table"


class TablesSpec(TemplateModel):
    model_config = ConfigDict(validate_default=True)

    default_style: str = "three_line"
    width: ParentWidthLength = "100%"
    autofit: bool = False
    repeat_header: bool = True
    allow_row_break: bool = False
    caption: TableCaptionSpec = Field(default_factory=TableCaptionSpec)
    styles: dict[str, TableStyleSpec] = Field(
        default_factory=lambda: {"three_line": TableStyleSpec()}
    )
    overflow: TableOverflowSpec = Field(default_factory=TableOverflowSpec)

    @model_validator(mode="after")
    def validate_default_style(self) -> TablesSpec:
        if self.default_style not in self.styles:
            raise ValueError(
                f"tables.default_style 必须存在于 tables.styles：{self.default_style!r}"
            )
        return self


class EquationsSpec(TemplateModel):
    converter: str = "default"
    inline_style: str = "equation_inline"
    block_style: str = "equation"
    alignment: Literal["left", "center", "right"] = "center"
    numbered_layout: Literal["tab_stop", "borderless_table", "custom_paragraph"] = (
        "tab_stop"
    )
    number_alignment: Literal["left", "center", "right"] = "right"
    unsupported_latex: Literal["error", "warning"] = "error"
    image_fallback: Literal["disabled", "explicit"] = "disabled"


# ---------------------------------------------------------------------------
# §3.16 fields / §3.17 cross_references / §3.18 toc / §3.19 bibliography
# ---------------------------------------------------------------------------


class FinalizerSpec(TemplateModel):
    draft: Literal["none", "auto", "word"] = "none"
    final_auto: Literal["none", "auto", "word"] = "auto"
    final_word: Literal["none", "auto", "word"] = "word"


class FieldsSpec(TemplateModel):
    update_on_open: bool = True
    cached_results: bool = True
    mark_dirty: bool = True
    finalizer: FinalizerSpec = Field(default_factory=FinalizerSpec)


class CrossReferencesSpec(TemplateModel):
    default_form: Literal["number", "label_number", "full"] = "label_number"
    page_reference: bool = False


class TocLevelSpec(TemplateModel):
    leader: Literal["none", "dots", "dashes", "line", "heavy", "middle_dot"] = "dots"
    page_number_tab: IndentLength = None

    @model_validator(mode="after")
    def validate_tab(self) -> TocLevelSpec:
        if self.page_number_tab is not None and self.page_number_tab.value <= 0:
            raise ValueError("toc.levels.*.page_number_tab 必须大于 0")
        return self


class TocLevelsSpec(TemplateModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    level1: TocLevelSpec = Field(default_factory=TocLevelSpec, alias="1")
    level2: TocLevelSpec = Field(default_factory=TocLevelSpec, alias="2")
    level3: TocLevelSpec = Field(default_factory=TocLevelSpec, alias="3")
    level4: TocLevelSpec = Field(default_factory=TocLevelSpec, alias="4")

    @model_validator(mode="before")
    @classmethod
    def stringify_keys(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): item for key, item in value.items()}
        return value


class TocSpec(TemplateModel):
    enabled: bool = True
    depth: int = Field(default=3, ge=1, le=4)
    title: str = "目录"
    include_page_numbers: bool = True
    right_align_page_numbers: bool = True
    hyperlink: bool = True
    levels: TocLevelsSpec = Field(default_factory=TocLevelsSpec)


class BibliographySpec(TemplateModel):
    model_config = ConfigDict(validate_default=True)

    provider: str = "default"
    style_file: str = "citations/style.csl"
    locale: str = "zh-CN"
    heading_region: str = "bibliography"
    paragraph_style: str = "bibliography"
    hanging_indent: IndentLength = "2em"
    line_spacing: LineSpacingSpec = Field(
        default_factory=lambda: LineSpacingSpec(type="single")
    )
    sort: Literal["style", "appearance"] = "style"
    uncited: Literal["exclude", "include"] = "exclude"
    missing_field_policy: Literal["warning", "error", "ignore"] = "warning"
    overrides_file: str | None = None
    presentation: Literal["inline", "superscript"] = "inline"

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, value: str) -> str:
        if BCP47_RE.fullmatch(value) is None:
            raise ValueError(f"bibliography.locale 必须是 BCP47 语言标签：{value!r}")
        return value


# ---------------------------------------------------------------------------
# 根模型（§3 顶层字段一览）
# ---------------------------------------------------------------------------


class TemplatePackageSpec(TemplateModel):
    schema_version: Literal[2]
    id: str = Field(min_length=1)
    version: str
    name: str = Field(min_length=1)
    language: str = "zh-CN"
    status: Literal["draft", "active", "deprecated", "archived"] = "draft"
    compatibility: CompatibilitySpec
    extends: ExtendsSpec | None = None
    word: WordSpec = Field(default_factory=WordSpec)
    page: PageSpec
    fonts: dict[str, FontRoleSpec]
    font_policy: FontPolicySpec = Field(default_factory=FontPolicySpec)
    styles: StylesSpec
    body: BodySpec = Field(default_factory=BodySpec)
    headings: HeadingsSpec = Field(default_factory=HeadingsSpec)
    regions: RegionsSpec
    sections: SectionsSpec = Field(default_factory=SectionsSpec)
    numbering: NumberingSpec = Field(default_factory=NumberingSpec)
    figures: FiguresSpec | None = None
    tables: TablesSpec | None = None
    equations: EquationsSpec | None = None
    fields: FieldsSpec = Field(default_factory=FieldsSpec)
    cross_references: CrossReferencesSpec = Field(default_factory=CrossReferencesSpec)
    toc: TocSpec = Field(default_factory=TocSpec)
    bibliography: BibliographySpec | None = None
    layouts: dict[RegionId, str] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if TEMPLATE_ID_RE.fullmatch(value) is None:
            raise ValueError(f"模板 id 格式无效：{value!r}（SCHEMA §3.1 正则）")
        return value

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if SEMVER_RE.fullmatch(value) is None:
            raise ValueError(f"version 必须是 Semver：{value!r}")
        return value

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if BCP47_RE.fullmatch(value) is None:
            raise ValueError(f"language 必须是 BCP47 语言标签：{value!r}")
        return value

    @model_validator(mode="after")
    def validate_cross_references(self) -> TemplatePackageSpec:
        """§3 各节 YAML 内交叉引用（token 引用存在性等）。"""
        errors: list[dict[str, Any]] = []
        paragraph_tokens = set(self.styles.paragraph.declared())
        character_tokens = set(self.styles.character.declared())
        heading_tokens = set(self.styles.heading.declared())

        def require_paragraph_token(token: str, loc: tuple[Any, ...]) -> None:
            if token not in paragraph_tokens:
                errors.append(
                    {
                        "type": "value_error",
                        "loc": loc,
                        "input": token,
                        "ctx": {
                            "error": ValueError(
                                f"引用的 paragraph token 未在 styles.paragraph 声明：{token}"
                            )
                        },
                    }
                )

        require_paragraph_token(self.body.style, ("body", "style"))
        for level, heading in self.headings.levels().items():
            style_token = heading.style if heading.style is not None else level
            if style_token not in heading_tokens:
                errors.append(
                    {
                        "type": "value_error",
                        "loc": ("headings", str(level), "style"),
                        "input": style_token,
                        "ctx": {
                            "error": ValueError(
                                "引用的 heading token 未在 styles.heading 声明："
                                f"{style_token}"
                            )
                        },
                    }
                )
        if self.figures is not None:
            require_paragraph_token(
                self.figures.caption.style, ("figures", "caption", "style")
            )
            require_paragraph_token(
                self.figures.source_note.style, ("figures", "source_note", "style")
            )
        if self.tables is not None:
            require_paragraph_token(
                self.tables.caption.style, ("tables", "caption", "style")
            )
        if self.equations is not None:
            require_paragraph_token(
                self.equations.block_style, ("equations", "block_style")
            )
            if self.equations.inline_style not in character_tokens:
                errors.append(
                    {
                        "type": "value_error",
                        "loc": ("equations", "inline_style"),
                        "input": self.equations.inline_style,
                        "ctx": {
                            "error": ValueError(
                                "引用的 character token 未在 styles.character 声明："
                                f"{self.equations.inline_style}"
                            )
                        },
                    }
                )
        if self.bibliography is not None:
            require_paragraph_token(
                self.bibliography.paragraph_style, ("bibliography", "paragraph_style")
            )
            if self.bibliography.heading_region not in self.regions.order:
                errors.append(
                    {
                        "type": "value_error",
                        "loc": ("bibliography", "heading_region"),
                        "input": self.bibliography.heading_region,
                        "ctx": {
                            "error": ValueError(
                                "heading_region 必须存在于 regions.order："
                                f"{self.bibliography.heading_region}"
                            )
                        },
                    }
                )
        for region, config in self.regions.configs().items():
            if config.section is not None and config.section not in SECTION_KEYS:
                errors.append(
                    {
                        "type": "value_error",
                        "loc": ("regions", region, "section"),
                        "input": config.section,
                        "ctx": {
                            "error": ValueError(
                                f"region section 必须存在于 sections：{config.section}"
                            )
                        },
                    }
                )
            if config.title_style not in heading_tokens:
                errors.append(
                    {
                        "type": "value_error",
                        "loc": ("regions", region, "title_style"),
                        "input": config.title_style,
                        "ctx": {
                            "error": ValueError(
                                "region title_style 引用的 heading token 未声明："
                                f"{config.title_style}"
                            )
                        },
                    }
                )
        if errors:
            raise ValidationError.from_exception_data(type(self).__name__, errors)
        return self


# ---------------------------------------------------------------------------
# §3.21 provenance.yaml
# ---------------------------------------------------------------------------


class OfficialDocumentSpec(TemplateModel):
    title: str = Field(min_length=1)
    version: str = Field(min_length=1)
    issued_date: Any = None
    source_type: Literal["official-docx", "official-pdf", "webpage", "manual"]
    source_hash: str | None = None
    source_url: str | None = None

    @field_validator("issued_date")
    @classmethod
    def validate_issued_date(cls, value: Any) -> Any:
        if value is None:
            return None
        import datetime as _dt

        if isinstance(value, _dt.date):
            return value
        if isinstance(value, str):
            try:
                return _dt.date.fromisoformat(value)
            except ValueError:
                pass
        raise ValueError(f"issued_date 必须是 ISO 8601 日期（YYYY-MM-DD）：{value!r}")

    @model_validator(mode="after")
    def validate_source_hash(self) -> OfficialDocumentSpec:
        if (
            self.source_type in ("official-docx", "official-pdf")
            and self.source_hash is None
        ):
            raise ValueError(
                f"source_type 为 {self.source_type} 时 source_hash 必需"
            )
        if self.source_hash is not None and SHA256_REF_RE.fullmatch(self.source_hash) is None:
            raise ValueError("source_hash 必须是 sha256: + 64 位小写十六进制")
        return self


class SchoolSpec(TemplateModel):
    name: str = Field(min_length=1)
    official_document: OfficialDocumentSpec


class MaintainerSpec(TemplateModel):
    name: str = Field(min_length=1)
    contact: str = Field(min_length=1)


class LicensesSpec(TemplateModel):
    template_code: str = Field(min_length=1)
    school_assets: str = Field(min_length=1)
    citation_style: str | None = None
    fonts: str | None = None


class ReviewSpec(TemplateModel):
    last_verified: Any
    verified_with: list[str] = Field(min_length=1)

    @field_validator("last_verified")
    @classmethod
    def validate_last_verified(cls, value: Any) -> Any:
        import datetime as _dt

        if isinstance(value, _dt.date):
            return value
        if isinstance(value, str):
            try:
                return _dt.date.fromisoformat(value)
            except ValueError:
                pass
        raise ValueError(f"last_verified 必须是 ISO 8601 日期（YYYY-MM-DD）：{value!r}")


class ProvenanceSpec(TemplateModel):
    school: SchoolSpec
    maintainers: list[MaintainerSpec] = Field(min_length=1)
    licenses: LicensesSpec
    review: ReviewSpec
    # sample 包使用 notes 记录生成方式；§3.21 未列出，本实现显式放行
    notes: str | None = None
