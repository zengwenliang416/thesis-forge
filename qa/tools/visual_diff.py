#!/usr/bin/env python3
"""视觉回归最小闭环工具（QUALITY_STRATEGY §9 的 Phase 0 落地）。

对比基线 PDF 与候选 PDF，按 §9.2 分类输出结构化差异：

1. 页数一致性（不一致 → P0）；
2. 文本层 diff（pdftotext -layout 逐页提取；整行丢失/新增 → P0
   「内容丢失/新增」；其余空白/字距漂移归 P2）；
3. 光栅哈希（pdftoppm 120dpi 灰度逐页 sha256；不一致 → needs-review，
   不直接判 P0——光栅对渲染器版本敏感，§9.3 要求人工审后更新基线）。

基线形态：`qa/baselines/visual/<name>/manifest.json`（逐页文本/光栅
哈希 + 工具版本 + 变更台账字段）。基线更新必须 `--update-baseline`
显式触发并填写 reason/reviewer（§9.3：不得 CI 自动接受）。

离线确定性：仅依赖本机 poppler 工具（pdftotext/pdftoppm），缺失时对应
检查降级为 skipped 并在报告中说明，不判失败。

用法：
    python qa/tools/visual_diff.py <baseline.pdf> <candidate.pdf> \
        [--json <报告路径>] [--raster-dpi 120]
    python qa/tools/visual_diff.py --update-baseline <pdf> <基线目录> \
        --reason "..." --reviewer "..." [--issue "…"]

退出码：0 无 P0 差异；1 存在 P0 差异；2 输入/工具错误。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from difflib import unified_diff
from pathlib import Path

P0 = "P0"
P2 = "P2"
NEEDS_REVIEW = "needs-review"

_PDFTOTEXT = shutil.which("pdftotext")
_PDFTOPPM = shutil.which("pdftoppm")


def _run(command: list[str], *, timeout: float = 120.0) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def _page_count(pdf: Path) -> int:
    # pdfinfo 若缺失则退化为 pdftotext 输出页分隔符计数
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        result = _run([pdfinfo, str(pdf)])
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1].strip())
    with tempfile.TemporaryDirectory(prefix="tf-vis-") as tmp:
        text_path = Path(tmp) / "out.txt"
        result = _run([_PDFTOTEXT, str(pdf), str(text_path)])
        if result.returncode != 0:
            raise ValueError(f"pdftotext 失败：{result.stderr.strip()[:200]}")
        return text_path.read_text(encoding="utf-8", errors="replace").count("\f") or (
            1 if text_path.stat().st_size else 0
        )


def _page_texts(pdf: Path) -> list[str]:
    """逐页文本（保留 -layout 版式；页内空白归一）。"""

    result = _run([_PDFTOTEXT, "-layout", str(pdf), "-"])
    if result.returncode != 0:
        raise ValueError(f"pdftotext 失败：{result.stderr.strip()[:200]}")
    pages = result.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return ["\n".join(line.rstrip() for line in page.splitlines()) for page in pages]


def _raster_hashes(pdf: Path, dpi: int) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="tf-vis-raster-") as tmp:
        out = Path(tmp) / "page"
        result = _run(
            [_PDFTOPPM, "-gray", "-r", str(dpi), "-png", str(pdf), str(out)]
        )
        if result.returncode != 0:
            raise ValueError(f"pdftoppm 失败：{result.stderr.strip()[:200]}")
        return [
            hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(tmp).glob("page-*.png"))
        ]


def _tool_version(executable: str) -> str | None:
    result = _run([executable, "-v"], timeout=15)
    first = (result.stderr or result.stdout).splitlines()
    return first[0].strip() if first else None


def build_manifest(pdf: Path, *, dpi: int, reason: str, reviewer: str, issue: str) -> dict:
    if _PDFTOTEXT is None:
        raise ValueError("pdftotext 不可用，无法建立基线")
    texts = _page_texts(pdf)
    manifest = {
        "schema": "docforge/visual-baseline-v1",
        "source": str(pdf),
        "page_count": len(texts),
        "text_hashes": [hashlib.sha256(t.encode()).hexdigest() for t in texts],
        "raster": {
            "dpi": dpi,
            "hashes": _raster_hashes(pdf, dpi) if _PDFTOPPM else None,
            "skipped_reason": None if _PDFTOPPM else "pdftoppm 不可用",
        },
        "tools": {
            "pdftotext": _tool_version(_PDFTOTEXT),
            "pdftoppm": _tool_version(_PDFTOPPM) if _PDFTOPPM else None,
        },
        "change_log": [{"reason": reason, "reviewer": reviewer, "issue": issue}],
    }
    if manifest["raster"]["hashes"] is not None and len(
        manifest["raster"]["hashes"]
    ) != len(texts):
        raise ValueError("光栅页数与文本页数不一致，拒绝建基线")
    return manifest


def compare_pdfs(
    baseline_pdf: Path, candidate_pdf: Path, *, dpi: int = 120
) -> dict:
    """逐项比对，产出 §9.2 分类的差异报告（dict，JSON 可序列化）。"""

    findings: list[dict] = []
    skipped: list[str] = []
    if _PDFTOTEXT is None:
        raise ValueError("pdftotext 不可用：文本层与页数检查无法执行")

    base_count = _page_count(baseline_pdf)
    cand_count = _page_count(candidate_pdf)
    if base_count != cand_count:
        findings.append(
            {
                "severity": P0,
                "kind": "page-count-mismatch",
                "baseline": base_count,
                "candidate": cand_count,
            }
        )

    base_texts = _page_texts(baseline_pdf)
    cand_texts = _page_texts(candidate_pdf)
    text_diffs: list[dict] = []
    for index, (base, cand) in enumerate(zip(base_texts, cand_texts), start=1):
        if base == cand:
            continue
        diff_lines = [
            line
            for line in unified_diff(
                base.splitlines(), cand.splitlines(), lineterm="", n=0
            )
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        ]
        lost = [line[1:].strip() for line in diff_lines if line.startswith("-") and line[1:].strip()]
        added = [line[1:].strip() for line in diff_lines if line.startswith("+") and line[1:].strip()]
        severity = P0 if (lost or added) else P2
        text_diffs.append(
            {
                "page": index,
                "severity": severity,
                "lost_lines": lost[:20],
                "added_lines": added[:20],
                "diff": diff_lines[:40],
            }
        )
    findings.extend(text_diffs)

    if _PDFTOPPM is None:
        skipped.append("raster-hash：pdftoppm 不可用")
    else:
        base_raster = _raster_hashes(baseline_pdf, dpi)
        cand_raster = _raster_hashes(candidate_pdf, dpi)
        if len(base_raster) == len(cand_raster):
            for index, (b_hash, c_hash) in enumerate(zip(base_raster, cand_raster), start=1):
                if b_hash != c_hash:
                    findings.append(
                        {
                            "severity": NEEDS_REVIEW,
                            "kind": "raster-hash-mismatch",
                            "page": index,
                            "baseline": b_hash,
                            "candidate": c_hash,
                            "note": "光栅差异对渲染器版本敏感，人工审后更新基线（§9.3）",
                        }
                    )
        else:
            skipped.append(
                f"raster-hash：页数不一致（{len(base_raster)} vs {len(cand_raster)}），交由页数检查判定"
            )

    p0 = [f for f in findings if f.get("severity") == P0]
    return {
        "baseline": str(baseline_pdf),
        "candidate": str(candidate_pdf),
        "page_count": [base_count, cand_count],
        "ok": not p0,
        "p0_count": len(p0),
        "needs_review_count": sum(
            1 for f in findings if f.get("severity") == NEEDS_REVIEW
        ),
        "skipped": skipped,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("baseline", nargs="?", help="基线 PDF 路径")
    parser.add_argument("candidate", nargs="?", help="候选 PDF 路径")
    parser.add_argument("--json", dest="json_path", help="差异报告 JSON 输出路径")
    parser.add_argument("--raster-dpi", type=int, default=120)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="由 <baseline> 指向的 PDF 生成 <candidate> 指向的基线目录",
    )
    parser.add_argument("--reason", help="基线更新原因（§9.3 必填）")
    parser.add_argument("--reviewer", help="基线更新审查人（§9.3 必填）")
    parser.add_argument("--issue", default="", help="关联 issue/PR")
    args = parser.parse_args(argv)

    if not args.baseline:
        parser.error("缺少 baseline 参数")
    baseline = Path(args.baseline).expanduser()

    if args.update_baseline:
        if not args.candidate:
            parser.error("--update-baseline 需要 <pdf> <基线目录>")
        if not args.reason or not args.reviewer:
            print(
                "✗ 基线更新必须填写 --reason 与 --reviewer（§9.3）",
                file=sys.stderr,
            )
            return 2
        target_dir = Path(args.candidate).expanduser()
        try:
            manifest = build_manifest(
                baseline, dpi=args.raster_dpi, reason=args.reason,
                reviewer=args.reviewer, issue=args.issue,
            )
        except ValueError as error:
            print(f"✗ {error}", file=sys.stderr)
            return 2
        target_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = target_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"✓ 基线已更新：{manifest_path}（{manifest['page_count']} 页）")
        return 0

    if not args.candidate:
        parser.error("缺少 candidate 参数")
    candidate = Path(args.candidate).expanduser()
    try:
        report = compare_pdfs(baseline, candidate, dpi=args.raster_dpi)
    except ValueError as error:
        print(f"✗ {error}", file=sys.stderr)
        return 2

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    status = "✓ 无 P0 差异" if report["ok"] else f"✗ {report['p0_count']} 项 P0 差异"
    print(f"{status}（pages {report['page_count'][0]}→{report['page_count'][1]}，"
          f"needs-review {report['needs_review_count']}，skipped {len(report['skipped'])}）")
    for finding in report["findings"]:
        if finding.get("severity") == P0:
            kind = finding.get("kind") or f"page-{finding.get('page')}"
            print(f"  [P0] {kind}: 丢失 {len(finding.get('lost_lines', []))} 行 / "
                  f"新增 {len(finding.get('added_lines', []))} 行")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
