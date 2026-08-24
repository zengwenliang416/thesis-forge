#!/usr/bin/env python3
"""Seam probe: template-v2-build-pipeline-p1 component-seam prototype.

只读探针（不修改生产代码）：验证设计 D1-D5 的组件接缝假设。
回答三个问题：
  S1  v2 包 API（load_package / lint / pack+unpack / merge_into_shell）
      从 application 层可直接消费的签名与产物。
  S2  v2 resolved_data -> ThesisTemplate 映射可行性：字段差集证据。
  S3  migrate 产出的真实 HUT v2 包可加载、可 lint、可映射（字段差集）。

用法: PYTHONPATH=<repo>/src python3 seam_probe.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "src"))

from thesis_forge.templates.model import ThesisTemplate
from thesis_forge.templates.v2 import (
    lint_package,
    load_package,
    merge_into_shell,
    migrate_template,
    pack_package,
    unpack_package,
)

SAMPLE_PKG = REPO / "spikes" / "phase0" / "docx-template" / "package-sample"
HUT_V03 = REPO / "templates" / "schools" / "hunan-university-of-technology" / "master-2026.yaml"


def probe_sample_package() -> dict:
    out = {"sample_load": None, "lint": None, "tftpl_roundtrip": None, "merge_signature": None}
    pkg = load_package(SAMPLE_PKG)
    out["sample_load"] = {
        "id": pkg.template.id,
        "schema_version": pkg.template.schema_version,
        "reference_docx": pkg.reference_docx.is_file(),
        "shell_docx": pkg.shell_docx.is_file() if pkg.shell_docx else None,
        "resolved_data_keys": sorted(pkg.resolved_data.keys()),
    }
    report = lint_package(SAMPLE_PKG, level="L2")
    out["lint"] = {"has_errors": report.has_errors, "issues": len(report.issues)}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        tftpl = tmp / "sample.tftpl"
        pack_package(SAMPLE_PKG, tftpl)
        unpacked = tmp / "unpacked"
        unpack_package(tftpl, unpacked)
        reloaded = load_package(unpacked)
        out["tftpl_roundtrip"] = {
            "packed_bytes": tftpl.stat().st_size,
            "reload_id": reloaded.template.id,
            "shell_after_unpack": reloaded.shell_docx.is_file() if reloaded.shell_docx else None,
        }
    # merge_into_shell 签名探针：以最小 compiled docx 验证锚点合并入口可调
    from thesis_forge.core.parser import parse_markdown_text

    from thesis_forge.core.compiler import compile_document
    from thesis_forge.renderers.docx import DocxRenderer

    md = "# 摘要 {#chap:abstract-zh}\n\n正文段落。\n"
    doc = parse_markdown_text(md, source_path=Path("probe.md"))
    plan = compile_document(doc)
    with tempfile.TemporaryDirectory() as tmp2:
        tmp2 = Path(tmp2)
        rendered = tmp2 / "rendered.docx"
        merged = tmp2 / "merged.docx"
        DocxRenderer().render(plan, rendered)
        ledger = merge_into_shell(SAMPLE_PKG / "shell.docx", rendered, merged)
        out["merge_signature"] = {
            "output_exists": merged.is_file(),
            "ledger_keys": sorted(ledger.__dict__.keys()) if hasattr(ledger, "__dict__") else "n/a",
            "output_bytes": merged.stat().st_size,
        }
    return out


def probe_hut_mapping() -> dict:
    out = {"migrate": None, "load": None, "direct_validate": None}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pkg_dir = tmp / "hut-v2"
        try:
            report = migrate_template(HUT_V03, pkg_dir)
            out["migrate"] = {"ok": True, "summary": report.summary, "entries": len(report.entries)}
        except Exception as error:  # noqa: BLE001
            out["migrate"] = {"ok": False, "error": str(error)[:300]}
            return out
        pkg = load_package(pkg_dir)
        out["load"] = {
            "id": pkg.template.id,
            "reference_docx": pkg.reference_docx.is_file(),
            "shell_docx": pkg.shell_docx.is_file() if pkg.shell_docx else None,
            "resolved_keys": sorted(pkg.resolved_data.keys()),
        }
        # 映射可行性：resolved_data 直接喂 ThesisTemplate.model_validate
        try:
            ThesisTemplate.model_validate(pkg.resolved_data)
            out["direct_validate"] = {"ok": True, "detail": "resolved_data 可直接构造 ThesisTemplate"}
        except Exception as error:  # noqa: BLE001
            import pydantic

            if isinstance(error, pydantic.ValidationError):
                missing = sorted({e["loc"][0] for e in error.errors() if e["type"] == "missing"})
                types = sorted(
                    {
                        ".".join(str(p) for p in e["loc"])
                        for e in error.errors()
                        if e["type"] != "missing"
                    }
                )
                out["direct_validate"] = {
                    "ok": False,
                    "error_count": len(error.errors()),
                    "missing_top_fields": missing,
                    "other_error_locs": types[:20],
                }
            else:
                out["direct_validate"] = {"ok": False, "error": str(error)[:300]}
    return out


def main() -> int:
    result = {
        "question": "v2 build pipeline component seams (classifier/mapping/shell-merge) feasible?",
        "sample_package": probe_sample_package(),
        "hut_mapping": probe_hut_mapping(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
