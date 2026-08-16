"""用 latex2mathml 逐条转换语料库，并用 MML2OMML.XSL 实测 MathML→OMML 路径。

latex2mathml（纯 Python，3.81.0）产出 presentation MathML；MathML→OMML 采用
Microsoft 随 Office 分发的 MML2OMML.XSL（XSLT 1.0）。本 spike 使用的副本镜像自
PaddlePaddle/PaddleX 仓库（assets/MML2OMML.XSL，见文件头注释与 REPORT 的来源说明）。

注意：meTypeset 镜像的 "Beta Version 070708" 副本是 XSLT 2.0，libxslt
（lxml/xsltproc）只支持 1.1，实测转换退化为纯文本拷贝，不可用；PaddleX 镜像的
正式版为 XSLT 1.0，lxml 可直接执行。

复跑：
    .venv/bin/pip install latex2mathml
    .venv/bin/python spikes/phase0/omml/convert_latex2mathml.py

输出：spikes/phase0/omml/results/latex2mathml_conversion.json
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from lxml import etree

SPIKE_DIR = Path(__file__).resolve().parent
CORPUS = SPIKE_DIR / "corpus" / "formulas.yaml"
XSL_PATH = SPIKE_DIR / "assets" / "MML2OMML.XSL"
RESULTS = SPIKE_DIR / "results"

OMML_ROOT = "{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath"


def main() -> None:
    from latex2mathml.converter import convert

    corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))["formulas"]
    transform = etree.XSLT(etree.parse(str(XSL_PATH)))

    entries = []
    for formula in corpus:
        entry: dict[str, object] = {"id": formula["id"], "latex": formula["latex"]}
        try:
            mathml = convert(formula["latex"])
        except Exception as error:  # noqa: BLE001 - spike 记录一切失败类型
            entry.update(
                {
                    "mathml_status": "failed",
                    "error_type": type(error).__name__,
                    "message": str(error).strip() or None,
                }
            )
            entries.append(entry)
            continue

        entry["mathml_status"] = "success"
        try:
            omml = transform(etree.fromstring(mathml.encode("utf-8")))
            fragment = etree.fromstring(
                etree.tostring(omml, encoding="utf-8")
            )
            entry["omml_status"] = (
                "success" if fragment.tag == OMML_ROOT else f"unexpected_root:{fragment.tag}"
            )
            entry["omml_omath_count"] = sum(
                1 for _ in fragment.iter(OMML_ROOT)
            )
        except Exception as error:  # noqa: BLE001
            entry.update(
                {
                    "omml_status": "failed",
                    "error_type": type(error).__name__,
                    "message": str(error).strip() or None,
                }
            )
        entries.append(entry)

    mathml_ok = sum(1 for entry in entries if entry["mathml_status"] == "success")
    omml_ok = sum(1 for entry in entries if entry.get("omml_status") == "success")
    summary = {
        "latex2mathml_version": "3.81.0",
        "xsl": "assets/MML2OMML.XSL (Microsoft Office 版，XSLT 1.0，镜像自 PaddlePaddle/PaddleX)",
        "total": len(entries),
        "mathml_success": mathml_ok,
        "mathml_coverage": round(mathml_ok / len(entries), 4),
        "omml_success": omml_ok,
        "omml_coverage": round(omml_ok / len(entries), 4),
        "mathml_failures": [
            {"id": e["id"], "error_type": e["error_type"], "message": e["message"]}
            for e in entries
            if e["mathml_status"] != "success"
        ],
    }

    RESULTS.mkdir(exist_ok=True)
    output = RESULTS / "latex2mathml_conversion.json"
    output.write_text(
        json.dumps({"summary": summary, "entries": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"total={summary['total']} mathml_ok={mathml_ok} omml_ok={omml_ok}")
    print(f"mathml_coverage={summary['mathml_coverage']:.2%}, omml_coverage={summary['omml_coverage']:.2%}")
    for failure in summary["mathml_failures"]:
        print(f"  FAILED {failure['id']}: {failure['error_type']}: {failure['message']}")
    print(f"-> {output}")


if __name__ == "__main__":
    main()
