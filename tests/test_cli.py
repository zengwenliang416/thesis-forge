from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from typer.testing import CliRunner

from thesis_forge.cli import app

runner = CliRunner()


def test_inspect_reports_semantics_without_writing_files(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
render:
  bibliography: "./references.bib"
  citation_style: "GB-T-7714-2025"
---

# 绪论 {#chap:intro}

参见 @fig:model，并引用 [@smith2025]。

- 第一项
- 第二项[^note]

[^note]: 脚注正文。
""",
        encoding="utf-8",
    )
    before = {path.name for path in tmp_path.iterdir()}

    result = runner.invoke(app, ["inspect", str(source)])

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["bibliography"]["path"] == "./references.bib"
    assert [block["kind"] for block in payload["blocks"]] == [
        "Heading",
        "Paragraph",
        "ListBlock",
        "FootnoteDefinition",
    ]
    assert payload["cross_references"][0]["target"] == "fig:model"
    assert payload["citations"][0]["keys"] == ["smith2025"]
    assert payload["footnote_references"][0]["label"] == "note"
    assert {path.name for path in tmp_path.iterdir()} == before


def test_inspect_reports_parse_error_without_traceback(tmp_path: Path):
    source = tmp_path / "broken.md"
    source.write_text("---\nthesis: [\n---\n", encoding="utf-8")

    result = runner.invoke(app, ["inspect", str(source)])

    assert result.exit_code == 2
    assert "解析失败" in result.stdout
    assert "YAML Front Matter 无效" in result.stdout
    assert "Traceback" not in result.stdout


def test_inspect_reports_read_error_without_traceback(tmp_path: Path):
    source = tmp_path / "missing.md"

    result = runner.invoke(app, ["inspect", str(source)])

    assert result.exit_code == 2
    assert "读取失败" in result.stdout
    assert source.name in result.stdout
    assert "Traceback" not in result.stdout


def test_validate_warning_only_exits_zero_and_is_deterministic(tmp_path: Path):
    source = tmp_path / "warning.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
---

# 绪论 {#chap:intro}

### 跳级标题 {#sec:jump}
""",
        encoding="utf-8",
    )
    args = [
        "validate",
        str(source),
        "--template",
        "templates/base/bachelor.yaml",
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == 0, first.stdout
    assert first.stdout == second.stdout
    assert "heading-level-jump" in first.stdout


def test_validate_errors_exit_one_and_reports_all_issues(tmp_path: Path):
    source = tmp_path / "invalid.md"
    source.write_text(
        """# 绪论 {#bad}

参见 @fig:missing。
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", str(source)])

    assert result.exit_code == 1
    assert "required-metadata" in result.stdout
    assert "missing-template" in result.stdout
    assert "invalid-id-prefix" in result.stdout
    assert "missing-reference" in result.stdout
    assert "Target" in result.stdout
    assert "fig:missing" in result.stdout
    assert "Traceback" not in result.stdout


def test_validate_explicit_template_overrides_missing_metadata_id(tmp_path: Path):
    source = tmp_path / "valid.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
render:
  template_id: does-not-exist
---

# 绪论 {#chap:intro}
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "validate",
            str(source),
            "--template",
            "templates/base/bachelor.yaml",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "未发现结构性问题" in result.stdout


def test_validate_invalid_template_reports_field_path_without_traceback(tmp_path: Path):
    source = tmp_path / "valid.md"
    source.write_text(
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
---

# 绪论 {#chap:intro}
""",
        encoding="utf-8",
    )
    template = tmp_path / "invalid.yaml"
    template.write_text(
        """id: invalid
name: Invalid
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

    result = runner.invoke(
        app,
        ["validate", str(source), "--template", str(template)],
    )

    assert result.exit_code == 1
    assert "invalid-template" in result.stdout
    assert "page.margin.top" in result.stdout
    assert "Traceback" not in result.stdout


def test_validate_reports_source_errors_without_traceback(tmp_path: Path):
    malformed = tmp_path / "broken.md"
    malformed.write_text("---\nthesis: [\n---\n", encoding="utf-8")

    parse_result = runner.invoke(app, ["validate", str(malformed)])
    read_result = runner.invoke(app, ["validate", str(tmp_path / "missing.md")])

    assert parse_result.exit_code == 2
    assert "解析失败" in parse_result.stdout
    assert "Traceback" not in parse_result.stdout
    assert read_result.exit_code == 2
    assert "读取失败" in read_result.stdout
    assert "Traceback" not in read_result.stdout


def test_validate_template_id_is_independent_of_process_cwd(
    tmp_path: Path,
    monkeypatch,
):
    project_root = Path(__file__).resolve().parents[1]
    source = project_root / "examples/bachelor-thesis/thesis.md"
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["validate", str(source)])

    assert result.exit_code == 0, result.stdout
    assert "未发现结构性问题" in result.stdout


def test_build_uses_resolved_template_and_writes_editable_docx(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    source = project_root / "examples/bachelor-thesis/thesis.md"
    output = tmp_path / "thesis.docx"

    result = runner.invoke(app, ["build", str(source), "-o", str(output)])

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
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
---

# 绪论 {#chap:intro}

::: figure {#fig:broken}
src: "./broken.png"
caption: "损坏图片"
:::
""",
        encoding="utf-8",
    )
    output = tmp_path / "broken.docx"
    output.write_bytes(b"previous-valid-output")

    result = runner.invoke(
        app,
        [
            "build",
            str(source),
            "--template",
            "templates/base/bachelor.yaml",
            "-o",
            str(output),
        ],
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
        """---
thesis:
  title: "测试论文"
author:
  name: "测试作者"
---

# 绪论 {#chap:intro}

::: equation {#eq:blackboard}
$$
\\mathbb{E}[X] = \\mu
$$
:::
""",
        encoding="utf-8",
    )
    output = tmp_path / "unsupported-math.docx"

    result = runner.invoke(
        app,
        [
            "build",
            str(source),
            "--template",
            "templates/base/bachelor.yaml",
            "-o",
            str(output),
        ],
    )

    assert result.exit_code == 2
    assert "构建失败" in result.stdout
    assert "Unsupported LaTeX command: \\mathbb" in result.stdout
    assert "Traceback" not in result.stdout
    assert not output.exists()


def test_build_reports_parse_stage_and_preserves_existing_output(tmp_path: Path):
    source = tmp_path / "broken.md"
    source.write_text("---\nthesis: [\n---\n", encoding="utf-8")
    output = tmp_path / "thesis.docx"
    output.write_bytes(b"previous-valid-output")

    result = runner.invoke(app, ["build", str(source), "-o", str(output)])

    assert result.exit_code == 2
    assert "构建失败" in result.stdout
    assert "parse" in result.stdout
    assert "YAML Front Matter 无效" in result.stdout
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
        """---
thesis:
  title: "离线引用"
author:
  name: "测试作者"
render:
  bibliography: "./references.bib"
  citation_style: "GB-T-7714-2025"
---

# 绪论 {#chap:intro}

正文引用 [@local2026]。

# 参考文献 {#chap:references}

::: bibliography
:::
""",
        encoding="utf-8",
    )
    output = tmp_path / "offline.docx"

    validate_result = runner.invoke(
        app,
        [
            "validate",
            str(source),
            "--template",
            "templates/base/bachelor.yaml",
        ],
    )
    build_result = runner.invoke(
        app,
        [
            "build",
            str(source),
            "--template",
            "templates/base/bachelor.yaml",
            "-o",
            str(output),
        ],
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
        """---
thesis:
  title: "未知引用"
author:
  name: "测试作者"
render:
  bibliography: "./references.bib"
---

# 绪论 {#chap:intro}

正文引用 [@missing]。
""",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "validate",
            str(source),
            "--template",
            "templates/base/bachelor.yaml",
        ],
    )

    assert result.exit_code == 1
    assert "missing-citation" in result.stdout
    assert "missing" in result.stdout
    assert "Traceback" not in result.stdout
