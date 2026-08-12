from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from thesis_forge.application.pdf_preview import (
    LibreOfficePdfPreviewExporter,
    _run_libreoffice_pdf_export,
    is_valid_pdf,
)


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
    document.write_bytes(b"docx")
    commands: list[tuple[str, ...]] = []
    profiles: list[Path] = []
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
        (output_directory / "thesis.pdf").write_bytes(b"%PDF-1.7\npreview")
        return process, job

    def fake_terminate(active_process, *, windows_job=None):
        terminated.append((active_process, windows_job))

    monkeypatch.setattr(
        "thesis_forge.application.pdf_preview.start_office_process",
        fake_start,
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
            str(document.resolve()),
        )
    ]
    assert terminated == [(process, job)]
    assert len(profiles) == 1
    assert not profiles[0].exists()


def test_libreoffice_runner_cleans_process_tree_after_timeout(
    tmp_path: Path,
    monkeypatch,
):
    document = tmp_path / "thesis.docx"
    output_directory = tmp_path / "converted"
    output_directory.mkdir()
    document.write_bytes(b"docx")
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
