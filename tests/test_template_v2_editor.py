"""Template Package v2 PackageEditor 合并与 L3/L4/L5 lint 测试（ADR-0002 本切片）。

- 合并正例：`spikes/phase0/docx-template/package-sample/` 的 shell.docx +
  examples/complete-thesis 经完整管线（parse → validate → compile → render，
  不走 finalizer）产出的 compiled.docx；断言 openxml_validate 全过、sections/
  页码格式保留、图片 rel 有效、书签配对、双跑字节一致、台账结构完整。
- 合并负例：缺 tf_body 锚点、宏、外部关系（§5.5 合并兜底拦截）。
- 边界落地：部件级 rels 递归（合成 header 内嵌图片）、footnotes 双侧 w:id
  重映射（向 shell 注入既有脚注部件）、numbering 双侧 numId 重映射（真实
  数据触发：shell styles.xml 引用 numId）。
- lint L3/L4/L5 正反例：在样例包副本上做定点变异。
"""

from __future__ import annotations

import copy
import json
import posixpath
import shutil
import zipfile
from pathlib import Path

import pytest
import yaml
from lxml import etree

from thesis_forge.application import preview_service
from thesis_forge.renderers.docx import DocxRenderer
from thesis_forge.templates import v2
from thesis_forge.templates.v2 import lint as lint_mod
from thesis_forge.templates.v2.package_editor import (
    PackageEditor,
    PackageMergeError,
    PackageView,
    merge_into_shell,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PACKAGE = REPO_ROOT / "spikes" / "phase0" / "docx-template" / "package-sample"
SHELL = SAMPLE_PACKAGE / "shell.docx"
SOURCE = REPO_ROOT / "examples" / "complete-thesis" / "thesis.md"
HUT_YAML = (
    REPO_ROOT / "templates" / "schools" / "hunan-university-of-technology" / "master-2026.yaml"
)

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _r(tag: str) -> str:
    return f"{{{R_NS}}}{tag}"


# 1x1 透明 PNG（确定性字节）
_PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080600000"
    "01f15c4890000000d49444154789c6260f8cfc0c70700012100774001"
    "850000000049454e44ae426082"
)


# ---------------------------------------------------------------------------
# 通用辅助
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def compiled_docx(tmp_path_factory) -> Path:
    """完整管线编译 complete-thesis（HUT 模板，不走 finalizer）。"""
    output = tmp_path_factory.mktemp("compiled") / "compiled.docx"
    preview = preview_service(SOURCE, template_path=HUT_YAML)
    assert not preview.errors, preview.errors
    assert preview.plan is not None
    DocxRenderer().render(preview.plan, output)
    return output


@pytest.fixture()
def package_copy(tmp_path: Path) -> Path:
    dest = tmp_path / "pkg"
    shutil.copytree(SAMPLE_PACKAGE, dest)
    return dest


def _validate(path: Path) -> dict:
    validate_docx = lint_mod._load_openxml_validate()
    assert validate_docx is not None
    return validate_docx(path)


def _rewrite_docx(src: Path, dst: Path, transforms: dict) -> None:
    """复制 docx 并对指定部件做变换；变换返回 None 表示删除该部件。"""
    with zipfile.ZipFile(src) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    for name, transform in transforms.items():
        result = transform(entries.get(name)) if callable(transform) else transform
        if result is None:
            entries.pop(name, None)
        else:
            entries[name] = result
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in entries.items():
            out.writestr(name, data)


def _edit_template_yaml(package_dir: Path, mutate) -> None:
    path = package_dir / "template.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def _issue_codes(report) -> set[str]:
    return {issue.code for issue in report.issues}


# ---------------------------------------------------------------------------
# PackageEditor 合并：正例
# ---------------------------------------------------------------------------


def test_merge_openxml_valid(compiled_docx: Path, tmp_path: Path) -> None:
    output = tmp_path / "merged.docx"
    merge_into_shell(SHELL, compiled_docx, output)

    report = _validate(output)
    assert report["ok"], [c for c in report["checks"] if c["status"] != "pass"]
    assert report["summary"]["passed"] == report["summary"]["total"]


