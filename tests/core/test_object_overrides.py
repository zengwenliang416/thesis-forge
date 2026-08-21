from __future__ import annotations

from pathlib import Path

from thesis_forge.core.model import ValidationIssue
from thesis_forge.core.parser import parse_markdown
from thesis_forge.core.validator import validate_document

OVERRIDE_CODES = {"orphan-layout-override", "layout-override-type-mismatch"}

THESIS_MD = r"""
# 绪论 {#chap:introduction}

::: figure {#fig:model}
src: assets/model.png
caption: 模型总体结构
:::

::: equation {#eq:loss}
$$
L=-\sum_i y_i \log \hat y_i
$$
:::

::: table {#tbl:result}
caption: 模型实验结果

| 指标 | 实验组 |
| --- | ---: |
| 准确率 | 96.2% |

:::
""".lstrip()

MANIFEST = """
schema: thesisforge.project.v2
project:
  id: layout-override-fixture
  language: zh-CN
document:
  source: thesis.md
resources:
  root: .
  assets: assets
render:
  template_id: example-university-2026
""".lstrip()


def write_project(tmp_path: Path, *, layout: str = "") -> Path:
    root = tmp_path / "project"
    (root / "assets").mkdir(parents=True)
    (root / "assets" / "model.png").write_bytes(b"png")
    (root / "thesis.md").write_text(THESIS_MD, encoding="utf-8")
    (root / "thesisforge.yaml").write_text(MANIFEST + layout, encoding="utf-8")
    return root


def override_issues(tmp_path: Path, *, layout: str = "") -> list[ValidationIssue]:
    root = write_project(tmp_path, layout=layout)
    document = parse_markdown(root / "thesis.md")
    issues = validate_document(document)
    return [issue for issue in issues if issue.code in OVERRIDE_CODES]


def test_valid_figure_width_override_produces_no_issues(tmp_path: Path) -> None:
    issues = override_issues(
        tmp_path,
        layout="layout:\n  objects:\n    fig:model:\n      width: 85%\n",
    )

    assert issues == []


def test_orphan_figure_override_is_an_error(tmp_path: Path) -> None:
    issues = override_issues(
        tmp_path,
        layout="layout:\n  objects:\n    fig:missing:\n      width: 85%\n",
    )

    assert len(issues) == 1
    issue = issues[0]
    assert issue.code == "orphan-layout-override"
    assert issue.severity == "error"
    assert issue.target == "fig:missing"
    assert issue.details["field"] == "width"


def test_width_override_on_equation_is_type_mismatch(tmp_path: Path) -> None:
    issues = override_issues(
        tmp_path,
        layout="layout:\n  objects:\n    eq:loss:\n      width: 85%\n",
    )

    assert len(issues) == 1
    issue = issues[0]
    assert issue.code == "layout-override-type-mismatch"
    assert issue.severity == "error"
    assert issue.target == "eq:loss"
    assert issue.details == {"field": "width", "expected": "fig", "actual": "eq"}


def test_width_override_on_table_is_type_mismatch(tmp_path: Path) -> None:
    issues = override_issues(
        tmp_path,
        layout="layout:\n  objects:\n    tbl:result:\n      width: 85%\n",
    )

    assert len(issues) == 1
    issue = issues[0]
    assert issue.code == "layout-override-type-mismatch"
    assert issue.severity == "error"
    assert issue.target == "tbl:result"
    assert issue.details == {"field": "width", "expected": "fig", "actual": "tbl"}


def test_orphan_override_with_non_figure_prefix_reports_orphan(tmp_path: Path) -> None:
    issues = override_issues(
        tmp_path,
        layout="layout:\n  objects:\n    tbl:missing:\n      width: 85%\n",
    )

    assert len(issues) == 1
    issue = issues[0]
    assert issue.code == "orphan-layout-override"
    assert issue.severity == "error"
    assert issue.target == "tbl:missing"


def test_projectless_document_silences_layout_override_rule(tmp_path: Path) -> None:
    source = tmp_path / "thesis.md"
    source.write_text(THESIS_MD, encoding="utf-8")

    issues = validate_document(parse_markdown(source))

    assert not any(issue.code in OVERRIDE_CODES for issue in issues)


def test_multiple_overrides_report_only_orphans_sorted(tmp_path: Path) -> None:
    issues = override_issues(
        tmp_path,
        layout=(
            "layout:\n"
            "  objects:\n"
            "    fig:model:\n"
            "      width: 85%\n"
            "    fig:zbogus:\n"
            "      width: 50%\n"
            "    fig:abogus:\n"
            "      width: 25%\n"
        ),
    )

    assert [issue.target for issue in issues] == ["fig:abogus", "fig:zbogus"]
    assert all(issue.code == "orphan-layout-override" for issue in issues)
    assert all(issue.severity == "error" for issue in issues)
