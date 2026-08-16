"""用 pandoc 把语料库公式逐条（及整体）转成 DOCX，记录失败条目。

pandoc 内部走 LaTeX → 原生 OMML（m:oMath）。pandoc 转换失败时不会报错退出，
而是输出 "Could not convert TeX math" 警告并把公式当纯文本写入，因此本脚本
用「stderr 警告 + 产物中 m:oMath 计数」双重判据。

复跑：
    .venv/bin/python spikes/phase0/omml/convert_pandoc.py

输出：
    spikes/phase0/omml/results/pandoc_conversion.json
    spikes/phase0/omml/output/pandoc_corpus.docx   （全部公式合并产物，供人工抽查）
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile

import yaml
from lxml import etree

SPIKE_DIR = Path(__file__).resolve().parent
CORPUS = SPIKE_DIR / "corpus" / "formulas.yaml"
RESULTS = SPIKE_DIR / "results"
OUTPUT = SPIKE_DIR / "output"

MATH_NS = {"m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
PANDOC_FORMAT = "markdown+tex_math_dollars"


def count_omath(docx_path: Path) -> int:
    with ZipFile(docx_path) as package:
        document = etree.fromstring(package.read("word/document.xml"))
    return len(document.xpath(".//m:oMath", namespaces=MATH_NS))


def convert_one(formula: dict[str, str], workdir: Path) -> dict[str, object]:
    if formula["usage"] == "inline":
        snippet = f"行内公式 ${formula['latex']}$ 混排。\n"
    else:
        snippet = f"$$\n{formula['latex']}\n$$\n"
    source = workdir / f"{formula['id']}.md"
    target = workdir / f"{formula['id']}.docx"
    source.write_text(snippet, encoding="utf-8")
    completed = subprocess.run(
        ["pandoc", "-f", PANDOC_FORMAT, "-t", "docx", "-o", str(target), str(source)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    stderr = completed.stderr.strip()
    warned = "Could not convert" in stderr
    omath_count = count_omath(target) if target.exists() else 0
    success = completed.returncode == 0 and not warned and omath_count >= 1
    return {
        "id": formula["id"],
        "status": "success" if success else "failed",
        "returncode": completed.returncode,
        "omath_count": omath_count,
        "stderr": stderr or None,
    }


def build_combined(corpus: dict[str, object]) -> dict[str, object]:
    OUTPUT.mkdir(exist_ok=True)
    lines = ["% OMML 语料库 pandoc 对照文档", ""]
    for formula in corpus["formulas"]:
        lines.append(f"## {formula['id']}")
        lines.append("")
        if formula["usage"] == "inline":
            lines.append(f"行内公式 ${formula['latex']}$ 混排场景。")
        else:
            lines.extend(("$$", formula["latex"], "$$"))
        lines.append("")
    source = OUTPUT / "pandoc_corpus.md"
    target = OUTPUT / "pandoc_corpus.docx"
    source.write_text("\n".join(lines), encoding="utf-8")
    completed = subprocess.run(
        ["pandoc", "-f", PANDOC_FORMAT, "-t", "docx", "-o", str(target), str(source)],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "returncode": completed.returncode,
        "omath_count": count_omath(target) if target.exists() else 0,
        "stderr": completed.stderr.strip() or None,
        "docx": str(target),
    }


def main() -> None:
    corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
    version = subprocess.run(
        ["pandoc", "--version"], check=True, capture_output=True, text=True
    ).stdout.splitlines()[0]

    entries = []
    with tempfile.TemporaryDirectory(prefix="omml-pandoc-") as tmp:
        workdir = Path(tmp)
        for formula in corpus["formulas"]:
            entries.append(convert_one(formula, workdir))

    combined = build_combined(corpus)
    success = sum(1 for entry in entries if entry["status"] == "success")
    summary = {
        "pandoc_version": version,
        "total": len(entries),
        "success": success,
        "failed": len(entries) - success,
        "coverage": round(success / len(entries), 4),
        "combined_omath_count": combined["omath_count"],
        "combined_returncode": combined["returncode"],
    }

    RESULTS.mkdir(exist_ok=True)
    output = RESULTS / "pandoc_conversion.json"
    output.write_text(
        json.dumps(
            {"summary": summary, "combined_stderr": combined["stderr"], "entries": entries},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"pandoc: {version}")
    print(f"total={summary['total']} success={summary['success']} failed={summary['failed']}")
    print(f"coverage={summary['coverage']:.2%}, combined m:oMath={combined['omath_count']}")
    for entry in entries:
        if entry["status"] != "success":
            print(f"  FAILED {entry['id']}: rc={entry['returncode']} omath={entry['omath_count']}")
    print(f"-> {output}")


if __name__ == "__main__":
    main()
