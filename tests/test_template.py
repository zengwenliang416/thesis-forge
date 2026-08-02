from pathlib import Path

import pytest

from thesis_forge.templates import (
    TemplateLoadError,
    TemplateNotFoundError,
    default_template_search_roots,
    load_template,
    resolve_template,
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
