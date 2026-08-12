from pathlib import Path

import pytest

from thesis_forge.templates import (
    BodySpec,
    CoverItemSpec,
    CoverSpec,
    HeaderFooterSpec,
    HeaderFooterVariantSpec,
    HeadingLevelSpec,
    LengthSpec,
    ListSpec,
    OrderedListLevelSpec,
    OrderedListSpec,
    PageNumberDisplaySpec,
    PageNumberSpec,
    ParagraphStyleSpec,
    SectionSpec,
    TemplateLoadError,
    TemplateNotFoundError,
    TocLevelSpec,
    UnorderedListLevelSpec,
    UnorderedListSpec,
    default_template_search_roots,
    load_template,
    resolve_template,
)


def test_list_policy_has_deterministic_renderer_neutral_defaults():
    template = load_template("templates/base/bachelor.yaml")

    assert len(template.list.ordered.levels) == 9
    assert [level.format for level in template.list.ordered.levels] == [
        "decimal"
    ] * 9
    assert [level.prefix for level in template.list.ordered.levels] == [""] * 9
    assert [level.suffix for level in template.list.ordered.levels] == ["."] * 9
    assert [str(level.left_indent) for level in template.list.ordered.levels] == [
        f"{36 * level}pt" for level in range(1, 10)
    ]
    assert [str(level.hanging_indent) for level in template.list.ordered.levels] == [
        "18pt"
    ] * 9
    assert [level.marker for level in template.list.unordered.levels] == [
        "•",
        "◦",
        "▪",
        "•",
        "◦",
        "▪",
        "•",
        "◦",
        "▪",
    ]
    assert template.list.ordered.for_level(20) is template.list.ordered.levels[-1]
    assert (
        template.list.unordered.for_level(20)
        is template.list.unordered.levels[-1]
    )


def test_hut_list_policy_is_explicit_while_legacy_template_uses_defaults():
    hut = load_template(
        "templates/schools/hunan-university-of-technology/master-2026.yaml"
    )
    example = load_template("templates/schools/example-university/2026.yaml")

    assert [level.format for level in hut.list.ordered.levels] == [
        "decimal",
        "lower_letter",
        "lower_roman",
    ]
    assert [level.suffix for level in hut.list.ordered.levels] == ["、", ")", ")"]
    assert [str(level.left_indent) for level in hut.list.ordered.levels] == [
        "24pt",
        "48pt",
        "72pt",
    ]
    assert [level.marker for level in hut.list.unordered.levels] == ["●", "○", "■"]
    assert all(
        level.style.font is not None
        and level.style.font.east_asia == "宋体"
        and str(level.style.size) == "12pt"
        and str(level.style.line_spacing.value) == "20pt"
        for level in (*hut.list.ordered.levels, *hut.list.unordered.levels)
    )
    assert hut.list.ordered.for_level(8) is hut.list.ordered.levels[-1]
    assert hut.list.unordered.for_level(8) is hut.list.unordered.levels[-1]

    assert len(example.list.ordered.levels) == 9
    assert [level.format for level in example.list.ordered.levels] == [
        "decimal"
    ] * 9
    assert [level.marker for level in example.list.unordered.levels[:3]] == [
        "•",
        "◦",
        "▪",
    ]


