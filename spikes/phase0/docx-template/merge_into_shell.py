#!/usr/bin/env python3
"""Phase 0 spike：把编译产物的正文 XML 按锚点合并进 shell.docx（路线②核心实证）。

流程：
1. 用项目完整管线（parse → validate → compile → DocxRenderer.render，不走 finalizer
   的 LibreOffice refresh）编译 examples/complete-thesis（HUT 模板）→ output/compiled.docx；
2. 在 OPC/ZIP 层级用 lxml 合并：取 compiled 正文首个分节符（封面节）之后的全部节点
   （丢弃其 body 级 final sectPr，由 shell 的 main sectPr 接管正文节），
   插入 shell.docx 的 tf_body 书签处并移除锚点段落；
3. 显式搬运清单（本 spike 的实证重点）：
   - relationships：imported 节点引用的 r:id/r:embed 全部重映射为新 rId，
     目标部件（media/header/footer/footnotes）复制进包并重命名避免冲突；
   - styles：按「被引用 + basedOn/next/link 闭包」最小搬运，同名冲突 compiled 胜出并记录；
   - numbering.xml：shell 正文无 numId 引用时整体替换，否则为未实现边界（显式报错）；
   - footnotes：shell 无 footnotes 部件时整体搬运 + Content Types/relationship 登记；
   - settings/theme/fontTable/docProps：保留 shell 的，不合并（记录为 ADR 决策点）。

产出：
- output/compiled.docx  管线直出（无 finalizer）
- output/merged.docx    合并产物
- output/merge-report.json  搬运清单 + 冲突记录 + 断言结果

运行（仓库根目录）：.venv/bin/python spikes/phase0/docx-template/merge_into_shell.py
"""

from __future__ import annotations

import copy
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spike_common import (
    NS,
    OUTPUT_DIR,
    PACKAGE_DIR,
    REPO_ROOT,
    ensure_dirs,
    run_openxml_validate,
    soffice_smoke,
    summarize_validation,
)

from docforge.application import preview_service
from docforge.renderers.docx import DocxRenderer

SOURCE = REPO_ROOT / "examples" / "complete-thesis" / "thesis.md"
HUT_YAML = (
    REPO_ROOT / "templates" / "schools" / "hunan-university-of-technology" / "master-2026.yaml"
)
SHELL_PATH = PACKAGE_DIR / "shell.docx"
COMPILED_PATH = OUTPUT_DIR / "compiled.docx"
MERGED_PATH = OUTPUT_DIR / "merged.docx"
REPORT_PATH = OUTPUT_DIR / "merge-report.json"

BODY_ANCHOR = "tf_body"
TOC_ANCHOR = "tf_toc"

RID_ATTRS = ("id", "embed", "link")  # r: 命名空间下需要重映射的属性名
STYLE_REF_TAGS = ("pStyle", "rStyle", "tblStyle")
STYLE_LINK_TAGS = ("basedOn", "next", "link")


def _w(tag: str) -> str:
    return f"{{{NS['w']}}}{tag}"


def _r(tag: str) -> str:
    return f"{{{NS['r']}}}{tag}"


def _pr(tag: str) -> str:
    return f"{{{NS['pr']}}}{tag}"


def _ct(tag: str) -> str:
    return f"{{{NS['ct']}}}{tag}"


def _serialize(root) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _rels_name_for(part_path: str) -> str:
    """word/header2.xml → word/_rels/header2.xml.rels"""
    directory, _, name = part_path.rpartition("/")
    return f"{directory}/_rels/{name}.rels"


def compile_thesis() -> Path:
    """完整管线编译 complete-thesis（不走 finalizer 的 LibreOffice refresh）。"""
    preview = preview_service(SOURCE, template_path=HUT_YAML)
    if preview.errors:
        raise SystemExit(f"编译前校验失败: {preview.errors}")
    assert preview.plan is not None
    DocxRenderer().render(preview.plan, COMPILED_PATH)
    return COMPILED_PATH


class PackageView:
    """DOCX 包的只读视图：原始字节 + 按需解析的 XML。"""

    def __init__(self, path: Path) -> None:
        self.path = path
        with zipfile.ZipFile(path) as archive:
            self.parts = {name: archive.read(name) for name in archive.namelist()}
        self._xml_cache: dict[str, etree._Element] = {}

    def xml(self, name: str) -> etree._Element:
        if name not in self._xml_cache:
            self._xml_cache[name] = etree.fromstring(self.parts[name])
        return self._xml_cache[name]

    def rels(self, part_path: str) -> dict[str, dict[str, str]]:
        """某个部件的 relationship 表：Id → {Type, Target, TargetMode}。"""
        rels_name = _rels_name_for(part_path)
        result: dict[str, dict[str, str]] = {}
        if rels_name not in self.parts:
            return result
        for rel in self.xml(rels_name):
            result[rel.get("Id")] = {
                "Type": rel.get("Type", ""),
                "Target": rel.get("Target", ""),
                "TargetMode": rel.get("TargetMode", "Internal"),
            }
        return result


