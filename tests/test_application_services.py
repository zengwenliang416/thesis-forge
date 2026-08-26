from __future__ import annotations

import errno
import os
import struct
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import pytest
from lxml import etree

from docforge import application
from docforge.application import (
    ApplicationDependencies,
    ApplicationStageError,
    BuildStage,
    BuildValidationError,
    PdfPreviewArtifact,
    build_service,
    inspect_service,
    validation_service,
)
from docforge.application.contracts import (
    ProjectIdentity,
    ProjectRequest,
    ProjectRequestIntent,
)
from docforge.application.office_refresh import (
    _CREATE_NEW_PROCESS_GROUP,
    _CREATE_NO_WINDOW,
    _CREATE_SUSPENDED,
    LibreOfficeDocumentRefresher,
    _automatic_refresh_enabled,
    _create_windows_job,
    _libreoffice_temporary_root,
    _run_libreoffice_refresh,
    _start_office_process,
    _terminate_process_tree,
    _toc_max_level,
    discover_libreoffice_executable,
    discover_libreoffice_python,
    refresh_document_safely,
)
from docforge.application.output import replace_output, temporary_output_path
from docforge.application.services import ProjectApplicationService
from docforge.core.parser_backend import create_parser_backend
from docforge.core.validator import ValidationContext
from docforge.renderers.docx.package import (
    DocxPackageValidationError,
    validate_docx_package,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CANONICAL_TEMPLATE = PROJECT_ROOT / "templates" / "base" / "bachelor.yaml"
_EXAMPLE_SOURCE_ROOT = tempfile.TemporaryDirectory(prefix="thesisforge-v2-")
EXAMPLE_SOURCE = Path(_EXAMPLE_SOURCE_ROOT.name) / "thesis.md"
EXAMPLE_SOURCE.write_text(
    "# 绪论 {#chap:introduction}\n\n正文。\n",
    encoding="utf-8",
)


def _canonical_context(document, template_path):
    return ValidationContext.from_document(
        document,
        template_path=template_path or _CANONICAL_TEMPLATE,
        required_metadata=(),
    )


def _canonical_dependencies(**overrides):
    return ApplicationDependencies(
        parser_backend=create_parser_backend(),
        context_factory=_canonical_context,
        **overrides,
    )


@pytest.fixture(autouse=True)
def _disable_default_pdf_preview(monkeypatch):
    monkeypatch.setattr(
        "docforge.application.pdf_preview.discover_libreoffice_executable",
        lambda: None,
    )


def _temporary_outputs(output: Path) -> list[Path]:
    return sorted(output.parent.glob(f".{output.name}.*.tmp.docx"))


def test_libreoffice_discovery_prefers_macos_application_bundle():
    expected = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")

    discovered = discover_libreoffice_executable(
        platform_name="darwin",
        environ={},
        which=lambda _name: "/opt/homebrew/bin/soffice",
        is_file=lambda path: path == expected,
    )

    assert discovered == expected


def test_libreoffice_discovery_uses_windows_program_files():
    expected = Path("C:/Program Files/LibreOffice/program/soffice.exe")

    discovered = discover_libreoffice_executable(
        platform_name="win32",
        environ={"ProgramFiles": "C:/Program Files"},
        which=lambda _name: None,
        is_file=lambda path: path == expected,
    )

    assert discovered == expected


def test_libreoffice_discovery_uses_linux_path_candidate():
    expected = Path("/opt/libreoffice/program/soffice")

    discovered = discover_libreoffice_executable(
        platform_name="linux",
        environ={},
        which=lambda name: str(expected) if name == "soffice" else None,
        is_file=lambda path: path == expected,
    )

    assert discovered == expected


def test_libreoffice_discovery_returns_none_when_runtime_is_missing():
    assert (
        discover_libreoffice_executable(
            platform_name="linux",
            environ={},
            which=lambda _name: None,
            is_file=lambda _path: False,
        )
        is None
    )


def test_libreoffice_discovery_prefers_explicit_override():
    expected = Path("/custom/libreoffice")

    discovered = discover_libreoffice_executable(
        platform_name="linux",
        environ={"THESISFORGE_LIBREOFFICE": str(expected)},
        which=lambda _name: None,
        is_file=lambda path: path == expected,
    )

    assert discovered == expected


def test_libreoffice_python_discovery_uses_macos_bundled_runtime():
    executable = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    expected = Path("/Applications/LibreOffice.app/Contents/Resources/python")

    discovered = discover_libreoffice_python(
        executable,
        environ={},
        is_file=lambda path: path == expected,
        which=lambda _name: None,
        can_import_uno=lambda path: path == expected,
    )

    assert discovered == expected


def test_libreoffice_python_discovery_rejects_runtime_without_uno(tmp_path: Path):
    executable = tmp_path / "soffice"
    incompatible = tmp_path / "python"
    incompatible.touch()

    discovered = discover_libreoffice_python(
        executable,
        environ={},
        is_file=Path.is_file,
        which=lambda _name: None,
        can_import_uno=lambda _path: False,
    )

    assert discovered is None


@pytest.mark.parametrize("value", ["0", "false", "NO", " off ", "disabled"])
def test_automatic_office_refresh_can_be_disabled(value: str):
    assert not _automatic_refresh_enabled({"THESISFORGE_OFFICE_REFRESH": value})


def test_automatic_office_refresh_defaults_to_enabled_for_empty_environment():
    assert _automatic_refresh_enabled({})


@pytest.mark.parametrize(
    ("field_xml", "expected"),
    [
        (b'TOC \\o "1-3" \\h \\z \\u', 3),
        (b"TOC \\o &quot;1-5&quot; \\h", 5),
        (b"REF fig_example \\h", None),
    ],
)
def test_toc_max_level_reads_real_field_switch(
    tmp_path: Path,
    field_xml: bytes,
    expected: int | None,
):
    document = tmp_path / "thesis.docx"
    _write_minimal_package(
        document,
        document_xml=(
            b"<w:document "
            b"xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
            b"<w:body><w:p><w:r><w:instrText>"
            + field_xml
            + b"</w:instrText></w:r></w:p></w:body></w:document>"
        ),
    )

    assert _toc_max_level(document) == expected


@pytest.mark.parametrize("mode", ["false", "error"])
def test_safe_document_refresh_restores_rendered_docx_on_failure(
    tmp_path: Path,
    mode: str,
):
    document = tmp_path / "thesis.docx"
    document.write_bytes(b"rendered-docx")

    class FailingRefresher:
        def refresh(self, path):
            Path(path).write_bytes(b"corrupted")
            if mode == "error":
                raise RuntimeError("refresh exploded")
            return False

    assert not refresh_document_safely(FailingRefresher(), document)
    assert document.read_bytes() == b"rendered-docx"


def test_safe_document_refresh_restores_rendered_docx_on_timeout(tmp_path: Path):
    document = tmp_path / "thesis.docx"
    document.write_bytes(b"rendered-docx")

    class TimingOutRefresher:
        def refresh(self, path):
            Path(path).write_bytes(b"corrupted")
            raise subprocess.TimeoutExpired("soffice", 1)

    assert not refresh_document_safely(TimingOutRefresher(), document)
    assert document.read_bytes() == b"rendered-docx"


def test_safe_document_refresh_preserves_renderer_owned_style_parts(
    tmp_path: Path,
):
    document = tmp_path / "thesis.docx"
    original_parts = {
        "word/document.xml": b"<document>dirty TOC field</document>",
        "word/styles.xml": "<styles>宋体 黑体 000000</styles>".encode(),
        "word/fontTable.xml": "<fonts>宋体 黑体</fonts>".encode(),
    }
    with ZipFile(document, "w", compression=ZIP_DEFLATED) as package:
        for name, content in original_parts.items():
            package.writestr(name, content)

    class MutatingRefresher:
        def refresh(self, path):
            with ZipFile(path) as source:
                entries = {
                    entry.filename: source.read(entry)
                    for entry in source.infolist()
                }
            entries["word/document.xml"] = b"<document>refreshed TOC result</document>"
            entries["word/styles.xml"] = b"<styles>MS Gothic theme blue</styles>"
            entries["word/fontTable.xml"] = b"<fonts>MS Gothic</fonts>"
            with ZipFile(path, "w", compression=ZIP_DEFLATED) as package:
                for name, content in entries.items():
                    package.writestr(name, content)
            return True

    assert refresh_document_safely(MutatingRefresher(), document)

    with ZipFile(document) as package:
        assert (
            package.read("word/document.xml")
            == b"<document>refreshed TOC result</document>"
        )
        assert package.read("word/styles.xml") == original_parts["word/styles.xml"]
        assert (
            package.read("word/fontTable.xml")
            == original_parts["word/fontTable.xml"]
        )


def test_safe_document_refresh_restores_renderer_parts_deleted_by_office(
    tmp_path: Path,
):
    document = tmp_path / "thesis.docx"
    original_parts = {
        "word/document.xml": b"<document>dirty TOC field</document>",
        "word/styles.xml": b"<styles>renderer styles</styles>",
        "word/fontTable.xml": b"<fonts>renderer fonts</fonts>",
    }
    with ZipFile(document, "w", compression=ZIP_DEFLATED) as package:
        for name, content in original_parts.items():
            package.writestr(name, content)

    class DeletingRefresher:
        def refresh(self, path):
            with ZipFile(path, "w", compression=ZIP_DEFLATED) as package:
                package.writestr(
                    "word/document.xml",
                    b"<document>refreshed TOC result</document>",
                )
            return True

    assert refresh_document_safely(DeletingRefresher(), document)

    with ZipFile(document) as package:
        assert (
            package.read("word/document.xml")
            == b"<document>refreshed TOC result</document>"
        )
        assert package.read("word/styles.xml") == original_parts["word/styles.xml"]
        assert (
            package.read("word/fontTable.xml")
            == original_parts["word/fontTable.xml"]
        )


def test_safe_document_refresh_restores_original_when_office_writes_invalid_zip(
    tmp_path: Path,
):
    document = tmp_path / "thesis.docx"
    with ZipFile(document, "w", compression=ZIP_DEFLATED) as package:
        package.writestr("word/document.xml", b"<document/>")
        package.writestr("word/styles.xml", b"<styles/>")
    original = document.read_bytes()

    class CorruptingRefresher:
        def refresh(self, path):
            Path(path).write_bytes(b"not-a-docx")
            return True

    assert not refresh_document_safely(CorruptingRefresher(), document)
    assert document.read_bytes() == original


def test_libreoffice_refresher_uses_discovered_runtime_and_injected_runner(
    tmp_path: Path,
):
    document = tmp_path / "thesis.docx"
    _write_minimal_package(
        document,
        document_xml=(
            b"<w:document "
            b"xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
            b"<w:body><w:p><w:r><w:instrText>TOC "
            b'\\o "1-3"</w:instrText></w:r></w:p></w:body></w:document>'
        ),
    )
    executable = tmp_path / "soffice"
    python_executable = tmp_path / "python"
    calls: list[tuple[Path, Path, Path, float, int]] = []

    def recording_runner(office, python, path, timeout, max_level):
        calls.append((office, python, path, timeout, max_level))
        path.write_bytes(b"refreshed-docx")

    refresher = LibreOfficeDocumentRefresher(
        executable=executable,
        python_executable=python_executable,
        timeout_seconds=12.5,
        runner=recording_runner,
    )

    assert refresher.refresh(document)
    assert calls == [(executable, python_executable, document, 12.5, 3)]
    assert document.read_bytes() == b"refreshed-docx"


def test_libreoffice_refresher_skips_document_without_toc_field(tmp_path: Path):
    document = tmp_path / "thesis.docx"
    _write_minimal_package(document)
    calls: list[Path] = []

    def unexpected_runner(_office, _python, path, _timeout, _max_level):
        calls.append(path)

    refresher = LibreOfficeDocumentRefresher(
        executable=tmp_path / "soffice",
        python_executable=tmp_path / "python",
        runner=unexpected_runner,
    )

    assert not refresher.refresh(document)
    assert calls == []


def test_libreoffice_refresher_restores_document_after_runner_failure(
    tmp_path: Path,
):
    document = tmp_path / "thesis.docx"
    _write_minimal_package(
        document,
        document_xml=(
            b"<w:document "
            b"xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
            b"<w:body><w:p><w:r><w:instrText>TOC "
            b'\\o "1-3"</w:instrText></w:r></w:p></w:body></w:document>'
        ),
    )
    original = document.read_bytes()
    seen: list[bytes] = []

    def failing_runner(_office, _python, path, _timeout, _max_level):
        seen.append(path.read_bytes())
        path.write_bytes(b"corrupted")
        raise RuntimeError("refresh failed")

    refresher = LibreOfficeDocumentRefresher(
        executable=tmp_path / "soffice",
        python_executable=tmp_path / "python",
        runner=failing_runner,
    )

    assert not refresher.refresh(document)
    assert seen == [original]
    assert document.read_bytes() == original


def test_libreoffice_runner_uses_headless_unique_process_state_and_cleans_profiles(
    tmp_path: Path,
    monkeypatch,
):
    document = tmp_path / "thesis.docx"
    document.write_bytes(b"docx")
    office_commands: list[tuple[str, ...]] = []
    helper_commands: list[tuple[str, ...]] = []
    terminated: list[object] = []

    class FakeProcess:
        pid = 42

        def poll(self):
            return None

    def fake_popen(command, **_kwargs):
        office_commands.append(tuple(command))
        return FakeProcess()

    def fake_run(command, **_kwargs):
        helper_commands.append(tuple(command))
        return subprocess.CompletedProcess(command, 0, "", "")

    def record_termination(process, *, windows_job=None):
        terminated.append((process, windows_job))

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "docforge.application.office_refresh._terminate_process_tree",
        record_termination,
    )

    for _ in range(2):
        _run_libreoffice_refresh(
            tmp_path / "soffice",
            tmp_path / "python",
            document,
            15.0,
            3,
        )

    assert len(office_commands) == 2
    assert all("--headless" in command for command in office_commands)
    assert office_commands[0] != office_commands[1]
    assert helper_commands[0][4] != helper_commands[1][4]
    profile_arguments = [
        next(part for part in command if part.startswith("-env:UserInstallation="))
        for command in office_commands
    ]
    assert profile_arguments[0] != profile_arguments[1]
    for argument in profile_arguments:
        assert not Path(argument.removeprefix("-env:UserInstallation=file://")).exists()
    assert len(terminated) == 2


