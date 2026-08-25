from __future__ import annotations

import errno
import subprocess
import zipfile
from pathlib import Path

import pytest

from thesis_forge.application.pdf_preview import (
    FallbackPdfPreviewExporter,
    LibreOfficePdfPreviewExporter,
    MicrosoftWordPdfPreviewExporter,
    _adapt_docx_font_aliases,
    _installed_font_families,
    _run_libreoffice_pdf_export,
    _run_microsoft_word_pdf_export,
    discover_microsoft_word_automation,
    is_valid_pdf,
    microsoft_word_preview_root,
    preferred_pdf_preview_exporter,
    preview_font_aliases,
)

DOCUMENT_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi='宋体' w:eastAsia="黑体" w:cs="Times New Roman"/>
        </w:rPr>
        <w:t>正文提到宋体和黑体，但这里不能被替换。</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>
""".encode()

FONT_TABLE_XML = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:font w:name="宋体"/>
  <w:font w:name="黑体"/>
</w:fonts>
""".encode()


def _write_docx_package(path: Path) -> None:
    document_entry = zipfile.ZipInfo("word/document.xml", (2024, 4, 7, 0, 0, 0))
    document_entry.compress_type = zipfile.ZIP_DEFLATED
    font_entry = zipfile.ZipInfo("word/fontTable.xml", (2024, 4, 7, 0, 0, 0))
    font_entry.compress_type = zipfile.ZIP_DEFLATED
    media_entry = zipfile.ZipInfo("word/media/image.bin", (2024, 4, 7, 0, 0, 0))
    media_entry.compress_type = zipfile.ZIP_STORED
    with zipfile.ZipFile(path, "w") as package:
        package.comment = b"thesisforge-test"
        package.writestr(document_entry, DOCUMENT_XML)
        package.writestr(font_entry, FONT_TABLE_XML)
        package.writestr(media_entry, b"\x00\x01font names: \xe5\xae\x8b\xe4\xbd\x93")


@pytest.mark.parametrize(
    ("platform", "families", "expected"),
    [
        (
            "darwin",
            {"Songti SC", "Heiti SC"},
            {
                "宋体": "Source Han Serif SC",
                "黑体": "PingFang SC",
            },
        ),
        ("darwin", {"Songti SC"}, {"宋体": "Source Han Serif SC"}),
        ("darwin", set(), {}),
        ("win32", {"Songti SC", "Heiti SC"}, {}),
        ("linux", {"Songti SC", "Heiti SC"}, {}),
    ],
)
def test_preview_font_aliases_require_supported_macos_families(
    platform: str,
    families: set[str],
    expected: dict[str, str],
):
    assert preview_font_aliases(platform, families) == expected


@pytest.mark.parametrize(
    ("failure", "returncode"),
    [
        (FileNotFoundError("fc-list"), None),
        (subprocess.TimeoutExpired("fc-list", 5), None),
        (None, 1),
    ],
)
def test_installed_font_probe_safely_returns_empty_on_failure(
    monkeypatch,
    failure: Exception | None,
    returncode: int | None,
):
    def fake_run(*_args, **_kwargs):
        if failure is not None:
            raise failure
        return subprocess.CompletedProcess([], returncode, stdout="", stderr="")

    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.subprocess.run",
        fake_run,
    )

    assert _installed_font_families() == frozenset()


def test_installed_font_probe_splits_localized_family_aliases(monkeypatch):
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.subprocess.run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            [],
            0,
            stdout="Songti SC,宋体-简\nHeiti SC,黑体-简\n",
            stderr="",
        ),
    )

    assert _installed_font_families() == frozenset(
        {"Songti SC", "宋体-简", "Heiti SC", "黑体-简"}
    )