def find_anchor_paragraph(body, name: str):
    """返回书签所在段落及其在 body 中的下标；锚点缺失为阻断错误。"""
    for bookmark in body.iter(_w("bookmarkStart")):
        if bookmark.get(_w("name")) == name:
            paragraph = bookmark.getparent()
            assert paragraph.tag == _w("p"), f"锚点 {name} 不在段落级"
            return paragraph, list(body).index(paragraph)
    raise SystemExit(f"shell.docx 缺少锚点书签 {name}（spec：缺失 body anchor 为阻断错误）")


def select_imported_children(compiled_body) -> tuple[list, dict]:
    """选取 compiled 正文中「首个分节符段落之后」的全部节点（深拷贝）。

    compiled 结构（实证）：[封面段落..., 封面分节符, 前置内容..., 前置分节符,
    正文内容..., final sectPr]。封面/声明由 shell 持有，故丢弃封面区与其分节符；
    final sectPr 由 shell 的 main sectPr 接管，同样不搬运。
    """
    children = list(compiled_body)
    cover_break_index = next(
        i
        for i, child in enumerate(children)
        if child.tag == _w("p") and child.find(f"{_w('pPr')}/{_w('sectPr')}") is not None
    )
    imported = [copy.deepcopy(child) for child in children[cover_break_index + 1 :]]
    dropped_final_sectpr = imported[-1].tag == _w("sectPr")
    if dropped_final_sectpr:
        imported = imported[:-1]
    info = {
        "compiled_body_children": len(children),
        "dropped_cover_region_children": cover_break_index + 1,
        "dropped_compiled_final_sectPr": dropped_final_sectpr,
        "imported_children": len(imported),
    }
    return imported, info


class CarryContext:
    """搬运上下文：目标包的新部件、新 relationship、内容类型登记与搬运台账。"""

    def __init__(self, shell: PackageView, compiled: PackageView) -> None:
        self.shell = shell
        self.compiled = compiled
        self.dst_rels_root = copy.deepcopy(shell.xml("word/_rels/document.xml.rels"))
        self.dst_parts: dict[str, bytes] = {}
        self.dst_names = set(shell.parts)
        self.used_rids = {rel.get("Id") for rel in self.dst_rels_root}
        self.ct_root = copy.deepcopy(shell.xml("[Content_Types].xml"))
        self.compiled_ct_overrides = {
            el.get("PartName"): el.get("ContentType")
            for el in compiled.xml("[Content_Types].xml")
            if el.tag == _ct("Override")
        }
        self.report: list[dict] = []

    def allocate_rid(self) -> str:
        numbers = [
            int(match.group(1))
            for rid in self.used_rids
            if (match := re.fullmatch(r"rId(\d+)", rid or ""))
        ]
        new_rid = f"rId{max(numbers, default=0) + 1}"
        self.used_rids.add(new_rid)
        return new_rid

    def allocate_part_name(self, src_path: str) -> str:
        """目标部件名冲突时按数字后缀递增（header2.xml→header3.xml，image1.png→image2.png）。"""
        if src_path not in self.dst_names:
            return src_path
        stem, dot, ext = src_path.rpartition(".")
        match = re.match(r"^(.*?)(\d+)$", stem)
        base, number = (match.group(1), int(match.group(2))) if match else (stem, 0)
        while True:
            number += 1
            candidate = f"{base}{number}{dot}{ext}"
            if candidate not in self.dst_names:
                return candidate

    def ensure_content_type(self, src_path: str, dst_path: str) -> None:
        override = self.compiled_ct_overrides.get(f"/{src_path}")
        if override is None:
            return  # 由 Default（如 png/xml）覆盖，无需登记
        part_name = f"/{dst_path}"
        existing = {el.get("PartName") for el in self.ct_root if el.tag == _ct("Override")}
        if part_name not in existing:
            element = etree.SubElement(self.ct_root, _ct("Override"))
            element.set("PartName", part_name)
            element.set("ContentType", override)

    def carry_relationship(self, src_rid: str) -> str:
        """把 compiled 的一条 relationship（含目标部件）搬进 shell，返回新 rId。"""
        rel = self.compiled.rels("word/document.xml")[src_rid]
        if rel["TargetMode"] == "External":
            raise SystemExit(f"compiled 含外部 relationship {src_rid}，spec 默认 forbid")
        src_path = posixpath.normpath(posixpath.join("word", rel["Target"]))
        dst_path = self.allocate_part_name(src_path)
        if _rels_name_for(src_path) in self.compiled.parts:
            # 本 spike 数据未触发（compiled 的 header/footer/footnotes 均无部件级 rels）；
            # 真实现需递归搬运并重映射部件内部 r:id，记录为已知边界。
            raise NotImplementedError(f"部件级 rels 递归搬运未覆盖: {src_path}")
        self.dst_parts[dst_path] = self.compiled.parts[src_path]
        self.dst_names.add(dst_path)
        new_rid = self.allocate_rid()
        element = etree.SubElement(self.dst_rels_root, _pr("Relationship"))
        element.set("Id", new_rid)
        element.set("Type", rel["Type"])
        element.set("Target", posixpath.relpath(dst_path, "word"))
        self.ensure_content_type(src_path, dst_path)
        self.report.append(
            {
                "src_rid": src_rid,
                "new_rid": new_rid,
                "type": rel["Type"].rsplit("/", 1)[-1],
                "src_part": src_path,
                "dst_part": dst_path,
                "renamed": src_path != dst_path,
            }
        )
        return new_rid