def test_libreoffice_temporary_root_prefers_short_macos_root(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(
        "docforge.application.office_refresh.sys.platform", "darwin"
    )
    monkeypatch.setattr(
        "docforge.application.office_refresh._MACOS_TEMPORARY_ROOT",
        str(tmp_path),
    )

    assert _libreoffice_temporary_root() == str(tmp_path)


def test_libreoffice_temporary_root_falls_back_when_macos_root_missing(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(
        "docforge.application.office_refresh.sys.platform", "darwin"
    )
    monkeypatch.setattr(
        "docforge.application.office_refresh._MACOS_TEMPORARY_ROOT",
        str(tmp_path / "missing"),
    )

    assert _libreoffice_temporary_root() is None


def test_libreoffice_temporary_root_falls_back_when_macos_root_not_writable(
    tmp_path: Path,
    monkeypatch,
):
    read_only = tmp_path / "read-only"
    read_only.mkdir()
    read_only.chmod(0o555)
    if os.access(read_only, os.W_OK):
        pytest.skip("non-writable check requires a non-root user")
    monkeypatch.setattr(
        "docforge.application.office_refresh.sys.platform", "darwin"
    )
    monkeypatch.setattr(
        "docforge.application.office_refresh._MACOS_TEMPORARY_ROOT",
        str(read_only),
    )

    assert _libreoffice_temporary_root() is None


def test_libreoffice_temporary_root_uses_default_off_macos(monkeypatch):
    monkeypatch.setattr(
        "docforge.application.office_refresh.sys.platform", "linux"
    )

    assert _libreoffice_temporary_root() is None


def test_libreoffice_runner_falls_back_to_default_temporary_root(
    tmp_path: Path,
    monkeypatch,
):
    document = tmp_path / "thesis.docx"
    document.write_bytes(b"docx")
    missing_root = tmp_path / "missing"
    profiles: list[Path] = []

    class FakeProcess:
        pid = 42

        def poll(self):
            return None

    def fake_popen(command, **_kwargs):
        profile_argument = next(
            part for part in command if part.startswith("-env:UserInstallation=")
        )
        profiles.append(
            Path(profile_argument.removeprefix("-env:UserInstallation=file://"))
        )
        return FakeProcess()

    def fake_run(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "docforge.application.office_refresh.sys.platform", "darwin"
    )
    monkeypatch.setattr(
        "docforge.application.office_refresh._MACOS_TEMPORARY_ROOT",
        str(missing_root),
    )
    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "docforge.application.office_refresh._terminate_process_tree",
        lambda _process, *, windows_job=None: None,
    )

    _run_libreoffice_refresh(
        tmp_path / "soffice",
        tmp_path / "python",
        document,
        15.0,
        3,
    )

    assert len(profiles) == 1
    assert missing_root not in profiles[0].parents
    assert not profiles[0].exists()


def test_windows_process_tree_cleanup_falls_back_when_taskkill_fails(monkeypatch):
    calls: list[tuple[str, ...]] = []

    class FakeProcess:
        pid = 42
        killed = False
        waits = 0

        def poll(self):
            return None

        def kill(self):
            self.killed = True

        def wait(self, timeout):
            self.waits += 1
            return 0

    def failing_taskkill(command, **_kwargs):
        calls.append(tuple(command))
        raise subprocess.CalledProcessError(1, command)

    process = FakeProcess()
    monkeypatch.setattr("docforge.application.office_refresh.os.name", "nt")
    monkeypatch.setattr(subprocess, "run", failing_taskkill)

    _terminate_process_tree(process)

    assert calls == [("taskkill", "/PID", "42", "/T", "/F")]
    assert process.killed
    assert process.waits == 1


def test_windows_job_owns_and_terminates_entire_office_process_tree():
    calls: list[tuple[object, ...]] = []

    class FakeKernel32:
        def CreateJobObjectW(self, security, name):
            calls.append(("create", security, name))
            return 101

        def SetInformationJobObject(self, handle, info_class, pointer, size):
            calls.append(
                (
                    "configure",
                    handle,
                    info_class,
                    pointer._obj.basic_limit_information.limit_flags,
                    size,
                )
            )
            return 1

        def AssignProcessToJobObject(self, handle, process_handle):
            calls.append(("assign", handle, process_handle))
            return 1

        def TerminateJobObject(self, handle, exit_code):
            calls.append(("terminate", handle, exit_code))
            return 1

        def CloseHandle(self, handle):
            calls.append(("close", handle))
            return 1

    class FakeProcess:
        _handle = 202
        waited = False
        killed = False

        def wait(self, timeout):
            self.waited = True
            return 0

        def kill(self):
            self.killed = True

    process = FakeProcess()
    job = _create_windows_job(process, kernel32=FakeKernel32())

    assert job is not None
    _terminate_process_tree(process, windows_job=job)

    assert calls[0] == ("create", None, None)
    assert calls[1][0:4] == ("configure", 101, 9, 0x00002000)
    assert ("assign", 101, 202) in calls
    assert ("terminate", 101, 1) in calls
    assert ("close", 101) in calls
    assert process.waited
    assert not process.killed


def test_windows_office_process_is_assigned_to_job_before_resume():
    calls: list[tuple[object, ...]] = []

    class FakeWinapi:
        INFINITE = 0xFFFFFFFF
        WAIT_OBJECT_0 = 0
        WAIT_TIMEOUT = 258

        def CreateProcess(
            self,
            application,
            command_line,
            process_attributes,
            thread_attributes,
            inherit_handles,
            creation_flags,
            environment,
            current_directory,
            startup_info,
        ):
            calls.append(
                (
                    "create-process",
                    application,
                    command_line,
                    process_attributes,
                    thread_attributes,
                    inherit_handles,
                    creation_flags,
                    environment,
                    current_directory,
                    startup_info,
                )
            )
            return 301, 302, 303, 304

        def WaitForSingleObject(self, handle, timeout):
            calls.append(("wait", handle, timeout))
            return self.WAIT_OBJECT_0

        def GetExitCodeProcess(self, handle):
            calls.append(("exit-code", handle))
            return 0

        def TerminateProcess(self, handle, exit_code):
            calls.append(("terminate-process", handle, exit_code))

        def CloseHandle(self, handle):
            calls.append(("close-process-handle", handle))

    class FakeKernel32:
        def CreateJobObjectW(self, security, name):
            calls.append(("create-job", security, name))
            return 401

        def SetInformationJobObject(self, handle, info_class, pointer, size):
            calls.append(("configure-job", handle, info_class, size))
            return 1

        def AssignProcessToJobObject(self, handle, process_handle):
            calls.append(("assign-job", handle, process_handle))
            return 1

        def ResumeThread(self, thread_handle):
            calls.append(("resume-thread", thread_handle))
            return 1

        def TerminateJobObject(self, handle, exit_code):
            calls.append(("terminate-job", handle, exit_code))
            return 1

        def CloseHandle(self, handle):
            calls.append(("close-kernel-handle", handle))
            return 1

    startup_info = object()
    process, job = _start_office_process(
        ("soffice.exe", "--headless"),
        winapi=FakeWinapi(),
        kernel32=FakeKernel32(),
        startup_info=startup_info,
    )

    create_call = calls[0]
    assert create_call[0] == "create-process"
    assert create_call[6] == (
        _CREATE_NEW_PROCESS_GROUP | _CREATE_SUSPENDED | _CREATE_NO_WINDOW
    )
    assert create_call[9] is startup_info
    assert calls.index(("assign-job", 401, 301)) < calls.index(
        ("resume-thread", 302)
    )
    assert ("close-kernel-handle", 302) in calls

    assert job is not None
    _terminate_process_tree(process, windows_job=job)

    assert ("terminate-job", 401, 1) in calls
    assert ("close-kernel-handle", 401) in calls
    assert ("close-process-handle", 301) in calls


def test_windows_office_resume_failure_closes_job_thread_and_process_handles():
    calls: list[tuple[object, ...]] = []

    class FakeWinapi:
        def CreateProcess(self, *_args):
            calls.append(("create-process",))
            return 301, 302, 303, 304

        def WaitForSingleObject(self, _handle, _timeout):
            return 258

        def TerminateProcess(self, handle, exit_code):
            calls.append(("terminate-process", handle, exit_code))

        def CloseHandle(self, handle):
            calls.append(("close-process-handle", handle))

    class FakeKernel32:
        def CreateJobObjectW(self, _security, _name):
            return 401

        def SetInformationJobObject(self, *_args):
            return 1

        def AssignProcessToJobObject(self, *_args):
            return 1

        def ResumeThread(self, thread_handle):
            calls.append(("resume-thread", thread_handle))
            return 0xFFFFFFFF

        def CloseHandle(self, handle):
            calls.append(("close-kernel-handle", handle))
            return 1

    with pytest.raises(OSError, match="Windows API call failed"):
        _start_office_process(
            ("soffice.exe", "--headless"),
            winapi=FakeWinapi(),
            kernel32=FakeKernel32(),
            startup_info=object(),
        )

    assert ("close-kernel-handle", 401) in calls
    assert ("close-kernel-handle", 302) in calls
    assert ("close-process-handle", 301) in calls


def test_windows_job_assignment_failure_terminates_suspended_process():
    calls: list[tuple[object, ...]] = []

    class FakeWinapi:
        INFINITE = 0xFFFFFFFF
        WAIT_OBJECT_0 = 0
        WAIT_TIMEOUT = 258

        def CreateProcess(self, *_args):
            calls.append(("create-process",))
            return 301, 302, 303, 304

        def WaitForSingleObject(self, handle, timeout):
            calls.append(("wait", handle, timeout))
            return self.WAIT_TIMEOUT

        def TerminateProcess(self, handle, exit_code):
            calls.append(("terminate-process", handle, exit_code))

        def CloseHandle(self, handle):
            calls.append(("close-process-handle", handle))

    class FakeKernel32:
        def CreateJobObjectW(self, _security, _name):
            return 401

        def SetInformationJobObject(self, *_args):
            return 1

        def AssignProcessToJobObject(self, handle, process_handle):
            calls.append(("assign-job", handle, process_handle))
            return 0

        def ResumeThread(self, thread_handle):
            calls.append(("resume-thread", thread_handle))
            return 1

        def CloseHandle(self, handle):
            calls.append(("close-kernel-handle", handle))
            return 1

    with pytest.raises(OSError, match="Windows API call failed"):
        _start_office_process(
            ("soffice.exe", "--headless"),
            winapi=FakeWinapi(),
            kernel32=FakeKernel32(),
            startup_info=object(),
        )

    assert ("assign-job", 401, 301) in calls
    assert not any(call[0] == "resume-thread" for call in calls)
    assert ("close-kernel-handle", 401) in calls
    assert ("terminate-process", 301, 1) in calls
    assert ("close-process-handle", 301) in calls
    assert ("close-kernel-handle", 302) in calls


def test_windows_job_cleanup_closes_process_handle_after_terminate_error():
    calls: list[str] = []

    class FailingJob:
        def terminate(self):
            calls.append("terminate-job")
            raise OSError("terminate failed")

        def close(self):
            calls.append("close-job")

    class FakeProcess:
        def wait(self, timeout):
            calls.append(f"wait-{timeout}")
            return 0

        def kill(self):
            calls.append("kill-process")

        def close(self):
            calls.append("close-process")

    with pytest.raises(OSError, match="terminate failed"):
        _terminate_process_tree(
            FakeProcess(),
            windows_job=FailingJob(),
        )

    assert calls == [
        "terminate-job",
        "close-job",
        "wait-5",
        "close-process",
    ]


def test_build_service_refreshes_before_validation_and_atomic_replace(
    tmp_path: Path,
):
    output = tmp_path / "thesis.docx"
    calls: list[str] = []

    class MinimalRenderer:
        def render(self, _plan, path):
            calls.append("render")
            _write_minimal_package(Path(path))
            return Path(path)

    class RecordingRefresher:
        def refresh(self, _path):
            calls.append("refresh")
            return True

    def recording_validator(path):
        calls.append("validate")
        validate_docx_package(path)

    def recording_replace(source, target):
        calls.append("replace")
        source.replace(target)

    class RecordingPdfExporter:
        def export(self, docx_path, pdf_path):
            calls.append("export-pdf")
            assert Path(docx_path) == output
            assert Path(docx_path).is_file()
            assert Path(pdf_path) == tmp_path / "thesis.preview.pdf"
            Path(pdf_path).write_bytes(b"%PDF-1.7\npreview")
            return PdfPreviewArtifact(
                path=Path(pdf_path),
                name=Path(pdf_path).name,
                engine="libreoffice",
                label="LibreOffice PDF",
            )

    result = build_service(
        EXAMPLE_SOURCE,
        output,
        dependencies=_canonical_dependencies(
            renderer=MinimalRenderer(),
            document_refresher=RecordingRefresher(),
            package_validator=recording_validator,
            replace_file=recording_replace,
            pdf_preview_exporter=RecordingPdfExporter(),
        ),
    )

    assert calls == ["render", "refresh", "validate", "replace", "export-pdf"]
    assert result.final_preview == PdfPreviewArtifact(
        path=tmp_path / "thesis.preview.pdf",
        name="thesis.preview.pdf",
        engine="libreoffice",
        label="LibreOffice PDF",
    )
    validate_docx_package(output)


@pytest.mark.parametrize("mode", ["none", "error"])
def test_build_service_pdf_preview_failure_does_not_fail_published_docx(
    tmp_path: Path,
    mode: str,
):
    output = tmp_path / "thesis.docx"

    class PreviewMissExporter:
        def export(self, docx_path, pdf_path):
            assert Path(docx_path) == output
            assert Path(docx_path).is_file()
            assert Path(pdf_path) == tmp_path / "thesis.preview.pdf"
            if mode == "error":
                raise RuntimeError("preview exploded")

    result = build_service(
        EXAMPLE_SOURCE,
        output,
        dependencies=_canonical_dependencies(
            pdf_preview_exporter=PreviewMissExporter(),
        ),
    )

    assert result.output_path == output
    assert result.final_preview is None
    validate_docx_package(output)


def test_build_service_allows_pdf_preview_export_to_be_disabled(tmp_path: Path):
    output = tmp_path / "thesis.docx"

    result = build_service(
        EXAMPLE_SOURCE,
        output,
        dependencies=_canonical_dependencies(pdf_preview_exporter=None),
    )

    assert result.final_preview is None
    validate_docx_package(output)


def test_application_dependencies_disable_pdf_preview_by_default():
    assert ApplicationDependencies().pdf_preview_exporter is None


@pytest.mark.parametrize("mode", ["false", "error"])
def test_build_service_restores_rendered_package_after_optional_refresh_failure(
    tmp_path: Path,
    mode: str,
):
    output = tmp_path / "thesis.docx"
    validated_bytes: list[bytes] = []

    class MinimalRenderer:
        def render(self, _plan, path):
            _write_minimal_package(Path(path))
            return Path(path)

    class FailingRefresher:
        def refresh(self, path):
            Path(path).write_bytes(b"corrupted")
            if mode == "error":
                raise RuntimeError("refresh exploded")
            return False

    def recording_validator(path):
        validated_bytes.append(Path(path).read_bytes())
        validate_docx_package(path)

    build_service(
        EXAMPLE_SOURCE,
        output,
        dependencies=_canonical_dependencies(
            renderer=MinimalRenderer(),
            document_refresher=FailingRefresher(),
            package_validator=recording_validator,
        ),
    )

    assert len(validated_bytes) == 1
    assert validated_bytes[0] != b"corrupted"
    assert output.read_bytes() == validated_bytes[0]
    validate_docx_package(output)


def test_successful_refresh_with_corrupt_package_preserves_previous_output(
    tmp_path: Path,
):
    output = tmp_path / "thesis.docx"
    output.write_bytes(b"previous-valid-output")

    class MinimalRenderer:
        def render(self, _plan, path):
            _write_minimal_package(Path(path))
            return Path(path)

    class CorruptingRefresher:
        def refresh(self, path):
            Path(path).write_bytes(b"corrupted")
            return True

    with pytest.raises(ApplicationStageError) as captured:
        build_service(
            EXAMPLE_SOURCE,
            output,
            dependencies=_canonical_dependencies(
                renderer=MinimalRenderer(),
                document_refresher=CorruptingRefresher(),
            ),
        )

    assert captured.value.stage is BuildStage.FINALIZE
    assert output.read_bytes() == b"previous-valid-output"
    assert _temporary_outputs(output) == []


def _write_minimal_package(
    path: Path,
    *,
    include_document: bool = True,
    content_types_xml: bytes | None = None,
    relationships_xml: bytes | None = None,
    document_xml: bytes = (
        b"<w:document "
        b"xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'/>"
    ),
    compression: int = ZIP_DEFLATED,
) -> None:
    with ZipFile(path, "w", compression=compression) as package:
        package.writestr(
            "[Content_Types].xml",
            content_types_xml
            or (
                b"<Types "
                b"xmlns='http://schemas.openxmlformats.org/package/2006/content-types'>"
                b"<Override PartName='/word/document.xml' "
                b"ContentType='application/vnd.openxmlformats-officedocument."
                b"wordprocessingml.document.main+xml'/>"
                b"</Types>"
            ),
        )
        package.writestr(
            "_rels/.rels",
            relationships_xml
            or (
                b"<Relationships "
                b"xmlns='http://schemas.openxmlformats.org/package/2006/relationships'>"
                b"<Relationship Id='rId1' "
                b"Type='http://schemas.openxmlformats.org/officeDocument/2006/"
                b"relationships/officeDocument' Target='word/document.xml'/>"
                b"</Relationships>"
            ),
        )
        if include_document:
            package.writestr("word/document.xml", document_xml)


def _semantic_snapshot(path: Path) -> tuple[object, ...]:
    namespaces = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    }
    with ZipFile(path) as package:
        document = etree.fromstring(package.read("word/document.xml"))
        footnotes = (
            etree.fromstring(package.read("word/footnotes.xml"))
            if "word/footnotes.xml" in package.namelist()
            else None
        )
        numbering = (
            etree.fromstring(package.read("word/numbering.xml"))
            if "word/numbering.xml" in package.namelist()
            else None
        )

    body_text = tuple(document.xpath(".//w:t/text()", namespaces=namespaces))
    fields = tuple(
        text.strip()
        for text in document.xpath(".//w:instrText/text()", namespaces=namespaces)
    )
    bookmarks = tuple(
        document.xpath(".//w:bookmarkStart/@w:name", namespaces=namespaces)
    )
    footnote_text = (
        tuple(footnotes.xpath(".//w:t/text()", namespaces=namespaces))
        if footnotes is not None
        else ()
    )
    numbering_levels = (
        tuple(
            (
                level.get(f"{{{namespaces['w']}}}ilvl"),
                tuple(level.xpath("./w:numFmt/@w:val", namespaces=namespaces)),
                tuple(level.xpath("./w:lvlText/@w:val", namespaces=namespaces)),
            )
            for level in numbering.xpath(".//w:lvl", namespaces=namespaces)
        )
        if numbering is not None
        else ()
    )
    return body_text, fields, bookmarks, footnote_text, numbering_levels


