from pathlib import Path

import pytest

from thesis_forge.core.ids import is_valid_stable_id, split_stable_id
from thesis_forge.core.model import (
    Algorithm,
    BibliographyBlock,
    Citation,
    CrossReference,
    Equation,
    Figure,
    FootnoteDefinition,
    FootnoteReference,
    Heading,
    ListBlock,
    Listing,
    Paragraph,
    Table,
    Text,
    inline_plain_text,
)
from thesis_forge.core.parser import ParseError, parse_markdown, parse_markdown_text


def test_parse_front_matter_and_blocks(tmp_path: Path):
    image = tmp_path / "model.png"
    image.write_bytes(b"exists")

    source = tmp_path / "thesis.md"
    source.write_text(
        """---
thesis:
  title: 测试论文
---

# 绪论 {#chap:intro}

## 研究背景 {#sec:bg}

如 @fig:model 所示。

::: figure {#fig:model}
src: "./model.png"
caption: "模型"
width: "80%"
:::
""",
        encoding="utf-8",
    )

    doc = parse_markdown(source)
    assert doc.metadata["thesis"]["title"] == "测试论文"
    assert any(isinstance(x, Heading) and x.id == "chap:intro" for x in doc.blocks)
    assert any(isinstance(x, Figure) and x.id == "fig:model" for x in doc.blocks)
    assert [x.target for x in doc.cross_references] == ["fig:model"]


def test_parse_markdown_text_preserves_the_logical_source_path(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text("# 磁盘旧标题\n", encoding="utf-8")

    doc = parse_markdown_text(
        "# 编辑器新标题\n\n::: figure {#fig:model}\nsrc: \"./model.png\"\n:::",
        source_path=source,
    )

    assert doc.source_path == source.resolve()
    assert any(
        isinstance(block, Heading) and inline_plain_text(block.inlines) == "编辑器新标题"
        for block in doc.blocks
    )


def test_parse_all_v1_semantic_objects_and_inline_order(tmp_path: Path):
    image = tmp_path / "model.png"
    image.write_bytes(b"exists")
    source = tmp_path / "thesis.md"
    source.write_text(
        """---
render:
  bibliography: "./references.bib"
  citation_style: "GB-T-7714-2025"
---

# 绪论 {#chap:intro}

见 @fig:model，并参考 [@smith2025, p. 12]。说明[^note]。

- 无序一
  - 无序二

3. 有序三
4. 有序四

::: figure {#fig:model}
src: "./model.png"
caption: "模型"
width: "80%"
:::

::: table {#tbl:result}
caption: "结果"

| 项目 | 数值 |
| --- | ---: |
| A | 1 |
:::

::: equation {#eq:loss}
$$
L = x + y
$$
:::

::: algorithm {#alg:train}
caption: "训练"

1. 初始化；
2. 训练。
:::

::: listing {#lst:predict}
caption: "预测"

```python
def predict(x):
    return x
```
:::

[^note]: 脚注正文引用 [@footnote-source]。
""",
        encoding="utf-8",
    )

    doc = parse_markdown(source)

    assert doc.bibliography is not None
    assert doc.bibliography.path == "./references.bib"
    assert doc.bibliography.citation_style == "GB-T-7714-2025"
    assert [type(block) for block in doc.blocks] == [
        Heading,
        Paragraph,
        ListBlock,
        ListBlock,
        Figure,
        Table,
        Equation,
        Algorithm,
        Listing,
        FootnoteDefinition,
    ]

    paragraph = doc.blocks[1]
    assert isinstance(paragraph, Paragraph)
    assert [type(item) for item in paragraph.inlines] == [
        Text,
        CrossReference,
        Text,
        Citation,
        Text,
        FootnoteReference,
        Text,
    ]
    citation = next(item for item in paragraph.inlines if isinstance(item, Citation))
    assert citation.keys == ["smith2025"]
    assert citation.locator == "p. 12"
    assert citation.location.line == 9
    assert citation.location.column is not None

    unordered = doc.blocks[2]
    assert isinstance(unordered, ListBlock)
    assert unordered.ordered is False
    assert [(item.level, inline_plain_text(item.inlines)) for item in unordered.items] == [
        (0, "无序一"),
        (1, "无序二"),
    ]

    ordered = doc.blocks[3]
    assert isinstance(ordered, ListBlock)
    assert ordered.ordered is True
    assert ordered.start == 3

    listing = next(block for block in doc.blocks if isinstance(block, Listing))
    assert listing.language == "python"
    assert listing.code == "def predict(x):\n    return x"

    footnote = doc.blocks[-1]
    assert isinstance(footnote, FootnoteDefinition)
    assert footnote.label == "note"
    assert any(isinstance(item, Citation) for item in footnote.inlines)
    assert [item.label for item in doc.footnote_references] == ["note"]
    assert [item.keys for item in doc.citations] == [["smith2025"], ["footnote-source"]]


def test_parse_bibliography_marker_as_renderer_neutral_block(tmp_path: Path):
    source = tmp_path / "thesis.md"
    source.write_text(
        """# 参考文献 {#chap:references}

::: bibliography
source: "./references.bib"
style: "GB-T-7714-2025"
:::
""",
        encoding="utf-8",
    )

    document = parse_markdown(source)

    assert isinstance(document.blocks[1], BibliographyBlock)
    assert document.blocks[1].location.line == 3
    assert document.blocks[1].id is None


def test_stable_id_utilities():
    assert is_valid_stable_id("fig:model")
    assert is_valid_stable_id("sec:related-work")
    assert not is_valid_stable_id("figure:model")
    assert not is_valid_stable_id("fig:")
    assert not is_valid_stable_id("fig:has space")
    assert split_stable_id("eq:loss") == ("eq", "loss")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("---\nthesis:\n  title: test\n", "缺少结束分隔符"),
        ("---\nthesis: [\n---\n", "YAML Front Matter 无效"),
        ("::: figure {#fig:x}\nsrc: x.png\n", "容器未闭合"),
    ],
)
def test_malformed_source_raises_parse_error(tmp_path: Path, text: str, message: str):
    source = tmp_path / "thesis.md"
    source.write_text(text, encoding="utf-8")

    with pytest.raises(ParseError, match=message):
        parse_markdown(source)


def test_empty_document_is_inspectable(tmp_path: Path):
    source = tmp_path / "empty.md"
    source.write_text("", encoding="utf-8")

    doc = parse_markdown(source)

    assert doc.metadata == {}
    assert doc.blocks == []
    assert doc.inline_content == []


def test_container_and_footnote_continuation_inline_locations(tmp_path: Path):
    text = """::: algorithm {#alg:train}
caption: "训练 [@caption-source]"

步骤引用 [@algorithm-source]。
:::

[^note]: 第一行。
    续行引用 [@footnote-source]。
"""
    source = tmp_path / "locations.md"
    source.write_text(text, encoding="utf-8")

    doc = parse_markdown(source)

    assert [citation.keys for citation in doc.citations] == [
        ["caption-source"],
        ["algorithm-source"],
        ["footnote-source"],
    ]
    assert [
        (citation.location.line, citation.location.column) for citation in doc.citations
    ] == [
        (2, 14),
        (4, 6),
        (8, 10),
    ]