def remap_rid_references(imported: list, ctx: CarryContext) -> dict:
    """重映射 imported 节点里的全部 r:id/r:embed/r:link，返回映射表。"""
    referenced: list[str] = []
    for element in imported:
        for node in element.iter():
            for attr in RID_ATTRS:
                value = node.get(_r(attr))
                if value is not None:
                    referenced.append(value)
    mapping = {rid: ctx.carry_relationship(rid) for rid in sorted(set(referenced))}
    for element in imported:
        for node in element.iter():
            for attr in RID_ATTRS:
                value = node.get(_r(attr))
                if value is not None:
                    node.set(_r(attr), mapping[value])
    return mapping


def carry_footnotes(imported: list, ctx: CarryContext) -> dict:
    """footnotes 部件搬运：按 w:id 关联（footnoteReference），不是 r:id。"""
    used = {
        el.get(_w("id")) for element in imported for el in element.iter(_w("footnoteReference"))
    }
    if not used:
        return {"used_footnote_ids": [], "action": "none"}
    if "word/footnotes.xml" in ctx.shell.parts:
        # 双方都有 footnotes 时需要按 w:id 合并去重，本 spike 未触发。
        raise NotImplementedError("shell 已有 footnotes 部件，id 合并未覆盖")
    rel = ctx.compiled.rels("word/document.xml")  # 确认 compiled footnotes 部件登记
    footnote_rid = next(r for r, v in rel.items() if v["Target"] == "footnotes.xml")
    new_rid = ctx.carry_relationship(footnote_rid)
    return {
        "used_footnote_ids": sorted(used),
        "action": "carried whole footnotes.xml",
        "new_rid": new_rid,
        "note": "w:id 无需重映射：shell 无既有脚注，id 空间不冲突",
    }


def merge_styles(imported: list, ctx: CarryContext) -> dict:
    """样式搬运：被引用样式 + basedOn/next/link 闭包；同名冲突 compiled 胜出。"""
    used: set[str] = set()
    for element in imported:
        for tag in STYLE_REF_TAGS:
            used.update(el.get(_w("val")) for el in element.iter(_w(tag)) if el.get(_w("val")))
    compiled_styles = ctx.compiled.xml("word/styles.xml")
    defined = {el.get(_w("styleId")): el for el in compiled_styles.iter(_w("style"))}
    closure: set[str] = set()
    worklist = list(used)
    while worklist:
        style_id = worklist.pop()
        if style_id in closure or style_id not in defined:
            continue
        closure.add(style_id)
        element = defined[style_id]
        for tag in STYLE_LINK_TAGS:
            link = element.find(_w(tag))
            if link is not None and link.get(_w("val")):
                worklist.append(link.get(_w("val")))

    shell_styles_root = copy.deepcopy(ctx.shell.xml("word/styles.xml"))
    shell_defined = {el.get(_w("styleId")): el for el in shell_styles_root.iter(_w("style"))}
    imported_ids, conflicts = [], []
    for style_id in sorted(closure):
        source_element = copy.deepcopy(defined[style_id])
        if style_id in shell_defined:
            shell_styles_root.replace(shell_defined[style_id], source_element)
            conflicts.append(style_id)
        else:
            shell_styles_root.append(source_element)
            imported_ids.append(style_id)
    ctx.dst_parts["word/styles.xml"] = _serialize(shell_styles_root)
    return {
        "used_by_imported": sorted(used),
        "closure": sorted(closure),
        "imported": imported_ids,
        "conflicts_compiled_wins": conflicts,
        "docDefaults_policy": "保留 shell 的 docDefaults/latentStyles，不合并",
    }


