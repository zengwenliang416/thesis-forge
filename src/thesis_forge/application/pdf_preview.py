from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Callable, Collection, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from time import monotonic, sleep
from typing import IO, Literal, Protocol
from xml.parsers import expat

from .office_refresh import (
    discover_libreoffice_executable,
    start_office_process,
    terminate_office_process_tree,
)
from .output import ReplaceFile, replace_output

PdfExportRunner = Callable[[Path, Path, Path, float], Path]
WordPdfExportRunner = Callable[[Path, Path, Path, float], Path]

_MACOS_WORD_APP_PATHS = (
    Path("/Applications/Microsoft Word.app"),
    Path.home() / "Applications/Microsoft Word.app",
)
_MACOS_WORD_AUTOMATION_SCRIPT = """\
on run argv
    set inputHfs to (POSIX file (item 1 of argv)) as text
    set outputHfs to (POSIX file (item 2 of argv)) as text
    set inputName to item 3 of argv
    set quitWhenDone to (item 4 of argv) is "true"
    tell application "Microsoft Word"
        set display alerts to alerts none
        open file name inputHfs read only true add to recent files false
        set wordDocument to document inputName
        try
            save as wordDocument file format format PDF file name outputHfs add to recent files false
        on error errorMessage number errorNumber
            try
                close wordDocument saving no
            end try
            if quitWhenDone then
                try
                    quit saving no
                end try
            end if
            error errorMessage number errorNumber
        end try
        close wordDocument saving no
        if quitWhenDone then
            quit saving no
        end if
    end tell
end run
"""
_MACOS_WORD_CLEANUP_SCRIPT = """\
on run argv
    set inputName to item 1 of argv
    tell application "Microsoft Word"
        try
            close document inputName saving no
        end try
    end tell
end run
"""
_WINDOWS_WORD_AUTOMATION_SCRIPT = r"""\
param(
    [Parameter(Mandatory = $true)][string]$DocumentPath,
    [Parameter(Mandatory = $true)][string]$PdfPath
)

$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($DocumentPath, $false, $true)
    foreach ($toc in $document.TablesOfContents) {
        $toc.Update()
    }
    foreach ($field in $document.Fields) {
        try {
            $field.Update() | Out-Null
        } catch {
        }
    }
    $document.Repaginate()
    $document.ExportAsFixedFormat($PdfPath, 17)
} finally {
    if ($null -ne $document) {
        $document.Close($false)
    }
    if ($null -ne $word) {
        $word.Quit()
    }
}
"""

_WORDPROCESSINGML_NAMESPACE = (
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
)
_MACOS_PREVIEW_FONT_CANDIDATES = {
    "宋体": (
        "Source Han Serif SC",
        frozenset({"Source Han Serif SC", "Songti SC", "STSong"}),
    ),
    "黑体": (
        "PingFang SC",
        frozenset({"PingFang SC", "Heiti SC"}),
    ),
}
_XML_ATTRIBUTE = re.compile(
    rb"(?P<prefix>[A-Za-z_][A-Za-z0-9_.-]*):"
    rb"(?P<local>[A-Za-z_][A-Za-z0-9_.-]*)"
    rb"(?P<head>\s*=\s*)(?P<quote>[\"'])(?P<value>[^\"']*)(?P=quote)"
)


@dataclass(frozen=True, slots=True)
class PdfPreviewArtifact:
    path: Path
    name: str
    engine: Literal["microsoft-word", "libreoffice"]
    label: str

    @property
    def file_name(self) -> str:
        return self.name


class PdfPreviewExporter(Protocol):
    def export(
        self,
        docx_path: str | Path,
        pdf_path: str | Path,
    ) -> PdfPreviewArtifact | None: ...


def derived_pdf_preview_path(docx_path: str | Path) -> Path:
    return Path(docx_path).with_suffix(".preview.pdf")


def is_valid_pdf(path: str | Path) -> bool:
    pdf_path = Path(path)
    try:
        if pdf_path.stat().st_size == 0:
            return False
        with pdf_path.open("rb") as stream:
            return stream.read(5) == b"%PDF-"
    except OSError:
        return False


def discover_microsoft_word_automation(
    platform: str | None = None,
) -> Path | None:
    active_platform = platform or sys.platform
    if active_platform == "darwin":
        if not any(path.is_dir() for path in _MACOS_WORD_APP_PATHS):
            return None
        automation = Path("/usr/bin/osascript")
        return automation if automation.is_file() else None
    if active_platform != "win32" or not _windows_word_is_registered():
        return None
    executable = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    return Path(executable) if executable else None


def _windows_word_is_registered() -> bool:
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CLASSES_ROOT,
            r"Word.Application\CurVer",
        ):
            return True
    except (ImportError, OSError):
        return False


