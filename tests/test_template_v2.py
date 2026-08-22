"""Template Package v2（ADR-0002 Phase 3 切片）：加载器、单位解析、L1/L2 lint 与 CLI。

正例使用 spike 样例包 `spikes/phase0/docx-template/package-sample/`；
其余用 tmp_path 构造最小包（加载器只读 template.yaml/provenance.yaml，
lint L1 另需 README/provenance/fixtures/minimal 等 §1.1 必需文件）。
"""

from __future__ import annotations

import json
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from thesis_forge.cli import app
from thesis_forge.templates import v2
from thesis_forge.templates.v2 import units
from thesis_forge.templates.v2.package import MAX_INHERITANCE_DEPTH
from thesis_forge.templates.v2.units import (
    CTX_BORDER_WIDTH,
    CTX_FONT_SIZE,
    CTX_INDENT,
    CTX_OVERFLOW_THRESHOLD,
    CTX_PAGE_GEOMETRY,
    CTX_PARENT_WIDTH,
    Length,
    LengthParseError,
    parse_length,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PACKAGE = (
    REPO_ROOT / "spikes" / "phase0" / "docx-template" / "package-sample"
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# fixture 构造辅助
# ---------------------------------------------------------------------------


def _template_data(package_id: str = "demo.pack", **overrides) -> dict:
    """最小合法 template.yaml 数据（schema_version 2）。"""
    data = {
        "schema_version": 2,
        "id": package_id,
        "version": "1.0.0",
        "name": "演示模板",
        "compatibility": {
            "thesisforge": ">=0.0.0",
            "document_types": ["master_thesis"],
        },
        "page": {
            "margin": {"top": "25mm", "bottom": "25mm", "inner": "30mm", "outer": "25mm"}
        },
        "fonts": {"body": {"east_asia": "宋体", "latin": "Times New Roman"}},
        "styles": {
            "paragraph": {"body": "TF Body"},
            # headings level2–4 默认引用同级 token，故最小包也需声明 1–4 级
            "heading": {
                "1": "TF Heading 1",
                "2": "TF Heading 2",
                "3": "TF Heading 3",
                "4": "TF Heading 4",
            },
        },
        "regions": {"order": ["main"]},
    }
    data.update(overrides)
    return data


def _write_template_yaml(package_dir: Path, data: dict) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "template.yaml").write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


_PROVENANCE_YAML = """school:
  name: 演示大学
  official_document:
    title: 演示大学学位论文撰写规范
    version: "2026"
    source_type: manual
maintainers:
  - name: 演示维护者
    contact: mailto:maintainer@example.invalid
licenses:
  template_code: Apache-2.0
  school_assets: CC0-1.0
review:
  last_verified: 2026-08-15
  verified_with:
    - LibreOffice 25.x
"""


def _write_docx(
    path: Path,
    *,
    macro: bool = False,
    external_target: str | None = None,
) -> None:
    """写出可通过完整 L3 的最小 OOXML 包；可按需注入宏部件或外部关系。

    L3 完整实现要求：sectPr 存在且页边距与 `_template_data` 的 page 声明一致
    （25/25/30/25mm ↔ 1417/1417/1701/1417 twips）、token 样式（TF Body /
    TF Heading 1-4，outline level 0-3）在 styles.xml 中定义、docDefaults 带
    绝对字号（L4 body 字号检查）。
    """
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        "</Types>"
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1701" '
        'w:header="850" w:footer="992" w:gutter="0"/>'
        "</w:sectPr></w:body></w:document>"
    )
    heading_styles = "".join(
        f'<w:style w:type="paragraph" w:styleId="TFHeading{level}">'
        f'<w:name w:val="TF Heading {level}"/><w:basedOn w:val="TFBody"/>'
        f"<w:pPr><w:outlineLvl w:val=\"{level - 1}\"/></w:pPr>"
        f'<w:rPr><w:sz w:val="32"/></w:rPr></w:style>'
        for level in (1, 2, 3, 4)
    )
    styles = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr><w:sz w:val="24"/></w:rPr></w:rPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="TFBody">'
        '<w:name w:val="TF Body"/><w:basedOn w:val="Normal"/>'
        '<w:rPr><w:sz w:val="24"/></w:rPr></w:style>'
        f"{heading_styles}</w:styles>"
    )
    rels_items = [
        (
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        )
    ]
    if external_target is not None:
        rels_items.append(
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/hyperlink" Target="{external_target}"'
            ' TargetMode="External"/>'
        )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(rels_items)}</Relationships>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
        'officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", styles)
        archive.writestr("word/_rels/document.xml.rels", rels)
        if macro:
            archive.writestr("word/vbaProject.bin", b"fake-macro")