def test_merge_preserves_sections_and_page_number_formats(
    compiled_docx: Path, tmp_path: Path
) -> None:
    output = tmp_path / "merged.docx"
    merge_into_shell(SHELL, compiled_docx, output)

    merged = PackageView(output)
    document = merged.xml("word/document.xml")
    sections = list(document.iter(_w("sectPr")))
    fmts = []
    for sect_pr in sections:
        pg_num = sect_pr.find(_w("pgNumType"))
        fmts.append(
            None
            if pg_num is None
            else {"fmt": pg_num.get(_w("fmt")), "start": pg_num.get(_w("start"))}
        )
    # shell 前置（lowerRoman）→ compiled 前置（upperRoman，内部节保留原样）→ shell 正文
    assert fmts == [
        {"fmt": "lowerRoman", "start": "1"},
        {"fmt": "upperRoman", "start": "1"},
        {"fmt": "decimal", "start": "1"},
    ]


def test_merge_image_relationships_valid(compiled_docx: Path, tmp_path: Path) -> None:
    output = tmp_path / "merged.docx"
    ledger = merge_into_shell(SHELL, compiled_docx, output)

    merged = PackageView(output)
    rels = merged.rels("word/document.xml")
    image_targets = [v["Target"] for v in rels.values() if v["Type"].endswith("/image")]
    resolved = {posixpath.normpath(posixpath.join("word", t)) for t in image_targets}
    # shell 占位 logo + compiled 插图，双双可解析
    assert len(image_targets) == 2
    assert not (resolved - set(merged.parts))
    document = merged.xml("word/document.xml")
    embed_rids = {el.get(_r("embed")) for el in document.iter() if el.get(_r("embed"))}
    assert embed_rids <= set(rels)
    # rId 全部重映射：映射表非空且新 rId 不与 shell 既有冲突
    assert ledger.rid_mapping
    assert set(ledger.rid_mapping.values()) <= set(rels)


def test_merge_bookmarks_and_content(compiled_docx: Path, tmp_path: Path) -> None:
    output = tmp_path / "merged.docx"
    merge_into_shell(SHELL, compiled_docx, output)

    merged = PackageView(output)
    document = merged.xml("word/document.xml")
    names = [el.get(_w("name")) for el in document.iter(_w("bookmarkStart"))]
    assert names.count("tf_toc") == 1  # toc 锚点保留
    assert "tf_body" not in names  # body 锚点已消费（书签对一并移除）
    starts = [el.get(_w("id")) for el in document.iter(_w("bookmarkStart"))]
    ends = [el.get(_w("id")) for el in document.iter(_w("bookmarkEnd"))]
    assert sorted(starts) == sorted(ends)  # 配对

    text = "".join(document.itertext())
    for keyword in ("原创性声明", "【姓名占位】", "摘要", "绪论", "参考文献", "致谢"):
        assert keyword in text


def test_merge_footnotes_and_numbering_defined(compiled_docx: Path, tmp_path: Path) -> None:
    output = tmp_path / "merged.docx"
    merge_into_shell(SHELL, compiled_docx, output)

    merged = PackageView(output)
    document = merged.xml("word/document.xml")
    footnotes = merged.xml("word/footnotes.xml")
    defined_footnotes = {el.get(_w("id")) for el in footnotes.iter(_w("footnote"))}
    used_footnotes = {el.get(_w("id")) for el in document.iter(_w("footnoteReference"))}
    assert used_footnotes <= defined_footnotes

    numbering = merged.xml("word/numbering.xml")
    defined_nums = {el.get(_w("numId")) for el in numbering.iter(_w("num"))}
    used_nums = {
        el.get(_w("val"))
        for el in document.iter(_w("numId"))
        if el.get(_w("val")) and el.get(_w("val")) != "0"
    }
    assert used_nums <= defined_nums


