from __future__ import annotations

import ctypes
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from html import unescape
from io import BytesIO
from pathlib import Path
from typing import Any, Protocol
from zipfile import BadZipFile, ZipFile, ZipInfo

ExecutableFinder = Callable[[str], str | None]
FilePredicate = Callable[[Path], bool]
PythonProbe = Callable[[Path], bool]
RefreshRunner = Callable[[Path, Path, Path, float, int], None]
_RENDERER_OWNED_PARTS = (
    "word/styles.xml",
    "word/fontTable.xml",
)
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_CREATE_SUSPENDED = 0x00000004
_CREATE_NO_WINDOW = 0x08000000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_RESUME_THREAD_FAILED = 0xFFFFFFFF


def _windows_error() -> OSError:
    last_error = getattr(ctypes, "get_last_error", lambda: 0)()
    win_error = getattr(ctypes, "WinError", None)
    if win_error is not None:
        return win_error(last_error)
    return OSError(last_error, "Windows API call failed")


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("read_operation_count", ctypes.c_ulonglong),
        ("write_operation_count", ctypes.c_ulonglong),
        ("other_operation_count", ctypes.c_ulonglong),
        ("read_transfer_count", ctypes.c_ulonglong),
        ("write_transfer_count", ctypes.c_ulonglong),
        ("other_transfer_count", ctypes.c_ulonglong),
    ]


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("per_process_user_time_limit", ctypes.c_longlong),
        ("per_job_user_time_limit", ctypes.c_longlong),
        ("limit_flags", ctypes.c_uint32),
        ("minimum_working_set_size", ctypes.c_size_t),
        ("maximum_working_set_size", ctypes.c_size_t),
        ("active_process_limit", ctypes.c_uint32),
        ("affinity", ctypes.c_size_t),
        ("priority_class", ctypes.c_uint32),
        ("scheduling_class", ctypes.c_uint32),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("basic_limit_information", _BasicLimitInformation),
        ("io_info", _IoCounters),
        ("process_memory_limit", ctypes.c_size_t),
        ("job_memory_limit", ctypes.c_size_t),
        ("peak_process_memory_used", ctypes.c_size_t),
        ("peak_job_memory_used", ctypes.c_size_t),
    ]


@dataclass(slots=True)
class _WindowsJob:
    handle: int
    kernel32: Any
    closed: bool = False

    def terminate(self) -> None:
        if self.closed:
            return
        if not self.kernel32.TerminateJobObject(self.handle, 1):
            raise _windows_error()

    def close(self) -> None:
        if self.closed:
            return
        if not self.kernel32.CloseHandle(self.handle):
            raise _windows_error()
        self.closed = True


class _OfficeProcess(Protocol):
    pid: int
    _handle: Any

    def poll(self) -> int | None: ...

    def wait(self, timeout: float | None = None) -> int | None: ...

    def kill(self) -> None: ...


@dataclass(slots=True)
class _WindowsProcess:
    _handle: Any
    pid: int
    command: tuple[str, ...]
    winapi: Any
    returncode: int | None = None
    closed: bool = False

    def poll(self) -> int | None:
        return self.wait(timeout=0)

    def wait(self, timeout: float | None = None) -> int | None:
        if self.returncode is not None:
            return self.returncode
        milliseconds = (
            self.winapi.INFINITE
            if timeout is None
            else max(0, int(timeout * 1000))
        )
        result = self.winapi.WaitForSingleObject(self._handle, milliseconds)
        if result == self.winapi.WAIT_TIMEOUT:
            if timeout == 0:
                return None
            raise subprocess.TimeoutExpired(self.command, timeout)
        if result != self.winapi.WAIT_OBJECT_0:
            raise OSError(f"WaitForSingleObject failed: {result}")
        self.returncode = self.winapi.GetExitCodeProcess(self._handle)
        return self.returncode

    def kill(self) -> None:
        if self.poll() is None:
            self.winapi.TerminateProcess(self._handle, 1)

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.winapi.CloseHandle(self._handle)