def microsoft_word_preview_root(
    platform: str | None = None,
) -> Path:
    override = os.environ.get("THESISFORGE_WORD_PREVIEW_ROOT")
    if override:
        return Path(override).expanduser()
    active_platform = platform or sys.platform
    if active_platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Containers"
            / "com.microsoft.Word"
            / "Data"
            / "Documents"
            / "ThesisForgePreview"
        )
    local_app_data = os.environ.get("LOCALAPPDATA")
    if active_platform == "win32" and local_app_data:
        return Path(local_app_data) / "ThesisForge" / "WordPreview"
    return Path(tempfile.gettempdir()) / "ThesisForge" / "WordPreview"


def _preview_export_canceled() -> bool:
    cancel_file = os.environ.get("THESISFORGE_CANCEL_FILE")
    return bool(cancel_file and Path(cancel_file).exists())


@contextmanager
def _word_automation_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".automation.lock"
    lock_file = lock_path.open("a+b")
    acquired = False
    try:
        _lock_file(lock_file)
        acquired = True
        yield
    finally:
        if acquired:
            _unlock_file(lock_file)
        lock_file.close()


def _lock_file(lock_file: IO[bytes]) -> None:
    deadline = monotonic() + 60.0
    if os.name == "nt":
        import msvcrt

        lock_file.seek(0)
        if lock_file.read(1) == b"":
            lock_file.write(b"\0")
            lock_file.flush()
        lock_file.seek(0)
        while True:
            try:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                if _preview_export_canceled():
                    raise InterruptedError("Microsoft Word preview was canceled")
                if monotonic() >= deadline:
                    raise TimeoutError("Microsoft Word preview lock timed out")
                sleep(0.05)
    else:
        import fcntl

        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except BlockingIOError:
                if _preview_export_canceled():
                    raise InterruptedError("Microsoft Word preview was canceled")
                if monotonic() >= deadline:
                    raise TimeoutError("Microsoft Word preview lock timed out")
                sleep(0.05)


def _unlock_file(lock_file: IO[bytes]) -> None:
    if os.name == "nt":
        import msvcrt

        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _run_microsoft_word_pdf_export(
    automation_executable: Path,
    document_path: Path,
    output_directory: Path,
    timeout_seconds: float,
) -> Path:
    output_path = output_directory / f"{document_path.stem}.pdf"
    if sys.platform == "darwin":
        existing_word_processes = _macos_word_process_ids()
        script_path = output_directory / "export.applescript"
        script_path.write_text(_MACOS_WORD_AUTOMATION_SCRIPT, encoding="utf-8")
        command = (
            str(automation_executable),
            str(script_path),
            str(document_path),
            str(output_path),
            document_path.name,
            "true" if not existing_word_processes else "false",
        )
    elif sys.platform == "win32":
        script_path = output_directory / "export.ps1"
        script_path.write_text(_WINDOWS_WORD_AUTOMATION_SCRIPT, encoding="utf-8")
        command = (
            str(automation_executable),
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-DocumentPath",
            str(document_path),
            "-PdfPath",
            str(output_path),
        )
    else:
        raise RuntimeError("Microsoft Word PDF export is unsupported on this platform")
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        if sys.platform == "darwin":
            if existing_word_processes:
                _cleanup_macos_word_previews(
                    automation_executable,
                    output_directory.parent,
                    document_path.name,
                )
            else:
                _terminate_new_macos_word_processes(existing_word_processes)
        raise
    except subprocess.CalledProcessError:
        if sys.platform == "darwin":
            if existing_word_processes:
                _cleanup_macos_word_previews(
                    automation_executable,
                    output_directory.parent,
                    document_path.name,
                )
            else:
                _terminate_new_macos_word_processes(existing_word_processes)
        raise
    return output_path


def _macos_word_process_ids() -> frozenset[int]:
    pgrep = Path("/usr/bin/pgrep")
    if not pgrep.is_file():
        return frozenset()
    try:
        result = subprocess.run(
            (str(pgrep), "-x", "Microsoft Word"),
            check=False,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.SubprocessError):
        return frozenset()
    if result.returncode != 0:
        return frozenset()
    return frozenset(
        int(value)
        for value in result.stdout.splitlines()
        if value.strip().isdigit()
    )


def _terminate_new_macos_word_processes(
    existing_processes: Collection[int],
) -> None:
    for process_id in _macos_word_process_ids() - frozenset(existing_processes):
        try:
            os.kill(process_id, signal.SIGTERM)
        except OSError:
            continue