def test_merge_numbering_double_side_remap(compiled_docx: Path, tmp_path: Path) -> None:
    """shell styles.xml 引用 numId（python-docx 默认列表样式）→ 走双侧重映射。"""
    output = tmp_path / "merged.docx"
    ledger = merge_into_shell(SHELL, compiled_docx, output)

    assert ledger.numbering["shell_num_ids_in_use"], "样例 shell 应引用 numId"
    assert "平移" in ledger.numbering["action"]
    assert ledger.numbering["num_id_map"]
    # 重映射后 compiled 的 numId 不与 shell 冲突且全部有定义
    merged = PackageView(output)
    numbering = merged.xml("word/numbering.xml")
    num_ids = [el.get(_w("numId")) for el in numbering.iter(_w("num"))]
    assert len(num_ids) == len(set(num_ids))
    assert _validate(output)["ok"]


def test_merge_deterministic_byte_identical(compiled_docx: Path, tmp_path: Path) -> None:
    first = tmp_path / "a.docx"
    second = tmp_path / "b.docx"
    ledger_a = merge_into_shell(SHELL, compiled_docx, first)
    ledger_b = merge_into_shell(SHELL, compiled_docx, second)

    assert first.read_bytes() == second.read_bytes()
    dict_a, dict_b = ledger_a.to_dict(), ledger_b.to_dict()
    dict_a.pop("output_docx")
    dict_b.pop("output_docx")
    assert dict_a == dict_b


def test_merge_ledger_structure(compiled_docx: Path, tmp_path: Path) -> None:
    output = tmp_path / "merged.docx"
    editor = PackageEditor.from_package(v2.load_package(SAMPLE_PACKAGE))
    ledger = editor.merge(compiled_docx, output)

    data = ledger.to_dict()
    assert data["anchors"]["body"]["status"] == "consumed"
    assert data["anchors"]["toc"]["status"] == "preserved"
    assert data["anchors"]["bibliography"]["status"] == "absent"
    assert data["selection"]["dropped_compiled_final_sectPr"] is True
    assert data["selection"]["imported_children"] > 0
    assert data["carried_relationships"], "应有搬运的 relationship 记录"
    assert all(
        {"src_rid", "new_rid", "type", "src_part", "dst_part", "renamed"}
        <= set(entry)
        for entry in data["carried_relationships"]
    )
    assert data["styles"]["policy"].startswith("token 对齐后 shell-wins")
    assert data["settings"]["applied"]["updateFields"] is True
    assert "theme1.xml" in data["not_merged"]
    assert "fontTable.xml" in data["not_merged"]
    # 台账可 JSON 序列化（落 build manifest 的前提）
    json.dumps(data, ensure_ascii=False)


def test_merge_shell_wins_style_conflict(compiled_docx: Path, tmp_path: Path) -> None:
    """D-3：Normal 等无 token 映射的冲突样式保留 shell 定义并记 warning。"""
    output = tmp_path / "merged.docx"
    ledger = merge_into_shell(SHELL, compiled_docx, output)

    shell = PackageView(SHELL)
    merged = PackageView(output)

    def normal_style(view: PackageView):
        styles = view.xml("word/styles.xml")
        return next(
            el for el in styles.iter(_w("style")) if el.get(_w("styleId")) == "Normal"
        )

    assert etree.tostring(normal_style(merged)) == etree.tostring(normal_style(shell))
    conflicts = {entry["style_id"]: entry for entry in ledger.styles["conflicts"]}
    assert "Normal" in conflicts
    assert conflicts["Normal"]["policy"] == "shell-wins"
    assert conflicts["Normal"]["token_aligned"] is False
    unmapped = [i for i in ledger.issues if i.code == "style-conflict-unmapped"]
    assert unmapped and all(i.severity == "warning" for i in unmapped)


