from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import NoReturn
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
OFFICE_RELATIONSHIPS_NAMESPACE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
WORDPROCESSING_NAMESPACE = (
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
)
DRAWINGML_NAMESPACE = "http://schemas.openxmlformats.org/drawingml/2006/main"
VML_NAMESPACE = "urn:schemas-microsoft-com:vml"
OFFICE_DOCUMENT_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/"
    "relationships/officeDocument"
)
HYPERLINK_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "hyperlink"
)
IMAGE_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "image"
)
HEADER_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "header"
)
FOOTER_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "footer"
)
FOOTNOTES_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "footnotes"
)
WORD_DOCUMENT_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document.main+xml"
)

W = lambda name: f"{{{WORDPROCESSING_NAMESPACE}}}{name}"
R_ID = f"{{{OFFICE_RELATIONSHIPS_NAMESPACE}}}id"
R_EMBED = f"{{{OFFICE_RELATIONSHIPS_NAMESPACE}}}embed"
R_LINK = f"{{{OFFICE_RELATIONSHIPS_NAMESPACE}}}link"

FIELD_TYPES = frozenset(
    {
        "NUMPAGES",
        "PAGE",
        "PAGEREF",
        "REF",
        "SECTIONPAGES",
        "SEQ",
        "TOC",
    }
)
STYLE_REFERENCE_TAGS = frozenset(
    {
        W("basedOn"),
        W("link"),
        W("next"),
        W("pStyle"),
        W("rStyle"),
        W("tblStyle"),
    }
)
BUILTIN_STYLE_IDS = frozenset({"FootnoteReference"})
BOOKMARK_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,39}$")


@dataclass(frozen=True, slots=True)
class _Relationship:
    relationship_id: str
    relationship_type: str
    target: str
    external: bool


class DocxPackageValidationError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "TF-DOCX-PACKAGE-001",
    ) -> None:
        if not code.startswith("TF-DOCX-"):
            raise ValueError("DOCX diagnostics must use the TF-DOCX-* family")
        self.code = code
        self.diagnostic_code = code
        self.detail = message
        super().__init__(f"{code}: {message}")


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
                _fail(
                    "TF-DOCX-OPC-001",
                    f"ZIP checksum failed for part: {corrupt_part}",
                )

            names = package.namelist()
            duplicates = tuple(
                sorted(name for name in set(names) if names.count(name) > 1)
            )
            if duplicates:
                _fail(
                    "TF-DOCX-OPC-002",
                    "package contains duplicate parts: " + ", ".join(duplicates),
                )

            available = set(names)
            missing = tuple(
                part for part in REQUIRED_PACKAGE_PARTS if part not in available
            )
            if missing:
                _fail(
                    "TF-DOCX-OPC-003",
                    "package is missing required parts: " + ", ".join(missing),
                )

            xml_parts = {
                part: package.read(part)
                for part in names
                if part.endswith((".xml", ".rels"))
            }
    except DocxPackageValidationError:
        raise
    except (BadZipFile, LargeZipFile, OSError, KeyError) as error:
        raise DocxPackageValidationError(
            f"invalid DOCX package: {error}",
            code="TF-DOCX-OPC-001",
        ) from error

    roots = _parse_xml_parts(xml_parts)
    _validate_core_parts(roots)
    relationships = _parse_relationships(roots, available)
    _validate_relationship_references(roots, relationships)
    bookmark_names = _validate_bookmarks(roots)
    _validate_fields(roots, bookmark_names)
    _validate_styles(roots)
    _validate_numbering(roots)
    _validate_footnotes(roots, relationships)
    _validate_sections(roots, relationships)
    _validate_media(roots, relationships)


def _parse_xml_parts(
    xml_parts: dict[str, bytes],
) -> dict[str, ElementTree.Element]:
    roots: dict[str, ElementTree.Element] = {}
    for part, content in xml_parts.items():
        try:
            roots[part] = ElementTree.fromstring(content)
        except ElementTree.ParseError as error:
            _fail(
                "TF-DOCX-OPC-004",
                f"package contains malformed XML in {part}: {error}",
            )
    return roots