def test_shared_services_reuse_one_application_boundary_without_output(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论 {#chap:intro}\n", encoding="utf-8")
    before = set(tmp_path.iterdir())

    inspection = inspect_service(source, dependencies=_canonical_dependencies())
    validation = validation_service(
        source,
        template_path=PROJECT_ROOT / "templates" / "base" / "bachelor.yaml",
        dependencies=_canonical_dependencies(),
    )

    assert inspection.document.source_path == source.resolve()
    assert validation.document.source_path == inspection.document.source_path
    assert validation.errors == ()
    assert validation.context.template is not None
    assert set(tmp_path.iterdir()) == before


def test_preview_service_compiles_without_renderer_or_output(tmp_path: Path):
    assert hasattr(application, "preview_service")
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论 {#chap:intro}\n", encoding="utf-8")
    calls: list[str] = []

    class UnexpectedRenderer:
        def render(self, _plan, _path):
            calls.append("render")
            raise AssertionError("preview must not render")

    before = set(tmp_path.iterdir())
    result = application.preview_service(
        source,
        template_path=PROJECT_ROOT / "templates" / "base" / "bachelor.yaml",
        dependencies=_canonical_dependencies(renderer=UnexpectedRenderer()),
    )

    assert result.document.source_path == source.resolve()
    assert result.context.template is not None
    assert result.errors == ()
    assert result.plan is not None
    assert calls == []
    assert set(tmp_path.iterdir()) == before


def test_preview_service_stops_before_compile_on_fatal_validation(tmp_path: Path):
    assert hasattr(application, "preview_service")
    source = tmp_path / "invalid.md"
    source.write_text("# 绪论 {#bad}\n", encoding="utf-8")
    calls: list[str] = []

    def unexpected_compiler(*_args, **_kwargs):
        calls.append("compile")
        raise AssertionError("compiler must not run")

    result = application.preview_service(
        source,
        dependencies=_canonical_dependencies(compiler=unexpected_compiler),
    )

    assert result.errors
    assert result.plan is None
    assert calls == []


def test_preview_service_normalizes_compile_failure(tmp_path: Path):
    assert hasattr(application, "preview_service")
    source = tmp_path / "thesis.md"
    source.write_text("# 绪论 {#chap:intro}\n", encoding="utf-8")

    def failing_compiler(*_args, **_kwargs):
        raise RuntimeError("preview compile exploded")

    with pytest.raises(ApplicationStageError) as captured:
        application.preview_service(
            source,
            template_path=PROJECT_ROOT / "templates" / "base" / "bachelor.yaml",
            dependencies=_canonical_dependencies(compiler=failing_compiler),
        )

    assert captured.value.stage is BuildStage.COMPILE
    assert str(captured.value) == "preview compile exploded"


def test_build_service_reports_progress_and_atomically_replaces_target(tmp_path: Path):
    output = tmp_path / "nested" / "thesis.docx"
    stages: list[BuildStage] = []

    result = build_service(
        EXAMPLE_SOURCE,
        output,
        on_progress=stages.append,
        dependencies=_canonical_dependencies(),
    )

    assert result.output_path == output
    assert output.is_file()
    assert stages == [
        BuildStage.PARSE,
        BuildStage.VALIDATE,
        BuildStage.COMPILE,
        BuildStage.RENDER,
        BuildStage.FINALIZE,
    ]
    assert _temporary_outputs(output) == []
    validate_docx_package(output)


@pytest.mark.parametrize(
    ("cancel_on_check", "expected_stage"),
    [
        (1, BuildStage.PARSE),
        (2, BuildStage.VALIDATE),
        (3, BuildStage.COMPILE),
        (4, BuildStage.RENDER),
        (5, BuildStage.FINALIZE),
        (6, BuildStage.FINALIZE),
    ],
)
def test_build_cancellation_at_every_boundary_preserves_previous_output(
    tmp_path: Path,
    cancel_on_check: int,
    expected_stage: BuildStage,
):
    output = tmp_path / "thesis.docx"
    output.write_bytes(b"previous-valid-output")
    checks = 0
    replacements: list[tuple[Path, Path]] = []

    class MinimalRenderer:
        def render(self, _plan, path):
            _write_minimal_package(Path(path))
            return Path(path)

    def should_cancel() -> bool:
        nonlocal checks
        checks += 1
        return checks == cancel_on_check

    def replace_file(source: Path, target: Path) -> None:
        replacements.append((source, target))
        source.replace(target)

    with pytest.raises(application.BuildCanceledError) as captured:
        build_service(
            EXAMPLE_SOURCE,
            output,
            should_cancel=should_cancel,
            dependencies=_canonical_dependencies(
                renderer=MinimalRenderer(),
                replace_file=replace_file,
            ),
        )

    assert captured.value.stage is expected_stage
    assert output.read_bytes() == b"previous-valid-output"
    assert _temporary_outputs(output) == []
    if cancel_on_check == 6:
        assert replacements == []


def test_progress_callback_failure_preserves_previous_output(tmp_path: Path):
    output = tmp_path / "thesis.docx"
    output.write_bytes(b"previous-valid-output")

    def failing_callback(stage: BuildStage) -> None:
        if stage is BuildStage.RENDER:
            raise RuntimeError("progress consumer failed")

    with pytest.raises(ApplicationStageError) as captured:
        build_service(
            EXAMPLE_SOURCE,
            output,
            on_progress=failing_callback,
            dependencies=_canonical_dependencies(),
        )

    assert captured.value.stage is BuildStage.RENDER
    assert str(captured.value) == "progress consumer failed"
    assert output.read_bytes() == b"previous-valid-output"
    assert _temporary_outputs(output) == []


def test_fatal_validation_stops_before_compile_render_or_output(tmp_path: Path):
    source = tmp_path / "invalid.md"
    source.write_text("# 绪论 {#bad}\n", encoding="utf-8")
    output = tmp_path / "thesis.docx"
    output.write_bytes(b"previous-valid-output")
    calls: list[str] = []

    def unexpected_compiler(*args, **kwargs):
        calls.append("compile")
        raise AssertionError("compiler must not run")

    class UnexpectedRenderer:
        def render(self, plan, path):
            calls.append("render")
            raise AssertionError("renderer must not run")

    dependencies = _canonical_dependencies(
        compiler=unexpected_compiler,
        renderer=UnexpectedRenderer(),
    )

    with pytest.raises(BuildValidationError) as captured:
        build_service(source, output, dependencies=dependencies)

    assert captured.value.stage is BuildStage.VALIDATE
    assert captured.value.issues
    assert calls == []
    assert output.read_bytes() == b"previous-valid-output"
    assert _temporary_outputs(output) == []


class _FailingRenderer:
    def render(self, plan, path):
        temporary = Path(path)
        temporary.write_bytes(b"partial-docx")
        raise RuntimeError("renderer exploded")


@pytest.mark.parametrize(
    ("failure_stage", "dependencies_factory"),
    [
        (
            BuildStage.PARSE,
            lambda defaults: replace(
                defaults,
                parser=lambda _source: (_ for _ in ()).throw(ValueError("parse exploded")),
            ),
        ),
        (
            BuildStage.VALIDATE,
            lambda defaults: replace(
                defaults,
                validator=lambda _document, _context: (_ for _ in ()).throw(
                    RuntimeError("validation exploded")
                ),
            ),
        ),
        (
            BuildStage.COMPILE,
            lambda defaults: replace(
                defaults,
                compiler=lambda *args, **kwargs: (_ for _ in ()).throw(
                    RuntimeError("compiler exploded")
                ),
            ),
        ),
        (
            BuildStage.RENDER,
            lambda defaults: replace(defaults, renderer=_FailingRenderer()),
        ),
        (
            BuildStage.FINALIZE,
            lambda defaults: replace(
                defaults,
                package_validator=lambda _path: (_ for _ in ()).throw(
                    DocxPackageValidationError("package exploded")
                ),
            ),
        ),
        (
            BuildStage.FINALIZE,
            lambda defaults: replace(
                defaults,
                replace_file=lambda _source, _target: (_ for _ in ()).throw(
                    PermissionError("replace exploded")
                ),
            ),
        ),
    ],
)
def test_failed_rebuild_preserves_old_output_and_cleans_temporary_files(
    tmp_path: Path,
    failure_stage: BuildStage,
    dependencies_factory,
):
    output = tmp_path / "thesis.docx"
    old_bytes = b"previous-valid-output"
    output.write_bytes(old_bytes)
    dependencies = dependencies_factory(_canonical_dependencies())

    with pytest.raises(ApplicationStageError) as captured:
        build_service(EXAMPLE_SOURCE, output, dependencies=dependencies)

    assert captured.value.stage is failure_stage
    assert output.read_bytes() == old_bytes
    assert _temporary_outputs(output) == []


def test_renderer_receives_unique_temporary_path_in_target_directory(tmp_path: Path):
    output = tmp_path / "thesis.docx"
    seen: list[Path] = []

    class RecordingRenderer:
        def render(self, plan, path):
            temporary = Path(path)
            seen.append(temporary)
            _write_minimal_package(temporary)
            return temporary

    dependencies = _canonical_dependencies(renderer=RecordingRenderer())

    build_service(EXAMPLE_SOURCE, output, dependencies=dependencies)

    assert len(seen) == 1
    assert seen[0].parent == output.parent
    assert seen[0] != output
    assert seen[0].name.startswith(f".{output.name}.")
    assert not seen[0].exists()


def test_temporary_output_context_cleans_partial_file_after_failure(tmp_path: Path):
    output = tmp_path / "nested" / "thesis.docx"
    seen: Path | None = None

    with (
        pytest.raises(RuntimeError, match="failed"),
        temporary_output_path(output) as temporary,
    ):
        seen = temporary
        temporary.write_bytes(b"partial")
        raise RuntimeError("failed")

    assert seen is not None
    assert seen.parent == output.parent
    assert not seen.exists()
    assert not output.exists()


def test_replace_output_uses_injected_atomic_replacer(tmp_path: Path):
    temporary = tmp_path / ".thesis.docx.token.tmp.docx"
    output = tmp_path / "thesis.docx"
    temporary.write_bytes(b"new-output")
    calls: list[tuple[Path, Path]] = []

    def recording_replace(source: Path, target: Path) -> None:
        calls.append((source, target))
        source.replace(target)

    replace_output(temporary, output, replace_file=recording_replace)

    assert calls == [(temporary, output)]
    assert output.read_bytes() == b"new-output"
    assert not temporary.exists()


def test_replace_output_stages_cross_device_sources_in_target_directory(
    tmp_path: Path,
):
    source_directory = tmp_path / "source"
    target_directory = tmp_path / "target"
    source_directory.mkdir()
    target_directory.mkdir()
    temporary = source_directory / "converted.pdf"
    output = target_directory / "thesis.preview.pdf"
    temporary.write_bytes(b"%PDF-1.7\npreview")
    calls: list[tuple[Path, Path]] = []

    def cross_device_replace(source: Path, target: Path) -> None:
        calls.append((source, target))
        if source == temporary:
            raise OSError(errno.EXDEV, "Cross-device link")
        source.replace(target)

    replace_output(temporary, output, replace_file=cross_device_replace)

    assert calls[0] == (temporary, output)
    assert calls[1][0].parent == output.parent
    assert calls[1][1] == output
    assert output.read_bytes() == b"%PDF-1.7\npreview"
    assert temporary.exists()
    assert not calls[1][0].exists()


@pytest.mark.parametrize(
    "package_factory",
    [
        lambda path: path.write_bytes(b"not-a-zip"),
        lambda path: _write_minimal_package(path, include_document=False),
        lambda path: _write_minimal_package(path, document_xml=b"<w:document"),
    ],
)
def test_docx_package_validation_rejects_invalid_packages(
    tmp_path: Path,
    package_factory,
):
    package_path = tmp_path / "invalid.docx"
    package_factory(package_path)

    with pytest.raises(DocxPackageValidationError):
        validate_docx_package(package_path)


def test_docx_package_validation_rejects_crc_corruption(tmp_path: Path):
    package_path = tmp_path / "corrupt-crc.docx"
    _write_minimal_package(package_path, compression=ZIP_STORED)
    with ZipFile(package_path) as package:
        document_info = package.getinfo("word/document.xml")

    archive = bytearray(package_path.read_bytes())
    name_length, extra_length = struct.unpack_from(
        "<HH",
        archive,
        document_info.header_offset + 26,
    )
    data_offset = document_info.header_offset + 30 + name_length + extra_length
    archive[data_offset] ^= 0xFF
    package_path.write_bytes(archive)

    with pytest.raises(DocxPackageValidationError):
        validate_docx_package(package_path)


def test_docx_package_validation_rejects_duplicate_parts(tmp_path: Path):
    package_path = tmp_path / "duplicate-part.docx"
    _write_minimal_package(package_path)
    with ZipFile(package_path) as package:
        document_xml = package.read("word/document.xml")

    with (
        pytest.warns(UserWarning, match="Duplicate name"),
        ZipFile(package_path, "a", compression=ZIP_DEFLATED) as package,
    ):
        package.writestr("word/document.xml", document_xml)

    with pytest.raises(DocxPackageValidationError, match="duplicate parts"):
        validate_docx_package(package_path)


@pytest.mark.parametrize(
    ("part", "replacement"),
    [
        (
            "[Content_Types].xml",
            b"<Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'/>",
        ),
        (
            "_rels/.rels",
            (
                b"<Relationships "
                b"xmlns='http://schemas.openxmlformats.org/package/2006/relationships'/>"
            ),
        ),
        (
            "word/document.xml",
            b"<not-a-word-document/>",
        ),
    ],
)
def test_docx_package_validation_rejects_wrong_core_package_semantics(
    tmp_path: Path,
    part: str,
    replacement: bytes,
):
    package_path = tmp_path / "invalid-semantics.docx"
    overrides = {
        "[Content_Types].xml": {"content_types_xml": replacement},
        "_rels/.rels": {"relationships_xml": replacement},
        "word/document.xml": {"document_xml": replacement},
    }
    _write_minimal_package(package_path, **overrides[part])

    with pytest.raises(DocxPackageValidationError):
        validate_docx_package(package_path)


def test_repeated_builds_have_equivalent_numbering_reference_and_field_semantics(
    tmp_path: Path,
):
    first = tmp_path / "first.docx"
    second = tmp_path / "second.docx"

    dependencies = _canonical_dependencies()
    build_service(EXAMPLE_SOURCE, first, dependencies=dependencies)
    build_service(EXAMPLE_SOURCE, second, dependencies=dependencies)

    assert _semantic_snapshot(first) == _semantic_snapshot(second)


def test_typed_project_application_service_loads_manifest_context() -> None:
    project_root = PROJECT_ROOT / "tests" / "fixtures" / "v2-project"
    request = ProjectRequest(
        project=ProjectIdentity(
            project_id="goal-fixture",
            project_root=project_root.resolve(),
            manifest_path=(project_root / "thesisforge.yaml").resolve(),
        ),
        intent=ProjectRequestIntent.INSPECT,
    )

    context = ProjectApplicationService().load(request)

    assert context.project.manifest.project.id == "goal-fixture"
    assert context.paths.source == (project_root / "thesis.md").resolve()
