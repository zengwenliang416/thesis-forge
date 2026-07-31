from __future__ import annotations

import struct
from dataclasses import replace
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import pytest
from lxml import etree

from thesis_forge.application import (
    ApplicationDependencies,
    ApplicationStageError,
    BuildStage,
    BuildValidationError,
    build_service,
    inspect_service,
    validation_service,
)
from thesis_forge.application.output import replace_output, temporary_output_path
from thesis_forge.renderers.docx.package import (
    DocxPackageValidationError,
    validate_docx_package,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SOURCE = PROJECT_ROOT / "examples" / "bachelor-thesis" / "thesis.md"


def _temporary_outputs(output: Path) -> list[Path]:
    return sorted(output.parent.glob(f".{output.name}.*.tmp.docx"))


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
    source.write_text(
        """---
thesis:
  title: "共享服务"
author:
  name: "测试作者"
---

# 绪论 {#chap:intro}
""",
        encoding="utf-8",
    )
    before = set(tmp_path.iterdir())

    inspection = inspect_service(source)
    validation = validation_service(
        source,
        template_path=PROJECT_ROOT / "templates" / "base" / "bachelor.yaml",
    )

    assert inspection.document.source_path == source.resolve()
    assert validation.document.source_path == inspection.document.source_path
    assert validation.errors == ()
    assert validation.context.template is not None
    assert set(tmp_path.iterdir()) == before


def test_build_service_reports_progress_and_atomically_replaces_target(tmp_path: Path):
    output = tmp_path / "nested" / "thesis.docx"
    stages: list[BuildStage] = []

    result = build_service(EXAMPLE_SOURCE, output, on_progress=stages.append)

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

    dependencies = ApplicationDependencies(
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
    dependencies = dependencies_factory(ApplicationDependencies())

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

    dependencies = ApplicationDependencies(renderer=RecordingRenderer())

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

    build_service(EXAMPLE_SOURCE, first)
    build_service(EXAMPLE_SOURCE, second)

    assert _semantic_snapshot(first) == _semantic_snapshot(second)