def _validate_core_parts(roots: dict[str, ElementTree.Element]) -> None:
    content_types = roots["[Content_Types].xml"]
    if content_types.tag != f"{{{CONTENT_TYPES_NAMESPACE}}}Types":
        _fail(
            "TF-DOCX-OPC-005",
            "package has an invalid [Content_Types].xml root",
        )
    document_override = any(
        node.get("PartName") == "/word/document.xml"
        and node.get("ContentType") == WORD_DOCUMENT_CONTENT_TYPE
        for node in content_types.findall(f"{{{CONTENT_TYPES_NAMESPACE}}}Override")
    )
    if not document_override:
        _fail(
            "TF-DOCX-OPC-006",
            "package does not declare the main Word document content type",
        )

    relationships = roots["_rels/.rels"]
    if relationships.tag != (
        f"{{{PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationships"
    ):
        _fail(
            "TF-DOCX-OPC-007",
            "package has an invalid root relationships part",
        )
    office_document = any(
        node.get("Type") == OFFICE_DOCUMENT_RELATIONSHIP
        and node.get("Target", "").lstrip("/") == "word/document.xml"
        for node in relationships.findall(
            f"{{{PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
        )
    )
    if not office_document:
        _fail(
            "TF-DOCX-OPC-008",
            "package does not relate to the main Word document",
        )

    document = roots["word/document.xml"]
    if document.tag != W("document"):
        _fail(
            "TF-DOCX-OPC-009",
            "package has an invalid main Word document root",
        )


def _relationship_source(part: str) -> str:
    if part == "_rels/.rels":
        return ""
    path = PurePosixPath(part)
    if not path.name.endswith(".rels"):
        _fail(
            "TF-DOCX-REL-001",
            f"invalid relationship part name: {part}",
        )
    return (path.parent.parent / path.name[:-5]).as_posix()


def _resolve_internal_target(source: str, target: str) -> str:
    base = PurePosixPath(source).parent if source else PurePosixPath(".")
    normalized = posixpath.normpath(
        posixpath.join(base.as_posix(), target.lstrip("/"))
    )
    if normalized in {".", ".."} or normalized.startswith("../"):
        _fail(
            "TF-DOCX-REL-002",
            f"relationship target escapes package root: {target}",
        )
    return normalized


def _parse_relationships(
    roots: dict[str, ElementTree.Element],
    available: set[str],
) -> dict[str, dict[str, _Relationship]]:
    relationships_by_source: dict[str, dict[str, _Relationship]] = {}
    relationship_tag = f"{{{PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
    relationships_root_tag = f"{{{PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationships"

    for part, root in roots.items():
        if not part.endswith(".rels"):
            continue
        if root.tag != relationships_root_tag:
            _fail(
                "TF-DOCX-REL-003",
                f"invalid relationships root in {part}",
            )
        source = _relationship_source(part)
        if source and source not in available:
            _fail(
                "TF-DOCX-REL-004",
                f"relationship source part is missing: {source}",
            )

        parsed: dict[str, _Relationship] = {}
        for node in root.findall(relationship_tag):
            relationship_id = node.get("Id")
            relationship_type = node.get("Type")
            raw_target = node.get("Target")
            target_mode = node.get("TargetMode")
            if not relationship_id or not relationship_type or not raw_target:
                _fail(
                    "TF-DOCX-REL-005",
                    f"relationship in {part} has incomplete attributes",
                )
            if relationship_id in parsed:
                _fail(
                    "TF-DOCX-REL-006",
                    f"duplicate relationship ID in {part}: {relationship_id}",
                )

            external = target_mode == "External"
            if external:
                if relationship_type != HYPERLINK_RELATIONSHIP:
                    _fail(
                        "TF-DOCX-REL-007",
                        "unexpected external relationship in "
                        f"{part}: {relationship_type}",
                    )
                resolved_target = raw_target
            else:
                resolved_target = _resolve_internal_target(source, raw_target)
                if resolved_target not in available:
                    _fail(
                        "TF-DOCX-REL-008",
                        f"relationship target is missing in {part}: "
                        f"{resolved_target}",
                    )

            parsed[relationship_id] = _Relationship(
                relationship_id=relationship_id,
                relationship_type=relationship_type,
                target=resolved_target,
                external=external,
            )
        relationships_by_source[source] = parsed

    return relationships_by_source