_UNO_REFRESH_SCRIPT = r"""
import sys
import time

import uno
from com.sun.star.beans import PropertyValue


def property_value(name, value):
    prop = PropertyValue()
    prop.Name = name
    prop.Value = value
    return prop


pipe_name, document_url, timeout_text, max_level_text = sys.argv[1:]
deadline = time.monotonic() + float(timeout_text)
local_context = uno.getComponentContext()
resolver = local_context.ServiceManager.createInstanceWithContext(
    "com.sun.star.bridge.UnoUrlResolver",
    local_context,
)
connection = (
    f"uno:pipe,name={pipe_name};urp;StarOffice.ComponentContext"
)

while True:
    try:
        context = resolver.resolve(connection)
        break
    except Exception:
        if time.monotonic() >= deadline:
            raise
        time.sleep(0.1)

desktop = context.ServiceManager.createInstanceWithContext(
    "com.sun.star.frame.Desktop",
    context,
)
document = desktop.loadComponentFromURL(
    document_url,
    "_blank",
    0,
    (
        property_value("Hidden", True),
        property_value("ReadOnly", False),
        property_value("MacroExecutionMode", 0),
        property_value("UpdateDocMode", 0),
    ),
)
if document is None:
    raise RuntimeError("LibreOffice returned no document")

try:
    indexes = document.getDocumentIndexes()
    index_count = indexes.getCount()
    if index_count == 0:
        bookmarks = document.getBookmarks()
        if not bookmarks.hasByName("tf_toc_index"):
            raise RuntimeError("LibreOffice found no TOC index or bookmark")
        anchor = bookmarks.getByName("tf_toc_index").getAnchor()
        index = document.createInstance("com.sun.star.text.ContentIndex")
        index.Title = ""
        index.CreateFromOutline = True
        index.Level = int(max_level_text)
        anchor.getText().insertTextContent(anchor, index, True)
        indexes = document.getDocumentIndexes()
        index_count = indexes.getCount()
        if index_count == 0:
            raise RuntimeError("LibreOffice could not create the TOC index")
    for index in range(index_count):
        indexes.getByIndex(index).update()
    text_fields = document.getTextFields()
    refresh = getattr(text_fields, "refresh", None)
    if refresh is not None:
        refresh()
    document.store()
finally:
    try:
        document.close(True)
    finally:
        desktop.terminate()
"""


class DocumentRefresher(Protocol):
    def refresh(self, path: str | Path) -> bool: ...


def _automatic_refresh_enabled(
    environ: Mapping[str, str] | None = None,
) -> bool:
    active_environ = os.environ if environ is None else environ
    value = active_environ.get("THESISFORGE_OFFICE_REFRESH", "auto")
    return value.strip().lower() not in {"0", "false", "no", "off", "disabled"}


def _toc_max_level(path: Path) -> int | None:
    try:
        with ZipFile(path) as package:
            document_xml = package.read("word/document.xml").decode("utf-8")
    except (BadZipFile, KeyError, OSError):
        return None
    match = re.search(
        r'TOC\s+\\o\s+"(\d+)-(\d+)"',
        unescape(document_xml),
    )
    if match is None:
        return None
    return int(match.group(2))


def _unique_paths(paths: list[Path]) -> tuple[Path, ...]:
    return tuple(dict.fromkeys(path.expanduser() for path in paths))


def _platform_candidates(
    platform_name: str,
    environ: Mapping[str, str],
) -> tuple[Path, ...]:
    candidates: list[Path] = []
    override = environ.get("THESISFORGE_LIBREOFFICE")
    if override:
        candidates.append(Path(override))

    if platform_name == "darwin":
        candidates.append(
            Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        )
    elif platform_name.startswith("win"):
        for key in ("ProgramFiles", "ProgramFiles(x86)"):
            root = environ.get(key)
            if root:
                candidates.append(
                    Path(root) / "LibreOffice" / "program" / "soffice.exe"
                )
    else:
        candidates.extend(
            (
                Path("/usr/bin/libreoffice"),
                Path("/usr/bin/soffice"),
                Path("/usr/lib/libreoffice/program/soffice"),
            )
        )
    return _unique_paths(candidates)


def discover_libreoffice_executable(
    *,
    platform_name: str | None = None,
    environ: Mapping[str, str] | None = None,
    which: ExecutableFinder = shutil.which,
    is_file: FilePredicate = Path.is_file,
) -> Path | None:
    active_platform = platform_name or sys.platform
    active_environ = os.environ if environ is None else environ

    for candidate in _platform_candidates(active_platform, active_environ):
        if is_file(candidate):
            return candidate

    names = (
        ("soffice.exe", "libreoffice.exe", "soffice", "libreoffice")
        if active_platform.startswith("win")
        else ("soffice", "libreoffice")
    )
    for name in names:
        resolved = which(name)
        if resolved:
            candidate = Path(resolved)
            if is_file(candidate):
                return candidate
    return None


