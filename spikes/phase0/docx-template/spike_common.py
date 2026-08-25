#!/usr/bin/env python3
"""Phase 0 docx-template spike 共享工具。

提供：统一路径、openxml_validate 调用、纯 stdlib 占位 PNG 生成、
soffice 冒烟转换。所有产物落盘在 spike 目录内，不依赖 /tmp。

用法（被 build_reference.py / build_shell.py / merge_into_shell.py 导入）：
    from spike_common import ...
"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SPIKE_DIR.parents[2]
PACKAGE_DIR = SPIKE_DIR / "package-sample"
ASSETS_DIR = PACKAGE_DIR / "assets"
OUTPUT_DIR = SPIKE_DIR / "output"
VALIDATOR = REPO_ROOT / "qa" / "tools" / "openxml_validate.py"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

NS = {
    "w": W_NS,
    "r": R_NS,
    "pr": PR_NS,
    "wp": WP_NS,
    "a": A_NS,
    "ct": CT_NS,
}


def ensure_dirs() -> None:
    """创建产物目录。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def run_openxml_validate(docx_path: Path) -> dict:
    """调用 qa/tools/openxml_validate.py，返回解析后的 JSON 报告。"""
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(docx_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    report["exit_code"] = result.returncode
    return report


def write_placeholder_png(path: Path, *, width: int = 480, height: int = 240) -> None:
    """用纯 stdlib 写一张确定性占位 PNG（蓝底白带 + 边框），模拟学校 logo。

    避免引入 Pillow 依赖；同参数生成字节完全一致，保证可重复构建。
    """

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    rows = bytearray()
    for y in range(height):
        rows.append(0)  # filter type: None
        for x in range(width):
            border = x < 4 or y < 4 or x >= width - 4 or y >= height - 4
            band = height // 3 <= y < 2 * height // 3
            if border:
                rgb = (0x1F, 0x3B, 0x73)
            elif band:
                rgb = (0xFF, 0xFF, 0xFF)
            else:
                rgb = (0x2E, 0x5C, 0xB8)
            rows.extend(rgb)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def soffice_smoke(docx_path: Path, *, work_dir: Path) -> dict:
    """用 LibreOffice 无头模式把 docx 转成 PDF，证明目标应用可无修复打开。

    UserInstallation 指向 spike 目录内的 profile，避免污染用户配置、避免 /tmp。
    soffice 不可用时返回 available=False，调用方据此降级为跳过。
    """
    soffice = shutil.which("soffice")
    if soffice is None:
        return {"available": False, "ok": False, "detail": "soffice 不在 PATH"}
    pdf_dir = work_dir / "pdf"
    profile_dir = work_dir / "lo-profile"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    profile_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            soffice,
            "--headless",
            "--norestore",
            f"-env:UserInstallation=file://{profile_dir}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_dir),
            str(docx_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    pdf_path = pdf_dir / f"{docx_path.stem}.pdf"
    ok = result.returncode == 0 and pdf_path.is_file() and pdf_path.stat().st_size > 0
    return {
        "available": True,
        "ok": ok,
        "returncode": result.returncode,
        "pdf": str(pdf_path) if pdf_path.is_file() else None,
        "pdf_bytes": pdf_path.stat().st_size if pdf_path.is_file() else 0,
        "stderr": result.stderr.strip()[-500:],
    }


def summarize_validation(report: dict) -> str:
    """把 openxml_validate 报告压成一行可读结论。"""
    failed = [c for c in report.get("checks", []) if c["status"] != "pass"]
    if not failed:
        return f"PASS ({report['summary']['total']} 项)"
    names = ", ".join(c["name"] for c in failed)
    return f"FAIL: {names}"
