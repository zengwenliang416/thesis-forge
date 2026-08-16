#!/usr/bin/env python3
"""DOCX（OOXML/OPC）结构校验工具。

校验项对应 docs/update/QUALITY_STRATEGY.md 第 8 节的 OpenXML/OPC 门禁：
ZIP 完整性、[Content_Types].xml、relationship 目标存在性与重复 ID、
XML well-formed、w:document 根元素、书签配对、field 配对、media 对应、
sectPr、styles/numbering/footnotes 引用一致性。

用法：
    python qa/tools/openxml_validate.py <file.docx> [--json <报告路径>]

退出码：0 全部通过；1 存在失败项；2 文件不可读。
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"

# 可能出现书签 / field / 样式引用的正文故事部件
STORY_PART = re.compile(r"^word/(document|header\d*|footer\d*|footnotes|endnotes|comments)\.xml$")

# Word 内置样式 ID：可经 w:latentStyles 机制解析，不要求 styles.xml 显式定义
BUILTIN_STYLE_IDS = frozenset(
    {
        "BalloonText",
        "CommentReference",
        "CommentSubject",
        "CommentText",
        "EndnoteReference",
        "EndnoteText",
        "FollowedHyperlink",
        "FootnoteReference",
        "FootnoteText",
        "Hyperlink",
        "LineNumber",
        "PageNumber",
    }
)


@dataclass
class CheckResult:
    """单项校验结果：pass/fail 加明细。"""

    name: str
    status: str = "pass"
    details: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.status = "fail"
        self.details.append(message)


class DocxPackage:
    """延迟解析的 DOCX 包视图，缓存已解析的 XML 部件。"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.zf = zipfile.ZipFile(path)
        self.names = set(self.zf.namelist())
        self._parsed: dict[str, etree._Element | None] = {}

    def close(self) -> None:
        self.zf.close()

    def xml(self, name: str) -> etree._Element | None:
        """解析 XML 部件；缺失或不合法返回 None（由 well-formed 检查报告）。"""
        if name not in self._parsed:
            self._parsed[name] = None
            if name in self.names:
                try:
                    self._parsed[name] = etree.fromstring(self.zf.read(name))
                except (etree.XMLSyntaxError, KeyError, zipfile.BadZipFile):
                    self._parsed[name] = None
        return self._parsed[name]

    def story_parts(self) -> list[str]:
        return sorted(name for name in self.names if STORY_PART.match(name))


def _rels_base(rels_name: str) -> str:
    # word/_rels/document.xml.rels -> word；_rels/.rels -> ""
    prefix, _, _ = rels_name.partition("_rels/")
    return prefix.rstrip("/")


def _resolve(base: str, target: str) -> str:
    # OPC 允许以 "/" 开头的包绝对路径
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(base, target))


def _iter_relationships(pkg: DocxPackage):
    """产出包内全部 relationship 记录（rels 名、基准目录、Id、Target、TargetMode）。"""
    for name in sorted(n for n in pkg.names if n.endswith(".rels")):
        root = pkg.xml(name)
        if root is None:
            continue  # 由 xml_wellformed 报告
        base = _rels_base(name)
        for rel in root:
            yield (
                name,
                base,
                rel.get("Id", ""),
                rel.get("Target", ""),
                rel.get("TargetMode", "Internal"),
            )