def test_docx_font_adapter_rewrites_only_exact_ooxml_font_attributes(
    tmp_path: Path,
):
    source = tmp_path / "source.docx"
    adapted = tmp_path / "adapted.docx"
    _write_docx_package(source)
    source_bytes = source.read_bytes()

    _adapt_docx_font_aliases(
        source,
        adapted,
        preview_font_aliases("darwin"),
    )

    assert source.read_bytes() == source_bytes
    with (
        zipfile.ZipFile(source) as source_package,
        zipfile.ZipFile(adapted) as adapted_package,
    ):
        assert adapted_package.comment == source_package.comment
        assert [
            (entry.filename, entry.date_time, entry.compress_type)
            for entry in adapted_package.infolist()
        ] == [
            (entry.filename, entry.date_time, entry.compress_type)
            for entry in source_package.infolist()
        ]
        adapted_document = adapted_package.read("word/document.xml")
        assert b'w:ascii="Source Han Serif SC"' in adapted_document
        assert b"w:hAnsi='Source Han Serif SC'" in adapted_document
        assert b'w:eastAsia="PingFang SC"' in adapted_document
        assert b'w:cs="Times New Roman"' in adapted_document
        assert "正文提到宋体和黑体，但这里不能被替换。".encode() in adapted_document
        assert (
            adapted_package.read("word/fontTable.xml")
            == FONT_TABLE_XML.replace(
                'w:name="宋体"'.encode(),
                b'w:name="Source Han Serif SC"',
            ).replace(
                'w:name="黑体"'.encode(),
                b'w:name="PingFang SC"',
            )
        )
        assert adapted_package.read("word/media/image.bin") == source_package.read(
            "word/media/image.bin"
        )


def test_docx_font_adapter_ignores_same_local_names_in_other_namespaces(
    tmp_path: Path,
):
    source = tmp_path / "source.docx"
    adapted = tmp_path / "adapted.docx"
    other_namespace_xml = b"""\
<x:document xmlns:x="urn:not-word">
  <x:rFonts x:ascii="\xe5\xae\x8b\xe4\xbd\x93"/>
  <x:font x:name="\xe9\xbb\x91\xe4\xbd\x93"/>
</x:document>
"""
    with zipfile.ZipFile(source, "w") as package:
        package.writestr("word/document.xml", other_namespace_xml)

    _adapt_docx_font_aliases(
        source,
        adapted,
        preview_font_aliases("darwin", {"Songti SC", "Heiti SC"}),
    )

    with zipfile.ZipFile(adapted) as package:
        assert package.read("word/document.xml") == other_namespace_xml


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b"%PDF-1.7\npreview", True),
        (b"", False),
        (b"not-a-pdf", False),
    ],
)
def test_pdf_validation_requires_non_empty_pdf_signature(
    tmp_path: Path,
    content: bytes,
    expected: bool,
):
    pdf_path = tmp_path / "preview.pdf"
    pdf_path.write_bytes(content)

    assert is_valid_pdf(pdf_path) is expected


def test_pdf_validation_rejects_missing_output(tmp_path: Path):
    assert not is_valid_pdf(tmp_path / "missing.pdf")


def test_microsoft_word_discovery_requires_word_and_platform_automation(
    tmp_path: Path,
    monkeypatch,
):
    word_app = tmp_path / "Microsoft Word.app"
    word_app.mkdir()
    osascript = tmp_path / "osascript"
    osascript.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview._MACOS_WORD_APP_PATHS",
        (word_app,),
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.Path",
        lambda value: osascript if value == "/usr/bin/osascript" else Path(value),
    )

    assert discover_microsoft_word_automation("darwin") == osascript

    word_app.rmdir()
    assert discover_microsoft_word_automation("darwin") is None
    assert discover_microsoft_word_automation("linux") is None


def test_microsoft_word_preview_root_uses_word_container_on_macos(monkeypatch):
    monkeypatch.delenv("THESISFORGE_WORD_PREVIEW_ROOT", raising=False)

    root = microsoft_word_preview_root("darwin")

    assert root == (
        Path.home()
        / "Library"
        / "Containers"
        / "com.microsoft.Word"
        / "Data"
        / "Documents"
        / "ThesisForgePreview"
    )


def test_microsoft_word_exporter_publishes_from_isolated_word_workspace(
    tmp_path: Path,
):
    docx_path = tmp_path / "thesis.docx"
    pdf_path = tmp_path / "thesis.preview.pdf"
    working_root = tmp_path / "word-workspace"
    automation = tmp_path / "osascript"
    docx_path.write_bytes(b"docx-source")
    calls: list[tuple[Path, Path, Path, float]] = []

    def runner(executable, document, output_directory, timeout):
        calls.append((executable, document, output_directory, timeout))
        assert document.parent == output_directory
        assert document.name == f"{output_directory.name}.docx"
        assert document.read_bytes() == b"docx-source"
        converted = output_directory / f"{document.stem}.pdf"
        converted.write_bytes(b"%PDF-1.7\nword")
        return converted

    artifact = MicrosoftWordPdfPreviewExporter(
        automation_executable=automation,
        timeout_seconds=12.5,
        runner=runner,
        working_root=working_root,
    ).export(docx_path, pdf_path)

    assert artifact is not None
    assert artifact.engine == "microsoft-word"
    assert artifact.label == "Microsoft Word PDF"
    assert artifact.file_name == "thesis.preview.pdf"
    assert pdf_path.read_bytes() == b"%PDF-1.7\nword"
    assert calls[0][0] == automation
    assert calls[0][3] == 12.5
    assert calls[0][2].parent == working_root
    assert not calls[0][2].exists()
    assert docx_path.read_bytes() == b"docx-source"


