#!/usr/bin/env python3
"""Phase 0 字段实证：真实办公软件打开与 Word 字段刷新行为。

1. no-repair：对每个样本（含无 updateFields 对照变体）跑
   qa/tools/no_repair_open.py --apps word,libreoffice（WPS 需 --with-wps），
   证据合并写入 results/no-repair.json。
   注意：带 w:updateFields 的样本在 Word 打开时会弹模态对话框
   「该文档包含的域可能引用了其他文件。是否更新该文档中的这些域？」，
   no_repair_open 的保守判定会记为 fail——该对话框文本会被本脚本
   在变体对照中实证为 updateFields 提示而非修复提示。
2. Word 刷新实证（AppleScript 驱动 Microsoft Word，全程不保存）：
   - 打开样本；若弹 updateFields 对话框则点击「否(N)」——保留生成态 cached
     result 以抓取真实「刷新前」快照，并记录 prompt 出现事实；
   - 刷新前抓取：TOC 条目数与文本、main story 全部字段 code/result、
     页眉页脚 story 字段 code/result；
   - update（TOC）+ update field（全部 story 字段）；
   - 刷新后再抓取，对比变化；
   - save as PDF 直接到 samples/<stem>-word-refreshed.pdf（samples/ 与
     被打开 docx 同目录，避免 Word 沙盒「授予文件访问权限」弹窗）；
   - 关闭不保存，校验样本 docx sha256 不变。
   证据写入 results/word-refresh.json。
3. 对照变体（验证打开弹窗的触发源）：
   - samples/<stem>-no-updatefields.docx（仅剥掉 w:updateFields）
   - samples/<stem>-no-updatefields-nodirty.docx（再剥掉全部 fldChar dirty）
   仅打开 + 抓取 + 关闭不保存，回答「无 cached 条目的 TOC 在 Word 打开时
   是否自动填充」以及「弹窗由 updateFields 还是 dirty 触发」。

用法：
    .venv/bin/python spikes/phase0/fields/verify_apps.py [--with-wps]
        [--skip-no-repair]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parent
ROOT = SPIKE_DIR.parents[2]
SAMPLES_DIR = SPIKE_DIR / "samples"
RESULTS_DIR = SPIKE_DIR / "results"
NO_REPAIR_OPEN = ROOT / "qa" / "tools" / "no_repair_open.py"

# Word updateFields 提示框的「不更新」按钮（中文 UI）
DECLINE_BUTTON = "否(N)"
GRANT_ACCESS_TITLE = "授予文件访问权限"
GRANT_ACCESS_CANCEL = "取消"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _osascript(script: str, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sample_docx_files() -> list[Path]:
    """样本清单：排除 macOS AppleDouble（._*）与 Word 锁文件（~$*）。"""
    return [
        path
        for path in sorted(SAMPLES_DIR.glob("*.docx"))
        if not path.name.startswith(("._", "~$"))
        and "-lo-refreshed" not in path.stem
        and "-no-updatefields" not in path.stem
        and "-keep-updatefields" not in path.stem
    ]


# ---------------------------------------------------------------- no-repair


def run_no_repair(samples: list[Path], apps: str) -> None:
    merged: dict[str, dict] = {}
    existing = RESULTS_DIR / "no-repair.json"
    if existing.is_file():
        merged = json.loads(existing.read_text(encoding="utf-8"))
    for sample in samples:
        json_path = RESULTS_DIR / f"no-repair-{sample.stem}.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(NO_REPAIR_OPEN),
                str(sample),
                "--apps",
                apps,
                "--timeout",
                "150",
                "--json",
                str(json_path),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=900,
        )
        merged[sample.stem] = json.loads(json_path.read_text(encoding="utf-8"))
        merged[sample.stem]["exit_code"] = proc.returncode
        print(f"no-repair {sample.stem}: exit={proc.returncode}")
        # no_repair_open 的 Word 检查若被 updateFields 模态框阻塞，弹窗会残留，
        # 不立即清场会挡住后续样本的打开与探测
        _word_cleanup([sample])
    (RESULTS_DIR / "no-repair.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# ------------------------------------------------------------- dialog watch


def _poll_word_dialog() -> dict | None:
    """探测 Word 模态对话框；返回 {kind, text, buttons} 或 None。"""
    script = """