def _validate_relationship_references(
    roots: dict[str, ElementTree.Element],
    relationships: dict[str, dict[str, _Relationship]],
) -> None:
    for part, root in roots.items():
        if part.endswith(".rels"):
            continue
        available = relationships.get(part, {})
        for element in root.iter():
            for attribute in (R_ID, R_EMBED, R_LINK):
                relationship_id = element.get(attribute)
                if relationship_id is None:
                    continue
                if relationship_id not in available:
                    _fail(
                        "TF-DOCX-REL-009",
                        f"{part} references missing relationship ID: "
                        f"{relationship_id}",
                    )


def _word_roots(
    roots: dict[str, ElementTree.Element],
) -> tuple[tuple[str, ElementTree.Element], ...]:
    return tuple(
        (part, root)
        for part, root in roots.items()
        if part.startswith("word/") and not part.endswith(".rels")
    )


def _validate_bookmarks(
    roots: dict[str, ElementTree.Element],
) -> set[str]:
    bookmark_names: set[str] = set()
    for part, root in _word_roots(roots):
        starts: dict[str, tuple[int, str]] = {}
        ends: dict[str, int] = {}
        for position, element in enumerate(root.iter()):
            if element.tag == W("bookmarkStart"):
                bookmark_id = element.get(W("id"))
                name = element.get(W("name"))
                if not bookmark_id or not name:
                    _fail(
                        "TF-DOCX-BOOKMARK-001",
                        f"{part} contains a bookmark without ID or name",
                    )
                if not BOOKMARK_NAME_PATTERN.fullmatch(name):
                    _fail(
                        "TF-DOCX-BOOKMARK-002",
                        f"invalid bookmark name in {part}: {name}",
                    )
                if bookmark_id in starts:
                    _fail(
                        "TF-DOCX-BOOKMARK-003",
                        f"duplicate bookmark start ID in {part}: "
                        f"{bookmark_id}",
                    )
                if name in bookmark_names:
                    _fail(
                        "TF-DOCX-BOOKMARK-004",
                        f"duplicate bookmark name: {name}",
                    )
                starts[bookmark_id] = (position, name)
                bookmark_names.add(name)
            elif element.tag == W("bookmarkEnd"):
                bookmark_id = element.get(W("id"))
                if not bookmark_id:
                    _fail(
                        "TF-DOCX-BOOKMARK-005",
                        f"{part} contains a bookmark end without an ID",
                    )
                if bookmark_id in ends:
                    _fail(
                        "TF-DOCX-BOOKMARK-006",
                        f"duplicate bookmark end ID in {part}: {bookmark_id}",
                    )
                ends[bookmark_id] = position

        for bookmark_id, (start_position, _) in starts.items():
            end_position = ends.get(bookmark_id)
            if end_position is None:
                _fail(
                    "TF-DOCX-BOOKMARK-007",
                    f"bookmark start has no matching end in {part}: "
                    f"{bookmark_id}",
                )
            if end_position < start_position:
                _fail(
                    "TF-DOCX-BOOKMARK-008",
                    f"bookmark end precedes start in {part}: {bookmark_id}",
                )
        for bookmark_id in ends:
            if bookmark_id not in starts:
                _fail(
                    "TF-DOCX-BOOKMARK-009",
                    f"bookmark end has no matching start in {part}: "
                    f"{bookmark_id}",
                )

    return bookmark_names