def test_microsoft_word_exporter_publishes_across_filesystems(
    tmp_path: Path,
):
    docx_path = tmp_path / "project" / "thesis.docx"
    pdf_path = tmp_path / "project" / "thesis.preview.pdf"
    working_root = tmp_path / "word-container"
    automation = tmp_path / "osascript"
    docx_path.parent.mkdir()
    docx_path.write_bytes(b"docx-source")
    replacements: list[tuple[Path, Path]] = []

    def runner(_executable, document, output_directory, _timeout):
        converted = output_directory / f"{document.stem}.pdf"
        converted.write_bytes(b"%PDF-1.7\nword")
        return converted

    def cross_device_replace(source: Path, target: Path) -> None:
        replacements.append((source, target))
        if source.parent != target.parent:
            raise OSError(errno.EXDEV, "Cross-device link")
        source.replace(target)

    artifact = MicrosoftWordPdfPreviewExporter(
        automation_executable=automation,
        runner=runner,
        replace_file=cross_device_replace,
        working_root=working_root,
    ).export(docx_path, pdf_path)

    assert artifact is not None
    assert replacements[0][0].parent.parent == working_root
    assert replacements[0][1] == pdf_path
    assert replacements[1][0].parent == pdf_path.parent
    assert replacements[1][1] == pdf_path
    assert pdf_path.read_bytes() == b"%PDF-1.7\nword"


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.TimeoutExpired("osascript", 1),
        RuntimeError("word failed"),
        PermissionError("automation denied"),
    ],
)
def test_microsoft_word_exporter_preserves_previous_pdf_on_failure(
    tmp_path: Path,
    failure: Exception,
):
    pdf_path = tmp_path / "thesis.preview.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nprevious")

    def failing_runner(_automation, _document, _output_directory, _timeout):
        raise failure

    artifact = MicrosoftWordPdfPreviewExporter(
        automation_executable=tmp_path / "osascript",
        runner=failing_runner,
        working_root=tmp_path / "word-workspace",
    ).export(tmp_path / "thesis.docx", pdf_path)

    assert artifact is None
    assert pdf_path.read_bytes() == b"%PDF-1.4\nprevious"


def test_microsoft_word_runner_uses_noninteractive_macos_script(
    tmp_path: Path,
    monkeypatch,
):
    document = tmp_path / "preview.docx"
    output_directory = tmp_path / "output"
    output_directory.mkdir()
    calls: list[tuple[tuple[str, ...], dict]] = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        Path(command[3]).write_bytes(b"%PDF-1.7\nword")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.sys.platform",
        "darwin",
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.subprocess.run",
        fake_run,
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview._macos_word_process_ids",
        lambda: frozenset(),
    )

    converted = _run_microsoft_word_pdf_export(
        tmp_path / "osascript",
        document,
        output_directory,
        15.0,
    )

    command, kwargs = calls[0]
    assert converted == output_directory / "preview.pdf"
    assert command[0] == str(tmp_path / "osascript")
    assert command[2:] == (
        str(document),
        str(converted),
        document.name,
        "true",
    )
    script = Path(command[1]).read_text(encoding="utf-8")
    assert 'tell application "Microsoft Word"' in script
    assert "set wordDocument to document inputName" in script
    assert "every document" not in script
    assert "active document" not in script
    assert "read only true" in script
    assert "add to recent files false" in script
    assert "close wordDocument saving no" in script
    assert "quit saving no" in script
    assert kwargs == {
        "check": True,
        "capture_output": True,
        "text": True,
        "timeout": 15.0,
    }