tell application "System Events"
    if not (exists process "Microsoft Word") then return "none"
    tell process "Microsoft Word"
        repeat with w in windows
            try
                if (subrole of w is "AXDialog") or (subrole of w is "AXSystemDialog") then
                    set dlgText to ""
                    try
                        set dlgText to name of every static text of w as text
                    end try
                    set dlgButtons to ""
                    try
                        set dlgButtons to name of every button of w as text
                    end try
                    return "title=" & (name of w) & "<<>>text=" & dlgText & ¬
                        "<<>>buttons=" & dlgButtons
                end if
            end try
        end repeat
        return "none"
    end tell
end tell
"""
    try:
        proc = _osascript(script, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = proc.stdout.strip()
    if proc.returncode != 0 or out == "none":
        return None
    parts = {}
    for segment in out.split("<<>>"):
        key, _, value = segment.partition("=")
        parts[key.strip()] = value.strip()
    text = parts.get("text", "")
    buttons = parts.get("buttons", "")
    title = parts.get("title", "")
    if GRANT_ACCESS_TITLE in title:
        kind = "grant_access"
    elif DECLINE_BUTTON in buttons and "是(Y)" in buttons:
        kind = "update_fields_prompt"
    else:
        kind = "other"
    return {"kind": kind, "title": title, "text": text, "buttons": buttons}


def _click_dialog_button(button_name: str) -> bool:
    script = f"""
tell application "System Events"
    tell process "Microsoft Word"
        repeat with w in windows
            try
                if (subrole of w is "AXDialog") or (subrole of w is "AXSystemDialog") then
                    repeat with b in buttons of w
                        if name of b is "{_escape(button_name)}" then
                            click b
                            return "clicked"
                        end if
                    end repeat
                end if
            end try
        end repeat
        return "not-found"
    end tell
