from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, LargeZipFile, ZipFile

REQUIRED_PACKAGE_PARTS = (
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml",
)
CORE_XML_PARTS = REQUIRED_PACKAGE_PARTS
CONTENT_TYPES_NAMESPACE = (
    "http://schemas.openxmlformats.org/package/2006/content-types"
)
PACKAGE_RELATIONSHIPS_NAMESPACE = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)
WORDPROCESSING_NAMESPACE = (
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
)
OFFICE_DOCUMENT_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/"
    "relationships/officeDocument"
)
WORD_DOCUMENT_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document.main+xml"
)


class DocxPackageValidationError(ValueError):
    pass


def list_package_parts(path: str | Path) -> tuple[str, ...]:
    with ZipFile(path) as package:
        return tuple(sorted(package.namelist()))


def read_package_part(path: str | Path, name: str) -> bytes:
    with ZipFile(path) as package:
        return package.read(name)


def validate_docx_package(path: str | Path) -> None:
    package_path = Path(path)
    try:
        with ZipFile(package_path) as package:
            corrupt_part = package.testzip()
            if corrupt_part is not None:
                raise DocxPackageValidationError(
                    f"DOCX ZIP checksum failed for part: {corrupt_part}"
                )

            names = package.namelist()
            duplicates = tuple(
                sorted(name for name in set(names) if names.count(name) > 1)
            )
            if duplicates:
                raise DocxPackageValidationError(
                    f"DOCX package contains duplicate parts: {', '.join(duplicates)}"
                )

            available = set(names)
            missing = tuple(part for part in REQUIRED_PACKAGE_PARTS if part not in available)
            if missing:
                raise DocxPackageValidationError(
                    f"DOCX package is missing required parts: {', '.join(missing)}"
                )

            xml_parts = {
                part: package.read(part)
                for part in CORE_XML_PARTS
            }
    except DocxPackageValidationError:
        raise
    except (BadZipFile, LargeZipFile, OSError, KeyError) as error:
        raise DocxPackageValidationError(f"Invalid DOCX package: {error}") from error

    roots: dict[str, ElementTree.Element] = {}
    for part, content in xml_parts.items():
        try:
            roots[part] = ElementTree.fromstring(content)
        except ElementTree.ParseError as error:
            raise DocxPackageValidationError(
                f"DOCX package contains malformed XML in {part}: {error}"
            ) from error

    content_types = roots["[Content_Types].xml"]
    if content_types.tag != f"{{{CONTENT_TYPES_NAMESPACE}}}Types":
        raise DocxPackageValidationError(
            "DOCX package has an invalid [Content_Types].xml root"
        )
    document_override = any(
        node.get("PartName") == "/word/document.xml"
        and node.get("ContentType") == WORD_DOCUMENT_CONTENT_TYPE
        for node in content_types.findall(
            f"{{{CONTENT_TYPES_NAMESPACE}}}Override"
        )
    )
    if not document_override:
        raise DocxPackageValidationError(
            "DOCX package does not declare the main Word document content type"
        )

    relationships = roots["_rels/.rels"]
    if relationships.tag != f"{{{PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationships":
        raise DocxPackageValidationError(
            "DOCX package has an invalid root relationships part"
        )
    office_document = any(
        node.get("Type") == OFFICE_DOCUMENT_RELATIONSHIP
        and node.get("Target", "").lstrip("/") == "word/document.xml"
        for node in relationships.findall(
            f"{{{PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
        )
    )
    if not office_document:
        raise DocxPackageValidationError(
            "DOCX package does not relate to the main Word document"
        )

    document = roots["word/document.xml"]
    if document.tag != f"{{{WORDPROCESSING_NAMESPACE}}}document":
        raise DocxPackageValidationError(
            "DOCX package has an invalid main Word document root"
        )
