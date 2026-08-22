"""Focused tests that the compiler derives semantics without document caches."""

from __future__ import annotations

from pathlib import Path

from thesis_forge.core import compiler as compiler_module
from thesis_forge.core.compiler import compile_document
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
from thesis_forge.core.parser import parse_markdown_text

CACHE_FIELDS = (
    "document.inline_content",
    "document.cross_references",
    "document.citations",
    "document.footnote_references",
)

SOURCE = """# 绪论 {#chap:intro}

引用 [@k1]，如 @fig:model 所示，脚注见[^n1]。

- 列表项引用 [@k2]

::: figure {#fig:model}
src: "./model.png"
caption: "模型 [@k4]"
:::

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


def test_compile_is_identical_after_clearing_document_caches() -> None:
    document = parse_markdown_text(SOURCE, source_path=Path("thesis.md"))
    plan_before = compile_document(document)
    document.inline_content.clear()
    document.cross_references.clear()
    document.citations.clear()
    document.footnote_references.clear()
    plan_after = compile_document(document)
    assert plan_after == plan_before


def test_compiler_source_contains_no_document_cache_reads() -> None:
    source = Path(compiler_module.__file__).read_text(encoding="utf-8")
    for field in CACHE_FIELDS:
        assert field not in source, f"compiler still reads the cache field {field}"