def test_merge_does_not_mutate_inputs(compiled_docx: Path, tmp_path: Path) -> None:
    shell_before = SHELL.read_bytes()
    compiled_before = compiled_docx.read_bytes()
    merge_into_shell(SHELL, compiled_docx, tmp_path / "merged.docx")
    assert SHELL.read_bytes() == shell_before
    assert compiled_docx.read_bytes() == compiled_before


# ---------------------------------------------------------------------------
# PackageEditor 合并：负例与边界
# ---------------------------------------------------------------------------


def test_merge_missing_body_anchor_rejected(compiled_docx: Path, tmp_path: Path) -> None:
    broken_shell = tmp_path / "shell-no-anchor.docx"

    def remove_body_anchor(content: bytes) -> bytes:
        root = etree.fromstring(content)
        for el in list(root.iter(_w("bookmarkStart"))):
            if el.get(_w("name")) == "tf_body":
                el.getparent().remove(el)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    _rewrite_docx(SHELL, broken_shell, {"word/document.xml": remove_body_anchor})

    with pytest.raises(PackageMergeError) as excinfo:
        merge_into_shell(broken_shell, compiled_docx, tmp_path / "out.docx")
    assert excinfo.value.code == "missing-body-anchor"


def test_merge_rejects_macro(compiled_docx: Path, tmp_path: Path) -> None:
    macro_compiled = tmp_path / "compiled-macro.docx"
    _rewrite_docx(compiled_docx, macro_compiled, {"word/vbaProject.bin": b"fake"})

    with pytest.raises(PackageMergeError) as excinfo:
        merge_into_shell(SHELL, macro_compiled, tmp_path / "out.docx")
    assert excinfo.value.code == "macro-detected"


def test_merge_rejects_external_relationship(compiled_docx: Path, tmp_path: Path) -> None:
    external_compiled = tmp_path / "compiled-external.docx"

    def inject_external(content: bytes) -> bytes:
        root = etree.fromstring(content)
        rel = etree.SubElement(root, f"{{{PR_NS}}}Relationship")
        rel.set("Id", "rId999")
        rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink")
        rel.set("Target", "https://evil.example/track")
        rel.set("TargetMode", "External")
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    _rewrite_docx(
        compiled_docx, external_compiled, {"word/_rels/document.xml.rels": inject_external}
    )

    with pytest.raises(PackageMergeError) as excinfo:
        merge_into_shell(SHELL, external_compiled, tmp_path / "out.docx")
    assert excinfo.value.code == "external-relationship"


def _write_synthetic_compiled(path: Path) -> None:
    """合成 compiled.docx：封面分节符 + 插图段落 + 内嵌 header 引用的内部节
    （header 内再嵌图片，触发部件级 rels 递归搬运）。"""
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Types xmlns="{CT_NS}">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="png" ContentType="image/png"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/header1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
        "</Types>"
    )
    blip = lambda rid: (
        f'<w:r><w:drawing><a:blip xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
        f' r:embed="{rid}"/></w:drawing></w:r>'
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}"><w:body>'
        "<w:p><w:r><w:t>封面</w:t></w:r></w:p>"
        f'<w:p><w:pPr><w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr></w:pPr></w:p>'
        f"<w:p>{blip('rId10')}</w:p>"
        "<w:p><w:r><w:t>正文</w:t></w:r></w:p>"
        f'<w:p><w:pPr><w:sectPr>'
        f'<w:headerReference w:type="default" r:id="rId11"/>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        "</w:sectPr></w:pPr></w:p>"
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>'
        "</w:body></w:document>"
    )
    doc_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Relationships xmlns="{PR_NS}">'
        '<Relationship Id="rId10" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>'
        '<Relationship Id="rId11" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>'
        "</Relationships>"
    )
    header = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<w:hdr xmlns:w="{W_NS}" xmlns:r="{R_NS}">'
        f"<w:p>{blip('rId1')}</w:p></w:hdr>"
    )
    header_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Relationships xmlns="{PR_NS}">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image2.png"/>'
        "</Relationships>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Relationships xmlns="{PR_NS}">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        out.writestr("[Content_Types].xml", content_types)
        out.writestr("_rels/.rels", root_rels)
        out.writestr("word/document.xml", document)
        out.writestr("word/_rels/document.xml.rels", doc_rels)
        out.writestr("word/header1.xml", header)
        out.writestr("word/_rels/header1.xml.rels", header_rels)
        out.writestr("word/media/image1.png", _PNG_1PX)
        out.writestr("word/media/image2.png", _PNG_1PX)