def _write_l1_complete_package(package_dir: Path, data: dict) -> Path:
    """写出满足 §1.1 必需文件的包（供 lint 负例聚焦单一诊断码）。"""
    _write_template_yaml(package_dir, data)
    word = data.get("word") or {}
    _write_docx(package_dir / word.get("reference_docx", "reference.docx"))
    (package_dir / "README.md").write_text(
        "# 演示模板\n\n## 使用说明\n\n略。\n\n## 已知限制\n\n略。\n",
        encoding="utf-8",
    )
    (package_dir / "provenance.yaml").write_text(_PROVENANCE_YAML, encoding="utf-8")
    (package_dir / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## {data['version']}\n\n- 初始版本。\n",
        encoding="utf-8",
    )
    minimal = package_dir / "fixtures" / "minimal"
    minimal.mkdir(parents=True)
    # L5 fixture 使用 canonical v2 source；metadata contract 由 lint 显式定义。
    (minimal / "thesis.md").write_text(
        "# 绪论 {#chap:intro}\n\n正文段落。\n",
        encoding="utf-8",
    )
    return package_dir


def _issue_codes(error: v2.PackageLoadError) -> set[str]:
    return {issue.code for issue in error.issues}


# ---------------------------------------------------------------------------
# 正例：spike 样例包
# ---------------------------------------------------------------------------


def test_sample_package_loads() -> None:
    package = v2.load_package(SAMPLE_PACKAGE)

    assert package.template.id == "hunan-university-of-technology.master.2026.sample"
    assert package.template.version == "0.1.0"
    assert package.reference_docx.is_file()
    assert package.shell_docx is not None and package.shell_docx.is_file()
    assert package.provenance is not None
    assert package.provenance.school.name == "湖南工业大学"
    assert "main" in package.template.regions.order
    assert package.inheritance_chain[0].sha256.startswith("sha256:")


def test_sample_package_lint_clean() -> None:
    report = v2.lint_package(SAMPLE_PACKAGE)

    assert report.levels_run == ("L1", "L2", "L3", "L4", "L5")
    assert report.errors == 0
    assert not report.has_errors
    # 样例包当前的已知 warning（spike 数据的合法漂移，非回归）：
    # tf_bibliography 锚点缺失回退、TF Heading 4 outline level 漂移、
    # verified_with 缺 primary 应用（word）记录
    assert report.warnings == 3
    assert {issue.code for issue in report.issues} == {
        "anchor-fallback",
        "outline-level-mismatch",
        "review-incomplete",
    }


# ---------------------------------------------------------------------------
# schema_version 拒绝策略（§8.3）
# ---------------------------------------------------------------------------


def test_load_rejects_legacy_schema_version(tmp_path: Path) -> None:
    package_dir = tmp_path / "legacy"
    _write_template_yaml(package_dir, _template_data(schema_version=1))

    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(package_dir)

    assert "unsupported-schema-version" in _issue_codes(excinfo.value)
    issue = next(
        issue
        for issue in excinfo.value.issues
        if issue.code == "unsupported-schema-version"
    )
    assert issue.severity == "error"
    assert issue.target == "schema_version"
    assert "migrate" in issue.message  # 指向显式迁移，不 fallback 解释旧模板


def test_load_rejects_newer_schema_version(tmp_path: Path) -> None:
    package_dir = tmp_path / "future"
    _write_template_yaml(package_dir, _template_data(schema_version=3))

    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(package_dir)

    assert "unsupported-schema-version" in _issue_codes(excinfo.value)
    issue = next(
        issue
        for issue in excinfo.value.issues
        if issue.code == "unsupported-schema-version"
    )
    assert "升级" in issue.message


def test_load_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(tmp_path / "does-not-exist")

    assert "missing-package-file" in _issue_codes(excinfo.value)


