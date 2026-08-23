"""Focused tests that the compiler derives semantics without document caches."""

from __future__ import annotations

from pathlib import Path

from thesis_forge.core import compiler as compiler_module
from thesis_forge.core import model as model_module
from thesis_forge.core.index import DocumentIndex
from thesis_forge.core.model import (
    Citation,
    Emphasis,
    FootnoteReference,
    Heading,
    Inline,
    Paragraph,
    Strong,
    Text,
    ThesisDocument,
)
from thesis_forge.core.parser_backend import create_parser_backend

BACKEND = create_parser_backend()

CACHE_FIELDS = (
    "document.inline_content",
    "document.cross_references",
    "document.citations",
    "document.footnote_references",
)

REMOVED_MEMBERS = (
    "inline_content",
    "cross_references",
    "citations",
    "footnote_references",
    "register_inlines",
)

SOURCE = """# 绪论 {#chap:intro}

引用 [@k1]，如[模型](#fig:model)所示，脚注见[^n1]。

- 列表项引用 [@k2]

![模型 [@k4]](./model.png){#fig:model}

[^n1]: 脚注内容 [@k3]。
"""


def test_document_index_exposes_full_preorder_inline_sequence() -> None:
    nested_citation = Citation(keys=["k"], raw="[@k]")
    nested = Strong(children=(Text(value="粗体"), Emphasis(children=(nested_citation,))))
    paragraph = Paragraph(inlines=[nested, FootnoteReference(label="n")])
    document = ThesisDocument(
        source_path=Path("thesis.md"), blocks=[Heading(level=1), paragraph]
    )
    index = DocumentIndex.from_document(document)
    sequence = list(index.inlines)
    assert sequence[0] is nested
    assert sequence[1] is nested.children[0]
    assert sequence[2] is nested.children[1]
    assert sequence[3] is nested_citation
    assert isinstance(sequence[4], FootnoteReference)
    assert sequence[4].label == "n"
    assert all(isinstance(inline, Inline) for inline in sequence)
    assert index.citations == (nested_citation,)


def test_thesis_document_has_no_manual_caches() -> None:
    document = BACKEND.parse_text(SOURCE, source_path=Path("thesis.md"))
    for member in REMOVED_MEMBERS:
        assert not hasattr(document, member), f"ThesisDocument still exposes {member}"
    index = DocumentIndex.from_document(document)
    assert [citation.keys for citation in index.citations] == [
        ["k1"],
        ["k2"],
        ["k4"],
        ["k3"],
    ]


def test_compiler_source_contains_no_document_cache_reads() -> None:
    source = Path(compiler_module.__file__).read_text(encoding="utf-8")
    for field in CACHE_FIELDS:
        assert field not in source, f"compiler still reads the cache field {field}"


def test_model_source_defines_no_manual_caches() -> None:
    source = Path(model_module.__file__).read_text(encoding="utf-8")
    assert "register_inlines" not in source
    for member in REMOVED_MEMBERS[:4]:
        assert f"{member}: list[" not in source, f"model still defines {member}"