def _validate_fields(
    roots: dict[str, ElementTree.Element],
    bookmark_names: set[str],
) -> None:
    for part, root in _word_roots(roots):
        stack: list[dict[str, object]] = []
        for element in root.iter():
            if element.tag == W("instrText"):
                if not stack:
                    _fail(
                        "TF-DOCX-FIELD-001",
                        f"instruction text appears outside a field in {part}",
                    )
                stack[-1]["instructions"].append(element.text or "")
                continue

            if element.tag != W("fldChar"):
                continue
            field_type = element.get(W("fldCharType"))
            if field_type == "begin":
                stack.append({"separate": False, "instructions": []})
            elif field_type == "separate":
                if not stack or bool(stack[-1]["separate"]):
                    _fail(
                        "TF-DOCX-FIELD-002",
                        f"field separate marker is out of order in {part}",
                    )
                stack[-1]["separate"] = True
            elif field_type == "end":
                if not stack:
                    _fail(
                        "TF-DOCX-FIELD-003",
                        f"field end marker is out of order in {part}",
                    )
                field = stack.pop()
                if not bool(field["separate"]):
                    _fail(
                        "TF-DOCX-FIELD-004",
                        f"field has no separate marker in {part}",
                    )
                instruction = " ".join(
                    str(value).strip()
                    for value in field["instructions"]
                    if str(value).strip()
                )
                tokens = instruction.split()
                if not tokens:
                    _fail(
                        "TF-DOCX-FIELD-005",
                        f"field has no instruction text in {part}",
                    )
                field_name = tokens[0].upper()
                if field_name not in FIELD_TYPES:
                    _fail(
                        "TF-DOCX-FIELD-006",
                        f"unsupported field instruction in {part}: "
                        f"{field_name}",
                    )
                if (
                    field_name in {"REF", "PAGEREF"}
                    and (len(tokens) < 2 or tokens[1] not in bookmark_names)
                ):
                    target = tokens[1] if len(tokens) > 1 else "<missing>"
                    _fail(
                        "TF-DOCX-FIELD-007",
                        f"{field_name} references an unknown bookmark "
                        f"in {part}: {target}",
                    )
            else:
                _fail(
                    "TF-DOCX-FIELD-008",
                    f"invalid field character type in {part}: {field_type}",
                )

        if stack:
            _fail(
                "TF-DOCX-FIELD-009",
                f"field is not closed in {part}",
            )


def _validate_styles(roots: dict[str, ElementTree.Element]) -> None:
    style_root = roots.get("word/styles.xml")
    style_ids: set[str] = set()
    if style_root is not None:
        if style_root.tag != W("styles"):
            _fail(
                "TF-DOCX-STYLE-001",
                "word/styles.xml has an invalid root",
            )
        for style in style_root.findall(W("style")):
            style_id = style.get(W("styleId"))
            if not style_id:
                _fail(
                    "TF-DOCX-STYLE-002",
                    "word/styles.xml contains a style without styleId",
                )
            if style_id in style_ids:
                _fail(
                    "TF-DOCX-STYLE-003",
                    f"duplicate style ID: {style_id}",
                )
            style_ids.add(style_id)
        style_ids.update(BUILTIN_STYLE_IDS)

    for part, root in _word_roots(roots):
        for element in root.iter():
            if element.tag not in STYLE_REFERENCE_TAGS:
                continue
            style_id = element.get(W("val"))
            if style_id is None:
                _fail(
                    "TF-DOCX-STYLE-004",
                    f"style reference has no value in {part}",
                )
            if style_id not in style_ids:
                _fail(
                    "TF-DOCX-STYLE-005",
                    f"style ID is not defined in {part}: {style_id}",
                )


