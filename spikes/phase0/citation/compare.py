"""Compare the three rendering engines on the GB/T 7714 corpus.

Reads results/pandoc.json, results/citeproc_py.json and
results/thesisforge.json (run the render_* scripts first) and writes
results/comparison.json + results/comparison.md.
"""

from __future__ import annotations

import json
import re

from corpus_meta import (
    INTENDED_TYPES,
    RESULTS,
    TYPE_COVERAGE_NOTES,
    corpus_keys_in_bib_order,
    load_csl_json,
    load_result,
)

TYPE_MARKER_RE = re.compile(r"\[([A-Z]{1,2}(?:/OL)?)\]")
FULLWIDTH_CHARS = "，：（）；．"
SPACELESS_RE = re.compile(r"\s+")


def compact(text: str) -> str:
    return SPACELESS_RE.sub("", text)


def extract_type_marker(text: str) -> str | None:
    match = TYPE_MARKER_RE.search(text)
    return match.group(1) if match else None


def classify_engine_diff(pandoc_text: str, citeproc_text: str) -> str:
    """Classify a pandoc-vs-citeproc-py difference into a named category."""
    pn, cn = compact(pandoc_text), compact(citeproc_text)
    if pn == cn:
        return "identical"
    marker = TYPE_MARKER_RE.search(pandoc_text)
    if marker and marker.group(0) not in citeproc_text:
        if pn.replace(marker.group(0), "", 1) == cn:
            return "type-marker-group-dropped"
        return "type-marker-dropped+other"
    if cn.replace("V.", "") == pn:
        return "spurious-version-label"
    if "版" in pandoc_text and "版" in citeproc_text:
        return "edition-ordinal-format"
    return "other"


def punctuation_profile(text: str) -> str:
    fullwidth = sum(text.count(char) for char in FULLWIDTH_CHARS)
    halfwidth = sum(text.count(char) for char in ",():;.") - text.count("10.")
    if fullwidth and not halfwidth:
        return "fullwidth"
    if halfwidth and not fullwidth:
        return "halfwidth"
    return "mixed" if fullwidth and halfwidth else "none"


def thesisforge_checks(key: str, tf_text: str, pandoc_text: str, csl_item: dict) -> dict:
    """Structured fact checks of a handwritten-formatter entry vs pandoc output."""
    expected_marker = INTENDED_TYPES[key]
    tf_marker = extract_type_marker(tf_text)
    checks: dict[str, object] = {
        "type_marker": tf_marker,
        "type_marker_matches_intended": tf_marker == expected_marker,
        "punctuation": punctuation_profile(tf_text),
        "pandoc_punctuation": punctuation_profile(pandoc_text),
    }
    missing: list[str] = []
    if "DOI" in csl_item and f"DOI:{csl_item['DOI']}" not in tf_text:
        missing.append("DOI")
    if "URL" in csl_item and csl_item["URL"] not in tf_text:
        missing.append("URL")
    if "page" in csl_item and str(csl_item["page"]) not in tf_text.replace("--", "-"):
        missing.append("pages")
    if "edition" in csl_item and str(csl_item["edition"]) not in tf_text:
        missing.append("edition")
    if "translator" in csl_item:
        names = " and ".join(
            part.get("family", "") + " " + part.get("given", "")
            for part in csl_item["translator"]
        )
        if not any(part.strip() and part.strip() in tf_text for part in names.split(" and ")):
            missing.append("translator")
    pandoc_has_etal = "等" in pandoc_text or "et al" in pandoc_text
    checks["pandoc_has_et_al_truncation"] = pandoc_has_etal
    checks["thesisforge_has_et_al_truncation"] = "等" in tf_text or "et al" in tf_text
    checks["missing_fields"] = missing
    return checks