end tell
"""
    try:
        proc = _osascript(script, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "clicked"


# ------------------------------------------------------------- Word session


def _word_open(path: Path, *, decline_update_prompt: bool, timeout: int = 150) -> dict:
    """打开文档并处理模态对话框，轮询确认文档出现。

    decline_update_prompt=True 时对 updateFields 提示点「否(N)」，
    保留生成态 cached result（用于刷新前快照）；False 时点「是(Y)」。
    """
    escaped = _escape(str(path.resolve()))
    _osascript('tell application "Microsoft Word" to activate', timeout=30)
    try:
        _osascript(
            f'tell application "Microsoft Word" to open POSIX file "{escaped}"',
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        pass  # open 事件可能已入队，交给轮询
    probe = (
        f'set targetPath to POSIX file "{escaped}" as text\n'
        'tell application "Microsoft Word"\n'
        "    set docPaths to full name of every document\n"
        "    if docPaths is missing value then set docPaths to {}\n"
        "    if class of docPaths is not list then set docPaths to {docPaths}\n"
        "    if docPaths contains targetPath then return true\n"
        "    return false\n"
        "end tell\n"
    )
    outcome = {"opened": False, "prompts_seen": []}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        dialog = _poll_word_dialog()
        if dialog is not None:
            if dialog["kind"] == "update_fields_prompt":
                outcome["prompts_seen"].append(dialog)
                button = DECLINE_BUTTON if decline_update_prompt else "是(Y)"
                _click_dialog_button(button)
            elif dialog["kind"] == "grant_access":
                outcome["prompts_seen"].append(dialog)
                _click_dialog_button(GRANT_ACCESS_CANCEL)
            # other 类型不擅动，继续轮询（交由超时暴露）
            time.sleep(1)
            continue
        try:
            proc = _osascript(probe, timeout=15)
            if proc.returncode == 0 and proc.stdout.strip() == "true":
                outcome["opened"] = True
                return outcome
        except subprocess.TimeoutExpired:
            pass  # Word 事件队列繁忙，继续轮询
        time.sleep(2)
    return outcome


def _word_close(path: Path) -> None:
    """关闭本测试文档（不保存），按完整路径匹配。"""
    escaped = _escape(str(path.resolve()))
    script = (
        f'set targetPath to POSIX file "{escaped}" as text\n'
        'tell application "Microsoft Word"\n'
        "    repeat 10 times\n"
        "        set docPaths to full name of every document\n"
        "        if docPaths is missing value then exit repeat\n"
        "        if class of docPaths is not list then set docPaths to {docPaths}\n"
        "        if docPaths does not contain targetPath then exit repeat\n"
        "        close (first document whose full name is targetPath) saving no\n"
        "        delay 1\n"
        "    end repeat\n"
        "end tell\n"
    )
    try:
        _osascript(script, timeout=60)
    except subprocess.TimeoutExpired:
        pass


_CAPTURE_SCRIPT = """set targetPath to POSIX file "{path}" as text
tell application "Microsoft Word"
    set doc to first document whose full name is targetPath
    set tocCount to count of tables of contents of doc
    set tocText to ""
    if tocCount > 0 then
        try
            set tocText to content of text object of table of contents 1 of doc
        on error errMsg
            set tocText to "ERROR: " & errMsg
        end try
    end if
    set fieldDump to ""
    set fieldCount to count of fields of doc
    repeat with i from 1 to fieldCount
        set f to field i of doc
        try
            set fieldDump to fieldDump & "<<F>>" & (content of field code of f) ¬
                & "<<R>>" & (content of result range of f) & linefeed
        on error errMsg
            set fieldDump to fieldDump & "<<F>>ERROR: " & errMsg & linefeed
        end try
    end repeat
    set storyDump to ""
    set storyTypes to {primary footer story, even pages footer story, ¬
        first page footer story, primary header story, even pages header story, ¬
        first page header story}
    set storyNames to {"primary footer", "even pages footer", "first page footer", ¬
        "primary header", "even pages header", "first page header"}
    repeat with i from 1 to 6
        try
            set sr to get story range doc story type (item i of storyTypes)
            set sfCount to count of fields of sr
            repeat with j from 1 to sfCount
                set f to field j of sr
                set storyDump to storyDump & "<<S>>" & (item i of storyNames) & ¬
                    "<<F>>" & (content of field code of f) & "<<R>>" & ¬
                    (content of result range of f) & linefeed
            end repeat
        end try
    end repeat
    return "<<TOC_COUNT>>" & tocCount & linefeed & "<<TOC_TEXT>>" & linefeed & ¬
        tocText & linefeed & "<<MAIN_FIELDS>>" & linefeed & fieldDump & ¬
        "<<STORY_FIELDS>>" & linefeed & storyDump
end tell
"""

_UPDATE_SCRIPT = """set targetPath to POSIX file "{path}" as text
tell application "Microsoft Word"
    set doc to first document whose full name is targetPath
    set tocLog to ""
    set tocCount to count of tables of contents of doc
    repeat with i from 1 to tocCount
        try
            update table of contents i of doc
            set tocLog to tocLog & "ok;"
        on error errMsg
            set tocLog to tocLog & "err:" & errMsg & ";"
        end try
    end repeat
    set okCount to 0
    set failCount to 0
    set fieldCount to count of fields of doc
    repeat with i from 1 to fieldCount
        set f to field i of doc
        try
            if update field f then
                set okCount to okCount + 1
            else
                set failCount to failCount + 1
            end if
        on error
            set failCount to failCount + 1
        end try
    end repeat
    set storyTypes to {primary footer story, even pages footer story, ¬
        first page footer story, primary header story, even pages header story, ¬
        first page header story}
    repeat with i from 1 to 6
        try
            set sr to get story range doc story type (item i of storyTypes)
            set sfCount to count of fields of sr
            repeat with j from 1 to sfCount
                set f to field j of sr
                try
                    if update field f then
                        set okCount to okCount + 1
                    else
                        set failCount to failCount + 1
                    end if
                on error
                    set failCount to failCount + 1
                end try
            end repeat
        end try
    end repeat
    return "toc:" & tocLog & " fields-ok:" & okCount & " fields-failed:" & failCount