def _validate_numbering(roots: dict[str, ElementTree.Element]) -> None:
    numbering_root = roots.get("word/numbering.xml")
    num_to_abstract: dict[str, str] = {}
    abstract_levels: dict[str, set[str]] = {}
    if numbering_root is not None:
        if numbering_root.tag != W("numbering"):
            _fail(
                "TF-DOCX-NUMBERING-001",
                "word/numbering.xml has an invalid root",
            )
        for abstract in numbering_root.findall(W("abstractNum")):
            abstract_id = abstract.get(W("abstractNumId"))
            if not abstract_id:
                _fail(
                    "TF-DOCX-NUMBERING-002",
                    "abstract numbering definition has no ID",
                )
            if abstract_id in abstract_levels:
                _fail(
                    "TF-DOCX-NUMBERING-003",
                    f"duplicate abstract numbering ID: {abstract_id}",
                )
            abstract_levels[abstract_id] = {
                level.get(W("ilvl"))
                for level in abstract.findall(W("lvl"))
                if level.get(W("ilvl")) is not None
            }
        for number in numbering_root.findall(W("num")):
            num_id = number.get(W("numId"))
            abstract_element = number.find(W("abstractNumId"))
            abstract_id = (
                abstract_element.get(W("val"))
                if abstract_element is not None
                else None
            )
            if not num_id or not abstract_id:
                _fail(
                    "TF-DOCX-NUMBERING-004",
                    "numbering instance is missing numId or abstractNumId",
                )
            if num_id in num_to_abstract:
                _fail(
                    "TF-DOCX-NUMBERING-005",
                    f"duplicate numbering ID: {num_id}",
                )
            if abstract_id not in abstract_levels:
                _fail(
                    "TF-DOCX-NUMBERING-006",
                    f"numbering instance references missing abstract ID: "
                    f"{abstract_id}",
                )
            num_to_abstract[num_id] = abstract_id

    for part, root in _word_roots(roots):
        for element in root.iter(W("numId")):
            num_id = element.get(W("val"))
            if not num_id or num_id not in num_to_abstract:
                _fail(
                    "TF-DOCX-NUMBERING-007",
                    f"numbering ID is not defined in {part}: {num_id}",
                )

        for num_pr in root.iter(W("numPr")):
            num_id_element = num_pr.find(W("numId"))
            level_element = num_pr.find(W("ilvl"))
            if num_id_element is None or level_element is None:
                continue
            num_id = num_id_element.get(W("val"))
            level = level_element.get(W("val"))
            abstract_id = num_to_abstract.get(num_id or "")
            if (
                abstract_id is not None
                and level is not None
                and level not in abstract_levels[abstract_id]
            ):
                _fail(
                    "TF-DOCX-NUMBERING-008",
                    f"numbering level is not defined in {part}: "
                    f"{num_id}/{level}",
                )


def _validate_footnotes(
    roots: dict[str, ElementTree.Element],
    relationships: dict[str, dict[str, _Relationship]],
) -> None:
    references: list[tuple[str, str]] = []
    for part, root in _word_roots(roots):
        for element in root.iter(W("footnoteReference")):
            footnote_id = element.get(W("id"))
            if not footnote_id or not footnote_id.isdigit():
                _fail(
                    "TF-DOCX-FOOTNOTE-001",
                    f"invalid footnote reference in {part}: {footnote_id}",
                )
            references.append((part, footnote_id))

    footnotes_root = roots.get("word/footnotes.xml")
    if references and footnotes_root is None:
        _fail(
            "TF-DOCX-FOOTNOTE-002",
            "document contains footnote references without footnotes.xml",
        )
    if footnotes_root is None:
        return
    if footnotes_root.tag != W("footnotes"):
        _fail(
            "TF-DOCX-FOOTNOTE-003",
            "word/footnotes.xml has an invalid root",
        )

    definitions: dict[str, ElementTree.Element] = {}
    for footnote in footnotes_root.findall(W("footnote")):
        footnote_id = footnote.get(W("id"))
        if footnote_id is None or footnote_id in definitions:
            _fail(
                "TF-DOCX-FOOTNOTE-004",
                f"duplicate or missing footnote ID: {footnote_id}",
            )
        definitions[footnote_id] = footnote
        if (
            footnote_id.isdigit()
            and footnote_id not in {"0"}
            and footnote.find(f".//{W('footnoteRef')}") is None
        ):
            _fail(
                "TF-DOCX-FOOTNOTE-005",
                f"footnote definition has no footnoteRef: {footnote_id}",
            )

    positive_definitions = {
        footnote_id for footnote_id in definitions if footnote_id.isdigit()
    }
    for part, footnote_id in references:
        if footnote_id not in positive_definitions:
            _fail(
                "TF-DOCX-FOOTNOTE-006",
                f"footnote reference has no definition in {part}: "
                f"{footnote_id}",
            )

    document_relationships = relationships.get("word/document.xml", {})
    if references and not any(
        relation.relationship_type == FOOTNOTES_RELATIONSHIP
        and relation.target == "word/footnotes.xml"
        for relation in document_relationships.values()
    ):
        _fail(
            "TF-DOCX-FOOTNOTE-007",
            "document footnotes are not related through document.xml.rels",
        )


