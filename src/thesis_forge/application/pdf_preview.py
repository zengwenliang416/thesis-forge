from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from .office_refresh import (
    discover_libreoffice_executable,
    start_office_process,
    terminate_office_process_tree,
)
from .output import ReplaceFile, replace_output

PdfExportRunner = Callable[[Path, Path, Path, float], Path]


@dataclass(frozen=True, slots=True)
class PdfPreviewArtifact:
    path: Path
    name: str
    engine: Literal["libreoffice"]
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
            str(document_path.resolve()),
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
