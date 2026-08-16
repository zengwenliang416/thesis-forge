"""Build golden/gbt7714-golden-v1.json from the pandoc citeproc output.

Each entry is machine-checked for structural completeness (ordinal, author,
title, GB/T type marker, source, year/volume/issue/pages). Entries with any
suspicion are flagged `review: pending-human-review` with explicit reasons.
Run render_pandoc.py first.
"""

from __future__ import annotations

import json
import re

from corpus_meta import (
    INTENDED_TYPES,
    ROOT,
    TYPE_COVERAGE_NOTES,
    corpus_keys_in_bib_order,
    load_csl_json,
    load_result,
)

GOLDEN_PATH = ROOT / "golden" / "gbt7714-golden-v1.json"
YEAR_RE = re.compile(r"(19|20)\d{2}")


def first_author_text(item: dict) -> str | None:
    authors = item.get("author") or []
    if not authors:
        return None
    first = authors[0]
    return first.get("literal") or first.get("family")


def first_substitute_text(item: dict) -> str | None:
    """First non-author contributor the CSL author macro would substitute."""
    for variable in ("editor", "translator"):
        names = item.get(variable) or []
        if names:
            return names[0].get("literal") or names[0].get("family")
    return None


def check_entry(key: str, ordinal: int, text: str, item: dict) -> tuple[dict, list[str]]:
    checks: dict[str, object] = {}
    reasons: list[str] = []

    checks["has_ordinal"] = ordinal >= 1
    if not checks["has_ordinal"]:
        reasons.append("序号缺失或非法")

    author = first_author_text(item)
    if author is None:
        substitute = first_substitute_text(item)
        if substitute is not None:
            checks["author_present"] = f"substitute contributor: {substitute}"
            if substitute not in text:
                reasons.append(f"替代责任者 {substitute}（编者/译者）未出现在渲染文本中")
        else:
            checks["author_present"] = "not-applicable (no author; title-first)"
            if not text.startswith(str(item.get("title", ""))[:10]):
                reasons.append("无著者条目未以题名起始")
    else:
        checks["author_present"] = author in text
        if not checks["author_present"]:
            reasons.append(f"首著者 {author} 未出现在渲染文本中")

    checks["title_present"] = str(item.get("title", "")) in text
    if not checks["title_present"]:
        reasons.append("题名未出现在渲染文本中")

    marker_match = re.search(r"\[([A-Z]{1,2}(?:/OL)?)\]", text)
    checks["type_marker"] = marker_match.group(1) if marker_match else None
    intended = INTENDED_TYPES[key]
    rendered_base = str(checks["type_marker"] or "").split("/", 1)[0]
    intended_base = intended.split("/", 1)[0]
    checks["type_marker_matches_intended"] = checks["type_marker"] == intended
    if checks["type_marker"] is None:
        reasons.append("缺少 GB/T 文献类型标识")
    elif rendered_base == intended_base and checks["type_marker"] != intended:
        reasons.append(
            f"类型标识 [{checks['type_marker']}] 附加了载体标识 /OL（目标 [{intended}]）；"
            "含 DOI/URL 的印刷型文献是否应标 /OL 需人工对照 GB/T 7714-2025 确认"
        )
    elif rendered_base != intended_base:
        reasons.append(
            f"类型标识 [{checks['type_marker']}] 与目标 [{intended}] 不一致"
        )

    checks["has_year"] = bool(YEAR_RE.search(text))
    if not checks["has_year"]:
        reasons.append("缺少年份")

    source_value = item.get("container-title") or item.get("publisher")
    checks["source_present"] = bool(source_value) and str(source_value) in text
    if source_value and not checks["source_present"]:
        reasons.append(f"出处 {source_value} 未出现在渲染文本中")

    for field, label in (("volume", "卷"), ("issue", "期"), ("page", "页码")):
        if field in item:
            present = str(item[field]) in text
            checks[f"has_{field}"] = present
            if not present:
                reasons.append(f"{label} {item[field]} 未出现在渲染文本中")

    if "DOI" in item:
        checks["has_doi"] = f"DOI:{item['DOI']}" in text
        if not checks["has_doi"]:
            reasons.append("DOI 未按 DOI: 前缀著录")
    if "URL" in item:
        checks["has_url"] = str(item["URL"]) in text
        if not checks["has_url"]:
            reasons.append("URL 未出现在渲染文本中")
    if "accessed" in item:
        accessed = "-".join(f"{part:02d}" for part in item["accessed"]["date-parts"][0])
        checks["has_accessed_date"] = f"[{accessed}]" in text
        if not checks["has_accessed_date"]:
            reasons.append(f"引用日期 [{accessed}] 未著录")

    if item.get("language") == "en-US":
        checks["western_entry_uses_et_al"] = "et al" in text
        if "等" in text:
            reasons.append("西文条目使用中文『等』而非 et al（CSL default-locale 固定 zh-CN）")

    if key in TYPE_COVERAGE_NOTES:
        reasons.append(TYPE_COVERAGE_NOTES[key])

    return checks, reasons


def main() -> int:
    pandoc = load_result("pandoc.json")
    rendered = {e["key"]: e for e in pandoc["entries"]}
    csl_items = load_csl_json()

    entries = []
    pending = 0
    for key in corpus_keys_in_bib_order():
        item = csl_items[key]
        entry = rendered[key]
        checks, reasons = check_entry(key, entry["ordinal"], entry["text"], item)
        review = "pending-human-review" if reasons else "passed-machine-check"
        pending += bool(reasons)
        entries.append(
            {
                "key": key,
                "ordinal": entry["ordinal"],
                "intended_type": INTENDED_TYPES[key],
                "text": entry["text"],
                "checks": checks,
                "review": review,
                "review_reasons": reasons,
            }
        )

    payload = {
        "schema": "thesisforge-spike/gbt7714-golden-v1",
        "source": {
            "engine": pandoc["engine"],
            "engine_version": pandoc["engine_version"],
            "csl_file": pandoc["csl_file"],
            "csl_sha256": pandoc["csl_sha256"],
            "corpus_bib": "corpus/gbt7714-corpus.bib",
            "generated_by": "build_golden.py",
        },
        "review_policy": (
            "机器初校仅检查结构完整性；任何疑义（类型标识不符、西文条目用『等』、"
            "字段缺失等）一律标 pending-human-review"
        ),
        "entries": entries,
    }
    GOLDEN_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"golden: {len(entries)} entries, {pending} pending-human-review")
    print(f"written: {GOLDEN_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