# ---------------------------------------------------------------------------
# 路径安全（§1.3）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rel", "expected"),
    [
        ("reference.docx", True),
        ("assets/logo.png", True),
        ("../outside.docx", False),
        ("a/../../b.docx", False),
        ("/abs/path.docx", False),
        ("C:/win/path.docx", False),
        ("C:\\win\\path.docx", False),
        ("back\\slash.docx", False),
        ("a//b.docx", False),
        ("a/./b.docx", False),
        ("", False),
    ],
)
def test_is_safe_package_path(rel: str, expected: bool) -> None:
    assert v2.is_safe_package_path(rel) is expected


@pytest.mark.parametrize(
    "field",
    [
        {"word": {"reference_docx": "../outside.docx"}},
        {"word": {"shell_docx": "/abs/shell.docx"}},
        {"bibliography": {"style_file": "citations/../../escape.csl"}},
        {"layouts": {"cover": "../escape.yaml"}},
    ],
    ids=["reference_docx", "shell_docx", "style_file", "layouts"],
)
def test_load_rejects_path_traversal(tmp_path: Path, field: dict) -> None:
    package_dir = tmp_path / "traversal"
    _write_template_yaml(package_dir, _template_data(**field))

    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(package_dir)

    assert "package-path-unsafe" in _issue_codes(excinfo.value)


def test_resolve_within_package_rejects_symlink_escape(tmp_path: Path) -> None:
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    outside = tmp_path / "outside.docx"
    outside.write_bytes(b"not-in-package")
    link = package_dir / "linked.docx"
    link.symlink_to(outside)

    assert v2.resolve_within_package(package_dir, "linked.docx") is None
    assert v2.resolve_within_package(package_dir, "../outside.docx") is None


# ---------------------------------------------------------------------------
# 单位解析（§2.2/§2.3）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "ctx", "value", "unit"),
    [
        ("25mm", CTX_PAGE_GEOMETRY, "25", "mm"),
        ("2.5cm", CTX_PAGE_GEOMETRY, "2.5", "cm"),
        ("12pt", CTX_FONT_SIZE, "12", "pt"),
        ("1in", CTX_PAGE_GEOMETRY, "1", "in"),
        ("2em", CTX_INDENT, "2", "em"),
        ("100%", CTX_PARENT_WIDTH, "100", "%"),
        # overflow.threshold 允许 >100%（§2.3 诊断延迟触发）
        ("120%", CTX_OVERFLOW_THRESHOLD, "120", "%"),
        (" 25mm ", CTX_PAGE_GEOMETRY, "25", "mm"),  # 允许首尾空白
    ],
)
def test_parse_length_valid(raw, ctx, value: str, unit: str) -> None:
    length = parse_length(raw, ctx)

    assert length == Length(value=Decimal(value), unit=unit)


@pytest.mark.parametrize(
    "raw",
    [
        "25",  # 裸数字
        25,  # 非字符串
        "25 mm",  # 内部空格
        "+25mm",  # 符号
        "2.5e1mm",  # 科学计数法
        "mm",  # 缺数值
        "25px",  # 未知单位
        "",
    ],
)
def test_parse_length_rejects_lexical_errors(raw) -> None:
    with pytest.raises(LengthParseError):
        parse_length(raw, CTX_PAGE_GEOMETRY)


def test_parse_length_none_literal_only_in_border_context() -> None:
    assert parse_length("none", CTX_BORDER_WIDTH) is None
    with pytest.raises(LengthParseError):
        parse_length("none", CTX_PAGE_GEOMETRY)


def test_parse_length_context_unit_matrix() -> None:
    with pytest.raises(LengthParseError, match="不允许用于该字段"):
        parse_length("2em", CTX_PAGE_GEOMETRY)  # 页面几何仅绝对单位
    with pytest.raises(LengthParseError, match="不允许用于该字段"):
        parse_length("50%", CTX_INDENT)  # 缩进不接受 %
    with pytest.raises(LengthParseError, match="不允许用于该字段"):
        parse_length("2em", CTX_FONT_SIZE)  # body 字号必须绝对（pt）
    with pytest.raises(LengthParseError, match="大于 0"):
        parse_length("0pt", CTX_FONT_SIZE)  # positive 上下文
    with pytest.raises(LengthParseError, match="不得超过 100%"):
        parse_length("101%", CTX_PARENT_WIDTH)


def test_parse_length_border_width_bounds() -> None:
    # §2.3：线宽换算后 ∈ [0.25pt, 12pt]
    with pytest.raises(LengthParseError, match="0.25pt"):
        parse_length("0.1pt", CTX_BORDER_WIDTH)
    with pytest.raises(LengthParseError, match="12pt"):
        parse_length("13pt", CTX_BORDER_WIDTH)
    assert parse_length("1.5pt", CTX_BORDER_WIDTH) == Length(Decimal("1.5"), "pt")