def discover_libreoffice_python(
    executable: Path,
    *,
    environ: Mapping[str, str] | None = None,
    is_file: FilePredicate = Path.is_file,
    which: ExecutableFinder = shutil.which,
    can_import_uno: PythonProbe | None = None,
) -> Path | None:
    active_environ = os.environ if environ is None else environ
    candidates: list[Path] = []
    override = active_environ.get("THESISFORGE_LIBREOFFICE_PYTHON")
    if override:
        candidates.append(Path(override))

    if executable.parent.name == "MacOS" and executable.parent.parent.name == "Contents":
        candidates.append(executable.parent.parent / "Resources" / "python")

    candidates.extend(
        (
            executable.parent / "python.exe",
            executable.parent / "python",
            executable.parent / "python.bin",
            Path(sys.executable),
        )
    )
    resolved_python = which("python3")
    if resolved_python:
        candidates.append(Path(resolved_python))
    probe = can_import_uno or _can_import_uno
    for candidate in _unique_paths(candidates):
        if is_file(candidate) and probe(candidate):
            return candidate
    return None


def _can_import_uno(python_executable: Path) -> bool:
    try:
        result = subprocess.run(
            (str(python_executable), "-B", "-c", "import uno"),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _process_options() -> dict[str, object]:
    return {"start_new_session": True}


def _load_windows_kernel32() -> Any:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
    ]
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.SetInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    kernel32.SetInformationJobObject.restype = ctypes.c_int
    kernel32.AssignProcessToJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    kernel32.AssignProcessToJobObject.restype = ctypes.c_int
    kernel32.TerminateJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    kernel32.TerminateJobObject.restype = ctypes.c_int
    kernel32.ResumeThread.argtypes = [ctypes.c_void_p]
    kernel32.ResumeThread.restype = ctypes.c_uint32
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    return kernel32


def _create_windows_job(
    process: _OfficeProcess,
    *,
    kernel32: Any | None = None,
) -> _WindowsJob | None:
    if os.name != "nt" and kernel32 is None:
        return None

    active_kernel32 = kernel32
    if active_kernel32 is None:
        active_kernel32 = _load_windows_kernel32()

    handle = active_kernel32.CreateJobObjectW(None, None)
    if not handle:
        raise _windows_error()

    job = _WindowsJob(handle=handle, kernel32=active_kernel32)
    information = _ExtendedLimitInformation()
    information.basic_limit_information.limit_flags = (
        _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    )
    try:
        if not active_kernel32.SetInformationJobObject(
            handle,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(information),
            ctypes.sizeof(information),
        ):
            raise _windows_error()
        if not active_kernel32.AssignProcessToJobObject(
            handle,
            process._handle,
        ):
            raise _windows_error()
    except BaseException:
        job.close()
        raise
    return job


def _start_office_process(
    command: tuple[str, ...],
    *,
    winapi: Any | None = None,
    kernel32: Any | None = None,
    startup_info: Any | None = None,
) -> tuple[_OfficeProcess, _WindowsJob | None]:
    if os.name != "nt" and winapi is None:
        return (
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **_process_options(),
            ),
            None,
        )

    active_winapi = winapi
    if active_winapi is None:
        import _winapi

        active_winapi = _winapi
    active_kernel32 = kernel32 or _load_windows_kernel32()
    active_startup_info = startup_info or subprocess.STARTUPINFO()
    creation_flags = (
        _CREATE_NEW_PROCESS_GROUP | _CREATE_SUSPENDED | _CREATE_NO_WINDOW
    )
    process_handle, thread_handle, process_id, _thread_id = (
        active_winapi.CreateProcess(
            command[0],
            subprocess.list2cmdline(command),
            None,
            None,
            False,
            creation_flags,
            None,
            None,
            active_startup_info,
        )
    )
    process = _WindowsProcess(
        _handle=process_handle,
        pid=process_id,
        command=command,
        winapi=active_winapi,
    )
    job: _WindowsJob | None = None
    try:
        job = _create_windows_job(process, kernel32=active_kernel32)
        if active_kernel32.ResumeThread(thread_handle) == _RESUME_THREAD_FAILED:
            raise _windows_error()
    except BaseException:
        try:
            if job is not None:
                job.close()
            else:
                process.kill()
        finally:
            process.close()
        raise
    finally:
        active_kernel32.CloseHandle(thread_handle)
    return process, job