def check_zip_integrity(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("zip_integrity")
    bad = pkg.zf.testzip()
    if bad is not None:
        result.fail(f"ZIP 条目 CRC 校验失败: {bad}")
    return result


def check_content_types(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("content_types")
    root = pkg.xml("[Content_Types].xml")
    if root is None:
        result.fail("[Content_Types].xml 缺失或不是合法 XML")
    elif root.tag != f"{{{CT_NS}}}Types":
        result.fail(f"根元素应为 Types，实际为 {root.tag}")
    return result


def check_relationship_targets(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("relationship_targets")
    for rels_name, base, rel_id, target, mode in _iter_relationships(pkg):
        if mode == "External":
            continue
        if not target:
            result.fail(f"{rels_name}: 关系 {rel_id} 缺少 Target")
            continue
        if _resolve(base, target) not in pkg.names:
            result.fail(f"{rels_name}: 关系 {rel_id} 目标部件不存在: {target}")
    return result


def check_duplicate_relationship_ids(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("duplicate_relationship_ids")
    for name in sorted(n for n in pkg.names if n.endswith(".rels")):
        root = pkg.xml(name)
        if root is None:
            continue
        counts = Counter(rel.get("Id", "") for rel in root)
        for rel_id, count in sorted(counts.items()):
            if count > 1:
                result.fail(f"{name}: relationship Id 重复 {count} 次: {rel_id}")
    return result


def check_xml_wellformed(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("xml_wellformed")
    for name in sorted(pkg.names):
        if not name.endswith((".xml", ".rels")):
            continue
        try:
            etree.fromstring(pkg.zf.read(name))
        except (  # 含 CRC 错误等，记录后继续校验其余项
            etree.XMLSyntaxError,
            zipfile.BadZipFile,
            RuntimeError,
            NotImplementedError,
            KeyError,
            ValueError,
            EOFError,
        ) as exc:
            result.fail(f"{name}: XML 解析失败: {exc}")
    return result


def check_document_root(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("document_root")
    root = pkg.xml("word/document.xml")
    if root is None:
        result.fail("word/document.xml 缺失或不是合法 XML")
    elif root.tag != f"{W}document":
        result.fail(f"根元素应为 w:document，实际为 {root.tag}")
    return result


def check_bookmark_pairing(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("bookmark_pairing")
    for name in pkg.story_parts():
        root = pkg.xml(name)
        if root is None:
            continue
        starts = Counter(el.get(f"{W}id") for el in root.iter(f"{W}bookmarkStart"))
        ends = Counter(el.get(f"{W}id") for el in root.iter(f"{W}bookmarkEnd"))
        for bookmark_id, count in sorted((starts - ends).items()):
            result.fail(f"{name}: bookmarkStart id={bookmark_id} 缺少 {count} 个 bookmarkEnd")
        for bookmark_id, count in sorted((ends - starts).items()):
            result.fail(f"{name}: bookmarkEnd id={bookmark_id} 缺少 {count} 个 bookmarkStart")
    return result


def check_field_pairing(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("field_pairing")
    for name in pkg.story_parts():
        root = pkg.xml(name)
        if root is None:
            continue
        stack: list[bool] = []  # True 表示已出现 separate；栈深度即嵌套层级
        for el in root.iter(f"{W}fldChar"):
            kind = el.get(f"{W}fldCharType")
            if kind == "begin":
                stack.append(False)
            elif kind == "separate":
                if not stack:
                    result.fail(f"{name}: fldChar separate 没有匹配的 begin")
                else:
                    stack[-1] = True
            elif kind == "end":
                if not stack:
                    result.fail(f"{name}: fldChar end 没有匹配的 begin")
                else:
                    stack.pop()
        if stack:
            result.fail(f"{name}: {len(stack)} 个 field 缺少匹配的 end")
    return result


def check_media_relationships(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("media_relationships")
    referenced = {
        _resolve(base, target)
        for _, base, _, target, mode in _iter_relationships(pkg)
        if mode != "External" and target
    }
    for name in sorted(n for n in pkg.names if "/media/" in n):
        if name not in referenced:
            result.fail(f"media 部件未被任何 relationship 引用: {name}")
    return result


def check_section_properties(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("section_properties")
    root = pkg.xml("word/document.xml")
    if root is None:
        result.fail("word/document.xml 缺失或不是合法 XML")
    elif not list(root.iter(f"{W}sectPr")):
        result.fail("word/document.xml 中不存在 w:sectPr")
    return result


def check_style_references(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("style_references")
    used: set[str] = set()
    for name in pkg.story_parts():
        root = pkg.xml(name)
        if root is None:
            continue
        for tag in ("pStyle", "rStyle", "tblStyle"):
            used.update(
                value for el in root.iter(f"{W}{tag}") if (value := el.get(f"{W}val"))
            )
    if not used:
        return result
    styles = pkg.xml("word/styles.xml")
    if styles is None:
        result.fail("正文引用了样式，但 word/styles.xml 缺失或不是合法 XML")
        return result
    defined = {el.get(f"{W}styleId") for el in styles.iter(f"{W}style")}
    for style_id in sorted(used - defined - BUILTIN_STYLE_IDS):
        result.fail(f"正文引用的样式未在 styles.xml 中定义: {style_id}")
    return result


def check_numbering_references(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("numbering_references")
    document = pkg.xml("word/document.xml")
    if document is None:
        result.fail("word/document.xml 缺失或不是合法 XML")
        return result
    used = {
        value
        for el in document.iter(f"{W}numId")
        if (value := el.get(f"{W}val")) and value != "0"
    }
    if not used:
        return result
    numbering = pkg.xml("word/numbering.xml")
    if numbering is None:
        result.fail("正文引用了 numId，但 word/numbering.xml 缺失或不是合法 XML")
        return result
    defined = {el.get(f"{W}numId") for el in numbering.iter(f"{W}num")}
    for num_id in sorted(used - defined):
        result.fail(f"正文引用的 numId 未在 numbering.xml 中定义: {num_id}")
    return result


def check_footnote_references(pkg: DocxPackage) -> CheckResult:
    result = CheckResult("footnote_references")
    document = pkg.xml("word/document.xml")
    if document is None:
        result.fail("word/document.xml 缺失或不是合法 XML")
        return result
    used = {
        value
        for el in document.iter(f"{W}footnoteReference")
        if (value := el.get(f"{W}id"))
    }
    if not used:
        return result
    footnotes = pkg.xml("word/footnotes.xml")
    if footnotes is None:
        result.fail("正文引用了脚注，但 word/footnotes.xml 缺失或不是合法 XML")
        return result
    defined = {el.get(f"{W}id") for el in footnotes.iter(f"{W}footnote")}
    for footnote_id in sorted(used - defined):
        result.fail(f"正文引用的脚注未在 footnotes.xml 中定义: id={footnote_id}")
    return result


CHECKS = (
    check_zip_integrity,
    check_content_types,
    check_relationship_targets,
    check_duplicate_relationship_ids,
    check_xml_wellformed,
    check_document_root,
    check_bookmark_pairing,
    check_field_pairing,
    check_media_relationships,
    check_section_properties,
    check_style_references,
    check_numbering_references,
    check_footnote_references,
)


def validate_docx(path: Path) -> dict:
    """执行全部校验并返回 JSON 可序列化报告。"""
    pkg = DocxPackage(path)
    try:
        checks = [check(pkg) for check in CHECKS]
    finally:
        pkg.close()
    failed = [check for check in checks if check.status != "pass"]
    return {
        "file": str(path),
        "ok": not failed,
        "summary": {
            "total": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
        "checks": [
            {"name": check.name, "status": check.status, "details": check.details}
            for check in checks
        ],
    }


def _emit(report: dict, json_path: Path | None) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if json_path is not None:
        json_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DOCX（OOXML/OPC）结构校验工具")
    parser.add_argument("docx", type=Path, help="待校验的 .docx 文件")
    parser.add_argument("--json", type=Path, default=None, help="可选：JSON 报告写入路径")
    args = parser.parse_args(argv)

    if not args.docx.is_file():
        _emit({"file": str(args.docx), "ok": False, "error": "文件不存在"}, args.json)
        return 2
    try:
        report = validate_docx(args.docx)
    except (zipfile.BadZipFile, OSError) as exc:
        _emit(
            {"file": str(args.docx), "ok": False, "error": f"文件不可读: {exc}"},
            args.json,
        )
        return 2
    _emit(report, args.json)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
