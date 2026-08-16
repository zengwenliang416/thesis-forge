#!/usr/bin/env python3
"""Phase 0 字段实证：LibreOffice finalizer（无头刷新）对字段的改写。

对每个样本：
1. 复制到临时目录（不动原样本）；
2. 走生产同款路径 refresh_document_safely(LibreOfficeDocumentRefresher, copy)；
3. 对比刷新前后 word/document.xml 的字段 cached result、TOC 区域文本、
   bookmark 清单、settings.xml 的 updateFields；
4. 刷新后的副本再跑 openxml_validate；
5. 差异写入 results/lo-refresh-diff.json，刷新后副本保留在
   samples/<stem>-lo-refreshed.docx 供人工抽查。

注意：office_refresh._run_libreoffice_refresh 在 darwin 上硬编码
tempfile dir="/tmp"，本机 /tmp 悬空（/private/tmp 缺失）会导致刷新失败。
本脚本通过 LibreOfficeDocumentRefresher.runner 注入点替换为等价实现
（复用 office_refresh 的 UNO 脚本与进程管理助手，仅临时目录改用
tempfile 默认行为），不修改项目既有文件。

用法：
    .venv/bin/python spikes/phase0/fields/verify_lo_refresh.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

from lxml import etree

SPIKE_DIR = Path(__file__).resolve().parent
ROOT = SPIKE_DIR.parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thesis_forge.application import office_refresh

SAMPLES_DIR = SPIKE_DIR / "samples"
RESULTS_DIR = SPIKE_DIR / "results"
OPENXML_VALIDATE = ROOT / "qa" / "tools" / "openxml_validate.py"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W = f"{{{W_NS}}}"
STORY_PART = re.compile(r"^word/(document|header\d*|footer\d*)\.xml$")


def _macos_safe_runner(
    executable: Path,
    python_executable: Path,
    document_path: Path,
    timeout_seconds: float,
    max_level: int,
) -> None:
    """等价于 office_refresh._run_libreoffice_refresh，但不硬编码 /tmp。"""
    with tempfile.TemporaryDirectory(prefix="thesisforge-lo-") as profile_name:
        profile_path = Path(profile_name).resolve()
        pipe_name = f"thesisforge_{uuid.uuid4().hex}"
        connection_timeout = max(1.0, timeout_seconds - 10.0)
        command = (
            str(executable),
            "--headless",
            "--nologo",
            "--nodefault",
            "--nofirststartwizard",
            "--norestore",
            f"-env:UserInstallation={profile_path.as_uri()}",
            f"--accept=pipe,name={pipe_name};urp;",
        )
        process, job = office_refresh.start_office_process(command)
        try:
            helper = subprocess.run(
                (
                    str(python_executable),
                    "-B",
                    "-c",
                    office_refresh._UNO_REFRESH_SCRIPT,
                    pipe_name,
                    document_path.resolve().as_uri(),
                    str(connection_timeout),
                    str(max_level),
                ),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            if helper.returncode != 0:
                detail = (helper.stderr or helper.stdout).strip()
                raise RuntimeError(
                    "LibreOffice UNO refresh failed"
                    + (f": {detail[-500:]}" if detail else "")
                )
        finally:
            office_refresh.terminate_office_process_tree(process, windows_job=job)


def _snapshot(path: Path) -> dict:
    """字段 cached result、TOC 区域文本、bookmark、updateFields 的快照。"""
    parts: dict[str, dict] = {}
    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        for name in sorted(n for n in names if STORY_PART.match(n)):
            root = etree.fromstring(package.read(name))
            fields: list[dict] = []
            stack: list[dict] = []
            for element in root.iter():
                if element.tag == f"{W}fldChar":
                    kind = element.get(f"{W}fldCharType")
                    if kind == "begin":
                        stack.append({"instruction": "", "result": [], "sep": False})
                    elif kind == "separate" and stack:
                        stack[-1]["sep"] = True
                    elif kind == "end" and stack:
                        fields.append(stack.pop())
                elif (
                    element.tag == f"{W}instrText" and stack and not stack[-1]["sep"]
                ):
                    stack[-1]["instruction"] += element.text or ""
                elif element.tag == f"{W}t" and stack and stack[-1]["sep"]:
                    stack[-1]["result"].append(element.text or "")
            bookmarks = sorted(
                root.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
            )
            parts[name] = {
                "fields": [
                    {
                        "instruction": " ".join(f["instruction"].split()),
                        "cached_result": "".join(f["result"]),
                    }
                    for f in fields
                ],
                "bookmarks": bookmarks,
            }
        settings = etree.fromstring(package.read("word/settings.xml"))
        update_fields = settings.find(f"{W}updateFields")
        update_fields_val = (
            update_fields.get(f"{W}val") if update_fields is not None else None
        )
    document_fields = parts.get("word/document.xml", {}).get("fields", [])
    toc_field = next(
        (f for f in document_fields if f["instruction"].startswith("TOC ")), None
    )
    return {
        "update_fields_setting": update_fields_val,
        "toc_cached_result": toc_field["cached_result"] if toc_field else None,
        "parts": parts,
    }


def _diff(before: dict, after: dict) -> dict:
    field_diffs = []
    part_names = sorted(set(before["parts"]) | set(after["parts"]))
    for part in part_names:
        before_fields = before["parts"].get(part, {}).get("fields", [])
        after_fields = after["parts"].get(part, {}).get("fields", [])
        if before_fields == after_fields:
            continue
        field_diffs.append(
            {
                "part": part,
                "before": before_fields,
                "after": after_fields,
            }
        )
    bookmark_diffs = []
    for part in part_names:
        b = set(before["parts"].get(part, {}).get("bookmarks", []))
        a = set(after["parts"].get(part, {}).get("bookmarks", []))
        if b != a:
            bookmark_diffs.append(
                {"part": part, "removed": sorted(b - a), "added": sorted(a - b)}
            )
    return {
        "update_fields_setting": {
            "before": before["update_fields_setting"],
            "after": after["update_fields_setting"],
        },
        "toc_cached_result_changed": (
            before["toc_cached_result"] != after["toc_cached_result"]
        ),
        "toc_cached_result_after_preview": (
            (after["toc_cached_result"] or "")[:400]
        ),
        "field_diffs": field_diffs,
        "bookmark_diffs": bookmark_diffs,
    }


def _openxml_ok(path: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(OPENXML_VALIDATE), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return {"exit_code": proc.returncode, "report": json.loads(proc.stdout)}


def experiment(sample: Path) -> dict:
    workdir = Path(tempfile.mkdtemp(prefix="tf-lo-refresh-"))
    copy = workdir / sample.name
    shutil.copyfile(sample, copy)
    try:
        before = _snapshot(copy)
        executable = office_refresh.discover_libreoffice_executable()
        if executable is None:
            return {"file": sample.name, "error": "未找到 LibreOffice"}
        python_executable = office_refresh.discover_libreoffice_python(executable)
        if python_executable is None:
            return {"file": sample.name, "error": "未找到可 import uno 的 python"}
        refresher = office_refresh.LibreOfficeDocumentRefresher(
            executable=executable,
            python_executable=python_executable,
            timeout_seconds=120.0,
            runner=_macos_safe_runner,
        )
        refreshed = office_refresh.refresh_document_safely(refresher, copy)
        result = {
            "file": sample.name,
            "libreoffice_executable": str(executable),
            "refreshed": refreshed,
        }
        if refreshed:
            after = _snapshot(copy)
            result["diff"] = _diff(before, after)
            result["openxml_validate_after"] = {
                "exit_code": _openxml_ok(copy)["exit_code"],
            }
            kept = SAMPLES_DIR / f"{sample.stem}-lo-refreshed.docx"
            shutil.copyfile(copy, kept)
            result["refreshed_copy"] = str(kept)
        return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    samples = sorted(
        path
        for path in SAMPLES_DIR.glob("*.docx")
        if not path.name.startswith(("._", "~$"))
        and "-lo-refreshed" not in path.stem
        and "-no-updatefields" not in path.stem
        and "-keep-updatefields" not in path.stem
    )
    if not samples:
        print("samples/ 下没有 docx，先运行 build_samples.py", file=sys.stderr)
        return 2
    report = {}
    for sample in samples:
        print(f"lo refresh experiment: {sample.stem}")
        report[sample.stem] = experiment(sample)
        print(f"  refreshed={report[sample.stem].get('refreshed')}")
    output = RESULTS_DIR / "lo-refresh-diff.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"written {output}")
    return 0 if all(r.get("refreshed") for r in report.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