def merge_numbering(ctx: CarryContext) -> dict:
    """numbering 搬运：shell 正文无 numId 引用时整体替换；否则为未实现边界。"""
    shell_used = {
        el.get(_w("val"))
        for el in ctx.shell.xml("word/document.xml").iter(_w("numId"))
        if el.get(_w("val")) and el.get(_w("val")) != "0"
    }
    if shell_used:
        raise NotImplementedError(f"shell 正文已引用 numId {sorted(shell_used)}，需重映射合并")
    ctx.dst_parts["word/numbering.xml"] = ctx.compiled.parts["word/numbering.xml"]
    compiled_num_ids = sorted(
        {el.get(_w("numId")) for el in ctx.compiled.xml("word/numbering.xml").iter(_w("num"))},
        key=int,
    )
    return {
        "shell_num_ids_in_use": sorted(shell_used),
        "action": "compiled numbering.xml 整体替换 shell 默认 numbering.xml",
        "compiled_num_ids": compiled_num_ids,
    }


def merge_packages() -> dict:
    """执行合并，返回搬运台账。"""
    shell = PackageView(SHELL_PATH)
    compiled = PackageView(COMPILED_PATH)

    shell_body = shell.xml("word/document.xml").find(_w("body"))
    compiled_body = compiled.xml("word/document.xml").find(_w("body"))
    anchor, anchor_index = find_anchor_paragraph(shell_body, BODY_ANCHOR)

    imported, selection_info = select_imported_children(compiled_body)
    ctx = CarryContext(shell, compiled)
    rid_mapping = remap_rid_references(imported, ctx)
    footnotes_info = carry_footnotes(imported, ctx)
    styles_info = merge_styles(imported, ctx)
    numbering_info = merge_numbering(ctx)

    # 插入策略：imported 节点插在锚点段落之前，随后移除锚点段落（含 tf_body 书签对）。
    # tf_toc 书签保留在 shell 目录区，本 spike 不向其中注入内容。
    for element in imported:
        anchor.addprevious(element)
    shell_body.remove(anchor)

    ctx.dst_parts["word/document.xml"] = _serialize(shell.xml("word/document.xml"))
    ctx.dst_parts["word/_rels/document.xml.rels"] = _serialize(ctx.dst_rels_root)
    ctx.dst_parts["[Content_Types].xml"] = _serialize(ctx.ct_root)

    with zipfile.ZipFile(SHELL_PATH) as archive:
        original_order = archive.namelist()
    with zipfile.ZipFile(MERGED_PATH, "w", zipfile.ZIP_DEFLATED) as out:
        for name in original_order:
            out.writestr(name, ctx.dst_parts.get(name, shell.parts[name]))
        for name, content in ctx.dst_parts.items():
            if name not in original_order:
                out.writestr(name, content)

    return {
        "anchor": BODY_ANCHOR,
        "anchor_body_index": anchor_index,
        "selection": selection_info,
        "rid_mapping": rid_mapping,
        "carried_relationships": ctx.report,
        "footnotes": footnotes_info,
        "styles": styles_info,
        "numbering": numbering_info,
        "not_merged": {
            "settings.xml": "保留 shell（compiled 的 evenAndOddHeaders 不并入）",
            "theme1.xml": "保留 shell",
            "fontTable.xml": "保留 shell（已含宋体/黑体）",
            "docProps": "保留 shell",
        },
    }