def test_merge_part_level_rels_recursion(tmp_path: Path) -> None:
    """SPIKE §3.6 边界落地：header 内嵌图片被递归搬运且内部 r:id 有效。"""
    compiled = tmp_path / "synthetic.docx"
    _write_synthetic_compiled(compiled)
    output = tmp_path / "merged.docx"
    ledger = merge_into_shell(SHELL, compiled, output)

    assert _validate(output)["ok"]
    merged = PackageView(output)
    carried = {entry["src_part"]: entry for entry in ledger.carried_relationships}
    assert "word/header1.xml" in carried
    header_dst = carried["word/header1.xml"]["dst_part"]
    assert header_dst != "word/header1.xml"  # 与 shell 既有 header 冲突 → 重命名
    # header 的内部 rels 被搬运且 Target 指向重命名后的图片部件
    header_rels_name = f"word/_rels/{posixpath.basename(header_dst)}.rels"
    assert header_rels_name in merged.parts
    inner = merged.rels(header_dst)
    inner_target = posixpath.normpath(posixpath.join("word", inner["rId1"]["Target"]))
    assert inner_target in merged.parts
    assert inner_target.startswith("word/media/")
    # header XML 内 r:embed 仍指向其部件级 rId（部件内命名空间独立）
    header_root = merged.xml(header_dst)
    embeds = {el.get(_r("embed")) for el in header_root.iter() if el.get(_r("embed"))}
    assert embeds == {"rId1"}


def test_merge_footnotes_double_side_remap(compiled_docx: Path, tmp_path: Path) -> None:
    """SPIKE §3.7 边界落地：shell 已有 footnotes 部件时按 w:id 重映射合并。"""
    shell_with_footnotes = tmp_path / "shell-footnotes.docx"
    footnotes_part = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<w:footnotes xmlns:w="{W_NS}">'
        '<w:footnote w:type="separator" w:id="-1"><w:p/></w:footnote>'
        '<w:footnote w:type="continuationSeparator" w:id="0"><w:p/></w:footnote>'
        '<w:footnote w:id="1"><w:p><w:r><w:t>shell 既有脚注</w:t></w:r></w:p></w:footnote>'
        "</w:footnotes>"
    )

    def add_ct_override(content: bytes) -> bytes:
        root = etree.fromstring(content)
        override = etree.SubElement(root, f"{{{CT_NS}}}Override")
        override.set("PartName", "/word/footnotes.xml")
        override.set(
            "ContentType",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml",
        )
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    def add_rel(content: bytes) -> bytes:
        root = etree.fromstring(content)
        rel = etree.SubElement(root, f"{{{PR_NS}}}Relationship")
        rel.set("Id", "rId100")
        rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes")
        rel.set("Target", "footnotes.xml")
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    def add_reference(content: bytes) -> bytes:
        root = etree.fromstring(content)
        body = root.find(_w("body"))
        anchor = next(
            el.getparent()
            for el in body.iter(_w("bookmarkStart"))
            if el.get(_w("name")) == "tf_body"
        )
        paragraph = etree.fromstring(
            f'<w:p xmlns:w="{W_NS}"><w:r><w:footnoteReference w:id="1"/></w:r></w:p>'
        )
        anchor.addprevious(paragraph)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    _rewrite_docx(
        SHELL,
        shell_with_footnotes,
        {
            "[Content_Types].xml": add_ct_override,
            "word/_rels/document.xml.rels": add_rel,
            "word/document.xml": add_reference,
            "word/footnotes.xml": footnotes_part.encode("utf-8"),
        },
    )

    output = tmp_path / "merged.docx"
    ledger = merge_into_shell(shell_with_footnotes, compiled_docx, output)

    assert ledger.footnotes["action"].startswith("merged with w:id remap")
    assert ledger.footnotes["id_map"] == {"1": "2"}  # shell 已占用 id=1
    merged = PackageView(output)
    footnotes = merged.xml("word/footnotes.xml")
    defined = {el.get(_w("id")) for el in footnotes.iter(_w("footnote"))}
    assert {"-1", "0", "1", "2"} <= defined
    document = merged.xml("word/document.xml")
    used = {el.get(_w("id")) for el in document.iter(_w("footnoteReference"))}
    assert used == {"1", "2"}  # shell 的 1 + compiled 重映射的 2
    assert used <= defined
    assert _validate(output)["ok"]


