from pathlib import Path

from thesis_forge.application.contracts import (
    BuildDiagnosticCategory,
    BuildIntent,
    BuildReportStage,
    BuildSourceRange,
    BuildValidationError,
)
from thesis_forge.core.model import (
    BibliographyConfig,
    BlockQuote,
    Figure,
    Heading,
    SourceLocation,
    Text,
    ThesisDocument,
    ValidationIssue,
)
from thesis_forge.core.parser_backend import create_parser_backend
from thesis_forge.core.validator import ValidationContext, validate_document
from thesis_forge.templates import load_template

PARSER = create_parser_backend()


def _parse(source: str, path: Path) -> ThesisDocument:
    return PARSER.parse_text(source, source_path=path)


def test_missing_cross_reference(tmp_path: Path):
    source = tmp_path / "thesis.md"
    document = _parse("# 绪论\n\n如[图](#fig:missing)所示。\n", source)
    issues = validate_document(document)
    assert any(x.code == "missing-reference" for x in issues)


def test_duplicate_id(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 第一章 {#chap:x}\n\n# 第二章 {#chap:x}\n", encoding="utf-8")
    issues = validate_document(
        _parse(source.read_text(encoding="utf-8"), source)
    )
    assert any(x.code == "duplicate-id" for x in issues)


def test_duplicate_id_validation_uses_nested_document_index(tmp_path: Path):
    first = Heading(
        id="sec:duplicate",
        level=1,
        inlines=[Text(value="第一处")],
        location=SourceLocation(
            line=3,
            column=1,
            end_line=3,
            end_column=5,
            source_file="thesis.md",
        ),
    )
    nested_duplicate = Heading(
        id="sec:duplicate",
        level=2,
        inlines=[Text(value="第二处")],
        location=SourceLocation(
            line=9,
            column=2,
            end_line=9,
            end_column=6,
            source_file="thesis.md",
        ),
    )
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[first, BlockQuote(children=(nested_duplicate,))],
    )

    duplicate_issues = [
        issue for issue in validate_document(document) if issue.code == "duplicate-id"
    ]

    assert len(duplicate_issues) == 1
    assert duplicate_issues[0].line == 9
    assert duplicate_issues[0].target == "sec:duplicate"
    assert duplicate_issues[0].details == {
        "object_id": "sec:duplicate",
        "related_message": "首次定义：sec:duplicate",
        "source_file": "thesis.md",
        "source_line": 9,
        "source_column": 2,
        "source_end_line": 9,
        "source_end_column": 6,
        "related_file": "thesis.md",
        "related_line": 3,
        "related_column": 1,
        "related_end_line": 3,
        "related_end_column": 5,
    }


def test_duplicate_id_build_report_preserves_canonical_locations(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text(
        "# 第一章 {#chap:x}\n\n# 第二章 {#chap:x}\n",
        encoding="utf-8",
    )
    issues = tuple(
        issue
        for issue in validate_document(
            _parse(source.read_text(encoding="utf-8"), source)
        )
        if issue.code == "duplicate-id"
    )

    report = BuildValidationError(issues).to_report(
        build_id="build-duplicate",
        intent=BuildIntent.PUBLISH,
        source_file="thesis.md",
    )

    assert len(report.diagnostics) == 1
    diagnostic = report.diagnostics[0]
    assert diagnostic.id == "validation-1"
    assert diagnostic.category is BuildDiagnosticCategory.SEMANTIC
    assert diagnostic.code == "TF-SEMANTIC-DUPLICATE-ID"
    assert diagnostic.stage is BuildReportStage.VALIDATE
    assert diagnostic.source == BuildSourceRange(
        file="thesis.md",
        start_line=3,
        end_line=3,
    )
    assert diagnostic.related_locations[0].source == BuildSourceRange(
        file="thesis.md",
        start_line=1,
        end_line=1,
    )
    assert diagnostic.related_locations[0].message == "首次定义：chap:x"
    assert diagnostic.details["object_id"] == "chap:x"
    assert diagnostic.details["source_line"] == 3
    assert diagnostic.details["related_line"] == 1


def test_locationless_duplicate_build_report_keeps_unique_ids_and_file_ranges(
    tmp_path: Path,
):
    document = ThesisDocument(
        source_path=tmp_path / "thesis.md",
        blocks=[
            Heading(id="sec:duplicate"),
            Heading(id="sec:duplicate"),
            Heading(id="sec:duplicate"),
        ],
    )
    issues = tuple(
        issue
        for issue in validate_document(document)
        if issue.code == "duplicate-id"
    )

    report = BuildValidationError(issues).to_report(
        build_id="build-locationless-duplicate",
        intent=BuildIntent.LIVE_PREVIEW,
        source_file="thesis.md",
    )

    assert [diagnostic.id for diagnostic in report.diagnostics] == [
        "validation-1",
        "validation-2",
    ]
    assert len({diagnostic.id for diagnostic in report.diagnostics}) == 2
    assert all(
        diagnostic.source == BuildSourceRange(file="thesis.md")
        for diagnostic in report.diagnostics
    )
    assert all(
        diagnostic.related_locations[0].source == BuildSourceRange(file="thesis.md")
        for diagnostic in report.diagnostics
    )


def test_validation_context_can_replace_default_rules(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论 {#chap:intro}\n", encoding="utf-8")
    document = _parse(source.read_text(encoding="utf-8"), source)

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
    document = _parse(
        """# 绪论 {#bad}

参见[图](#fig:missing)，并引用 [@smith2025]。

![错误前缀](missing.png){#fig:figure}
""",
        source,
    )
    document.blocks.append(
        Figure(
            id="chap:figure",
            src="missing.png",
            caption_inlines=(Text(value="错误前缀"),),
        )
    )

    issues = validate_document(document)
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
        """# 绪论 {#chap:intro}

![模型](model.png){#fig:model}
""",
        encoding="utf-8",
    )
    context = ValidationContext(template=load_template(template_path))

    issues = validate_document(
        _parse(source.read_text(encoding="utf-8"), source),
        context,
    )

    assert any(
        issue.code == "missing-template-style" and issue.target == "figure"
        for issue in issues
    )


def test_validation_context_resolves_manifest_template_id(tmp_path: Path):
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
    project_root = tmp_path / "project"
    project_root.mkdir()
    source = project_root / "thesis.md"
    source.write_text("# 绪论 {#chap:intro}\n", encoding="utf-8")
    (project_root / "thesisforge.yaml").write_text(
        """schema: thesisforge.project.v2
project:
  id: template-fixture
  language: zh-CN
document:
  source: thesis.md
render:
  template_id: school-2026
""",
        encoding="utf-8",
    )
    document = PARSER.parse_file(source)

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

参见[图](#fig:missing)。
""",
        encoding="utf-8",
    )
    document = _parse(source.read_text(encoding="utf-8"), source)

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
    document = _parse("# 绪论 {#chap:intro}\n", source)
    document.bibliography = BibliographyConfig(path="./missing.bib")
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(document, context)

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
    document = _parse(
        "# 绪论 {#chap:intro}\n\n![越界资源](../secret.png){#fig:secret}\n",
        source,
    )
    document.bibliography = BibliographyConfig(path="../references.bib")
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(document, context)
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
    document = _parse(
        "# 绪论 {#chap:intro}\n\n已有研究 [@known]，未知研究 [@missing-key]。\n",
        source,
    )
    document.bibliography = BibliographyConfig(path="./references.bib")
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(document, context)

    missing = [issue for issue in issues if issue.code == "missing-citation"]
    assert [(issue.line, issue.target) for issue in missing] == [(3, "missing-key")]
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
    document = _parse("# 绪论 {#chap:intro}\n\n引用 [@bad]。\n", source)
    document.bibliography = BibliographyConfig(path="./references.bib")
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(document, context)

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
    document = _parse("# 绪论 {#chap:intro}\n\n引用 [@known]。\n", source)
    document.metadata = {
        "thesis": {"title": "测试论文"},
        "author": {"name": "测试作者"},
    }
    document.bibliography = BibliographyConfig(path="./references.bib")
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
    document = _parse("# 绪论 {#chap:intro}\n\n已有研究 [@known]。\n", source)
    document.bibliography = BibliographyConfig(
        path="./references.bib",
        citation_style="apa-7",
    )
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(document, context)

    unsupported = [issue for issue in issues if issue.code == "unsupported-citation-style"]
    assert len(unsupported) == 1
    assert unsupported[0].severity == "error"
    assert unsupported[0].target == "apa-7"
    assert unsupported[0].line == 3
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
    document = _parse("# 绪论 {#chap:intro}\n\n已有研究 [@known]。\n", source)
    document.bibliography = BibliographyConfig(
        path="./references.bib",
        citation_style="gbt7714",
    )
    context = ValidationContext(
        template=load_template("templates/base/bachelor.yaml"),
    )

    issues = validate_document(document, context)

    assert not any(issue.code == "unsupported-citation-style" for issue in issues)
    assert context.bibliography_database is not None