def test_length_absolute_conversions() -> None:
    assert Length(Decimal(1), "in").to_points() == Decimal(72)
    # ROUND_HALF_UP 取整到 twips，避免 Decimal 精度尾巴
    assert Length(Decimal("25.4"), "mm").to_twips() == 1440
    assert Length(Decimal("2.54"), "cm").to_twips() == 1440
    assert str(Length(Decimal("2.50"), "em")) == "2.5em"
    with pytest.raises(LengthParseError):
        Length(Decimal(2), "em").to_points()  # 相对单位无绝对值


def test_units_report_field_path() -> None:
    with pytest.raises(LengthParseError, match="page.margin.top"):
        parse_length("25", CTX_PAGE_GEOMETRY, field_path="page.margin.top")


def test_schema_surfaces_unit_error_as_invalid_template(tmp_path: Path) -> None:
    package_dir = tmp_path / "bad-unit"
    _write_template_yaml(
        package_dir,
        _template_data(page={"margin": {"top": "25", "bottom": "25mm",
                                        "inner": "30mm", "outer": "25mm"}}),
    )

    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(package_dir)

    assert "invalid-template" in _issue_codes(excinfo.value)
    targets = {issue.target for issue in excinfo.value.issues}
    assert any(target and "margin" in target for target in targets)


# ---------------------------------------------------------------------------
# extends 继承（§4.3 决策 D-2）
# ---------------------------------------------------------------------------


def _write_chain_package(
    roots: Path,
    dirname: str,
    package_id: str,
    version: str,
    **overrides,
) -> Path:
    package_dir = roots / dirname
    _write_template_yaml(
        package_dir, _template_data(package_id, version=version, **overrides)
    )
    return package_dir


def test_extends_merges_whitelisted_sections(tmp_path: Path) -> None:
    roots = tmp_path / "roots"
    _write_chain_package(
        roots,
        "base",
        "demo.base",
        "1.0.0",
        toc={"depth": 2, "title": "目 录"},
        regions={"order": ["cover", "main", "bibliography"]},
    )
    # 同 id 的更高版本候选：继承解析必须选满足区间的最高版本（§4.3 第 5 条）
    _write_chain_package(
        roots,
        "base-newer",
        "demo.base",
        "1.2.0",
        toc={"depth": 3, "title": "目 录"},
        regions={"order": ["cover", "main", "bibliography"]},
    )
    child_dir = tmp_path / "child"
    _write_template_yaml(
        child_dir,
        _template_data(
            "demo.child",
            extends={"id": "demo.base", "version": ">=1.0.0"},
            page={"margin": {"top": "20mm"}},
            regions={"order": ["main"]},
        ),
    )

    package = v2.load_package(child_dir, search_roots=(roots,))

    # header/compatibility 不继承：保留子包自身声明
    assert package.template.id == "demo.child"
    # 白名单节继承：toc 来自父包，且取最高版本 1.2.0 的 depth
    assert package.template.toc.depth == 3
    assert package.section_sources["toc"] == "demo.base"
    # map 深合并：子覆盖 top、其余 margin 键继承父包
    assert package.template.page.margin.top == units.Length(Decimal(20), "mm")
    assert package.template.page.margin.bottom == units.Length(Decimal(25), "mm")
    # list 一律 replace：子包 order 替换而非拼接父包
    assert package.template.regions.order == ["main"]
    assert package.section_sources["regions"] == "demo.child"
    # 继承链记录：子在前、父在后，均带确定性内容哈希
    assert [entry.id for entry in package.inheritance_chain] == ["demo.child", "demo.base"]
    assert package.inheritance_chain[1].path == (roots / "base-newer").resolve()
    assert package.inheritance_chain[1].version == "1.2.0"
    assert all(
        entry.sha256.startswith("sha256:") for entry in package.inheritance_chain
    )