def verify_merged() -> dict:
    """lxml 断言：sections/页码格式/图片 relationship/书签配对/脚注/编号/内容完整性。"""
    evidence: dict[str, object] = {}
    merged = PackageView(MERGED_PATH)
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
    evidence["section_pg_num"] = fmts
    assert len(sections) == 3, (
        f"应为 3 个 sectPr（shell 前置 + compiled 前置 + shell 正文），实际 {len(sections)}"
    )
    assert fmts[0] == {"fmt": "lowerRoman", "start": "1"}, "shell 前置节未保留"
    assert fmts[1] == {"fmt": "upperRoman", "start": "1"}, "compiled 前置节未搬运"
    assert fmts[2] == {"fmt": "decimal", "start": "1"}, "shell 正文节未保留"

    # 图片 relationship：shell logo 与 compiled 插图都必须可解析到真实部件
    rels = merged.rels("word/document.xml")
    image_targets = [v["Target"] for v in rels.values() if v["Type"].endswith("/image")]
    resolved = {posixpath.normpath(posixpath.join("word", target)) for target in image_targets}
    missing = resolved - set(merged.parts)
    evidence["image_relationships"] = {
        "targets": sorted(resolved),
        "missing_parts": sorted(missing),
    }
    assert len(image_targets) == 2 and not missing

    # 正文 r:embed 引用的 rId 必须在 rels 中存在（重映射有效性）
    embed_rids = {el.get(_r("embed")) for el in document.iter() if el.get(_r("embed"))}
    assert embed_rids <= set(rels), f"存在悬空 r:embed: {embed_rids - set(rels)}"
    evidence["embed_rids_valid"] = sorted(embed_rids)

    # 书签：tf_toc 保留且唯一，tf_body 已消费；配对由 openxml_validate 把关
    bookmark_names = [el.get(_w("name")) for el in document.iter(_w("bookmarkStart"))]
    evidence["bookmarks"] = {
        "tf_toc_present": bookmark_names.count(TOC_ANCHOR) == 1,
        "tf_body_consumed": BODY_ANCHOR not in bookmark_names,
        "total": len(bookmark_names),
    }
    assert bookmark_names.count(TOC_ANCHOR) == 1
    assert BODY_ANCHOR not in bookmark_names

    # 脚注：footnoteReference id=1 必须在搬运来的 footnotes.xml 中定义
    footnotes = merged.xml("word/footnotes.xml")
    defined_footnotes = {el.get(_w("id")) for el in footnotes.iter(_w("footnote"))}
    used_footnotes = {el.get(_w("id")) for el in document.iter(_w("footnoteReference"))}
    assert used_footnotes <= defined_footnotes
    evidence["footnotes"] = {
        "used": sorted(used_footnotes),
        "defined": sorted(defined_footnotes),
    }

    # 编号：numId 引用必须在 numbering.xml 中定义
    numbering = merged.xml("word/numbering.xml")
    defined_nums = {el.get(_w("numId")) for el in numbering.iter(_w("num"))}
    used_nums = {
        el.get(_w("val"))
        for el in document.iter(_w("numId"))
        if el.get(_w("val")) and el.get(_w("val")) != "0"
    }
    assert used_nums <= defined_nums
    evidence["numbering"] = {"used": sorted(used_nums), "defined_count": len(defined_nums)}

    # 内容完整性：shell 前置页与 compiled 正文并存
    text = "".join(document.itertext())
    for expected in ("原创性声明", "【姓名占位】", "摘要", "绪论", "参考文献", "致谢"):
        assert expected in text, f"合并产物缺少内容: {expected}"
    evidence["content_keywords_present"] = True

    # 样式：imported 内容引用的样式必须全部有定义
    styles = merged.xml("word/styles.xml")
    defined_styles = {el.get(_w("styleId")) for el in styles.iter(_w("style"))}
    used_styles = {
        el.get(_w("val"))
        for tag in STYLE_REF_TAGS
        for el in document.iter(_w(tag))
        if el.get(_w("val"))
    }
    evidence["undefined_styles"] = sorted(used_styles - defined_styles)
    return evidence


def main() -> None:
    ensure_dirs()
    if not SHELL_PATH.is_file():
        raise SystemExit(f"缺少 {SHELL_PATH}，请先运行 build_shell.py")
    compiled = compile_thesis()
    ledger = merge_packages()

    validation = run_openxml_validate(MERGED_PATH)
    evidence = verify_merged()
    smoke = soffice_smoke(MERGED_PATH, work_dir=OUTPUT_DIR / "merged-smoke")

    report = {
        "compiled_docx": str(compiled),
        "shell_docx": str(SHELL_PATH),
        "merged_docx": str(MERGED_PATH),
        "validation": summarize_validation(validation),
        "soffice_smoke": smoke,
        "ledger": ledger,
        "evidence": evidence,
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not validation["ok"]:
        raise SystemExit("openxml 校验未通过，见 merge-report.json")
    if smoke.get("available") and not smoke["ok"]:
        raise SystemExit("soffice 冒烟转换失败，见 merge-report.json")


if __name__ == "__main__":
    main()
