#!/usr/bin/env python3
"""三办公软件「无修复打开」验证工具（macOS）。

验证 Microsoft Word / WPS / LibreOffice 能否无修复提示地打开生成的 .docx，
输出 JSON 证据（应用、版本、结果、耗时、备注）。被测文件只读打开，
Word/WPS 侧一律「关闭不保存」，不会修改被测文件。

结果取值：
    pass                  打开成功且无修复迹象
    fail                  打开失败、超时或疑似修复对话框
    pending-human-review  已打开但无法脚本判断（WPS），需人工确认
    skipped               本机未安装该应用

用法：
    python qa/tools/no_repair_open.py <file.docx> [--apps word,libreoffice,wps]
        [--timeout 90] [--json <证据路径>]

退出码：0 全部通过（pending-human-review / skipped 不计失败）；1 存在失败；2 文件不可读。
"""

from __future__ import annotations

import argparse
import json
import plistlib
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

LIBREOFFICE_BIN = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
WORD_APP = Path("/Applications/Microsoft Word.app")
WPS_APP_CANDIDATES = (
    Path("/Applications/wpsoffice.app"),
    Path("/Applications/WPS Office.app"),
)

# 结果取值中不算失败的集合
NON_FAILURE = {"pass", "pending-human-review", "skipped"}


def _record(app: str, version: str, result: str, duration: float, notes: str) -> dict:
    return {
        "app": app,
        "version": version,
        "result": result,
        "duration_seconds": round(duration, 2),
        "notes": notes,
    }


def _app_version(app_path: Path) -> str:
    """从 .app 的 Info.plist 读取版本号。"""
    plist = app_path / "Contents" / "Info.plist"
    try:
        with plist.open("rb") as stream:
            data = plistlib.load(stream)
    except (OSError, plistlib.InvalidFileException):
        return "unknown"
    return str(
        data.get("CFBundleShortVersionString") or data.get("CFBundleVersion") or "unknown"
    )


