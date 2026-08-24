from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import yaml
from typer.testing import CliRunner

from thesis_forge.cli import app

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "tests" / "fixtures" / "v2-project"


def _write_project(
    root: Path,
    *,
    source: str = "thesis.md",
    template_id: str = "example-university-2026",
    bibliography: str | None = None,
    metadata: bool = True,
) -> Path:
    manifest = {
        "schema": "thesisforge.project.v2",
        "project": {"id": "cli-test-project", "language": "zh-CN"},
        "document": {"source": source},
        "resources": {
            "root": ".",
            "assets": ".",
        },
        "render": {
            "template_id": template_id,
            "citation_style": "GB-T-7714-2025",
        },
        "output": {"directory": "output", "docx": "thesis.docx"},
    }
    if bibliography is not None:
        manifest["resources"]["bibliography"] = bibliography
    if metadata:
        manifest["metadata"] = {
            "title": {"zh": "测试论文"},
            "author": {"name": "测试作者"},
        }
    (root / "thesisforge.yaml").write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return root


runner = CliRunner()


def test_inspect_reports_semantics_without_writing_files(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text(
        """# 绪论 {#chap:intro}

参见[图](#fig:model)，并引用 [@smith2025]。

- 第一项
- 第二项[^note]

[^note]: 脚注正文。
""",
        encoding="utf-8",
    )
    project = _write_project(
        tmp_path,
        source=source.name,
        bibliography="references.bib",
    )
    before = {path.name for path in tmp_path.iterdir()}

    result = runner.invoke(app, ["inspect", str(project)])

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["bibliography"] is None
    assert [block["kind"] for block in payload["blocks"]] == [
        "Heading",
        "Paragraph",
        "ListBlock",
        "FootnoteDefinition",
    ]
    assert [inline["kind"] for inline in payload["inline_content"]] == [
        "Text",
        "Text",
        "CrossReference",
        "Text",
        "Citation",
        "Text",
        "Text",
        "Text",
        "FootnoteReference",
        "Text",
    ]
    assert payload["cross_references"][0]["target"] == "fig:model"
    assert payload["citations"][0]["keys"] == ["smith2025"]
    assert payload["footnote_references"][0]["label"] == "note"
    assert {path.name for path in tmp_path.iterdir()} == before


def test_inspect_rejects_legacy_front_matter_without_traceback(tmp_path: Path):
    source = tmp_path / "broken.md"
    source.write_text("---\nthesis: [\n---\n", encoding="utf-8")
    project = _write_project(tmp_path, source=source.name)

    result = runner.invoke(app, ["inspect", str(project)])

    assert result.exit_code == 2
    assert "解析失败" in result.stdout
    assert "TF-SOURCE-LEGACY-001" in result.stdout
    assert "Traceback" not in result.stdout


def test_inspect_reports_read_error_without_traceback(tmp_path: Path):
    project = _write_project(tmp_path)

    result = runner.invoke(app, ["inspect", str(project)])

    assert result.exit_code == 2
    assert "TF-PROJECT-SOURCE-MISSING" in result.stdout
    assert "Traceback" not in result.stdout


def test_validate_warning_only_exits_zero_and_is_deterministic(tmp_path: Path):
    source = tmp_path / "warning.md"
    source.write_text(
        """# 绪论 {#chap:intro}

### 跳级标题 {#sec:jump}
""",
        encoding="utf-8",
    )
    project = _write_project(tmp_path, source=source.name)
    args = ["validate", str(project)]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == 0, first.stdout
    assert first.stdout == second.stdout
    assert "heading-level-jump" in first.stdout


def test_validate_errors_exit_one_and_reports_all_issues(tmp_path: Path):
    source = tmp_path / "invalid.md"
    source.write_text(
        """# 绪论 {#bad}

参见[图](#fig:missing)。
""",
        encoding="utf-8",
    )
    project = _write_project(tmp_path, source=source.name, metadata=False)

    result = runner.invoke(app, ["validate", str(project)])

    assert result.exit_code == 1
    assert "required-metadata" in result.stdout
    assert "invalid-id-prefix" in result.stdout
    assert "missing-reference" in result.stdout
    assert "Target" in result.stdout
    assert "fig:missing" in result.stdout
    assert "Traceback" not in result.stdout


def test_validate_manifest_template_with_metadata_succeeds(tmp_path: Path):
    source = tmp_path / "valid.md"
    source.write_text(
        """# 绪论 {#chap:intro}
""",
        encoding="utf-8",
    )
    project = _write_project(tmp_path, source=source.name)

    result = runner.invoke(app, ["validate", str(project)])

    assert result.exit_code == 0, result.stdout
    assert "未发现结构性问题" in result.stdout


def test_validate_missing_manifest_template_reports_without_traceback(tmp_path: Path):
    source = tmp_path / "valid.md"
    source.write_text(
        """# 绪论 {#chap:intro}
""",
        encoding="utf-8",
    )
    project = _write_project(
        tmp_path,
        source=source.name,
        template_id="does-not-exist",
    )

    result = runner.invoke(app, ["validate", str(project)])

    assert result.exit_code == 1
    assert "missing-template" in result.stdout
    assert "Traceback" not in result.stdout


def test_validate_reports_source_errors_without_traceback(tmp_path: Path):
    malformed = tmp_path / "broken.md"
    malformed.write_text("---\nthesis: [\n---\n", encoding="utf-8")
    project = _write_project(tmp_path, source=malformed.name)
    missing_project = tmp_path / "missing-project"
    missing_project.mkdir()
    _write_project(missing_project)

    parse_result = runner.invoke(app, ["validate", str(project)])
    read_result = runner.invoke(app, ["validate", str(missing_project)])

    assert parse_result.exit_code == 2
    assert "解析失败" in parse_result.stdout
    assert "TF-SOURCE-LEGACY-001" in parse_result.stdout
    assert "Traceback" not in parse_result.stdout
    assert read_result.exit_code == 2
    assert "TF-PROJECT-SOURCE-MISSING" in read_result.stdout
    assert "Traceback" not in read_result.stdout


def test_validate_template_id_is_independent_of_process_cwd(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["validate", str(PROJECT)])

    assert result.exit_code == 0, result.stdout
    assert "未发现结构性问题" in result.stdout


def test_build_uses_resolved_template_and_writes_editable_docx(tmp_path: Path):
    output = tmp_path / "thesis.docx"

    result = runner.invoke(app, ["build", str(PROJECT), "-o", str(output)])

    assert result.exit_code == 0, result.stdout
    assert "已生成 DOCX" in result.stdout
    assert output.is_file()
    with ZipFile(output) as package:
        document_xml = package.read("word/document.xml").decode("utf-8")
        styles_xml = package.read("word/styles.xml").decode("utf-8")
    assert "[TODO:" not in document_xml
    assert 'w:eastAsia="宋体"' in styles_xml


def test_build_reports_invalid_image_without_traceback(tmp_path: Path):
    image = tmp_path / "broken.png"
    image.write_bytes(b"not-a-real-png")
    source = tmp_path / "thesis.md"
    source.write_text(
        """# 绪论 {#chap:intro}

![损坏图片](broken.png){#fig:broken}
""",
        encoding="utf-8",
    )
    project = _write_project(tmp_path, source=source.name)
    output = tmp_path / "broken.docx"
    output.write_bytes(b"previous-valid-output")

    result = runner.invoke(
        app,
        ["build", str(project), "-o", str(output)],
    )

    assert result.exit_code == 2
    assert "构建失败" in result.stdout
    assert "render" in result.stdout
    assert "无法识别图片" in result.stdout
    assert "Traceback" not in result.stdout
    assert output.read_bytes() == b"previous-valid-output"
    assert list(tmp_path.glob(f".{output.name}.*.tmp.docx")) == []


def test_build_reports_unsupported_latex_without_traceback(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text(
        """# 绪论 {#chap:intro}

$$
\\mathbb{E}[X] = \\mu
$$
{#eq:blackboard}
""",
        encoding="utf-8",
    )
    project = _write_project(tmp_path, source=source.name)
    output = tmp_path / "unsupported-math.docx"
    report_path = tmp_path / "unsupported-math-report.json"

    result = runner.invoke(
        app,
        [
            "build",
            str(project),
            "-o",
            str(output),
            "--report-json",
            str(report_path),
        ],
    )

    assert result.exit_code == 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert "编译停止" in report["message"]
    diagnostic = report["report"]["diagnostics"][0]
    assert diagnostic["code"] == "unsupported-math"
    assert diagnostic["details"]["command"] == r"\mathbb"
    assert "Traceback" not in result.stdout
    assert not output.exists()


def test_build_reports_parse_stage_and_preserves_existing_output(tmp_path: Path):
    source = tmp_path / "broken.md"
    source.write_text("---\nthesis: [\n---\n", encoding="utf-8")
    project = _write_project(tmp_path, source=source.name)
    output = tmp_path / "thesis.docx"
    report_path = tmp_path / "parse-report.json"
    output.write_bytes(b"previous-valid-output")

    result = runner.invoke(
        app,
        [
            "build",
            str(project),
            "-o",
            str(output),
            "--report-json",
            str(report_path),
        ],
    )

    assert result.exit_code == 2
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert "构建失败" in report["message"]
    assert report["report"]["failedStage"] == "parse"
    assert "TF-SOURCE-LEGACY-001" in report["message"]
    assert "Traceback" not in result.stdout
    assert output.read_bytes() == b"previous-valid-output"
    assert list(tmp_path.glob(f".{output.name}.*.tmp.docx")) == []


def test_validate_and_build_local_bibliography_offline(tmp_path: Path):
    (tmp_path / "references.bib").write_text(
        """@article{local2026,
  author = {Doe, Jane},
  title = {Offline Citations},
  journal = {Local Journal},
  year = {2026},
  pages = {1--9}
}
""",
        encoding="utf-8",
    )
    source = tmp_path / "thesis.md"
    source.write_text(
        """# 绪论 {#chap:intro}

正文引用 [@local2026]。

# 参考文献 {#chap:references}
""",
        encoding="utf-8",
    )
    project = _write_project(
        tmp_path,
        source=source.name,
        bibliography="references.bib",
    )
    output = tmp_path / "offline.docx"

    validate_result = runner.invoke(app, ["validate", str(project)])
    build_result = runner.invoke(
        app,
        ["build", str(project), "-o", str(output)],
    )

    assert validate_result.exit_code == 0, validate_result.stdout
    assert build_result.exit_code == 0, build_result.stdout
    with ZipFile(output) as package:
        document_xml = package.read("word/document.xml").decode("utf-8")
    assert "[1]" in document_xml
    assert "DOE J. Offline Citations[J]. Local Journal, 2026: 1-9." in document_xml
    assert "[@local2026]" not in document_xml


def test_validate_reports_unknown_local_citation_without_traceback(tmp_path: Path):
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
        """# 绪论 {#chap:intro}

正文引用 [@missing]。
""",
        encoding="utf-8",
    )
    project = _write_project(
        tmp_path,
        source=source.name,
        bibliography="references.bib",
    )

    result = runner.invoke(app, ["validate", str(project)])

    assert result.exit_code == 1
    assert "missing-citation" in result.stdout


def test_validate_json_option_returns_structured_diagnostics(tmp_path: Path):
    source = tmp_path / "json.md"
    source.write_text("# 绪论\n", encoding="utf-8")
    project = _write_project(
        tmp_path,
        source=source.name,
        metadata=False,
    )

    result = runner.invoke(app, ["validate", str(project), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["issues"][0]["code"] == "required-metadata"
    assert "missing" in result.stdout
    assert "Traceback" not in result.stdout