def test_merge_from_package_without_shell_rejected(tmp_path: Path, compiled_docx: Path) -> None:
    (tmp_path / "template.yaml").write_text(
        (SAMPLE_PACKAGE / "template.yaml").read_text(encoding="utf-8").replace(
            "  shell_docx: shell.docx\n", ""
        ),
        encoding="utf-8",
    )
    resolved = v2.load_package(tmp_path)
    assert resolved.shell_docx is None
    with pytest.raises(PackageMergeError) as excinfo:
        PackageEditor.from_package(resolved)
    assert excinfo.value.code == "missing-package-file"


# ---------------------------------------------------------------------------
# lint L3：正例（样例包全层）与定点变异负例
# ---------------------------------------------------------------------------


def test_lint_l3_missing_token_style(package_copy: Path) -> None:
    _edit_template_yaml(
        package_copy, lambda data: data["styles"]["paragraph"].__setitem__("body", "No Such Style")
    )
    report = v2.lint_package(package_copy, level="L3")
    missing = [i for i in report.issues if i.code == "missing-token-style"]
    assert missing and missing[0].severity == "error"
    assert missing[0].target == "styles.paragraph.body"


def test_lint_l3_style_type_mismatch(package_copy: Path) -> None:
    # "TF Body" 已是 paragraph token，会被 schema 跨类别重名规则拦截；
    # 用非 token 的段落样式 "Quote" 触达 L3 的类型比对
    _edit_template_yaml(
        package_copy,
        lambda data: data["styles"]["character"].__setitem__("code", "Quote"),
    )
    report = v2.lint_package(package_copy, level="L3")
    mismatch = [i for i in report.issues if i.code == "style-type-mismatch"]
    assert mismatch and mismatch[0].severity == "error"


def test_lint_l3_anchor_duplicate(package_copy: Path) -> None:
    def duplicate_anchor(content: bytes) -> bytes:
        root = etree.fromstring(content)
        body = root.find(_w("body"))
        anchor = next(
            el.getparent()
            for el in body.iter(_w("bookmarkStart"))
            if el.get(_w("name")) == "tf_body"
        )
        clone = copy.deepcopy(anchor)
        for el in clone.iter():
            if el.get(_w("id")) is not None:
                el.set(_w("id"), "7001")
        anchor.addprevious(clone)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    _rewrite_docx(
        package_copy / "shell.docx",
        package_copy / "shell.docx",
        {"word/document.xml": duplicate_anchor},
    )
    report = v2.lint_package(package_copy, level="L3")
    duplicates = [i for i in report.issues if i.code == "anchor-duplicate"]
    assert duplicates and duplicates[0].severity == "error"


def test_lint_l3_missing_body_anchor(package_copy: Path) -> None:
    def remove_anchor(content: bytes) -> bytes:
        root = etree.fromstring(content)
        for el in list(root.iter(_w("bookmarkStart"))):
            if el.get(_w("name")) == "tf_body":
                el.getparent().remove(el)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    _rewrite_docx(
        package_copy / "shell.docx",
        package_copy / "shell.docx",
        {"word/document.xml": remove_anchor},
    )
    report = v2.lint_package(package_copy, level="L3")
    missing = [i for i in report.issues if i.code == "missing-body-anchor"]
    assert missing and missing[0].severity == "error"