def main() -> int:
    pandoc = {e["key"]: e for e in load_result("pandoc.json")["entries"]}
    citeproc = {e["key"]: e for e in load_result("citeproc_py.json")["entries"]}
    thesisforge_result = load_result("thesisforge.json")
    thesisforge = {e["key"]: e for e in thesisforge_result["entries"]}
    tf_failures = {f["key"]: f["error"] for f in thesisforge_result["failures"]}
    csl_items = load_csl_json()

    per_key: dict[str, dict] = {}
    class_counts: dict[str, int] = {}
    for key in corpus_keys_in_bib_order():
        p_text = pandoc[key]["text"]
        c_text = citeproc[key]["text"]
        diff_class = classify_engine_diff(p_text, c_text)
        class_counts[diff_class] = class_counts.get(diff_class, 0) + 1
        record: dict[str, object] = {
            "ordinal": pandoc[key]["ordinal"],
            "intended_type": INTENDED_TYPES[key],
            "pandoc": p_text,
            "citeproc_py": c_text,
            "pandoc_vs_citeproc_py": {
                "identical_exact": p_text == c_text,
                "identical_ignoring_whitespace": compact(p_text) == compact(c_text),
                "difference_class": diff_class,
            },
            "coverage_note": TYPE_COVERAGE_NOTES.get(key),
        }
        if key in thesisforge:
            tf_text = thesisforge[key]["text"]
            record["thesisforge"] = {
                "status": "rendered",
                "text": tf_text,
                "checks": thesisforge_checks(key, tf_text, p_text, csl_items[key]),
            }
        else:
            record["thesisforge"] = {"status": "failed", "error": tf_failures.get(key)}
        per_key[key] = record

    total = len(per_key)
    identical = sum(
        1
        for r in per_key.values()
        if r["pandoc_vs_citeproc_py"]["identical_ignoring_whitespace"]  # type: ignore[index]
    )
    summary = {
        "corpus_size": total,
        "pandoc_vs_citeproc_py": {
            "identical_ignoring_whitespace": identical,
            "consistency_rate": round(identical / total, 4),
            "difference_classes": class_counts,
        },
        "thesisforge": {
            "rendered": len(thesisforge),
            "failed": len(tf_failures),
        },
    }
    payload = {"summary": summary, "keys": per_key}
    (RESULTS / "comparison.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_markdown(summary, per_key)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def write_markdown(summary: dict, per_key: dict[str, dict]) -> None:
    lines = [
        "# 条目 × 引擎对照表（GB/T 7714-2025 corpus）",
        "",
        f"- 语料规模：{summary['corpus_size']} 条",
        (
            "- pandoc vs citeproc-py 一致（忽略空白）："
            f"{summary['pandoc_vs_citeproc_py']['identical_ignoring_whitespace']}/"
            f"{summary['corpus_size']}（一致率 "
            f"{summary['pandoc_vs_citeproc_py']['consistency_rate']:.1%}）"
        ),
        f"- 差异分类计数：{summary['pandoc_vs_citeproc_py']['difference_classes']}",
        (
            "- thesisforge 手写 formatter：可渲染 "
            f"{summary['thesisforge']['rendered']} 条，无法渲染 "
            f"{summary['thesisforge']['failed']} 条"
        ),
        "",
        "| # | key | 目标类型 | pandoc==citeproc-py | 差异类别 | thesisforge | 备注 |",
        "|---|-----|---------|--------------------|---------|------------|------|",
    ]
    for key, record in per_key.items():
        pvc = record["pandoc_vs_citeproc_py"]
        same = "是" if pvc["identical_ignoring_whitespace"] else "否"
        tf = record["thesisforge"]
        if tf["status"] == "rendered":
            checks = tf["checks"]
            parts = []
            if not checks["type_marker_matches_intended"]:
                parts.append(f"类型标识 {checks['type_marker']}≠{record['intended_type']}")
            if checks["missing_fields"]:
                parts.append("缺 " + "/".join(checks["missing_fields"]))
            if checks["pandoc_has_et_al_truncation"] and not checks[
                "thesisforge_has_et_al_truncation"
            ]:
                parts.append("无等/et al 截断")
            if checks["punctuation"] != checks["pandoc_punctuation"]:
                parts.append("半角标点")
            tf_cell = "可渲染；" + ("；".join(parts) if parts else "结构一致")
        else:
            tf_cell = "失败：" + str(tf["error"]).split(":", 1)[0]
        note = record["coverage_note"] or ""
        lines.append(
            f"| {record['ordinal']} | {key} | [{record['intended_type']}] | {same} | "
            f"{pvc['difference_class']} | {tf_cell} | {note} |"
        )
    lines += [
        "",
        "## 逐条全文对照",
        "",
    ]
    for key, record in per_key.items():
        lines.append(f"### [{record['ordinal']}] {key}（目标 [{record['intended_type']}]）")
        lines.append("")
        lines.append(f"- pandoc：`{record['pandoc']}`")
        lines.append(f"- citeproc-py：`{record['citeproc_py']}`")
        tf = record["thesisforge"]
        if tf["status"] == "rendered":
            lines.append(f"- thesisforge：`{tf['text']}`")
        else:
            lines.append(f"- thesisforge：无法渲染 — {tf['error']}")
        lines.append("")
    (RESULTS / "comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"written: {RESULTS / 'comparison.md'}")


if __name__ == "__main__":
    raise SystemExit(main())