def test_fallback_exporter_uses_first_available_engine(tmp_path: Path):
    calls: list[str] = []
    pdf_path = tmp_path / "thesis.preview.pdf"

    class MissingExporter:
        def export(self, _docx_path, _pdf_path):
            calls.append("word")

    class AvailableExporter:
        def export(self, _docx_path, target):
            calls.append("libreoffice")
            Path(target).write_bytes(b"%PDF-1.7\nfallback")
            return type(
                "Artifact",
                (),
                {
                    "path": Path(target),
                    "name": Path(target).name,
                    "engine": "libreoffice",
                    "label": "LibreOffice PDF",
                },
            )()

    artifact = FallbackPdfPreviewExporter(
        (MissingExporter(), AvailableExporter()),
    ).export(tmp_path / "thesis.docx", pdf_path)

    assert artifact is not None
    assert artifact.engine == "libreoffice"
    assert calls == ["word", "libreoffice"]


def test_preferred_exporter_skips_all_engines_after_cancellation(
    tmp_path: Path,
    monkeypatch,
):
    cancel_file = tmp_path / "cancel"
    cancel_file.write_text("cancel", encoding="utf-8")
    monkeypatch.setenv("THESISFORGE_CANCEL_FILE", str(cancel_file))
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.discover_microsoft_word_automation",
        lambda: (_ for _ in ()).throw(AssertionError("Word discovery must not run")),
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.discover_libreoffice_executable",
        lambda: (_ for _ in ()).throw(
            AssertionError("LibreOffice discovery must not run")
        ),
    )

    artifact = preferred_pdf_preview_exporter().export(
        tmp_path / "thesis.docx",
        tmp_path / "thesis.preview.pdf",
    )

    assert artifact is None


def test_libreoffice_exporter_publishes_valid_pdf_atomically(tmp_path: Path):
    docx_path = tmp_path / "thesis.docx"
    pdf_path = tmp_path / "thesis.preview.pdf"
    executable = tmp_path / "soffice"
    docx_path.write_bytes(b"docx")
    calls: list[tuple[Path, Path, Path, float]] = []
    replacements: list[tuple[Path, Path]] = []

    def runner(office, document, output_directory, timeout):
        calls.append((office, document, output_directory, timeout))
        converted = output_directory / "thesis.pdf"
        converted.write_bytes(b"%PDF-1.7\npreview")
        return converted

    def replace_file(source: Path, target: Path) -> None:
        replacements.append((source, target))
        source.replace(target)

    artifact = LibreOfficePdfPreviewExporter(
        executable=executable,
        timeout_seconds=12.5,
        runner=runner,
        replace_file=replace_file,
    ).export(docx_path, pdf_path)

    assert artifact is not None
    assert artifact.file_name == "thesis.preview.pdf"
    assert artifact.engine == "libreoffice"
    assert artifact.label == "LibreOffice PDF"
    assert calls[0][0:2] == (executable, docx_path)
    assert calls[0][3] == 12.5
    assert calls[0][2].parent == pdf_path.parent
    assert replacements == [(calls[0][2] / "thesis.pdf", pdf_path)]
    assert pdf_path.read_bytes() == b"%PDF-1.7\npreview"
    assert not calls[0][2].exists()


def test_libreoffice_exporter_returns_none_when_runtime_is_missing(
    tmp_path: Path,
    monkeypatch,
):
    calls: list[Path] = []

    def unexpected_runner(_office, document, _output_directory, _timeout):
        calls.append(document)
        raise AssertionError("runner must not execute")

    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.discover_libreoffice_executable",
        lambda: None,
    )

    artifact = LibreOfficePdfPreviewExporter(
        runner=unexpected_runner,
    ).export(tmp_path / "thesis.docx", tmp_path / "thesis.preview.pdf")

    assert artifact is None
    assert calls == []


@pytest.mark.parametrize(
    "failure",
    [
        subprocess.TimeoutExpired("soffice", 1),
        RuntimeError("conversion failed"),
        PermissionError("conversion denied"),
    ],
)
def test_libreoffice_exporter_treats_conversion_failure_as_unavailable(
    tmp_path: Path,
    failure: Exception,
):
    pdf_path = tmp_path / "thesis.preview.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nprevious")

    def failing_runner(_office, _document, _output_directory, _timeout):
        raise failure

    artifact = LibreOfficePdfPreviewExporter(
        executable=tmp_path / "soffice",
        runner=failing_runner,
    ).export(tmp_path / "thesis.docx", pdf_path)

    assert artifact is None
    assert pdf_path.read_bytes() == b"%PDF-1.4\nprevious"