def test_list_policy_accepts_semantic_formats_markers_and_paragraph_styles():
    policy = ListSpec(
        ordered=OrderedListSpec(
            levels=(
                OrderedListLevelSpec(
                    format="lower_roman",
                    prefix="(",
                    suffix=")",
                    alignment="right",
                    left_indent="20mm",
                    hanging_indent="5mm",
                    style=ParagraphStyleSpec(
                        font={"east_asia": "宋体", "latin": "Times New Roman"},
                        size="11pt",
                        color="112233",
                        space_after="6pt",
                        line_spacing={"type": "multiple", "value": 1.25},
                    ),
                ),
            )
        ),
        unordered=UnorderedListSpec(
            levels=(
                UnorderedListLevelSpec(
                    marker="◆",
                    left_indent="30pt",
                    hanging_indent="12pt",
                ),
            )
        ),
    )

    assert policy.ordered.levels[0].format == "lower_roman"
    assert policy.ordered.levels[0].prefix == "("
    assert policy.ordered.levels[0].suffix == ")"
    assert policy.ordered.levels[0].style.color == "112233"
    assert policy.unordered.levels[0].marker == "◆"


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: OrderedListLevelSpec(format="greek"),
            "Input should be",
        ),
        (
            lambda: UnorderedListLevelSpec(marker="   "),
            "marker 不能为空",
        ),
        (
            lambda: OrderedListLevelSpec(left_indent="2em"),
            "绝对单位",
        ),
        (
            lambda: OrderedListLevelSpec(
                left_indent="10pt",
                hanging_indent="11pt",
            ),
            "不能大于",
        ),
        (
            lambda: OrderedListSpec(levels=()),
            "at least 1",
        ),
        (
            lambda: UnorderedListSpec(
                levels=tuple(UnorderedListLevelSpec() for _ in range(10))
            ),
            "at most 9",
        ),
    ],
)
def test_list_policy_rejects_invalid_formats_markers_levels_and_geometry(
    factory,
    message: str,
):
    with pytest.raises(ValueError, match=message):
        factory()