def _cleanup_macos_word_previews(
    automation_executable: Path,
    working_root: Path,
    document_name: str,
) -> None:
    try:
        with tempfile.TemporaryDirectory(
            prefix="cleanup-",
            dir=working_root,
        ) as cleanup_name:
            script_path = Path(cleanup_name) / "cleanup.applescript"
            script_path.write_text(_MACOS_WORD_CLEANUP_SCRIPT, encoding="utf-8")
            subprocess.run(
                (
                    str(automation_executable),
                    str(script_path),
                    document_name,
                ),
                check=False,
                capture_output=True,
                text=True,
                timeout=10.0,
            )
    except (OSError, subprocess.SubprocessError):
        pass


def _installed_font_families() -> frozenset[str]:
    result = None
    candidates = [shutil.which("fc-list")]
    if sys.platform == "darwin":
        candidates.extend(
            (
                "/opt/homebrew/bin/fc-list",
                "/usr/local/bin/fc-list",
            )
        )
    for candidate in candidates:
        if not candidate:
            continue
        try:
            result = subprocess.run(
                (candidate, "--format=%{family}\n"),
                check=False,
                capture_output=True,
                text=True,
                timeout=5.0,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        break
    if result is None:
        return frozenset()
    if result.returncode != 0:
        return frozenset()
    return frozenset(
        family.strip()
        for line in result.stdout.splitlines()
        for family in line.split(",")
        if family.strip()
    )


def preview_font_aliases(
    platform: str,
    installed_families: Collection[str] | None = None,
) -> Mapping[str, str]:
    if platform != "darwin":
        return {}
    available = (
        frozenset(installed_families)
        if installed_families is not None
        else _installed_font_families()
    )
    return {
        source: alias
        for source, (alias, candidates) in _MACOS_PREVIEW_FONT_CANDIDATES.items()
        if candidates & available
    }


def _replace_ooxml_font_attributes(
    content: bytes,
    aliases: Mapping[str, str],
) -> bytes:
    if not aliases:
        return content
    encoded_aliases = {
        source.encode(): target.encode() for source, target in aliases.items()
    }
    namespace_stack: list[dict[str, str]] = [{}]
    pending_namespaces: list[tuple[str, str]] = []
    replacements: list[tuple[int, int, bytes]] = []
    parser = expat.ParserCreate(namespace_separator="|")

    def start_namespace(prefix: str | None, uri: str) -> None:
        pending_namespaces.append((prefix or "", uri))

    def start_element(name: str, _attributes: Mapping[str, str]) -> None:
        namespaces = namespace_stack[-1].copy()
        namespaces.update(pending_namespaces)
        pending_namespaces.clear()
        namespace_stack.append(namespaces)
        namespace, _, local_name = name.partition("|")
        if namespace != _WORDPROCESSINGML_NAMESPACE:
            return
        attribute_names = (
            {"ascii", "hAnsi", "eastAsia", "cs"}
            if local_name == "rFonts"
            else {"name"} if local_name == "font" else set()
        )
        if not attribute_names:
            return
        tag_start = parser.CurrentByteIndex
        tag_end = _xml_start_tag_end(content, tag_start)
        for match in _XML_ATTRIBUTE.finditer(content, tag_start, tag_end):
            prefix = match.group("prefix").decode("ascii")
            local = match.group("local").decode("ascii")
            if (
                namespaces.get(prefix) != _WORDPROCESSINGML_NAMESPACE
                or local not in attribute_names
            ):
                continue
            replacement = encoded_aliases.get(match.group("value"))
            if replacement is not None:
                replacements.append(
                    (match.start("value"), match.end("value"), replacement)
                )

    def end_element(_name: str) -> None:
        namespace_stack.pop()

    parser.StartNamespaceDeclHandler = start_namespace
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    try:
        parser.Parse(content, True)
    except expat.ExpatError:
        return content
    adapted = content
    for start, end, replacement in reversed(replacements):
        adapted = adapted[:start] + replacement + adapted[end:]
    return adapted


def _xml_start_tag_end(content: bytes, start: int) -> int:
    quote: int | None = None
    for index in range(start, len(content)):
        value = content[index]
        if quote is None and value in (ord('"'), ord("'")):
            quote = value
        elif value == quote:
            quote = None
        elif quote is None and value == ord(">"):
            return index + 1
    return len(content)


def _adapt_docx_font_aliases(
    source_path: Path,
    target_path: Path,
    aliases: Mapping[str, str],
) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with (
        zipfile.ZipFile(source_path, "r") as source,
        zipfile.ZipFile(target_path, "w") as target,
    ):
        target.comment = source.comment
        for entry in source.infolist():
            content = source.read(entry)
            if entry.filename.startswith("word/") and entry.filename.endswith(".xml"):
                content = _replace_ooxml_font_attributes(content, aliases)
            target.writestr(entry, content)
    return target_path


def _run_libreoffice_pdf_export(
    executable: Path,
    document_path: Path,
    output_directory: Path,
    timeout_seconds: float,
) -> Path:
    temporary_root = "/tmp" if sys.platform == "darwin" else None
    with tempfile.TemporaryDirectory(
        prefix="thesisforge-lo-pdf-",
        dir=temporary_root,
    ) as profile_name:
        profile_path = Path(profile_name).resolve()
        conversion_document = document_path
        aliases = preview_font_aliases(sys.platform)
        if aliases:
            conversion_document = _adapt_docx_font_aliases(
                document_path,
                profile_path / document_path.name,
                aliases,
            )
        command = (
            str(executable),
            "--headless",
            "--nologo",
            "--nodefault",
            "--nofirststartwizard",
            "--norestore",
            f"-env:UserInstallation={profile_path.as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_directory.resolve()),
            str(conversion_document.resolve()),
        )
        office_process, windows_job = start_office_process(command)
        try:
            return_code = office_process.wait(timeout=timeout_seconds)
            if return_code != 0:
                raise RuntimeError(f"LibreOffice PDF export failed with exit code {return_code}")
        finally:
            terminate_office_process_tree(
                office_process,
                windows_job=windows_job,
            )
    return output_directory / f"{document_path.stem}.pdf"


@dataclass(frozen=True, slots=True)
class MicrosoftWordPdfPreviewExporter:
    automation_executable: Path | None = None
    timeout_seconds: float = 60.0
    runner: WordPdfExportRunner = _run_microsoft_word_pdf_export
    replace_file: ReplaceFile = os.replace
    working_root: Path | None = None

    def export(
        self,
        docx_path: str | Path,
        pdf_path: str | Path,
    ) -> PdfPreviewArtifact | None:
        document_path = Path(docx_path)
        target_path = Path(pdf_path)
        automation = (
            self.automation_executable
            or discover_microsoft_word_automation()
        )
        if automation is None:
            return None
        if _preview_export_canceled():
            return None

        root = self.working_root or microsoft_word_preview_root()
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with _word_automation_lock(root), tempfile.TemporaryDirectory(
                prefix="render-",
                dir=root,
            ) as working_name:
                working_directory = Path(working_name)
                working_document = working_directory / f"{working_directory.name}.docx"
                shutil.copyfile(document_path, working_document)
                converted_path = self.runner(
                    automation,
                    working_document,
                    working_directory,
                    self.timeout_seconds,
                )
                if not is_valid_pdf(converted_path):
                    return None
                replace_output(
                    converted_path,
                    target_path,
                    replace_file=self.replace_file,
                )
        # Word automation is optional and falls back without failing the DOCX build.
        except Exception:  # noqa: BLE001
            return None

        return PdfPreviewArtifact(
            path=target_path,
            name=target_path.name,
            engine="microsoft-word",
            label="Microsoft Word PDF",
        )


@dataclass(frozen=True, slots=True)
class LibreOfficePdfPreviewExporter:
    executable: Path | None = None
    timeout_seconds: float = 60.0
    runner: PdfExportRunner = _run_libreoffice_pdf_export
    replace_file: ReplaceFile = os.replace

    def export(
        self,
        docx_path: str | Path,
        pdf_path: str | Path,
    ) -> PdfPreviewArtifact | None:
        document_path = Path(docx_path)
        target_path = Path(pdf_path)
        executable = self.executable or discover_libreoffice_executable()
        if executable is None:
            return None
        if _preview_export_canceled():
            return None

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(
                prefix=f".{target_path.name}.",
                suffix=".tmp",
                dir=target_path.parent,
            ) as output_name:
                output_directory = Path(output_name)
                converted_path = self.runner(
                    executable,
                    document_path,
                    output_directory,
                    self.timeout_seconds,
                )
                if not is_valid_pdf(converted_path):
                    return None
                replace_output(
                    converted_path,
                    target_path,
                    replace_file=self.replace_file,
                )
        # Exporters are best-effort integrations and must not escape into DOCX builds.
        except Exception:  # noqa: BLE001
            return None

        return PdfPreviewArtifact(
            path=target_path,
            name=target_path.name,
            engine="libreoffice",
            label="LibreOffice PDF",
        )


@dataclass(frozen=True, slots=True)
class FallbackPdfPreviewExporter:
    exporters: tuple[PdfPreviewExporter, ...]

    def export(
        self,
        docx_path: str | Path,
        pdf_path: str | Path,
    ) -> PdfPreviewArtifact | None:
        for exporter in self.exporters:
            if _preview_export_canceled():
                return None
            try:
                artifact = exporter.export(docx_path, pdf_path)
            except Exception:  # noqa: BLE001
                artifact = None
            if artifact is not None:
                return artifact
        return None


def preferred_pdf_preview_exporter() -> PdfPreviewExporter:
    return FallbackPdfPreviewExporter(
        (
            MicrosoftWordPdfPreviewExporter(),
            LibreOfficePdfPreviewExporter(),
        )
    )