def _terminate_process_tree(
    process: _OfficeProcess,
    *,
    windows_job: _WindowsJob | None = None,
) -> None:
    if windows_job is not None:
        cleanup_error: OSError | None = None
        try:
            windows_job.terminate()
        except OSError as error:
            cleanup_error = error
        try:
            windows_job.close()
        except OSError as error:
            cleanup_error = cleanup_error or error
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        finally:
            close = getattr(process, "close", None)
            if close is not None:
                close()
        if cleanup_error is not None:
            raise cleanup_error
        return

    if process.poll() is not None:
        return

    if os.name == "nt":
        try:
            subprocess.run(
                ("taskkill", "/PID", str(process.pid), "/T", "/F"),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGCONT)
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=3)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGCONT)
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass


start_office_process = _start_office_process
terminate_office_process_tree = _terminate_process_tree


def _run_libreoffice_refresh(
    executable: Path,
    python_executable: Path,
    document_path: Path,
    timeout_seconds: float,
    max_level: int,
) -> None:
    temporary_root = "/tmp" if sys.platform == "darwin" else None
    with tempfile.TemporaryDirectory(
        prefix="thesisforge-lo-",
        dir=temporary_root,
    ) as profile_name:
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
        office_process, windows_job = _start_office_process(command)
        try:
            helper = subprocess.run(
                (
                    str(python_executable),
                    "-B",
                    "-c",
                    _UNO_REFRESH_SCRIPT,
                    pipe_name,
                    document_path.resolve().as_uri(),
                    str(connection_timeout),
                    str(max_level),
                ),
                check=False,
                capture_output=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
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
            _terminate_process_tree(
                office_process,
                windows_job=windows_job,
            )


def refresh_document_safely(
    refresher: DocumentRefresher,
    path: str | Path,
) -> bool:
    document_path = Path(path)
    original = document_path.read_bytes()
    preserved_parts = _read_package_parts(original, _RENDERER_OWNED_PARTS)
    try:
        refreshed = refresher.refresh(document_path)
        if refreshed and preserved_parts:
            _restore_package_parts(document_path, preserved_parts)
    except (BadZipFile, OSError, RuntimeError, subprocess.SubprocessError):
        refreshed = False
    if refreshed:
        return True
    document_path.write_bytes(original)
    return False


@dataclass(frozen=True, slots=True)
class _PackagePart:
    entry: ZipInfo
    content: bytes


def _read_package_parts(
    package_bytes: bytes,
    part_names: tuple[str, ...],
) -> dict[str, _PackagePart]:
    try:
        with ZipFile(BytesIO(package_bytes)) as package:
            entries = {entry.filename: entry for entry in package.infolist()}
            return {
                name: _PackagePart(
                    entry=entries[name],
                    content=package.read(name),
                )
                for name in part_names
                if name in entries
            }
    except (BadZipFile, OSError):
        return {}


def _restore_package_parts(
    package_path: Path,
    preserved_parts: Mapping[str, _PackagePart],
) -> None:
    refreshed_bytes = package_path.read_bytes()
    output = BytesIO()
    with (
        ZipFile(BytesIO(refreshed_bytes)) as refreshed,
        ZipFile(output, "w") as restored,
    ):
        restored.comment = refreshed.comment
        restored_names: set[str] = set()
        for entry in refreshed.infolist():
            restored_names.add(entry.filename)
            preserved = preserved_parts.get(entry.filename)
            restored.writestr(
                entry,
                preserved.content if preserved is not None else refreshed.read(entry),
            )
        for name in _RENDERER_OWNED_PARTS:
            preserved = preserved_parts.get(name)
            if preserved is not None and name not in restored_names:
                restored.writestr(preserved.entry, preserved.content)
    package_path.write_bytes(output.getvalue())


@dataclass(frozen=True, slots=True)
class LibreOfficeDocumentRefresher:
    executable: Path | None = None
    python_executable: Path | None = None
    timeout_seconds: float = 60.0
    runner: RefreshRunner = _run_libreoffice_refresh

    def refresh(self, path: str | Path) -> bool:
        document_path = Path(path)
        max_level = _toc_max_level(document_path)
        if max_level is None:
            return False
        if self.executable is None and not _automatic_refresh_enabled():
            return False

        executable = self.executable or discover_libreoffice_executable()
        if executable is None:
            return False
        python_executable = self.python_executable or discover_libreoffice_python(
            executable
        )
        if python_executable is None:
            return False

        original = document_path.read_bytes()
        try:
            self.runner(
                executable,
                python_executable,
                document_path,
                self.timeout_seconds,
                max_level,
            )
        except (OSError, RuntimeError, subprocess.SubprocessError):
            document_path.write_bytes(original)
            return False
        return True
