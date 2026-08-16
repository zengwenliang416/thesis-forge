#!/usr/bin/env python3
"""Phase 0 字段实证：解包样本 DOCX，盘点全部 Word 字段状态。

对每个样本提取：
- 全部字段指令（w:instrText）、fldChar dirty 状态、cached result 文本
  （按 story 部件分组：document / header* / footer* / footnotes）
- bookmark 清单（名称、id、所在部件）
- settings.xml 的 w:updateFields

输出 results/fields-inventory.json。

用法：
    .venv/bin/python spikes/phase0/fields/inspect_fields.py
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

SPIKE_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = SPIKE_DIR / "samples"
RESULTS_DIR = SPIKE_DIR / "results"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
STORY_PART = re.compile(
    r"^word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$"
)


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


def _extract_fields(root: etree._Element) -> list[dict]:
    """按文档序遍历 fldChar/instrText，重建字段的 指令/dirty/cached result。"""
    fields: list[dict] = []
    # 栈元素：{instruction, dirty, result_parts, has_separate}
    stack: list[dict] = []
    for element in root.iter():
        if element.tag == f"{W}fldChar":
            kind = element.get(f"{W}fldCharType")
            if kind == "begin":
                stack.append(
                    {
                        "instruction": "",
                        "dirty": element.get(f"{W}dirty") == "true",
                        "result_parts": [],
                        "has_separate": False,
                    }
                )
            elif kind == "separate" and stack:
                stack[-1]["has_separate"] = True
            elif kind == "end" and stack:
                fields.append(stack.pop())
        elif element.tag == f"{W}instrText" and stack and not stack[-1]["has_separate"]:
            stack[-1]["instruction"] += element.text or ""
        elif element.tag == f"{W}t" and stack and stack[-1]["has_separate"]:
            stack[-1]["result_parts"].append(element.text or "")
    return [
        {
            "instruction": " ".join(field["instruction"].split()),
            "dirty": field["dirty"],
            "has_cached_result": bool(field["has_separate"]),
            "cached_result": "".join(field["result_parts"]),
        }
        for field in fields
    ]


def _extract_bookmarks(root: etree._Element) -> list[dict]:
    return [
        {"name": el.get(f"{W}name"), "id": el.get(f"{W}id")}
        for el in root.iter(f"{W}bookmarkStart")
    ]


def inspect_sample(path: Path) -> dict:
    parts_report: dict[str, dict] = {}
    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        for name in sorted(n for n in names if STORY_PART.match(n)):
            root = etree.fromstring(package.read(name))
            fields = _extract_fields(root)
            bookmarks = _extract_bookmarks(root)
            if fields or bookmarks:
                parts_report[name] = {"fields": fields, "bookmarks": bookmarks}
        settings = etree.fromstring(package.read("word/settings.xml"))
        update_fields = settings.find(f"{W}updateFields")
        update_fields_val = (
            update_fields.get(f"{W}val") if update_fields is not None else None
        )
    all_fields = [
        {**field, "part": part}
        for part, data in parts_report.items()
        for field in data["fields"]
    ]
    return {
        "file": path.name,
        "update_fields_setting": update_fields_val,
        "field_count": len(all_fields),
        "fields_by_kind": _count_by_kind(all_fields),
        "parts": parts_report,
    }


def _count_by_kind(fields: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for field in fields:
        kind = field["instruction"].split(" ", 1)[0] if field["instruction"] else "?"
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        path.stem: inspect_sample(path)
        for path in _sample_docx_files()
    }
    output = RESULTS_DIR / "fields-inventory.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for stem, data in report.items():
        print(f"{stem}: {data['field_count']} fields {data['fields_by_kind']}")
    print(f"written {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