@pytest.mark.parametrize("content", [None, b"", b"not-a-pdf"])
def test_libreoffice_exporter_rejects_missing_empty_or_invalid_pdf(
    tmp_path: Path,
    content: bytes | None,
):
    pdf_path = tmp_path / "thesis.preview.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nprevious")

    def invalid_runner(_office, _document, output_directory, _timeout):
        converted = output_directory / "thesis.pdf"
        if content is not None:
            converted.write_bytes(content)
        return converted

    artifact = LibreOfficePdfPreviewExporter(
        executable=tmp_path / "soffice",
        runner=invalid_runner,
    ).export(tmp_path / "thesis.docx", pdf_path)

    assert artifact is None
    assert pdf_path.read_bytes() == b"%PDF-1.4\nprevious"


def test_libreoffice_exporter_preserves_previous_pdf_when_replace_fails(
    tmp_path: Path,
):
    pdf_path = tmp_path / "thesis.preview.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nprevious")

    def runner(_office, _document, output_directory, _timeout):
        converted = output_directory / "thesis.pdf"
        converted.write_bytes(b"%PDF-1.7\nnew")
        return converted

    artifact = LibreOfficePdfPreviewExporter(
        executable=tmp_path / "soffice",
        runner=runner,
        replace_file=lambda _source, _target: (_ for _ in ()).throw(
            PermissionError("replace denied")
        ),
    ).export(tmp_path / "thesis.docx", pdf_path)

    assert artifact is None
    assert pdf_path.read_bytes() == b"%PDF-1.4\nprevious"


def test_libreoffice_runner_uses_isolated_profile_and_process_cleanup(
    tmp_path: Path,
    monkeypatch,
):
    document = tmp_path / "thesis.docx"
    output_directory = tmp_path / "converted"
    output_directory.mkdir()
    _write_docx_package(document)
    source_bytes = document.read_bytes()
    commands: list[tuple[str, ...]] = []
    profiles: list[Path] = []
    converted_documents: list[Path] = []
    terminated: list[tuple[object, object]] = []

    class FakeProcess:
        pid = 42

        def wait(self, timeout):
            assert timeout == 15.0
            return 0

    process = FakeProcess()
    job = object()

    def fake_start(command):
        commands.append(command)
        profile_argument = next(
            part for part in command if part.startswith("-env:UserInstallation=")
        )
        profiles.append(Path(profile_argument.removeprefix("-env:UserInstallation=file://")))
        converted_document = Path(command[-1])
        converted_documents.append(converted_document)
        assert converted_document.parent == profiles[-1]
        assert converted_document.name == document.name
        with zipfile.ZipFile(converted_document) as package:
            assert b"Source Han Serif SC" in package.read("word/document.xml")
            assert b"PingFang SC" in package.read("word/document.xml")
        (output_directory / "thesis.pdf").write_bytes(b"%PDF-1.7\npreview")
        return process, job

    def fake_terminate(active_process, *, windows_job=None):
        terminated.append((active_process, windows_job))

    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.start_office_process",
        fake_start,
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview._installed_font_families",
        lambda: frozenset({"Songti SC", "Heiti SC"}),
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.terminate_office_process_tree",
        fake_terminate,
    )

    converted = _run_libreoffice_pdf_export(
        tmp_path / "soffice",
        document,
        output_directory,
        15.0,
    )

    assert converted == output_directory / "thesis.pdf"
    assert commands == [
        (
            str(tmp_path / "soffice"),
            "--headless",
            "--nologo",
            "--nodefault",
            "--nofirststartwizard",
            "--norestore",
            commands[0][6],
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_directory.resolve()),
            str(converted_documents[0].resolve()),
        )
    ]
    assert terminated == [(process, job)]
    assert len(profiles) == 1
    assert not profiles[0].exists()
    assert not converted_documents[0].exists()
    assert document.read_bytes() == source_bytes