def test_extends_sha256_lock(tmp_path: Path) -> None:
    roots = tmp_path / "roots"
    base_dir = _write_chain_package(roots, "base", "demo.base", "1.0.0")

    locked_dir = tmp_path / "locked"
    _write_template_yaml(
        locked_dir,
        _template_data(
            "demo.locked",
            extends={
                "id": "demo.base",
                "version": ">=1.0.0",
                "sha256": v2.package_content_hash(base_dir),
            },
        ),
    )
    package = v2.load_package(locked_dir, search_roots=(roots,))
    assert package.template.id == "demo.locked"

    tampered_dir = tmp_path / "tampered"
    _write_template_yaml(
        tampered_dir,
        _template_data(
            "demo.tampered",
            extends={
                "id": "demo.base",
                "version": ">=1.0.0",
                "sha256": "sha256:" + "0" * 64,
            },
        ),
    )
    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(tampered_dir, search_roots=(roots,))
    assert "hash-mismatch" in _issue_codes(excinfo.value)


def test_extends_detects_cycle(tmp_path: Path) -> None:
    roots = tmp_path / "roots"
    _write_chain_package(
        roots, "pkg-a", "demo.a", "1.0.0",
        extends={"id": "demo.b", "version": ">=1.0.0"},
    )
    _write_chain_package(
        roots, "pkg-b", "demo.b", "1.0.0",
        extends={"id": "demo.a", "version": ">=1.0.0"},
    )

    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(roots / "pkg-a", search_roots=(roots,))

    assert "template-inheritance-cycle" in _issue_codes(excinfo.value)


def test_extends_enforces_depth_limit(tmp_path: Path) -> None:
    roots = tmp_path / "roots"
    chain_length = MAX_INHERITANCE_DEPTH + 1
    for index in range(chain_length):
        overrides = {}
        if index + 1 < chain_length:
            overrides["extends"] = {
                "id": f"demo.p{index + 1}",
                "version": ">=1.0.0",
            }
        _write_chain_package(
            roots, f"pkg-{index}", f"demo.p{index}", "1.0.0", **overrides
        )

    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(roots / "pkg-0", search_roots=(roots,))

    assert "inheritance-depth-exceeded" in _issue_codes(excinfo.value)


def test_extends_reports_unresolvable_parent(tmp_path: Path) -> None:
    roots = tmp_path / "roots"
    _write_chain_package(roots, "base", "demo.base", "1.0.0")

    missing_dir = tmp_path / "missing"
    _write_template_yaml(
        missing_dir,
        _template_data(
            "demo.orphan", extends={"id": "demo.ghost", "version": ">=1.0.0"}
        ),
    )
    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(missing_dir, search_roots=(roots,))
    assert "missing-template" in _issue_codes(excinfo.value)

    unsatisfied_dir = tmp_path / "unsatisfied"
    _write_template_yaml(
        unsatisfied_dir,
        _template_data(
            "demo.unsatisfied", extends={"id": "demo.base", "version": ">=9.0.0"}
        ),
    )
    with pytest.raises(v2.PackageLoadError) as excinfo:
        v2.load_package(unsatisfied_dir, search_roots=(roots,))
    assert "unsatisfied-parent-version" in _issue_codes(excinfo.value)


# ---------------------------------------------------------------------------
# L1 宏 / 外部关系扫描（§5.5）
# ---------------------------------------------------------------------------


def test_lint_l1_detects_macro(tmp_path: Path) -> None:
    package_dir = tmp_path / "macro-pack"
    data = _template_data("demo.macro", word={"reference_docx": "reference.docx"})
    _write_l1_complete_package(package_dir, data)
    _write_docx(package_dir / "reference.docx", macro=True)

    report = v2.lint_package(package_dir)

    macro_issues = [issue for issue in report.issues if issue.code == "macro-detected"]
    assert macro_issues, "应报告 macro-detected"
    assert macro_issues[0].severity == "error"
    assert report.has_errors


def test_lint_l1_detects_external_relationship(tmp_path: Path) -> None:
    package_dir = tmp_path / "external-pack"
    data = _template_data("demo.external", word={"reference_docx": "reference.docx"})
    _write_l1_complete_package(package_dir, data)
    _write_docx(
        package_dir / "reference.docx", external_target="https://evil.example/track"
    )

    report = v2.lint_package(package_dir)

    external = [
        issue for issue in report.issues if issue.code == "external-relationship"
    ]
    assert external, "应报告 external-relationship"
    assert external[0].severity == "error"
    assert "forbid" in external[0].message


