"""qa/tools/visual_diff.py 最小闭环测试（QUALITY_STRATEGY §9 Phase 0）。

用程序化生成的最小确定性 PDF（正确 xref 表）驱动正负例；依赖本机
pdftotext（缺失时整文件 skip，与 soffice/pandoc 集成测试同款守卫）。
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "qa" / "tools" / "visual_diff.py"

HAS_PDFTOTEXT = shutil.which("pdftotext") is not None

_spec = importlib.util.spec_from_file_location("visual_diff", TOOL)
visual_diff = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("visual_diff", visual_diff)
_spec.loader.exec_module(visual_diff)

pytestmark = pytest.mark.skipif(not HAS_PDFTOTEXT, reason="pdftotext not available")


def _minimal_pdf(texts: list[str]) -> bytes:
    """生成 n 页、每页一段 Helvetica 文本的最小 PDF（xref 偏移精确）。"""

    objects: list[bytes] = []
    page_ids: list[int] = []
    next_id = 3  # 1=Catalog 2=Pages，正文对象从 3 起
    content_ids: list[int] = []
    for text in texts:
        page_id = next_id
        content_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)
        content_ids.append(content_id)
        escaped = text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode()
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 "
            b"/BaseFont /Helvetica >> >> >> /Contents "
            + f"{content_id} 0 R".encode()
            + b" >>"
        )
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        )
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    header = b"%PDF-1.4\n"
    body = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    body += f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>\nendobj\n".encode()
    chunks = [header, body]
    offsets = [0]
    length = len(header) + len(body)
    offsets.append(length)
    for index, obj in enumerate(objects, start=3):
        chunk = f"{index} 0 obj\n".encode() + obj + b"\nendobj\n"
        chunks.append(chunk)
        length += len(chunk)
        offsets.append(length)
    xref_pos = length
    xref = f"xref\n0 {len(objects) + 3}\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        xref += f"{offset:010d} 00000 n \n"
    trailer = (
        f"trailer\n<< /Size {len(objects) + 3} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    )
    return b"".join(chunks) + xref.encode() + trailer.encode()


@pytest.fixture
def base_pdf(tmp_path: Path) -> Path:
    pdf = tmp_path / "base.pdf"
    pdf.write_bytes(_minimal_pdf(["Chapter One Intro", "Chapter Two Methods"]))
    return pdf


def test_identical_pdfs_pass(base_pdf: Path, tmp_path: Path) -> None:
    twin = tmp_path / "twin.pdf"
    twin.write_bytes(base_pdf.read_bytes())

    report = visual_diff.compare_pdfs(base_pdf, twin)

    assert report["ok"] is True
    assert report["p0_count"] == 0
    assert report["page_count"] == [2, 2]


def test_content_loss_is_p0(base_pdf: Path, tmp_path: Path) -> None:
    changed = tmp_path / "changed.pdf"
    changed.write_bytes(_minimal_pdf(["Chapter One Intro", "Chapter Three Conclusion"]))

    report = visual_diff.compare_pdfs(base_pdf, changed)

    assert report["ok"] is False
    p0 = [f for f in report["findings"] if f["severity"] == "P0"]
    assert p0, "整行内容变化必须判 P0"
    page2 = next(f for f in p0 if f.get("page") == 2)
    assert "Chapter Two Methods" in page2["lost_lines"]
    assert "Chapter Three Conclusion" in page2["added_lines"]


def test_page_count_mismatch_is_p0(base_pdf: Path, tmp_path: Path) -> None:
    shorter = tmp_path / "shorter.pdf"
    shorter.write_bytes(_minimal_pdf(["Chapter One Intro"]))

    report = visual_diff.compare_pdfs(base_pdf, shorter)

    assert report["ok"] is False
    assert any(
        f.get("kind") == "page-count-mismatch" and f["severity"] == "P0"
        for f in report["findings"]
    )


def test_baseline_update_requires_reason_and_reviewer(base_pdf: Path, tmp_path: Path) -> None:
    target = tmp_path / "baseline" / "cover"

    exit_no_reason = visual_diff.main(
        ["--update-baseline", str(base_pdf), str(target)]
    )
    assert exit_no_reason == 2
    assert not target.exists()

    exit_ok = visual_diff.main(
        [
            "--update-baseline", str(base_pdf), str(target),
            "--reason", "Alpha gate 首建基线", "--reviewer", "zwl",
        ]
    )
    assert exit_ok == 0
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "thesisforge/visual-baseline-v1"
    assert manifest["page_count"] == 2
    assert len(manifest["text_hashes"]) == 2
    assert manifest["change_log"][0]["reviewer"] == "zwl"


def test_cli_exit_codes(base_pdf: Path, tmp_path: Path) -> None:
    twin = tmp_path / "twin.pdf"
    twin.write_bytes(base_pdf.read_bytes())
    changed = tmp_path / "changed.pdf"
    changed.write_bytes(_minimal_pdf(["Chapter One Intro", "Different"]))
    json_path = tmp_path / "report.json"

    assert (
        visual_diff.main([str(base_pdf), str(twin), "--json", str(json_path)]) == 0
    )
    assert json.loads(json_path.read_text(encoding="utf-8"))["ok"] is True
    assert visual_diff.main([str(base_pdf), str(changed)]) == 1
