#!/usr/bin/env python3
"""Phase 0 字段实证：样本 DOCX 结构校验（openxml_validate + XPath 断言）。

对每个样本执行：
1. qa/tools/openxml_validate.py 全量 OOXML/OPC 门禁校验；
2. XPath 结构断言：
   - TOC field 指令为 TOC \\o "1-3" \\h \\z \\u，且无 cached 条目（生成态）
   - 每个 fig/tbl/eq 书签都有对应 SEQ 字段（SEQ 总数 == 编号对象总数）
   - 每个 REF 字段指向存在的 bookmark
   - PAGE（及模板要求时的 NUMPAGES）出现在 footer 部件中
   - 各 section 的 pgNumType fmt 符合模板（前置 roman / 正文 decimal）

输出 results/structure-checks.json；任一断言失败退出码为 1。

用法：
    .venv/bin/python spikes/phase0/fields/verify_structure.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from lxml import etree

SPIKE_DIR = Path(__file__).resolve().parent
ROOT = SPIKE_DIR.parents[2]
SAMPLES_DIR = SPIKE_DIR / "samples"
RESULTS_DIR = SPIKE_DIR / "results"
OPENXML_VALIDATE = ROOT / "qa" / "tools" / "openxml_validate.py"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W = f"{{{W_NS}}}"

TOC_INSTRUCTION = 'TOC \\o "1-3" \\h \\z \\u'
NUMBERED_BOOKMARK_PREFIXES = ("tf_fig_", "tf_tbl_", "tf_eq_")
# 每个样本期望的 pgNumType fmt 集合（按 sectPr 出现顺序去重）
EXPECTED_PAGE_FORMATS = {
    "complete-thesis-example": ["none?", "lowerRoman", "decimal"],
    "minimal-hut": ["none?", "upperRoman", "decimal"],
}


def _sample_docx_files() -> list[Path]:
    """样本清单：排除 macOS AppleDouble（._*）、Word 锁文件（~$*）、
    LO 刷新副本（*-lo-refreshed）与对照变体（*-no-updatefields）。"""
    return [
        path
        for path in sorted(SAMPLES_DIR.glob("*.docx"))
        if not path.name.startswith(("._", "~$"))
        and "-lo-refreshed" not in path.stem
        and "-no-updatefields" not in path.stem
        and "-keep-updatefields" not in path.stem
    ]


def _document_fields(document: etree._Element) -> list[dict]:
    """提取 document.xml 顶层字段（指令 + cached result）。"""
    fields: list[dict] = []
    stack: list[dict] = []
    for element in document.iter():
        if element.tag == f"{W}fldChar":
            kind = element.get(f"{W}fldCharType")
            if kind == "begin":
                stack.append({"instruction": "", "result": [], "separate": False})
            elif kind == "separate" and stack:
                stack[-1]["separate"] = True
            elif kind == "end" and stack:
                fields.append(stack.pop())
        elif element.tag == f"{W}instrText" and stack and not stack[-1]["separate"]:
            stack[-1]["instruction"] += element.text or ""
        elif element.tag == f"{W}t" and stack and stack[-1]["separate"]:
            stack[-1]["result"].append(element.text or "")
    return [
        {
            "instruction": " ".join(f["instruction"].split()),
            "cached_result": "".join(f["result"]),
        }
        for f in fields
    ]


def _footer_fields(package: zipfile.ZipFile) -> list[str]:
    instructions: list[str] = []
    for name in sorted(package.namelist()):
        if re.match(r"^word/footer\d*\.xml$", name):
            root = etree.fromstring(package.read(name))
            instructions.extend(
                " ".join(text.split())
                for text in root.xpath(".//w:instrText/text()", namespaces=NS)
            )
    return instructions


def check_sample(path: Path) -> dict:
    checks: list[dict] = []

    def record(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "status": "pass" if ok else "fail", "detail": detail})

    # 1) openxml_validate 门禁
    proc = subprocess.run(
        [sys.executable, str(OPENXML_VALIDATE), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    openxml_report = json.loads(proc.stdout)
    failed = [c for c in openxml_report["checks"] if c["status"] != "pass"]
    record(
        "openxml_validate",
        proc.returncode == 0,
        "全部通过" if not failed else json.dumps(failed, ensure_ascii=False),
    )

    with zipfile.ZipFile(path) as package:
        document = etree.fromstring(package.read("word/document.xml"))
        fields = _document_fields(document)
        bookmarks = set(
            document.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
        )
        footer_instructions = _footer_fields(package)

    # 2) TOC 指令正确且生成态无 cached 条目
    toc_fields = [f for f in fields if f["instruction"] == TOC_INSTRUCTION]
    record(
        "toc_instruction",
        len(toc_fields) == 1 and toc_fields[0]["cached_result"] == "",
        f"TOC 字段 {len(toc_fields)} 个；cached result 长度 "
        f"{len(toc_fields[0]['cached_result']) if toc_fields else '-'}",
    )

    # 3) 每个 fig/tbl/eq 书签对应一个 SEQ 字段
    numbered = sorted(
        name
        for name in bookmarks
        if name.startswith(NUMBERED_BOOKMARK_PREFIXES)
    )
    seq_fields = [f for f in fields if f["instruction"].startswith("SEQ ")]
    record(
        "seq_per_numbered_object",
        len(seq_fields) == len(numbered) and len(numbered) > 0,
        f"编号对象书签 {numbered}；SEQ 字段 {len(seq_fields)} 个",
    )

    # 4) REF 指向存在的 bookmark
    ref_targets = [
        match.group(1)
        for f in fields
        if (match := re.match(r"REF (\S+)", f["instruction"]))
    ]
    missing = sorted(set(ref_targets) - bookmarks)
    record(
        "ref_targets_exist",
        bool(ref_targets) and not missing,
        f"REF 目标 {sorted(set(ref_targets))}；缺失 {missing or '无'}",
    )

    # 5) PAGE/NUMPAGES 在 footer
    has_page = "PAGE" in footer_instructions
    record(
        "page_field_in_footer",
        has_page,
        f"footer 字段指令 {sorted(set(footer_instructions))}",
    )

    # 6) pgNumType fmt 符合模板期望
    formats = []
    for sect in document.xpath(".//w:sectPr", namespaces=NS):
        fmt = sect.xpath("./w:pgNumType/@w:fmt", namespaces=NS)
        value = fmt[0] if fmt else "none?"
        if not formats or formats[-1] != value:
            formats.append(value)
    expected = EXPECTED_PAGE_FORMATS.get(path.stem)
    record(
        "page_number_formats",
        expected is None or formats == expected,
        f"实际 {formats}；期望 {expected}",
    )

    return {
        "file": path.name,
        "ok": all(c["status"] == "pass" for c in checks),
        "checks": checks,
    }


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        path.stem: check_sample(path) for path in _sample_docx_files()
    }
    output = RESULTS_DIR / "structure-checks.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for stem, data in report.items():
        for check in data["checks"]:
            print(f"{stem} [{check['status']}] {check['name']}: {check['detail']}")
    print(f"written {output}")
    return 0 if all(data["ok"] for data in report.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