def test_libreoffice_runner_uses_source_docx_when_font_probe_has_no_candidate(
    tmp_path: Path,
    monkeypatch,
):
    document = tmp_path / "thesis.docx"
    output_directory = tmp_path / "converted"
    output_directory.mkdir()
    _write_docx_package(document)
    commands: list[tuple[str, ...]] = []

    class FakeProcess:
        pid = 42

        def wait(self, timeout):
            assert timeout == 15.0
            return 0

    def fake_start(command):
        commands.append(command)
        (output_directory / "thesis.pdf").write_bytes(b"%PDF-1.7\npreview")
        return FakeProcess(), None

    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview._installed_font_families",
        lambda: frozenset(),
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.start_office_process",
        fake_start,
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.terminate_office_process_tree",
        lambda _process, *, windows_job=None: None,
    )

    converted = _run_libreoffice_pdf_export(
        tmp_path / "soffice",
        document,
        output_directory,
        15.0,
    )

    assert converted == output_directory / "thesis.pdf"
    assert Path(commands[0][-1]) == document.resolve()


@pytest.mark.parametrize("platform", ["linux", "win32"])
def test_libreoffice_runner_uses_source_docx_without_macos_aliases(
    tmp_path: Path,
    monkeypatch,
    platform: str,
):
    document = tmp_path / "thesis.docx"
    output_directory = tmp_path / "converted"
    output_directory.mkdir()
    _write_docx_package(document)
    commands: list[tuple[str, ...]] = []

    class FakeProcess:
        pid = 42

        def wait(self, timeout):
            assert timeout == 15.0
            return 0

    def fake_start(command):
        commands.append(command)
        (output_directory / "thesis.pdf").write_bytes(b"%PDF-1.7\npreview")
        return FakeProcess(), None

    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.sys.platform",
        platform,
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.start_office_process",
        fake_start,
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.terminate_office_process_tree",
        lambda _process, *, windows_job=None: None,
    )

    converted = _run_libreoffice_pdf_export(
        tmp_path / "soffice",
        document,
        output_directory,
        15.0,
    )

    assert converted == output_directory / "thesis.pdf"
    assert Path(commands[0][-1]) == document.resolve()


def test_libreoffice_runner_cleans_process_tree_after_timeout(
    tmp_path: Path,
    monkeypatch,
):
    document = tmp_path / "thesis.docx"
    output_directory = tmp_path / "converted"
    output_directory.mkdir()
    _write_docx_package(document)
    terminated: list[tuple[object, object]] = []

    class TimingOutProcess:
        pid = 42

        def wait(self, timeout):
            raise subprocess.TimeoutExpired("soffice", timeout)

    process = TimingOutProcess()
    job = object()

    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.start_office_process",
        lambda _command: (process, job),
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.terminate_office_process_tree",
        lambda active_process, *, windows_job=None: terminated.append(
            (active_process, windows_job)
        ),
    )

    with pytest.raises(subprocess.TimeoutExpired):
        _run_libreoffice_pdf_export(
            tmp_path / "soffice",
            document,
            output_directory,
            1.0,
        )

    assert terminated == [(process, job)]


def test_libreoffice_runner_falls_back_to_default_temporary_root(
    tmp_path: Path,
    monkeypatch,
):
    document = tmp_path / "thesis.docx"
    output_directory = tmp_path / "converted"
    output_directory.mkdir()
    _write_docx_package(document)
    missing_root = tmp_path / "missing"
    profiles: list[Path] = []

    class FakeProcess:
        pid = 42

        def wait(self, timeout):
            assert timeout == 15.0
            return 0

    def fake_start(command):
        profile_argument = next(
            part for part in command if part.startswith("-env:UserInstallation=")
        )
        profiles.append(
            Path(profile_argument.removeprefix("-env:UserInstallation=file://"))
        )
        (output_directory / "thesis.pdf").write_bytes(b"%PDF-1.7\npreview")
        return FakeProcess(), None

    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.sys.platform", "darwin"
    )
    monkeypatch.setattr(
        "thesis_forge.application.office_refresh._MACOS_TEMPORARY_ROOT",
        str(missing_root),
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview._installed_font_families",
        lambda: frozenset(),
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.start_office_process",
        fake_start,
    )
    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.terminate_office_process_tree",
        lambda _process, *, windows_job=None: None,
    )

    converted = _run_libreoffice_pdf_export(
        tmp_path / "soffice",
        document,
        output_directory,
        15.0,
    )

    assert converted == output_directory / "thesis.pdf"
    assert len(profiles) == 1
    assert missing_root not in profiles[0].parents
    assert not profiles[0].exists()
