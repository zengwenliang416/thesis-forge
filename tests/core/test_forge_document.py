from __future__ import annotations

from pathlib import Path

from thesis_forge import core
from thesis_forge.core import model
from thesis_forge.core.index import DocumentIndex
from thesis_forge.core.parser_backend import create_parser_backend

SOURCE = """# 概述 {#chap:overview}

正文引用 [@source]，并参见 [概述](#chap:overview)。
"""


def test_public_core_exports_only_forge_document() -> None:
    assert hasattr(core, "ForgeDocument")
    assert hasattr(model, "ForgeDocument")
    assert not hasattr(core, "ThesisDocument")
    assert not hasattr(model, "ThesisDocument")


def test_repeated_parsing_preserves_semantics_and_source_locations() -> None:
    parser = create_parser_backend()
    source_path = Path("document.md")

    first = parser.parse_text(SOURCE, source_path=source_path)
    second = parser.parse_text(SOURCE, source_path=source_path)

    assert isinstance(first, model.ForgeDocument)
    assert first == second
    assert first.source_path == source_path.resolve()
    assert first.index_by_id() == second.index_by_id()
    assert DocumentIndex.from_document(first) == DocumentIndex.from_document(second)
    assert all(block.location.line is not None for block in first.blocks)


def test_identical_markdown_is_profile_independent() -> None:
    parser = create_parser_backend()

    general = parser.parse_text(SOURCE, source_path="general/document.md")
    academic = parser.parse_text(SOURCE, source_path="academic/document.md")

    assert general.metadata == academic.metadata
    assert general.blocks == academic.blocks
    assert general.bibliography == academic.bibliography