end tell
"""


def _parse_capture(raw: str) -> dict:
    markers = ("TOC_COUNT", "TOC_TEXT", "MAIN_FIELDS", "STORY_FIELDS")

    def _section(name: str) -> str:
        marker = f"<<{name}>>"
        start = raw.find(marker)
        if start < 0:
            return ""
        start += len(marker)
        following = [
            index
            for other in markers
            if (index := raw.find(f"<<{other}>>", start)) > start
        ]
        end = min(following) if following else len(raw)
        return raw[start:end].strip("\n")

    def _norm(value: str) -> str:
        # AppleScript 对空结果返回字面量 missing value
        return "" if value.strip() == "missing value" else value

    main_fields = []
    for line in _section("MAIN_FIELDS").splitlines():
        if "<<F>>" not in line:
            continue
        _, _, rest = line.partition("<<F>>")
        code, _, result = rest.partition("<<R>>")
        main_fields.append({"code": code.strip(), "result": _norm(result)})
    story_fields = []
    for line in _section("STORY_FIELDS").splitlines():
        if "<<S>>" not in line:
            continue
        _, _, rest = line.partition("<<S>>")
        story, _, rest = rest.partition("<<F>>")
        code, _, result = rest.partition("<<R>>")
        story_fields.append(
            {"story": story.strip(), "code": code.strip(), "result": _norm(result)}
        )
    return {
        "toc_count": _section("TOC_COUNT").strip(),
        "toc_text": _norm(_section("TOC_TEXT")),
        "main_fields": main_fields,
        "story_fields": story_fields,
    }


def _word_capture(path: Path) -> dict:
    script = _CAPTURE_SCRIPT.replace("{path}", _escape(str(path.resolve())))
    # Word 弹窗关闭后事件队列可能仍处于模态过渡期（-1708），
    # 每轮先清弹窗再试，最多 5 轮
    proc = None
    for _ in range(5):
        dialog = _poll_word_dialog()
        if dialog is not None:
            if dialog["kind"] == "update_fields_prompt":
                _click_dialog_button(DECLINE_BUTTON)
            elif dialog["kind"] == "grant_access":
                _click_dialog_button(GRANT_ACCESS_CANCEL)
            time.sleep(1)
            continue
        proc = _osascript(script, timeout=180)
        if proc.returncode == 0:
            return _parse_capture(proc.stdout)
        if "-1708" not in proc.stderr:
            break
        time.sleep(2)
    return {"error": (proc.stderr.strip()[-500:] if proc else "dialog-loop")}


def _word_update(path: Path) -> str:
    script = _UPDATE_SCRIPT.replace("{path}", _escape(str(path.resolve())))
    proc = None
    for _ in range(5):
        dialog = _poll_word_dialog()
        if dialog is not None:
            if dialog["kind"] == "update_fields_prompt":
                _click_dialog_button(DECLINE_BUTTON)
            elif dialog["kind"] == "grant_access":
                _click_dialog_button(GRANT_ACCESS_CANCEL)
            time.sleep(1)
            continue
        proc = _osascript(script, timeout=240)
        if proc.returncode == 0:
            return proc.stdout.strip()
        if "-1708" not in proc.stderr:
            break
        time.sleep(2)
    return "error: " + (proc.stderr.strip()[-500:] if proc else "dialog-loop")


def _word_export_pdf(path: Path, pdf_target: Path) -> dict:
    """save as PDF 到 samples/（与被测 docx 同目录，避免沙盒授权弹窗）。

    save as 会把文档改挂到 PDF 路径；导出后立即把文档关联改回
    原 docx 不可行，因此导出后统一由 _word_close_any 按两个路径关闭。
    """
    pdf_target.unlink(missing_ok=True)
    escaped = _escape(str(path.resolve()))
    script = (
        f'set targetPath to POSIX file "{escaped}" as text\n'
        'tell application "Microsoft Word"\n'
        "    set doc to first document whose full name is targetPath\n"
        "    save as doc file format format PDF file name "
        f'"{_escape(str(pdf_target.resolve()))}"\n'
        "end tell\n"
    )
    proc = _osascript(script, timeout=180)
    # 处理可能出现的沙盒授权弹窗
    dialog = _poll_word_dialog()
    if dialog is not None and dialog["kind"] == "grant_access":
        _click_dialog_button(GRANT_ACCESS_CANCEL)
    return {
        "pdf_exported": pdf_target.is_file(),
        "pdf_path": str(pdf_target) if pdf_target.is_file() else None,
        "save_as_stderr": proc.stderr.strip()[-300:] if proc.returncode != 0 else "",
    }


def _word_close_any(*paths: Path) -> None:
    """按多个候选路径关闭文档（不保存）：save as 后文档可能改挂到 PDF。"""
    candidates = ", ".join(
        f'POSIX file "{_escape(str(path.resolve()))}" as text' for path in paths
    )
    script = (
        f"set candidates to {{{candidates}}}\n"
        'tell application "Microsoft Word"\n'
        "    repeat with p in candidates\n"
        "        repeat 10 times\n"
        "            set docPaths to full name of every document\n"
        "            if docPaths is missing value then exit repeat\n"
        "            if class of docPaths is not list then set docPaths to {docPaths}\n"
        "            if docPaths does not contain p then exit repeat\n"
        "            close (first document whose full name is p) saving no\n"
        "            delay 1\n"
        "        end repeat\n"
        "    end repeat\n"
        "end tell\n"
    )
    try:
        _osascript(script, timeout=120)
    except subprocess.TimeoutExpired:
        pass


def word_refresh_experiment(sample: Path) -> dict:
    before_digest = _digest(sample)
    pdf_target = SAMPLES_DIR / f"{sample.stem}-word-refreshed.pdf"
    result: dict = {"file": sample.name, "sha256_before": before_digest}
    open_outcome = _word_open(sample, decline_update_prompt=True)
    result["open"] = open_outcome
    if not open_outcome["opened"]:
        result["error"] = "Word 未能在超时内打开样本"
        _word_close(sample)
        return result
    try:
        result["before_update"] = _word_capture(sample)
        result["update_log"] = _word_update(sample)
        result["after_update"] = _word_capture(sample)
        result["pdf"] = _word_export_pdf(sample, pdf_target)
    finally:
        _word_close_any(sample, pdf_target.with_suffix(".pdf"))
    result["sha256_after"] = _digest(sample)
    result["docx_unchanged"] = result["sha256_after"] == before_digest
    return result


def word_open_only_experiment(sample: Path) -> dict:
    """对照变体：仅打开 + 抓取 + 关闭不保存（不主动更新字段）。"""
    before_digest = _digest(sample)
    result: dict = {"file": sample.name, "sha256_before": before_digest}
    open_outcome = _word_open(sample, decline_update_prompt=True)
    result["open"] = open_outcome
    if not open_outcome["opened"]:
        result["error"] = "Word 未能在超时内打开样本"
        _word_close(sample)
        return result
    try:
        result["opened_state"] = _word_capture(sample)
    finally:
        _word_close(sample)
    result["sha256_after"] = _digest(sample)
    result["docx_unchanged"] = result["sha256_after"] == before_digest
    return result


# ---------------------------------------------------------------- variants


def _word_cleanup(paths: list[Path]) -> None:
    """no-repair 之后清场：点掉遗留模态对话框并关闭全部测试文档。"""
    for _ in range(10):
        dialog = _poll_word_dialog()
        if dialog is None:
            break
        if dialog["kind"] == "update_fields_prompt":
            _click_dialog_button(DECLINE_BUTTON)
        elif dialog["kind"] == "grant_access":
            _click_dialog_button(GRANT_ACCESS_CANCEL)
        else:
            break
        time.sleep(1)
    for path in paths:
        _word_close(path)
    lock_files = list(SAMPLES_DIR.glob("~$*.docx"))
    for lock in lock_files:
        lock.unlink(missing_ok=True)


def make_variant(sample: Path, *, strip_updatefields: bool, strip_dirty: bool) -> Path:
    """构造对照变体：可选择剥掉 settings.xml 的 w:updateFields 和/或
    全部 story 部件里 fldChar 的 w:dirty="true"。其余字节不变的副本。"""
    suffix = "-no-updatefields" if strip_updatefields else "-keep-updatefields"
    if strip_dirty:
        suffix += "-nodirty"
    variant = SAMPLES_DIR / f"{sample.stem}{suffix}.docx"
    with zipfile.ZipFile(sample) as source:
        entries = {info.filename: (info, source.read(info)) for info in source.infolist()}
    if strip_updatefields:
        settings_info, settings_bytes = entries["word/settings.xml"]
        text = settings_bytes.decode("utf-8")
        for pattern in (
            '<w:updateFields w:val="true"/>',
            '<w:updateFields w:val="true"></w:updateFields>',
            '<w:updateFields w:val="on"/>',
        ):
            if pattern in text:
                text = text.replace(pattern, "")
                break
        else:
            raise RuntimeError(f"{sample.name} 的 settings.xml 中未找到 updateFields")
        entries["word/settings.xml"] = (settings_info, text.encode("utf-8"))
    if strip_dirty:
        for name in list(entries):
            if not re.match(r"^word/(document|header\d*|footer\d*)\.xml$", name):
                continue
            info, data = entries[name]
            entries[name] = (info, data.replace(b' w:dirty="true"', b""))
    with zipfile.ZipFile(variant, "w", zipfile.ZIP_DEFLATED) as out:
        for info, data in entries.values():
            out.writestr(info, data)
    return variant


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-wps",
        action="store_true",
        help="no-repair 阶段包含 WPS（默认跳过，WPS 为 pending-human-review）",
    )
    parser.add_argument(
        "--skip-no-repair",
        action="store_true",
        help="跳过 no-repair 阶段（仅跑 Word 实证）",
    )
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    samples = _sample_docx_files()
    if not samples:
        print("samples/ 下没有 docx，先运行 build_samples.py", file=sys.stderr)
        return 2

    variants = [
        variant
        for sample in samples
        for variant in (
            make_variant(sample, strip_updatefields=True, strip_dirty=False),
            make_variant(sample, strip_updatefields=True, strip_dirty=True),
            make_variant(sample, strip_updatefields=False, strip_dirty=True),
        )
    ]
    print(f"variants: {[v.name for v in variants]}")

    if not args.skip_no_repair:
        apps = "word,libreoffice,wps" if args.with_wps else "word,libreoffice"
        run_no_repair(samples + variants, apps)
        _word_cleanup(samples + variants)

    word_report: dict[str, dict] = {}
    for sample in samples:
        print(f"word refresh experiment: {sample.stem}")
        word_report[sample.stem] = word_refresh_experiment(sample)
        entry = word_report[sample.stem]
        print(
            f"  opened={entry['open']['opened']} "
            f"prompts={len(entry['open']['prompts_seen'])} "
            f"docx_unchanged={entry.get('docx_unchanged')} "
            f"update_log={entry.get('update_log')!r}"
        )
    for variant in variants:
        print(f"word open-only experiment: {variant.stem}")
        word_report[variant.stem] = word_open_only_experiment(variant)
        entry = word_report[variant.stem]
        print(
            f"  opened={entry['open']['opened']} "
            f"prompts={len(entry['open']['prompts_seen'])} "
            f"docx_unchanged={entry.get('docx_unchanged')}"
        )
    (RESULTS_DIR / "word-refresh.json").write_text(
        json.dumps(word_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    ok = all(
        entry.get("docx_unchanged") and entry["open"]["opened"]
        for entry in word_report.values()
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
