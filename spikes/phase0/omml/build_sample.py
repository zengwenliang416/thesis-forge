"""用项目完整管线构建 OMML 语料样例 DOCX，并做结构断言。

管线：parse_markdown → ValidationContext/validate_document → compile_document
      → DocxRenderer.render（与 thesis_forge.application.services 同一链路，
      仅跳过 LibreOffice 字段刷新与 PDF 预览，保持离线确定性）。

包含 corpus 中项目子集能转换的全部 display 公式（逐条 ::: equation 容器），
另加一段行内公式混排场景（现有语法不支持行内数学，作为事实记录）。

断言（lxml XPath，结果落盘 JSON）：
  1. 每个公式段落都有 m:oMath；
  2. 编号公式带 SEQ field（w:instrText 含 "SEQ TF_Equation_"，
     名称规则见 thesis_forge.core.compiler._sequence_instruction）；
  3. 编号公式带 bookmark（w:bookmarkStart 名 tf_eq_*）。

复跑：
    .venv/bin/python spikes/phase0/omml/build_sample.py

输出：
    spikes/phase0/omml/output/sample.docx
    spikes/phase0/omml/output/sample_thesis.md
    spikes/phase0/omml/results/omml_assertions.json
    spikes/phase0/omml/results/openxml_validate_report.json
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import yaml
from lxml import etree

SPIKE_DIR = Path(__file__).resolve().parent
ROOT = SPIKE_DIR.parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thesis_forge.core.compiler import compile_document
from thesis_forge.core.math import LatexMathConverter, MathConversionError
from thesis_forge.core.parser import parse_markdown
from thesis_forge.core.validator import ValidationContext, validate_document
from thesis_forge.renderers.docx import DocxRenderer

CORPUS = SPIKE_DIR / "corpus" / "formulas.yaml"
RESULTS = SPIKE_DIR / "results"
OUTPUT = SPIKE_DIR / "output"
TEMPLATE = ROOT / "templates" / "schools" / "example-university" / "2026.yaml"
VALIDATOR = ROOT / "qa" / "tools" / "openxml_validate.py"
PYTHON = ROOT / ".venv" / "bin" / "python"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
BOOKMARK_INVALID_RE = re.compile(r"[^A-Za-z0-9_]")


def bookmark_name(source_id: str) -> str:
    """与 thesis_forge.core.compiler._bookmark_name 同一规则。"""
    return f"tf_{BOOKMARK_INVALID_RE.sub('_', source_id)}"[:40]


def build_markdown(display: list[dict[str, str]], inline: list[dict[str, str]]) -> str:
    lines = [
        "---",
        "thesis:",
        "  title: OMML 语料验证样例",
        "author:",
        "  name: ThesisForge",
        "render:",
        "  template_id: example-university-2026",
        "---",
        "",
        "# 公式语料验证 {#chap:omml}",
        "",
        "以下公式来自 spikes/phase0/omml 语料库，覆盖项目 LaTeX 子集可转换的全部条目。",
        "",
    ]
    for formula in display:
        lines.append(f"{formula['id']}（{formula['scenario']}）：")
        lines.append("")
        lines.append(f"::: equation {{#eq:{formula['id']}}}")
        lines.append("$$")
        lines.append(formula["latex"])
        lines.append("$$")
        lines.append(":::")
        lines.append("")
    inline_text = "、".join(f"${formula['latex']}$" for formula in inline)
    lines.append(
        f"行内混排场景：正文中夹注公式 {inline_text}，观察其是否被转换为 OMML。"
    )
    lines.append("")
    lines.append(f"交叉引用：式 @eq:{display[0]['id']} 为语料第一条编号公式。")
    lines.append("")
    return "\n".join(lines)


def run_pipeline(markdown_path: Path, output_path: Path) -> dict[str, object]:
    document = parse_markdown(markdown_path)
    context = ValidationContext.from_document(document, template_path=TEMPLATE)
    issues = validate_document(document, context)
    errors = [issue for issue in issues if issue.severity == "error"]
    if errors:
        raise RuntimeError(f"验证未通过: {[str(e) for e in errors]}")
    if context.template is None:
        raise RuntimeError("模板未成功解析")
    plan = compile_document(
        document,
        template=context.template,
        template_path=context.template_path,
        bibliography_database=context.bibliography_database,
    )
    renderer = DocxRenderer()
    renderer.render(plan, output_path)
    return {
        "equation_instructions": sum(
            1 for node in plan.nodes if node.kind == "equation"
        ),
        "validation_issue_count": len(issues),
    }


def run_openxml_validate(docx_path: Path) -> dict[str, object]:
    report_path = RESULTS / "openxml_validate_report.json"
    completed = subprocess.run(
        [str(PYTHON), str(VALIDATOR), "--json", str(report_path), str(docx_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "exit_code": completed.returncode,
        "report_path": str(report_path),
        "stdout": completed.stdout.strip() or None,
        "stderr": completed.stderr.strip() or None,
    }


def assert_omml_structure(
    docx_path: Path, display: list[dict[str, str]], inline: list[dict[str, str]]
) -> dict[str, object]:
    with ZipFile(docx_path) as package:
        document = etree.fromstring(package.read("word/document.xml"))

    omath_nodes = document.xpath(".//m:oMath", namespaces=NS)
    seq_fields = [
        " ".join(text.split())
        for text in document.xpath(".//w:instrText/text()", namespaces=NS)
        if text.strip().startswith("SEQ TF_Equation_")
    ]
    bookmark_names = document.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)

    per_equation = []
    for formula in display:
        source_id = f"eq:{formula['id']}"
        name = bookmark_name(source_id)
        starts = document.xpath(
            f".//w:bookmarkStart[@w:name='{name}']", namespaces=NS
        )
        paragraph = starts[0].getparent() if starts else None
        has_omath = (
            paragraph is not None
            and bool(paragraph.xpath(".//m:oMath", namespaces=NS))
        )
        has_seq = (
            paragraph is not None
            and any(
                text.strip().startswith("SEQ TF_Equation_")
                for text in paragraph.xpath(".//w:instrText/text()", namespaces=NS)
            )
        )
        per_equation.append(
            {
                "id": formula["id"],
                "bookmark": name,
                "bookmark_found": bool(starts),
                "has_omath": has_omath,
                "has_seq_field": has_seq,
                "ok": bool(starts) and has_omath and has_seq,
            }
        )

    body_text = "".join(document.xpath(".//w:body//w:t/text()", namespaces=NS))
    inline_evidence = [
        {
            "id": formula["id"],
            "latex": formula["latex"],
            "found_as_literal_text": formula["latex"] in body_text,
        }
        for formula in inline
    ]

    return {
        "omath_total": len(omath_nodes),
        "omath_expected": len(display),
        "seq_equation_field_count": len(seq_fields),
        "bookmark_total": len(bookmark_names),
        "per_equation": per_equation,
        "per_equation_all_ok": all(item["ok"] for item in per_equation),
        "inline_math_converted": any(
            paragraph.xpath(".//m:oMath", namespaces=NS)
            for paragraph in document.xpath(".//w:p", namespaces=NS)
            if "$" in "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))
        ),
        "inline_literal_evidence": inline_evidence,
    }


def main() -> None:
    corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
    converter = LatexMathConverter()
    display, inline = [], []
    skipped = []
    for formula in corpus["formulas"]:
        try:
            converter.convert(formula["latex"])
        except MathConversionError as error:
            skipped.append({"id": formula["id"], "reason": str(error)})
            continue
        (inline if formula["usage"] == "inline" else display).append(formula)

    OUTPUT.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    markdown_path = OUTPUT / "sample_thesis.md"
    markdown_path.write_text(build_markdown(display, inline), encoding="utf-8")
    docx_path = OUTPUT / "sample.docx"

    pipeline_info = run_pipeline(markdown_path, docx_path)
    validation = run_openxml_validate(docx_path)
    assertions = assert_omml_structure(docx_path, display, inline)

    report = {
        "display_equations_included": len(display),
        "inline_formulas": [formula["id"] for formula in inline],
        "skipped_by_subset": skipped,
        "pipeline": pipeline_info,
        "openxml_validate": validation,
        "assertions": assertions,
    }
    output = RESULTS / "omml_assertions.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"included display equations: {len(display)}, skipped: {len(skipped)}")
    print(f"m:oMath total={assertions['omath_total']} expected={assertions['omath_expected']}")
    print(f"SEQ equation fields={assertions['seq_equation_field_count']}")
    print(f"per_equation_all_ok={assertions['per_equation_all_ok']}")
    print(f"inline_math_converted={assertions['inline_math_converted']}")
    print(f"openxml_validate exit={validation['exit_code']}")
    print(f"-> {docx_path}")
    print(f"-> {output}")


if __name__ == "__main__":
    main()