def _validate_sections(
    roots: dict[str, ElementTree.Element],
    relationships: dict[str, dict[str, _Relationship]],
) -> None:
    document = roots["word/document.xml"]
    section_properties = tuple(document.iter(W("sectPr")))
    if not section_properties:
        return

    parent_map = {
        child: parent
        for parent in document.iter()
        for child in parent
    }
    body = document.find(W("body"))
    if body is None:
        _fail(
            "TF-DOCX-SECTION-001",
            "document contains sections without a body",
        )
    if list(body)[-1] is not section_properties[-1]:
        _fail(
            "TF-DOCX-SECTION-002",
            "final section properties are not the last body child",
        )

    document_relationships = relationships.get("word/document.xml", {})
    for section in section_properties:
        parent = parent_map.get(section)
        if parent is not body and (parent is None or parent.tag != W("pPr")):
            _fail(
                "TF-DOCX-SECTION-003",
                "section properties have an invalid parent",
            )
        for reference, expected_type in (
            (W("headerReference"), HEADER_RELATIONSHIP),
            (W("footerReference"), FOOTER_RELATIONSHIP),
        ):
            for node in section.findall(reference):
                relationship_id = node.get(R_ID)
                relation = document_relationships.get(relationship_id or "")
                if relation is None or relation.relationship_type != expected_type:
                    _fail(
                        "TF-DOCX-SECTION-004",
                        "section header/footer reference is invalid: "
                        f"{relationship_id}",
                    )


def _validate_media(
    roots: dict[str, ElementTree.Element],
    relationships: dict[str, dict[str, _Relationship]],
) -> None:
    for part, root in _word_roots(roots):
        media_nodes = list(root.iter(f"{{{DRAWINGML_NAMESPACE}}}blip"))
        media_nodes.extend(root.iter(f"{{{VML_NAMESPACE}}}imagedata"))
        source_relationships = relationships.get(part, {})
        for node in media_nodes:
            relationship_id = node.get(R_EMBED) or node.get(R_LINK) or node.get(R_ID)
            if relationship_id is None:
                _fail(
                    "TF-DOCX-MEDIA-001",
                    f"media reference has no relationship ID in {part}",
                )
            relation = source_relationships.get(relationship_id)
            if relation is None or relation.external:
                _fail(
                    "TF-DOCX-MEDIA-002",
                    f"media reference is not an internal image relation in "
                    f"{part}: {relationship_id}",
                )
            if relation.relationship_type != IMAGE_RELATIONSHIP:
                _fail(
                    "TF-DOCX-MEDIA-003",
                    f"media reference uses a non-image relationship in "
                    f"{part}: {relationship_id}",
                )


def _fail(code: str, message: str) -> NoReturn:
    raise DocxPackageValidationError(message, code=code)
