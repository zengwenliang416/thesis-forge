from __future__ import annotations

from pathlib import Path

import pytest

from thesis_forge.core.model import CodeBlock
from thesis_forge.core.parser import ParseError
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend

BACKEND = MarkdownItParserBackend()


@pytest.mark.parametrize(
    ("source", "code", "replacement"),
    [
        (
            "---\ntitle: Legacy\n---\n# Thesis\n",
            "TF-SOURCE-LEGACY-001",
            "thesisforge.yaml",
        ),
        (
            (
                "::: figure {#fig:model}\n"
                'src: "assets/model.png"\n'
                'caption: "Model"\n'
                ":::\n"
            ),
            "TF-SOURCE-LEGACY-002",
            "![caption](assets/image.png){#fig:example}",
        ),
        (
            "The architecture is shown in @fig:model.\n",
            "TF-SOURCE-LEGACY-003",
            "[label](#fig:example)",
        ),
    ],
    ids=["front-matter", "container", "cross-reference"],
)
def test_legacy_source_is_rejected_before_generic_parsing(
    source: str,
    code: str,
    replacement: str,
) -> None:
    with pytest.raises(ParseError) as captured:
        BACKEND.parse_text(source, source_path=Path("legacy.md"))

    message = str(captured.value)
    assert code in message
    assert replacement in message


def test_legacy_markers_inside_fenced_code_remain_literal() -> None:
    source = (
        "```text\n"
        "::: figure {#fig:inside}\n"
        "@fig:inside\n"
        "---\n"
        "```\n"
    )

    document = BACKEND.parse_text(source, source_path=Path("code.md"))

    assert len(document.blocks) == 1
    assert isinstance(document.blocks[0], CodeBlock)
    assert "@fig:inside" in document.blocks[0].code


def test_legacy_markers_inside_inline_code_remain_literal() -> None:
    source = "`@fig:inline` and `::: figure` remain code.\n"

    document = BACKEND.parse_text(source, source_path=Path("inline-code.md"))

    assert document.blocks