def test_lint_l3_undeclared_anchor_warning(package_copy: Path) -> None:
    def add_anchor(content: bytes) -> bytes:
        root = etree.fromstring(content)
        body = root.find(_w("body"))
        anchor = next(
            el.getparent()
            for el in body.iter(_w("bookmarkStart"))
            if el.get(_w("name")) == "tf_body"
        )
        clone = copy.deepcopy(anchor)
        for el in clone.iter():
            if el.get(_w("name")) == "tf_body":
                el.set(_w("name"), "tf_extra")
            if el.get(_w("id")) is not None:
                el.set(_w("id"), "7002")
        anchor.addprevious(clone)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    _rewrite_docx(
        package_copy / "shell.docx",
        package_copy / "shell.docx",
        {"word/document.xml": add_anchor},
    )
    report = v2.lint_package(package_copy, level="L3")
    undeclared = [i for i in report.issues if i.code == "anchor-undeclared"]
    assert undeclared and undeclared[0].severity == "warning"


def test_lint_l3_sectpr_child_order(package_copy: Path) -> None:
    def break_order(content: bytes) -> bytes:
        root = etree.fromstring(content)
        sect_pr = next(root.iter(_w("sectPr")))
        pg_num = sect_pr.find(_w("pgNumType"))
        sect_pr.remove(pg_num)
        sect_pr.append(pg_num)  # pgNumType 移到 cols/docGrid 之后
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    _rewrite_docx(
        package_copy / "shell.docx",
        package_copy / "shell.docx",
        {"word/document.xml": break_order},
    )
    report = v2.lint_package(package_copy, level="L3")
    invalid = [i for i in report.issues if i.code == "invalid-word-asset"]
    assert any("顺序" in i.message for i in invalid)


def test_lint_l3_template_reference_drift(package_copy: Path) -> None:
    _edit_template_yaml(
        package_copy,
        lambda data: data["page"]["margin"].__setitem__("top", "20mm"),
    )
    report = v2.lint_package(package_copy, level="L3")
    drift = [i for i in report.issues if i.code == "template-reference-drift"]
    assert any(i.target == "page.margin.top" for i in drift)
    assert all(i.severity == "warning" for i in drift)


def test_lint_l3_section_policy_mismatch(package_copy: Path) -> None:
    _edit_template_yaml(
        package_copy,
        lambda data: data["sections"]["main"]["page_number"].__setitem__(
            "format", "roman-lower"
        ),
    )
    report = v2.lint_package(package_copy, level="L3")
    mismatch = [i for i in report.issues if i.code == "section-policy-mismatch"]
    assert mismatch and all(i.severity == "warning" for i in mismatch)


# ---------------------------------------------------------------------------
# lint L4：语义检查正负例
# ---------------------------------------------------------------------------


def test_lint_l4_missing_citation_style(package_copy: Path) -> None:
    _edit_template_yaml(
        package_copy,
        lambda data: data.__setitem__("bibliography", {"provider": "default"}),
    )
    report = v2.lint_package(package_copy, level="L4")
    missing = [i for i in report.issues if i.code == "missing-template-asset"]
    assert any(i.target == "bibliography.style_file" for i in missing)


def test_lint_l4_floating_placement_capability(package_copy: Path) -> None:
    _edit_template_yaml(
        package_copy,
        lambda data: data.__setitem__("figures", {"placement": "floating"}),
    )
    report = v2.lint_package(package_copy, level="L4")
    capability = [i for i in report.issues if i.code == "unsupported-capability"]
    assert any(i.target == "figures.placement" for i in capability)


def test_lint_l4_ineffective_toc_level(package_copy: Path) -> None:
    _edit_template_yaml(
        package_copy,
        lambda data: data.__setitem__(
            "toc", {"depth": 2, "levels": {3: {"leader": "dots"}}}
        ),
    )
    report = v2.lint_package(package_copy, level="L4")
    ineffective = [i for i in report.issues if i.code == "ineffective-config"]
    assert any(i.target == "toc.levels.3" for i in ineffective)