def test_lint_l1_external_relationship_allowlist(tmp_path: Path) -> None:
    package_dir = tmp_path / "allowlist-pack"
    data = _template_data(
        "demo.allowlist",
        word={
            "reference_docx": "reference.docx",
            "external_relationships": "allowlist",
            "external_relationship_allowlist": ["https://cdn.example.com"],
        },
    )
    _write_l1_complete_package(package_dir, data)
    _write_docx(
        package_dir / "reference.docx",
        external_target="https://cdn.example.com/fonts/font.woff",
    )

    report = v2.lint_package(package_dir)

    external = [
        issue for issue in report.issues if issue.code == "external-relationship"
    ]
    assert external, "白名单命中应报告 info 记录"
    assert all(issue.severity == "info" for issue in external)
    assert report.errors == 0


def test_lint_l1_missing_required_files(tmp_path: Path) -> None:
    package_dir = tmp_path / "bare"
    _write_template_yaml(package_dir, _template_data("demo.bare"))

    report = v2.lint_package(package_dir, level="L1")

    codes = {issue.code for issue in report.issues}
    assert "missing-package-file" in codes  # reference.docx / fixtures
    assert "provenance-missing" in codes
    assert "readme-missing" in codes
    assert report.levels_run == ("L1",)


# ---------------------------------------------------------------------------
# CLI 接线
# ---------------------------------------------------------------------------


def test_cli_template_lint_clean_package() -> None:
    result = runner.invoke(app, ["template", "lint", str(SAMPLE_PACKAGE)])

    assert result.exit_code == 0, result.stdout
    # 样例包带 3 个已知 warning（见 test_sample_package_lint_clean），以表格输出
    assert "outline-level-mismatch" in result.stdout


def test_cli_template_lint_json_output() -> None:
    result = runner.invoke(
        app, ["template", "lint", str(SAMPLE_PACKAGE), "--json"]
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["errors"] == 0
    assert payload["warnings"] == 3
    assert payload["levels_run"] == ["L1", "L2", "L3", "L4", "L5"]
    assert {issue["code"] for issue in payload["issues"]} == {
        "anchor-fallback",
        "outline-level-mismatch",
        "review-incomplete",
    }


def test_cli_template_lint_single_level() -> None:
    result = runner.invoke(
        app, ["template", "lint", str(SAMPLE_PACKAGE), "--level", "L1", "--json"]
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["levels_run"] == ["L1"]


def test_cli_template_lint_invalid_package_exits_one(tmp_path: Path) -> None:
    package_dir = tmp_path / "legacy"
    _write_template_yaml(package_dir, _template_data(schema_version=1))

    result = runner.invoke(app, ["template", "lint", str(package_dir), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    codes = {issue["code"] for issue in payload["issues"]}
    assert "unsupported-schema-version" in codes
    assert payload["levels_run"] == ["L1"]  # L1 error 后更高层跳过（§6）


def test_cli_template_lint_missing_directory_exits_two(tmp_path: Path) -> None:
    result = runner.invoke(app, ["template", "lint", str(tmp_path / "missing")])

    assert result.exit_code == 2
    assert "读取失败" in result.stdout


def test_cli_template_lint_unknown_level_exits_two() -> None:
    result = runner.invoke(
        app, ["template", "lint", str(SAMPLE_PACKAGE), "--level", "L9"]
    )

    assert result.exit_code == 2
    assert "参数错误" in result.stdout


def test_cli_template_inspect_outputs_structure() -> None:
    result = runner.invoke(app, ["template", "inspect", str(SAMPLE_PACKAGE)])

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["format"] == "template-package-v2"
    assert payload["id"] == "hunan-university-of-technology.master.2026.sample"
    assert payload["version"] == "0.1.0"
    assert payload["inheritance_chain"][0]["sha256"].startswith("sha256:")
    assert "resolved" not in payload


def test_cli_template_inspect_resolved() -> None:
    result = runner.invoke(
        app, ["template", "inspect", str(SAMPLE_PACKAGE), "--resolved"]
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert "resolved" in payload
    assert payload["resolved"]["schema_version"] == 2
    assert payload["resolved"]["regions"]["order"][0] == "cover"
    assert "section_sources" in payload


def test_cli_template_inspect_invalid_package_exits_two(tmp_path: Path) -> None:
    package_dir = tmp_path / "broken"
    _write_template_yaml(package_dir, _template_data(schema_version=1))

    result = runner.invoke(app, ["template", "inspect", str(package_dir)])

    assert result.exit_code == 2
    assert "加载失败" in result.stdout
    assert "unsupported-schema-version" in result.stdout