def _escape_applescript(text: str) -> str:
    # AppleScript 字符串字面量转义
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _run_osascript(script: str, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _find_soffice() -> str | None:
    found = shutil.which("soffice")
    if found:
        return found
    if LIBREOFFICE_BIN.is_file():
        return str(LIBREOFFICE_BIN)
    return None


def _soffice_version(soffice: str) -> str:
    try:
        proc = subprocess.run(
            [soffice, "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    # 形如 "LibreOffice 25.2.3.2 ..."，取第二个字段
    parts = proc.stdout.split()
    return parts[1] if len(parts) >= 2 else "unknown"


def check_libreoffice(docx: Path, timeout: int = 90) -> dict:
    """headless 转 PDF：成功且产出 PDF 视为 pass。"""
    start = time.monotonic()
    soffice = _find_soffice()
    if soffice is None:
        return _record("libreoffice", "unknown", "skipped", 0.0, "未找到 soffice，跳过")
    version = _soffice_version(soffice)
    tmpdir = Path(tempfile.mkdtemp(prefix="tf-no-repair-lo-"))
    try:
        # 独立用户配置，避免与运行中的 LibreOffice 实例冲突
        profile = tmpdir / "lo-profile"
        command = [
            soffice,
            f"-env:UserInstallation=file://{profile}",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmpdir),
            str(docx),
        ]
        try:
            proc = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, check=False
            )
        except subprocess.TimeoutExpired:
            return _record(
                "libreoffice",
                version,
                "fail",
                time.monotonic() - start,
                f"转换超时（>{timeout}s）",
            )
        output = (proc.stdout + proc.stderr).strip()
        pdf = tmpdir / f"{docx.stem}.pdf"
        if proc.returncode == 0 and pdf.is_file():
            return _record(
                "libreoffice",
                version,
                "pass",
                time.monotonic() - start,
                f"成功导出 PDF（{pdf.stat().st_size} 字节）",
            )
        return _record(
            "libreoffice",
            version,
            "fail",
            time.monotonic() - start,
            f"退出码 {proc.returncode}；输出: {output[-500:]}",
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _word_dialog_note() -> str:
    """用 System Events 探测 Word 对话框/Sheet；无权限时降级。"""
    script = (
        'tell application "System Events"\n'
        '    if not (exists process "Microsoft Word") then return "0"\n'
        '    tell process "Microsoft Word"\n'
        '        set d to count of (windows whose subrole is "AXDialog" '
        'or subrole is "AXSystemDialog")\n'
        "        set s to 0\n"
        "        repeat with w in windows\n"
        "            try\n"
        "                set s to s + (count of sheets of w)\n"
        "            end try\n"
        "        end repeat\n"
        "        return (d + s) as text\n"
        "    end tell\n"
        "end tell\n"
    )
    try:
        proc = _run_osascript(script, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return "对话框探测失败，仅依据 open 成败判断"
    if proc.returncode != 0:
        return "System Events 无辅助功能权限，降级为仅依据 open 成败判断"
    count = proc.stdout.strip()
    if count and count != "0":
        return f"探测到 {count} 个 Word 对话框，疑似修复提示"
    return "未探测到对话框"


def _word_document_opened(path: str) -> bool:
    """轮询用：Word 文档集合中是否已出现目标路径。

    Word 的 full name 返回 HFS 路径（Macintosh HD:private:...），
    需用 POSIX file  coercion 转成同一形式再比较。
    """
    script = (
        f'set targetPath to POSIX file "{_escape_applescript(path)}" as text\n'
        'tell application "Microsoft Word"\n'
        "    set docPaths to full name of every document\n"
        "    if docPaths is missing value then set docPaths to {}\n"
        "    if class of docPaths is not list then set docPaths to {docPaths}\n"
        "    if docPaths contains targetPath then return true\n"
        "    return false\n"
        "end tell\n"
    )
    try:
        proc = _run_osascript(script, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _word_close_without_saving(path: str) -> None:
    """尽力关闭 Word 中本测试文档（不保存），按完整路径匹配，不影响其它文档。"""
    script = (
        f'set targetPath to POSIX file "{_escape_applescript(path)}" as text\n'
        'tell application "Microsoft Word"\n'
        "    repeat 10 times\n"
        "        set docPaths to full name of every document\n"
        "        if docPaths is missing value then exit repeat\n"
        "        if class of docPaths is not list then set docPaths to {docPaths}\n"
        "        if docPaths does not contain targetPath then exit repeat\n"
        "        set docName to name of (first document whose full name is targetPath)\n"
        "        close document docName saving no\n"
        "        delay 1\n"
        "    end repeat\n"
        "end tell\n"
    )
    try:
        _run_osascript(script, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        pass


def check_word(docx: Path, timeout: int = 90) -> dict:
    """activate + Word 自身 open 命令打开文档并轮询确认；最后关闭不保存。

    不用 Finder/`open -a`：实测该路径下 Word 可能长时间不处理打开请求。
    open 事件会进入 Word 事件队列，冷启动时 osascript 调用可能超时，
    但事件仍会被处理，因此 open 失败不直接判负，以轮询结果为准。
    """
    start = time.monotonic()
    if not WORD_APP.is_dir():
        return _record("word", "unknown", "skipped", 0.0, "未安装 Microsoft Word，跳过")
    version = _app_version(WORD_APP)
    path = str(docx.resolve())
    activate = 'tell application "Microsoft Word" to activate'
    open_doc = (
        'tell application "Microsoft Word" to open POSIX file '
        f'"{_escape_applescript(path)}"'
    )
    try:
        _run_osascript(activate, timeout=30)
        _run_osascript(open_doc, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        pass  # 打开事件可能已入队，交给轮询判断
    deadline = start + timeout
    opened = False
    while time.monotonic() < deadline:
        if _word_document_opened(path):
            opened = True
            break
        time.sleep(2)
    if not opened:
        # 超时未打开：常见原因是模态修复对话框挡住了事件处理
        notes = [f"文档未在 {timeout}s 内打开，疑似模态对话框（修复提示）", _word_dialog_note()]
        _word_close_without_saving(path)
        return _record("word", version, "fail", time.monotonic() - start, "；".join(notes))
    dialog_note = _word_dialog_note()
    _word_close_without_saving(path)
    if "疑似修复提示" in dialog_note:
        return _record("word", version, "fail", time.monotonic() - start, dialog_note)
    return _record(
        "word",
        version,
        "pass",
        time.monotonic() - start,
        f"打开成功并关闭（不保存）；{dialog_note}",
    )


def _wps_close_note(basename: str) -> str:
    """尽力关闭 WPS 中本测试文档的窗口；无权限时提示人工确认。"""
    script = (
        'tell application "System Events"\n'
        '    if not (exists process "wpsoffice") then return "no-process"\n'
        '    tell process "wpsoffice"\n'
        '        set wins to every window whose name contains '
        f'"{_escape_applescript(basename)}"\n'
        "        repeat with w in wins\n"
        "            try\n"
        "                click button 1 of w\n"
        "            end try\n"
        "        end repeat\n"
        '        return "closed"\n'
        "    end tell\n"
        "end tell\n"
    )
    try:
        proc = _run_osascript(script, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return "WPS 窗口关闭失败，请人工确认无残留窗口"
    if proc.returncode != 0 or proc.stdout.strip() not in {"closed", "no-process"}:
        return "无辅助功能权限，无法自动关闭 WPS 窗口，请人工确认"
    return "已尝试关闭 WPS 中的本测试文档窗口"


def check_wps(docx: Path, timeout: int = 90, wait: int = 8) -> dict:
    """WPS 无可靠脚本接口：打开后等待数秒，进程存活即标 pending-human-review。"""
    start = time.monotonic()
    app = next((path for path in WPS_APP_CANDIDATES if path.is_dir()), None)
    if app is None:
        return _record("wps", "unknown", "skipped", 0.0, "未安装 WPS，跳过")
    version = _app_version(app)
    try:
        proc = subprocess.run(
            ["open", "-a", str(app), str(docx)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _record(
            "wps", version, "fail", time.monotonic() - start, f"open 命令超时（>{timeout}s）"
        )
    if proc.returncode != 0:
        return _record(
            "wps",
            version,
            "fail",
            time.monotonic() - start,
            f"open 命令失败: {proc.stderr.strip()[-300:]}",
        )
    time.sleep(wait)
    alive = (
        subprocess.run(["pgrep", "-f", "wpsoffice"], capture_output=True, check=False).returncode
        == 0
    )
    close_note = _wps_close_note(docx.name)
    if alive:
        return _record(
            "wps",
            version,
            "pending-human-review",
            time.monotonic() - start,
            "WPS 已打开文档（无脚本接口判断修复提示），需人工确认；" + close_note,
        )
    return _record(
        "wps",
        version,
        "fail",
        time.monotonic() - start,
        "WPS 进程在等待期内退出；" + close_note,
    )


APP_CHECKS = {
    "word": check_word,
    "libreoffice": check_libreoffice,
    "wps": check_wps,
}


def run_checks(docx: Path, apps: list[str], timeout: int) -> dict:
    """对选定应用逐个验证，返回 JSON 可序列化证据。"""
    results = [APP_CHECKS[app](docx, timeout=timeout) for app in apps]
    return {
        "file": str(docx),
        "ok": all(item["result"] in NON_FAILURE for item in results),
        "results": results,
    }


def _emit(report: dict, json_path: Path | None) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if json_path is not None:
        json_path.write_text(payload + "\n", encoding="utf-8")
    print(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="三办公软件「无修复打开」验证工具（macOS）")
    parser.add_argument("docx", type=Path, help="待验证的 .docx 文件")
    parser.add_argument(
        "--apps",
        default="word,libreoffice,wps",
        help="逗号分隔的应用子集：word,libreoffice,wps（默认全部）",
    )
    parser.add_argument("--timeout", type=int, default=90, help="单个应用的超时秒数")
    parser.add_argument("--json", type=Path, default=None, help="可选：JSON 证据写入路径")
    args = parser.parse_args(argv)

    apps = [item.strip() for item in args.apps.split(",") if item.strip()]
    unknown = sorted(set(apps) - set(APP_CHECKS))
    if unknown or not apps:
        choices = ",".join(APP_CHECKS)
        parser.error(f"未知应用: {','.join(unknown) or '(空)'}（可选: {choices}）")

    if not args.docx.is_file() or not zipfile.is_zipfile(args.docx):
        _emit({"file": str(args.docx), "ok": False, "error": "文件不可读"}, args.json)
        return 2
    report = run_checks(args.docx, apps, args.timeout)
    _emit(report, args.json)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