def test_lint_l4_cover_heading_numbering_ineffective(package_copy: Path) -> None:
    def mutate(data: dict) -> None:
        data["regions"]["cover"] = {"heading_numbering": True}

    _edit_template_yaml(package_copy, mutate)
    report = v2.lint_package(package_copy, level="L4")
    ineffective = [i for i in report.issues if i.code == "ineffective-config"]
    assert any("cover" in (i.target or "") for i in ineffective)


def test_lint_l2_page_number_contradiction(package_copy: Path) -> None:
    def mutate(data: dict) -> None:
        data["sections"]["main"]["page_number"] = {"display": False, "format": "decimal"}

    _edit_template_yaml(package_copy, mutate)
    report = v2.lint_package(package_copy, level="L2")
    invalid = [i for i in report.issues if i.code == "invalid-template"]
    assert invalid and report.has_errors


def test_lint_l4_numbering_source_present_positive() -> None:
    """正例：样例包 numbering.chapter.source=heading_1 且级别 1 已声明，无报错。"""
    report = v2.lint_package(SAMPLE_PACKAGE, level="L4")
    assert "numbering-source-missing" not in _issue_codes(report)


# ---------------------------------------------------------------------------
# lint L5：fixture 冒烟正负例
# ---------------------------------------------------------------------------


def test_lint_l5_sample_fixture_passes() -> None:
    report = v2.lint_package(SAMPLE_PACKAGE, level="L5")
    assert report.errors == 0
    assert "fixture-build-failed" not in _issue_codes(report)


def test_lint_l5_fixture_without_markdown_fails(package_copy: Path) -> None:
    (package_copy / "fixtures" / "minimal" / "thesis.md").unlink()
    report = v2.lint_package(package_copy, level="L5")
    failed = [i for i in report.issues if i.code == "fixture-build-failed"]
    assert failed and failed[0].severity == "error"


def test_lint_l5_fixture_validator_error_fails(package_copy: Path) -> None:
    (package_copy / "fixtures" / "minimal" / "dup.md").write_text(
        "---\nthesis:\n  title: 示例\nauthor:\n  name: 张三\n---\n\n"
        "# 绪论 {#chap:dup}\n\n# 重复 {#chap:dup}\n",
        encoding="utf-8",
    )
    report = v2.lint_package(package_copy, level="L5")
    failed = [i for i in report.issues if i.code == "fixture-build-failed"]
    assert any("duplicate-id" in i.message for i in failed)


def test_lint_l5_expected_manifest_checked(package_copy: Path) -> None:
    expected_dir = package_copy / "expected"
    expected_dir.mkdir()
    (expected_dir / "manifest.json").write_text(
        json.dumps({"version": 1, "builds": [
            {"fixture": "fixtures/minimal", "output": "minimal.docx"}
        ]}),
        encoding="utf-8",
    )
    report = v2.lint_package(package_copy, level="L5")
    skipped = [i for i in report.issues if i.code == "fixture-assertions-skipped"]
    assert skipped and skipped[0].severity == "info"

    (expected_dir / "manifest.json").write_text(
        json.dumps({"version": 2}), encoding="utf-8"
    )
    report = v2.lint_package(package_copy, level="L5")
    invalid = [i for i in report.issues if i.code == "invalid-template"]
    assert any("manifest.json" in (i.target or "") for i in invalid)


# ---------------------------------------------------------------------------
# CLI：单层层级
# ---------------------------------------------------------------------------


def test_cli_template_lint_level_l5() -> None:
    from typer.testing import CliRunner

    from thesis_forge.cli import app

    result = CliRunner().invoke(
        app, ["template", "lint", str(SAMPLE_PACKAGE), "--level", "L5", "--json"]
    )
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["levels_run"] == ["L5"]
    assert payload["errors"] == 0
