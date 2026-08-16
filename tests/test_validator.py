from pathlib import Path

from thesis_forge.core.model import ValidationIssue
from thesis_forge.core.parser import parse_markdown
from thesis_forge.core.validator import ValidationContext, validate_document
from thesis_forge.templates import load_template


def test_missing_cross_reference(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论\n\n如 @fig:missing 所示。\n", encoding="utf-8")
    issues = validate_document(parse_markdown(source))
    assert any(x.code == "missing-reference" for x in issues)


def test_duplicate_id(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 第一章 {#chap:x}\n\n# 第二章 {#chap:x}\n", encoding="utf-8")
    issues = validate_document(parse_markdown(source))
    assert any(x.code == "duplicate-id" for x in issues)


def test_validation_context_can_replace_default_rules(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论 {#chap:intro}\n", encoding="utf-8")
    document = parse_markdown(source)

    def custom_rule(_document, _context):
        return [
            ValidationIssue(
                code="custom-rule",
                severity="warning",
                message="自定义规则",
                line=7,
            )
        ]

    issues = validate_document(
        document,
        ValidationContext(rules=(custom_rule,)),
    )

    assert [issue.code for issue in issues] == ["custom-rule"]


def test_validation_reports_metadata_ids_bibliography_and_resources(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text(
        """# 绪论 {#bad}

参见 @fig:missing，并引用 [@smith2025]。

::: figure {#chap:figure}
src: "./missing.png"
caption: "错误前缀"
:::
""",
        encoding="utf-8",
    )

    issues = validate_document(parse_markdown(source))
    codes = {issue.code for issue in issues}

    assert {
        "required-metadata",
        "missing-template",
        "invalid-id-prefix",
        "missing-reference",
        "missing-image",
        "missing-bibliography",
    } <= codes
    assert all(issue.message.isascii() for issue in issues)


def test_validation_uses_template_context_and_checks_style_coverage(tmp_path: Path):
    template_path = tmp_path / "template.yaml"
    template_path.write_text(
        """id: minimal
name: Minimal
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
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
---

# 绪论 {#chap:intro}

::: figure {#fig:model}
src: "./model.png"
caption: "模型"
:::
""",
        encoding="utf-8",
    )
    context = ValidationContext(template=load_template(template_path))

    issues = validate_document(parse_markdown(source), context)

    assert any(
        issue.code == "missing-template-style" and issue.target == "figure"
        for issue in issues
    )


def test_validation_context_resolves_front_matter_template_id(tmp_path: Path):
    template_root = tmp_path / "templates"
    template_root.mkdir()
    template_path = template_root / "school.yaml"
    template_path.write_text(
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
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
render:
  template_id: school-2026
---

# 绪论 {#chap:intro}
""",
        encoding="utf-8",
    )
    document = parse_markdown(source)

    context = ValidationContext.from_document(
        document,
        template_roots=(template_root,),
    )
    issues = validate_document(document, context)

    assert context.template is not None
    assert context.template.id == "school-2026"
    assert not any(issue.code.startswith("missing-template") for issue in issues)


def test_validation_issues_are_deterministically_sorted(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text(
        """# 绪论 {#chap:intro}

### 跳级标题 {#sec:jump}

参见 @fig:missing。
""",
        encoding="utf-8",
    )
    document = parse_markdown(source)

    first = validate_document(document)
    second = validate_document(document)

    assert first == second
    assert [(issue.line, issue.severity, issue.code) for issue in first] == sorted(
        [(issue.line, issue.severity, issue.code) for issue in first],
        key=lambda item: (
            -1 if item[0] is None else item[0],
            {"error": 0, "warning": 1, "info": 2}[item[1]],
            item[2],
        ),
    )


def test_configured_bibliography_is_checked_without_citations(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
render:
  bibliography: "./missing.bib"
---

# 绪论 {#chap:intro}
""",
        encoding="utf-8",
    )
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(parse_markdown(source), context)

    assert any(
        issue.code == "missing-bibliography"
        and issue.target == "./missing.bib"
        for issue in issues
    )


def test_resource_paths_cannot_escape_document_root(tmp_path: Path):
    document_root = tmp_path / "document"
    document_root.mkdir()
    (tmp_path / "secret.png").write_bytes(b"secret")
    (tmp_path / "references.bib").write_text("@book{x}", encoding="utf-8")
    source = document_root / "thesis.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
render:
  bibliography: "../references.bib"
---

# 绪论 {#chap:intro}

::: figure {#fig:secret}
src: "../secret.png"
caption: "越界资源"
:::
""",
        encoding="utf-8",
    )
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(parse_markdown(source), context)
    escaped_targets = {
        issue.target
        for issue in issues
        if issue.code == "resource-path-escape"
    }

    assert escaped_targets == {"../secret.png", "../references.bib"}


def test_validation_loads_bibliography_and_reports_missing_citation_at_source_line(
    tmp_path: Path,
):
    (tmp_path / "references.bib").write_text(
        """@article{known,
  author = {Doe, Jane},
  title = {Known Record},
  journal = {Journal},
  year = {2025}
}
""",
        encoding="utf-8",
    )
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
render:
  bibliography: "./references.bib"
---

# 绪论 {#chap:intro}

已有研究 [@known]，未知研究 [@missing-key]。
""",
        encoding="utf-8",
    )
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(parse_markdown(source), context)

    missing = [issue for issue in issues if issue.code == "missing-citation"]
    assert [(issue.line, issue.target) for issue in missing] == [(12, "missing-key")]
    assert context.bibliography_database is not None
    assert tuple(context.bibliography_database.records) == ("known",)


def test_validation_reports_invalid_bibliography_without_missing_key_noise(
    tmp_path: Path,
):
    (tmp_path / "references.bib").write_text(
        "@misc{bad, author={Doe, Jane}, title={Unsupported}, year={2025}}",
        encoding="utf-8",
    )
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
render:
  bibliography: "./references.bib"
---

# 绪论 {#chap:intro}

引用 [@bad]。
""",
        encoding="utf-8",
    )
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(parse_markdown(source), context)

    invalid = [issue for issue in issues if issue.code == "invalid-bibliography"]
    assert len(invalid) == 1
    assert invalid[0].target == "./references.bib"
    assert invalid[0].details["error_type"] == "UnsupportedBibliographyTypeError"
    assert not any(issue.code == "missing-citation" for issue in issues)
    assert context.bibliography_database is None


def test_reused_validation_context_clears_stale_bibliography_when_rules_change(
    tmp_path: Path,
):
    (tmp_path / "references.bib").write_text(
        """@book{known,
  author = {Doe, Jane},
  title = {Known},
  publisher = {Press},
  year = {2026}
}
""",
        encoding="utf-8",
    )
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
render:
  bibliography: "./references.bib"
---

# 绪论 {#chap:intro}

引用 [@known]。
""",
        encoding="utf-8",
    )
    document = parse_markdown(source)
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    assert validate_document(document, context) == []
    assert context.bibliography_database is not None

    context.rules = ()
    assert validate_document(document, context) == []
    assert context.bibliography_database is None


def test_validation_reports_unsupported_citation_style(tmp_path: Path):
    (tmp_path / "references.bib").write_text(
        """@article{known,
  author = {Doe, Jane},
  title = {Known Record},
  journal = {Journal},
  year = {2025}
}
""",
        encoding="utf-8",
    )
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
render:
  bibliography: "./references.bib"
  citation_style: "apa-7"
---

# 绪论 {#chap:intro}

已有研究 [@known]。
""",
        encoding="utf-8",
    )
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(parse_markdown(source), context)

    unsupported = [issue for issue in issues if issue.code == "unsupported-citation-style"]
    assert len(unsupported) == 1
    assert unsupported[0].severity == "error"
    assert unsupported[0].target == "apa-7"
    assert unsupported[0].line == 13
    assert "GB-T-7714-2025" in unsupported[0].details["supported_styles"]
    # 样式不可解析时不应静默加载并继续渲染。
    assert context.bibliography_database is None
    assert not any(issue.code == "missing-citation" for issue in issues)


def test_validation_accepts_citation_style_alias_and_template_default(tmp_path: Path):
    (tmp_path / "references.bib").write_text(
        """@article{known,
  author = {Doe, Jane},
  title = {Known Record},
  journal = {Journal},
  year = {2025}
}
""",
        encoding="utf-8",
    )
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
render:
  bibliography: "./references.bib"
  citation_style: "gbt7714"
---

# 绪论 {#chap:intro}

已有研究 [@known]。
""",
        encoding="utf-8",
    )
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(parse_markdown(source), context)

    assert not any(issue.code == "unsupported-citation-style" for issue in issues)
    assert context.bibliography_database is not None