def test_cover_policy_has_deterministic_renderer_neutral_defaults():
    template = load_template("templates/base/bachelor.yaml")

    assert [item.field for item in template.cover.items] == [
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
    assert all(item.style.alignment == "center" for item in template.cover.items)


def test_cover_item_requires_exactly_one_content_source():
    with pytest.raises(ValueError, match="必须且只能配置"):
        CoverItemSpec()
    with pytest.raises(ValueError, match="必须且只能配置"):
        CoverItemSpec(field="thesis.title", text="论文题目")
    with pytest.raises(ValueError, match="text 不能为空"):
        CoverItemSpec(text="   ")


def test_cover_policy_rejects_duplicate_metadata_fields():
    with pytest.raises(ValueError, match="重复 field: thesis.title"):
        CoverSpec(
            items=(
                CoverItemSpec(field="thesis.title"),
                CoverItemSpec(field="thesis.title"),
            )
        )


def test_load_example_template():
    template = load_template("templates/schools/example-university/2026.yaml")
    assert template.id == "example-university-2026"
    assert template.body.font.east_asia == "宋体"
    assert str(template.page.margin.top) == "25mm"
    assert str(template.heading.level1.size) == "16pt"
    assert template.figure is not None
    assert template.figure.numbering.mode == "chapter"
    assert template.figure.caption.position == "bottom"
    assert template.citation is not None
    assert template.citation.style == "GB-T-7714-2025"
    assert template.sections.cover is not None
    assert template.sections.cover.page_number.format == "none"
    assert template.sections.front_matter is not None
    assert template.sections.front_matter.page_number.format == "roman-lower"
    assert template.sections.front_matter.page_number.restart == 1
    assert template.sections.main is not None
    assert template.sections.main.header.text == "XX大学本科毕业论文"
    assert template.sections.main.footer.enabled is True
    assert template.sections.main.page_number.format == "decimal"
    assert template.sections.main.page_number.restart == 1


def test_template_models_sections_headers_footers_and_page_numbers(tmp_path: Path):
    path = tmp_path / "template.yaml"
    path.write_text(
        """id: typed-template
name: Typed Template
year: 2026
page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  font:
    east_asia: 宋体
    latin: Times New Roman
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
sections:
  main:
    start: new_page
    header:
      enabled: true
      text: "论文标题"
    footer:
      enabled: true
    page_number:
      format: decimal
      restart: 1
citation:
  style: GB-T-7714-2025
""",
        encoding="utf-8",
    )

    template = load_template(path)

    assert template.sections.main is not None
    assert template.sections.main.start == "new_page"
    assert template.sections.main.header.text == "论文标题"
    assert template.sections.main.footer.enabled is True
    assert template.sections.main.page_number.format == "decimal"
    assert template.sections.main.page_number.restart == 1


def test_invalid_length_reports_field_path(tmp_path: Path):
    path = tmp_path / "invalid.yaml"
    path.write_text(
        """id: invalid-length
name: Invalid Length
year: 2026
page:
  size: A4
  orientation: portrait
  margin:
    top: 25
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  font:
    east_asia: 宋体
    latin: Times New Roman
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert "page.margin.top" in str(exc_info.value)
    assert "mm / cm / pt / em" in str(exc_info.value)


def test_missing_required_heading_style_reports_field_path(tmp_path: Path):
    path = tmp_path / "missing-heading.yaml"
    path.write_text(
        """id: missing-heading
name: Missing Heading
year: 2026
page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  font:
    east_asia: 宋体
    latin: Times New Roman
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert "heading" in str(exc_info.value)


def test_resolve_template_prefers_explicit_path(tmp_path: Path):
    explicit = tmp_path / "explicit.yaml"
    explicit.write_text(
        """id: explicit
name: Explicit
year: 2026
page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  font:
    east_asia: 宋体
    latin: Times New Roman
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
""",
        encoding="utf-8",
    )

    resolved = resolve_template(
        explicit_path=explicit,
        template_id="ignored-id",
        search_roots=(),
    )

    assert resolved.path == explicit.resolve()
    assert resolved.template.id == "explicit"


def test_explicit_template_path_requires_yaml_extension(tmp_path: Path):
    path = tmp_path / "template.txt"
    path.write_text("id: text-template\n", encoding="utf-8")

    with pytest.raises(TemplateLoadError) as exc_info:
        resolve_template(
            explicit_path=path,
            template_id=None,
            search_roots=(),
        )

    assert ".yaml or .yml" in str(exc_info.value)


def test_resolve_template_by_id_and_report_missing(tmp_path: Path):
    root = tmp_path / "templates"
    root.mkdir()
    template = root / "school.yaml"
    template.write_text(
        """id: school-2026
name: School
year: 2026
page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  font:
    east_asia: 宋体
    latin: Times New Roman
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
""",
        encoding="utf-8",
    )

    resolved = resolve_template(
        explicit_path=None,
        template_id="school-2026",
        search_roots=(root,),
    )
    assert resolved.path == template.resolve()

    with pytest.raises(TemplateNotFoundError):
        resolve_template(
            explicit_path=None,
            template_id="missing",
            search_roots=(root,),
        )


def test_empty_ancestor_templates_directory_does_not_hide_packaged_templates(
    tmp_path: Path,
):
    source = tmp_path / "user" / "project" / "thesis.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Thesis\n", encoding="utf-8")
    unrelated_templates = tmp_path / "user" / "templates"
    unrelated_templates.mkdir()
    (unrelated_templates / "desktop.ini").write_text("", encoding="utf-8")

    resolved = resolve_template(
        explicit_path=None,
        template_id="example-university-2026",
        search_roots=default_template_search_roots(source),
    )

    assert resolved.template.id == "example-university-2026"
    assert unrelated_templates not in resolved.path.parents


def test_resolve_template_id_surfaces_malformed_matching_yaml(tmp_path: Path):
    root = tmp_path / "templates"
    root.mkdir()
    broken = root / "broken.yaml"
    broken.write_text("id: broken\npage: [\n", encoding="utf-8")

    with pytest.raises(TemplateLoadError) as exc_info:
        resolve_template(
            explicit_path=None,
            template_id="broken",
            search_roots=(root,),
        )

    assert "$yaml" in str(exc_info.value)


def test_p0_paragraph_semantic_toc_bibliography_and_section_models(
    tmp_path: Path,
):
    path = tmp_path / "p0.yaml"
    path.write_text(
        """id: p0-template
name: P0 Template
year: 2026
page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
  header_distance: 15mm
  footer_distance: 17.5mm
  document_grid:
    type: lines
    line_pitch: 20pt
body:
  font:
    east_asia: 宋体
    latin: Times New Roman
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  space_before: 0pt
  space_after: 0pt
  line_spacing:
    type: fixed
    value: 20pt
  widow_control: true
heading:
  level1:
    size: 16pt
    bold: true
    alignment: center
    keep_with_next: true
    outline_level: 0
semantic_styles:
  abstract_zh:
    title:
      size: 16pt
      bold: true
      alignment: center
    body:
      size: 12pt
      first_line_indent: 2em
    keywords:
      size: 12pt
      first_line_indent: 0em
  abstract_en:
    body:
      font:
        east_asia: 宋体
        latin: Times New Roman
      size: 12pt
    keywords:
      size: 12pt
toc:
  title:
    size: 16pt
    alignment: center
  level1:
    size: 12pt
    left_indent: 0em
    page_number_tab: 150mm
    leader: dots
  level2:
    size: 12pt
    left_indent: 1em
    page_number_tab: 150mm
    leader: dots
bibliography:
  title:
    size: 16pt
    alignment: center
  entry:
    size: 10.5pt
    hanging_indent: 2em
    line_spacing:
      type: fixed
      value: 20pt
sections:
  main:
    header:
      default:
        enabled: true
        text: Odd Header
        bottom_border:
          style: single
          width: 0.5pt
      even:
        enabled: true
        text: Even Header
      first:
        enabled: false
    footer:
      default:
        enabled: true
        page_number:
          alignment: center
          page_prefix: ""
          page_suffix: ""
          include_total: false
    page_number:
      format: decimal
      restart: 1
      display:
        alignment: center
        page_prefix: ""
        page_suffix: ""
        include_total: false
citation:
  style: GB-T-7714-2025
  presentation: superscript
""",
        encoding="utf-8",
    )

    template = load_template(path)

    assert isinstance(template.body, ParagraphStyleSpec)
    assert str(template.body.space_before) == "0pt"
    assert template.body.widow_control is True
    assert template.heading.level1.keep_with_next is True
    assert template.heading.level1.outline_level == 0
    assert template.semantic_styles.abstract_zh is not None
    assert str(template.semantic_styles.abstract_zh.body.first_line_indent) == "2em"
    assert template.toc is not None
    assert str(template.toc.level1.page_number_tab) == "150mm"
    assert template.toc.level1.leader == "dots"
    assert template.bibliography is not None
    assert str(template.bibliography.entry.hanging_indent) == "2em"
    assert str(template.page.header_distance) == "15mm"
    assert template.page.document_grid is not None
    assert template.sections.main is not None
    assert template.sections.main.header.default is not None
    assert template.sections.main.header.default.text == "Odd Header"
    assert template.sections.main.header.even is not None
    assert template.sections.main.header.even.text == "Even Header"
    assert template.sections.main.footer.default is not None
    assert template.sections.main.footer.default.page_number is not None
    assert template.sections.main.footer.default.page_number.include_total is False
    assert template.sections.main.page_number.display.include_total is False
    assert template.citation is not None
    assert template.citation.presentation == "superscript"


def test_legacy_template_defaults_remain_compatible():
    template = load_template("templates/schools/example-university/2026.yaml")

    assert template.body.space_before is None
    assert template.body.space_after is None
    assert template.body.widow_control is None
    assert template.sections.main is not None
    assert template.sections.main.header.default is not None
    assert template.sections.main.header.default.enabled is True
    assert template.sections.main.header.default.text == "XX大学本科毕业论文"
    assert template.sections.main.page_number.display.page_prefix == "第 "
    assert template.sections.main.page_number.display.include_total is True
    assert template.citation is not None
    assert template.citation.presentation == "inline"


@pytest.mark.parametrize(
    "path",
    [
        "templates/base/bachelor.yaml",
        "templates/schools/example-university/2026.yaml",
    ],
)
def test_all_builtin_templates_remain_valid(path: str):
    template = load_template(path)

    assert template.id
    assert isinstance(template.body, ParagraphStyleSpec)
    assert template.heading.level1.size is not None


def test_unknown_common_paragraph_field_reports_exact_path(tmp_path: Path):
    path = tmp_path / "unknown-paragraph-field.yaml"
    path.write_text(
        """id: unknown-paragraph-field
name: Unknown Paragraph Field
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
  magic_spacing: 3pt
heading:
  level1:
    size: 16pt
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert "body.magic_spacing" in str(exc_info.value)
    assert "Extra inputs are not permitted" in str(exc_info.value)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10pt", "10pt"),
        ("20pt", "20pt"),
        ("100mm", "100mm"),
        ("150mm", "150mm"),
        ("10.50pt", "10.5pt"),
    ],
)
def test_length_string_preserves_integer_trailing_zeroes(raw: str, expected: str):
    assert str(LengthSpec.model_validate(raw)) == expected


def test_body_and_heading_inheritance_preserves_required_fields_and_defaults():
    body_schema = BodySpec.model_json_schema()
    heading_schema = HeadingLevelSpec.model_json_schema()

    assert set(body_schema["required"]) == {
        "size",
        "first_line_indent",
        "line_spacing",
    }
    assert body_schema["properties"]["alignment"]["default"] == "justify"
    assert "default" not in body_schema["properties"]["font"]
    assert heading_schema["required"] == ["size"]
    assert heading_schema["properties"]["bold"]["default"] is False
    assert heading_schema["properties"]["italic"]["default"] is False
    assert heading_schema["properties"]["alignment"]["default"] == "left"
    assert heading_schema["properties"]["page_break_before"]["default"] is False


@pytest.mark.parametrize("color", ["auto", "000000", "336699", "abcdef"])
def test_paragraph_style_accepts_auto_or_six_digit_color(color: str):
    assert ParagraphStyleSpec(color=color).color == color


@pytest.mark.parametrize("color", ["#000000", "000", "GGGGGG", "transparent"])
def test_paragraph_style_rejects_invalid_color(color: str):
    with pytest.raises(ValueError):
        ParagraphStyleSpec(color=color)


def test_body_font_size_rejects_em_without_absolute_base(tmp_path: Path):
    path = tmp_path / "relative-body-size.yaml"
    path.write_text(
        """id: relative-body-size
name: Relative Body Size
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 1em
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 1.5em
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == "body.size"
    assert "绝对单位" in str(exc_info.value)


@pytest.mark.parametrize(
    "header_yaml",
    [
        """      enabled: false
      default:
        enabled: true
""",
        """      text: ""
      default:
        enabled: true
""",
        """      different_first_page: false
      first:
        enabled: false
""",
    ],
)
def test_header_footer_rejects_mixed_legacy_and_variant_fields(
    tmp_path: Path,
    header_yaml: str,
):
    path = tmp_path / "mixed-header.yaml"
    path.write_text(
        f"""id: mixed-header
name: Mixed Header
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
sections:
  main:
    header:
{header_yaml}""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == "sections.main.header"


def test_new_header_variant_does_not_project_into_legacy_renderer_fields(
    tmp_path: Path,
):
    path = tmp_path / "new-header.yaml"
    path.write_text(
        """id: new-header
name: New Header
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
sections:
  main:
    header:
      default:
        enabled: true
        text: New Header
      first:
        enabled: false
""",
        encoding="utf-8",
    )

    template = load_template(path)
    assert template.sections.main is not None
    header = template.sections.main.header
    assert header.enabled is False
    assert header.text is None
    assert header.different_first_page is False
    assert header.default is not None
    assert header.default.text == "New Header"
    assert header.first is not None
    assert header.first.enabled is False


def test_first_line_and_hanging_indent_cannot_both_be_positive(tmp_path: Path):
    path = tmp_path / "invalid-indent.yaml"
    path.write_text(
        """id: invalid-indent
name: Invalid Indent
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  hanging_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == "body.hanging_indent"
    assert "first_line_indent" in str(exc_info.value)
    assert "hanging_indent" in str(exc_info.value)


@pytest.mark.parametrize(
    ("spacing_yaml", "message"),
    [
        ("    type: fixed\n", "fixed"),
        ("    type: fixed\n    value: 1.5\n", "fixed"),
        ("    type: multiple\n", "multiple"),
        ("    type: multiple\n    value: 0\n", "multiple"),
        ("    type: single\n    value: 20pt\n", "single"),
    ],
)
def test_invalid_line_spacing_reports_exact_path(
    tmp_path: Path,
    spacing_yaml: str,
    message: str,
):
    path = tmp_path / "invalid-spacing.yaml"
    path.write_text(
        f"""id: invalid-spacing
name: Invalid Spacing
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
{spacing_yaml}
heading:
  level1:
    size: 16pt
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == "body.line_spacing"
    assert message in str(exc_info.value)


def test_invalid_toc_enum_reports_exact_path(tmp_path: Path):
    path = tmp_path / "invalid-toc-enum.yaml"
    path.write_text(
        """id: invalid-toc-enum
name: Invalid TOC Enum
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
toc:
  level1:
    leader: stars
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == "toc.level1.leader"


def test_toc_level_defaults_keep_entries_flush_and_use_dot_leaders():
    level = TocLevelSpec()

    assert str(level.first_line_indent) == "0pt"
    assert level.page_number_tab is None
    assert level.leader == "dots"


def test_invalid_toc_page_number_tab_reports_exact_path(tmp_path: Path):
    path = tmp_path / "invalid-toc-tab.yaml"
    path.write_text(
        """id: invalid-toc-tab
name: Invalid TOC Tab
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
toc:
  level1:
    page_number_tab: 0pt
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == "toc.level1.page_number_tab"
    assert "大于 0" in str(exc_info.value)


def test_toc_rejects_unsupported_fourth_level(tmp_path: Path):
    path = tmp_path / "invalid-toc-level.yaml"
    path.write_text(
        """id: invalid-toc-level
name: Invalid TOC Level
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
toc:
  level4:
    page_number_tab: 150mm
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == "toc.level4"


def test_invalid_header_border_width_reports_complete_path(tmp_path: Path):
    path = tmp_path / "invalid-border.yaml"
    path.write_text(
        """id: invalid-border
name: Invalid Border
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
sections:
  main:
    header:
      default:
        bottom_border:
          width: 1px
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == (
        "sections.main.header.default.bottom_border.width"
    )


def test_table_three_line_widths_are_configurable(tmp_path: Path):
    path = tmp_path / "table-three-line.yaml"
    path.write_text(
        """id: table-three-line
name: Table Three Line
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
table:
  style: three_line
  three_line:
    top_width: 2pt
    header_width: 0.5pt
    bottom_width: 1pt
  caption:
    position: top
    prefix: 表
""",
        encoding="utf-8",
    )

    template = load_template(path)

    assert str(template.table.three_line.top_width) == "2pt"
    assert str(template.table.three_line.header_width) == "0.5pt"
    assert str(template.table.three_line.bottom_width) == "1pt"


@pytest.mark.parametrize("header_width", ["1em", "0.1pt", "13pt"])
def test_invalid_table_three_line_width_reports_complete_path(
    tmp_path: Path,
    header_width: str,
):
    path = tmp_path / "invalid-table-three-line.yaml"
    path.write_text(
        f"""id: invalid-table-three-line
name: Invalid Table Three Line
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
table:
  style: three_line
  three_line:
    header_width: {header_width}
  caption:
    position: top
    prefix: 表
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == "table.three_line.header_width"


@pytest.mark.parametrize(
    ("part", "variant", "include_total"),
    [
        ("header", "default", "false"),
        ("header", "first", "true"),
        ("header", "even", "false"),
        ("footer", "default", "true"),
        ("footer", "first", "false"),
        ("footer", "even", "true"),
    ],
)
def test_page_number_format_none_rejects_enabled_variant_page_fields(
    tmp_path: Path,
    part: str,
    variant: str,
    include_total: str,
):
    path = tmp_path / "disabled-page-number.yaml"
    path.write_text(
        f"""id: disabled-page-number
name: Disabled Page Number
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
sections:
  main:
    {part}:
      {variant}:
        enabled: true
        page_number:
          include_total: {include_total}
    page_number:
      format: none
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == (
        f"sections.main.{part}.{variant}.page_number"
    )
    assert "PAGE/NUMPAGES" in str(exc_info.value)


def test_disabled_variant_may_define_dormant_page_number_policy(tmp_path: Path):
    path = tmp_path / "disabled-page-number-variant.yaml"
    path.write_text(
        """id: disabled-page-number-variant
name: Disabled Page Number Variant
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
sections:
  main:
    footer:
      default:
        enabled: false
        page_number:
          include_total: true
    page_number:
      format: none
""",
        encoding="utf-8",
    )

    template = load_template(path)
    assert template.sections.main is not None
    assert template.sections.main.footer.default is not None
    assert template.sections.main.footer.default.enabled is False


def test_direct_section_model_construction_enforces_page_number_conflict():
    footer = HeaderFooterSpec(
        default=HeaderFooterVariantSpec(
            page_number=PageNumberDisplaySpec(include_total=False)
        )
    )

    with pytest.raises(ValueError) as exc_info:
        SectionSpec(
            footer=footer,
            page_number=PageNumberSpec(format="none"),
        )

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("footer", "default", "page_number")
    assert "PAGE/NUMPAGES" in error["msg"]


def test_page_number_format_none_rejects_restart(tmp_path: Path):
    path = tmp_path / "invalid-page-number-restart.yaml"
    path.write_text(
        """id: invalid-page-number-restart
name: Invalid Page Number Restart
year: 2026
page:
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
sections:
  main:
    page_number:
      format: none
      restart: 1
""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == "sections.main.page_number"
    assert "restart" in str(exc_info.value)


@pytest.mark.parametrize(
    ("margin_policy", "page_policy", "section_policy", "expected_path"),
    [
        (
            "    top: 1em\n    bottom: 25mm\n    left: 30mm\n    right: 25mm\n",
            "",
            "",
            "page.margin.top",
        ),
        (
            "    top: 25mm\n    bottom: 1em\n    left: 30mm\n    right: 25mm\n",
            "",
            "",
            "page.margin.bottom",
        ),
        (
            "    top: 25mm\n    bottom: 25mm\n    left: 1em\n    right: 25mm\n",
            "",
            "",
            "page.margin.left",
        ),
        (
            "    top: 25mm\n    bottom: 25mm\n    left: 30mm\n    right: 1em\n",
            "",
            "",
            "page.margin.right",
        ),
        (
            "    top: 25mm\n    bottom: 25mm\n    left: 30mm\n    right: 25mm\n",
            "  header_distance: 1em\n",
            "",
            "page.header_distance",
        ),
        (
            "    top: 25mm\n    bottom: 25mm\n    left: 30mm\n    right: 25mm\n",
            "  footer_distance: 1em\n",
            "",
            "page.footer_distance",
        ),
        (
            "    top: 25mm\n    bottom: 25mm\n    left: 30mm\n    right: 25mm\n",
            "  document_grid:\n    type: lines\n    line_pitch: 1em\n",
            "",
            "page.document_grid.line_pitch",
        ),
        (
            "    top: 25mm\n    bottom: 25mm\n    left: 30mm\n    right: 25mm\n",
            "",
            """sections:
  main:
    header:
      default:
        bottom_border:
          width: 1em
""",
            "sections.main.header.default.bottom_border.width",
        ),
        (
            "    top: 25mm\n    bottom: 25mm\n    left: 30mm\n    right: 25mm\n",
            "",
            """sections:
  main:
    header:
      default:
        bottom_border:
          space: 1em
""",
            "sections.main.header.default.bottom_border.space",
        ),
    ],
)
def test_physical_page_and_border_lengths_reject_em(
    tmp_path: Path,
    margin_policy: str,
    page_policy: str,
    section_policy: str,
    expected_path: str,
):
    path = tmp_path / "invalid-physical-length.yaml"
    path.write_text(
        f"""id: invalid-physical-length
name: Invalid Physical Length
year: 2026
page:
  margin:
{margin_policy}
{page_policy}body:
  size: 12pt
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
heading:
  level1:
    size: 16pt
{section_policy}""",
        encoding="utf-8",
    )

    with pytest.raises(TemplateLoadError) as exc_info:
        load_template(path)

    assert exc_info.value.field_errors[0][0] == expected_path
    assert "mm / cm / pt" in str(exc_info.value)
