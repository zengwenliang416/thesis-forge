"""Parser 契约测试：将 docs/MARKDOWN_SPEC.md v0.2 逐条落成可执行断言。

每个测试的 docstring 标注对应的规范条目。本文件同时锁定当前实现的
降级行为与位置粒度（块级仅行号、column 恒为 None），供 ADR-0001
Parser 后端迁移后对比回归。
"""

from __future__ import annotations

import pytest

from thesis_forge.core.index import DocumentIndex
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
    InlineCode,
    ListBlock,
    Listing,
    Paragraph,
    Strong,
    Table,
    Text,
    inline_plain_text,
)
from thesis_forge.core.parser import ParseError, parse_markdown_text


def parse(text: str):
    return parse_markdown_text(text, source_path="contract.md")


# ---------------------------------------------------------------------------
# Front Matter
# ---------------------------------------------------------------------------


def test_contract_front_matter_mapping_and_render_config():
    """SPEC「Front Matter」：元数据为普通 YAML 映射；render.bibliography /
    render.citation_style 进入文档级 BibliographyConfig。"""
    doc = parse(
        """---
document:
  type: bachelor_thesis
thesis:
  title: "测试论文"
render:
  template_id: "school-2026"
  bibliography: "./references.bib"
  citation_style: "GB-T-7714-2025"
---

# 绪论 {#chap:intro}
"""
    )

    assert doc.metadata["document"]["type"] == "bachelor_thesis"
    assert doc.metadata["thesis"]["title"] == "测试论文"
    assert doc.metadata["render"]["template_id"] == "school-2026"
    assert doc.bibliography is not None
    assert doc.bibliography.path == "./references.bib"
    assert doc.bibliography.citation_style == "GB-T-7714-2025"


def test_contract_front_matter_optional():
    """SPEC「Front Matter」：Front Matter 可选，缺省时元数据为空映射。"""
    doc = parse("# 绪论 {#chap:intro}\n")

    assert doc.metadata == {}
    assert doc.bibliography is None
    assert [type(block) for block in doc.blocks] == [Heading]


def test_contract_front_matter_unclosed_raises():
    """SPEC「Error Behavior」：Front Matter 必须闭合，否则 ParseError。"""
    with pytest.raises(ParseError, match="缺少结束分隔符"):
        parse("---\nthesis:\n  title: 测试\n")


def test_contract_front_matter_must_be_mapping():
    """SPEC「Error Behavior」：Front Matter 根节点必须是键值映射。"""
    with pytest.raises(ParseError, match="必须是键值映射"):
        parse("---\n- 甲\n- 乙\n---\n")


def test_contract_front_matter_invalid_yaml_raises():
    """SPEC「Error Behavior」：无效 YAML 抛 ParseError。"""
    with pytest.raises(ParseError, match="YAML Front Matter 无效"):
        parse("---\nthesis: [\n---\n")


# ---------------------------------------------------------------------------
# Heading
# ---------------------------------------------------------------------------


def test_contract_heading_levels_and_ids():
    """SPEC「Heading」：ATX 1–6 级标题；`{#id}` 可选，可省略 ID。"""
    doc = parse(
        """# 一级 {#chap:a}
## 二级 {#sec:b}
### 三级
###### 六级
"""
    )

    assert [block.level for block in doc.blocks] == [1, 2, 3, 6]
    assert [block.id for block in doc.blocks] == ["chap:a", "sec:b", None, None]
    assert all(isinstance(block, Heading) for block in doc.blocks)


def test_contract_heading_inline_extraction():
    """SPEC「Heading」：标题文本做 inline 提取，并注册进文档级索引。"""
    doc = parse("## 结果 [@k1] 见 @fig:x {#sec:r}\n")

    heading = doc.blocks[0]
    assert isinstance(heading, Heading)
    # derived text: CrossReference fallback is None → target
    assert inline_plain_text(heading.inlines) == "结果 [@k1] 见 fig:x"
    assert [type(item) for item in heading.inlines] == [
        Text,
        Citation,
        Text,
        CrossReference,
    ]
    index = DocumentIndex.from_document(doc)
    assert [citation.keys for citation in index.citations] == [["k1"]]
    assert [ref.target for ref in index.cross_references] == ["fig:x"]
    citation = index.citations[0]
    assert (citation.location.line, citation.location.column) == (1, 7)


# ---------------------------------------------------------------------------
# Paragraph And Inline Content / Citation / CrossReference
# ---------------------------------------------------------------------------


def test_contract_paragraph_inline_sequence_and_positions():
    """SPEC「Paragraph And Inline Content」：CrossReference / Citation /
    FootnoteReference 按出现顺序保留，行列精确；其余内容为 Text。"""
    doc = parse("如 @fig:model 所示，已有研究给出相关结论 [@smith2025, p. 12]。[^note]\n")

    paragraph = doc.blocks[0]
    assert isinstance(paragraph, Paragraph)
    assert [type(item) for item in paragraph.inlines] == [
        Text,
        CrossReference,
        Text,
        Citation,
        Text,
        FootnoteReference,
    ]

    crossref = paragraph.inlines[1]
    assert isinstance(crossref, CrossReference)
    assert crossref.target == "fig:model"
    assert (crossref.location.line, crossref.location.column) == (1, 3)

    citation = paragraph.inlines[3]
    assert isinstance(citation, Citation)
    assert citation.keys == ["smith2025"]
    assert citation.locator == "p. 12"
    assert citation.raw == "[@smith2025, p. 12]"
    assert (citation.location.line, citation.location.column) == (1, 28)

    footnote_ref = paragraph.inlines[5]
    assert isinstance(footnote_ref, FootnoteReference)
    assert footnote_ref.label == "note"


def test_contract_citation_forms():
    """SPEC「Citation」：单 key、多 key、带 locator 三种形态；Parser 保存
    keys、raw 与 locator，不在解析阶段格式化。"""
    doc = parse(
        "单文献 [@smith2025]。\n\n多文献：[@smith2025; @wang2024]。\n\n带页码：[@smith2025, p. 12]。\n"
    )

    index = DocumentIndex.from_document(doc)
    assert [citation.keys for citation in index.citations] == [
        ["smith2025"],
        ["smith2025", "wang2024"],
        ["smith2025"],
    ]
    assert [citation.locator for citation in index.citations] == [None, None, "p. 12"]
    assert index.citations[1].raw == "[@smith2025; @wang2024]"


def test_contract_cross_reference_all_prefixes():
    """SPEC「Reserved IDs」：七种前缀 fig/tbl/eq/alg/lst/sec/chap 均可被
    `@prefix:name` 引用。"""
    doc = parse("见 @fig:a @tbl:b @eq:c @alg:d @lst:e @sec:f @chap:g。\n")

    assert [ref.target for ref in DocumentIndex.from_document(doc).cross_references] == [
        "fig:a",
        "tbl:b",
        "eq:c",
        "alg:d",
        "lst:e",
        "sec:f",
        "chap:g",
    ]


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_contract_unordered_list_levels_and_markers():
    """SPEC「List」：无序列表；两空格一级缩进；保留 marker 与层级。"""
    doc = parse("- 第一项\n  - 第二级项目\n")

    block = doc.blocks[0]
    assert isinstance(block, ListBlock)
    assert block.ordered is False
    assert block.start is None
    assert [(item.level, item.marker, item.ordinal, inline_plain_text(item.inlines)) for item in block.items] == [
        (0, "-", None, "第一项"),
        (1, "-", None, "第二级项目"),
    ]


def test_contract_ordered_list_start_number():
    """SPEC「List」：有序列表保留起始序号与各项 ordinal。"""
    doc = parse("3. 从 3 开始\n4. 下一项\n")

    block = doc.blocks[0]
    assert isinstance(block, ListBlock)
    assert block.ordered is True
    assert block.start == 3
    assert [item.ordinal for item in block.items] == [3, 4]
    assert [inline_plain_text(item.inlines) for item in block.items] == ["从 3 开始", "下一项"]


def test_contract_list_item_inline_extraction():
    """SPEC「List」：列表项正文做 inline 提取；位置从正文起点计算。"""
    doc = parse("- 见 @fig:m 与 [@k]\n")

    block = doc.blocks[0]
    assert isinstance(block, ListBlock)
    item = block.items[0]
    assert [type(inline) for inline in item.inlines] == [
        Text,
        CrossReference,
        Text,
        Citation,
    ]
    index = DocumentIndex.from_document(doc)
    assert [ref.target for ref in index.cross_references] == ["fig:m"]
    assert [citation.keys for citation in index.citations] == [["k"]]
    crossref = item.inlines[1]
    assert isinstance(crossref, CrossReference)
    assert (crossref.location.line, crossref.location.column) == (1, 5)


def test_contract_mixed_markers_truncate_list_block():
    """SPEC「List」：有序/无序 marker 切换静默截断当前列表块，后续行
    另起新列表块，无诊断。"""
    doc = parse("1. 有序一\n2. 有序二\n- 无序一\n")

    assert [type(block) for block in doc.blocks] == [ListBlock, ListBlock]
    ordered, unordered = doc.blocks
    assert isinstance(ordered, ListBlock) and isinstance(unordered, ListBlock)
    assert ordered.ordered is True
    assert ordered.start == 1
    assert [inline_plain_text(item.inlines) for item in ordered.items] == ["有序一", "有序二"]
    assert unordered.ordered is False
    assert [inline_plain_text(item.inlines) for item in unordered.items] == ["无序一"]


# ---------------------------------------------------------------------------
# Containers
# ---------------------------------------------------------------------------


def test_contract_figure_container():
    """SPEC「Figure」：容器头 `{#id}` + kv 元数据；caption 值做 inline 提取。"""
    doc = parse(
        """::: figure {#fig:model}
src: "./images/model.png"
caption: "模型总体结构 [@cap-src]"
width: "85%"
:::
"""
    )

    figure = doc.blocks[0]
    assert isinstance(figure, Figure)
    assert figure.id == "fig:model"
    assert figure.src == "./images/model.png"
    assert inline_plain_text(figure.caption_inlines) == "模型总体结构 [@cap-src]"
    assert figure.width == "85%"
    caption_citation = figure.caption_inlines[1]
    assert (caption_citation.location.line, caption_citation.location.column) == (3, 18)
    index = DocumentIndex.from_document(doc)
    assert [citation.keys for citation in index.citations] == [["cap-src"]]
    assert index.citations[0].location.line == 3


def test_contract_table_container_populates_structured_rows_and_inlines():
    """SPEC「Table」：表格 caption、header/body rows、alignment 和 cell
    inline content 都进入结构化 Table IR。"""
    doc = parse(
        """::: table {#tbl:results}
caption: "实验结果"

| 模型 | AUROC |
| --- | ---: |
| A [@cell-src] | 0.91 |
:::
"""
    )

    table = doc.blocks[0]
    assert isinstance(table, Table)
    assert table.id == "tbl:results"
    assert inline_plain_text(table.caption_inlines) == "实验结果"
    assert len(table.rows) == 2
    assert table.rows[0].header is True
    assert table.rows[1].header is False
    assert [cell.alignment for cell in table.rows[0].cells] == [None, "right"]
    cell_citation = table.rows[1].cells[0].inlines[1]
    assert cell_citation.location.line == 6
    assert inline_plain_text(table.rows[1].cells[0].inlines) == "A [@cell-src]"
    assert inline_plain_text(table.rows[1].cells[1].inlines) == "0.91"
    index = DocumentIndex.from_document(doc)
    assert [citation.keys for citation in index.citations] == [["cell-src"]]
    assert index.citations[0].location.line == 6


def test_contract_equation_container_strips_dollar_fence():
    """SPEC「Equation」：存在首尾 `$$` 时剥离。"""
    doc = parse("::: equation {#eq:loss}\n$$\nL = x + y\n$$\n:::\n")

    equation = doc.blocks[0]
    assert isinstance(equation, Equation)
    assert equation.id == "eq:loss"
    assert equation.latex == "L = x + y"


def test_contract_equation_container_dollar_fence_optional():
    """SPEC「Equation」：公式体可以省略 `$$` 包裹，内容原样保留。"""
    doc = parse("::: equation {#eq:loss}\nL = x + y\n:::\n")

    equation = doc.blocks[0]
    assert isinstance(equation, Equation)
    assert equation.latex == "L = x + y"


def test_contract_algorithm_container_body_and_inlines():
    """SPEC「Algorithm」：正文按原文保留在 Algorithm.body；正文行做
    inline 提取。"""
    doc = parse(
        """::: algorithm {#alg:train}
caption: "训练流程"

1. 初始化参数；
2. 读取数据 [@alg-src]。
:::
"""
    )

    algorithm = doc.blocks[0]
    assert isinstance(algorithm, Algorithm)
    assert algorithm.id == "alg:train"
    assert inline_plain_text(algorithm.caption_inlines) == "训练流程"
    assert "1. 初始化参数；" in algorithm.body
    assert "2. 读取数据 [@alg-src]。" in algorithm.body
    body_citation = algorithm.body_lines[1][1]
    assert isinstance(body_citation, Citation)
    assert (body_citation.location.line, body_citation.location.column) == (5, 9)
    index = DocumentIndex.from_document(doc)
    assert [citation.keys for citation in index.citations] == [["alg-src"]]
    assert index.citations[0].location.line == 5


def test_contract_listing_language_kv_wins_over_fence():
    """SPEC「Listing」：`language:` 元数据优先于围栏 info string；围栏行
    不进入 Listing.code。"""
    doc = parse(
        """::: listing {#lst:predict}
caption: "预测函数"
language: "python"

```javascript
def predict(x):
    return model(x)
```
:::
"""
    )

    listing = doc.blocks[0]
    assert isinstance(listing, Listing)
    assert listing.id == "lst:predict"
    assert listing.language == "python"
    assert listing.code == "def predict(x):\n    return model(x)"


def test_contract_listing_language_inferred_from_fence_info_string():
    """SPEC「Listing」：未提供 `language:` 时使用围栏 info string 推断语言。"""
    doc = parse("::: listing {#lst:infer}\n```python\nx = 1\n```\n:::\n")

    listing = doc.blocks[0]
    assert isinstance(listing, Listing)
    assert listing.language == "python"
    assert listing.code == "x = 1"


def test_contract_listing_fence_optional_and_language_none():
    """SPEC「Listing」：围栏可省略；语言两种来源都缺失时为 None。"""
    doc = parse("::: listing {#lst:raw}\nx = 1\n:::\n")

    listing = doc.blocks[0]
    assert isinstance(listing, Listing)
    assert listing.language is None
    assert listing.code == "x = 1"


def test_contract_bibliography_marker_block():
    """SPEC「Bibliography Placement」：`::: bibliography` 解析为
    renderer-neutral BibliographyBlock，无 ID。"""
    doc = parse("# 参考文献 {#chap:references}\n\n::: bibliography\n:::\n")

    marker = doc.blocks[1]
    assert isinstance(marker, BibliographyBlock)
    assert marker.id is None
    assert marker.location.line == 3


# ---------------------------------------------------------------------------
# Footnote
# ---------------------------------------------------------------------------


def test_contract_footnote_definition_and_continuation():
    """SPEC「Footnote」：`[^label]` 引用与定义按 label 稳定匹配；四空格
    续行并入定义正文。"""
    doc = parse("正文引用。[^note]\n\n[^note]: 第一行。\n    第二行续行。\n")

    assert [
        ref.label for ref in DocumentIndex.from_document(doc).footnote_references
    ] == ["note"]
    definition = doc.blocks[1]
    assert isinstance(definition, FootnoteDefinition)
    assert definition.label == "note"
    # derived text: continuation lines carry no SoftBreak yet
    assert inline_plain_text(definition.inlines) == "第一行。第二行续行。"
    assert definition.location.line == 3


def test_contract_footnote_definition_inline_extraction():
    """SPEC「Footnote」/「Paragraph And Inline Content」：脚注定义（含续行）
    做 inline 提取。"""
    doc = parse("[^src]: 引用 [@fn-src]。\n    续行见 @fig:m。\n")

    index = DocumentIndex.from_document(doc)
    assert [citation.keys for citation in index.citations] == [["fn-src"]]
    assert [ref.target for ref in index.cross_references] == ["fig:m"]
    assert index.citations[0].location.line == 1
    crossref = index.cross_references[0]
    assert crossref.location.line == 2


# ---------------------------------------------------------------------------
# Error Behavior / 降级策略
# ---------------------------------------------------------------------------


def test_contract_unclosed_container_error_contains_line_number():
    """SPEC「Error Behavior」：容器必须由 `:::` 闭合；未闭合抛 ParseError，
    消息含容器起始行号。"""
    with pytest.raises(ParseError, match="第 3 行的 figure 容器未闭合"):
        parse('# 标题\n\n::: figure {#fig:x}\nsrc: "./a.png"\n')


def test_contract_unknown_container_silently_degrades_to_paragraph():
    """SPEC「Error Behavior」：未知 `:::` 容器静默降级为段落原文，无诊断。"""
    doc = parse("::: unknown {#x}\n内容\n:::\n")

    assert [type(block) for block in doc.blocks] == [Paragraph]
    paragraph = doc.blocks[0]
    assert isinstance(paragraph, Paragraph)
    assert "::: unknown {#x}" in inline_plain_text(paragraph.inlines)
    assert "内容" in inline_plain_text(paragraph.inlines)
    assert all(isinstance(inline, Text) for inline in paragraph.inlines)


def test_contract_unsupported_constructs_degrade_to_paragraph():
    """SPEC「Markdown 基础结构（V1 支持集）」：斜体/链接/行内图片不支持，
    静默降级为段落文本；粗体保留语义并由渲染器输出真实粗体。"""
    doc = parse("这是 **粗体**、*斜体*、[链接](https://example.com) 与 ![图片](./a.png) 的段落。\n")

    assert [type(block) for block in doc.blocks] == [Paragraph]
    paragraph = doc.blocks[0]
    assert isinstance(paragraph, Paragraph)
    assert "粗体" in inline_plain_text(paragraph.inlines)
    assert "[链接](https://example.com)" in inline_plain_text(paragraph.inlines)
    assert "![图片](./a.png)" in inline_plain_text(paragraph.inlines)
    assert any(
        isinstance(inline, Strong)
        and [type(child) for child in inline.children] == [Text]
        and inline.children[0].value == "粗体"
        for inline in paragraph.inlines
    )
    assert DocumentIndex.from_document(doc).citations == ()
    assert DocumentIndex.from_document(doc).cross_references == ()


def test_contract_inline_code_preserves_semantics_without_markers():
    doc = parse("字段组合为 `tenant_id / env / app_id`。\n")

    paragraph = doc.blocks[0]
    assert isinstance(paragraph, Paragraph)
    assert any(
        isinstance(inline, InlineCode)
        and inline.value == "tenant_id / env / app_id"
        for inline in paragraph.inlines
    )


def test_contract_top_level_fenced_code_degrades_to_paragraph():
    """SPEC「Markdown 基础结构（V1 支持集）」：顶层 ``` 围栏代码块不支持，
    静默降级为段落文本。"""
    doc = parse("```python\ndef f():\n    return 1\n```\n")

    assert [type(block) for block in doc.blocks] == [Paragraph]
    paragraph = doc.blocks[0]
    assert isinstance(paragraph, Paragraph)
    assert inline_plain_text(paragraph.inlines).startswith("```python")
    assert "def f():" in inline_plain_text(paragraph.inlines)
    assert all(isinstance(inline, Text) for inline in paragraph.inlines)


# ---------------------------------------------------------------------------
# 源码位置粒度
# ---------------------------------------------------------------------------


def test_contract_block_level_location_line_only():
    """SPEC「源码位置粒度」：块级 object 只有行号，column 恒为 None
    （锁定现状，供后端迁移对比）。"""
    doc = parse(
        """# 绪论 {#chap:intro}

第一段。

::: figure {#fig:m}
src: "./a.png"
:::

[^note]: 脚注定义。
"""
    )

    heading, paragraph, figure, footnote = doc.blocks
    assert isinstance(heading, Heading)
    assert (heading.location.line, heading.location.column) == (1, None)
    assert isinstance(paragraph, Paragraph)
    assert (paragraph.location.line, paragraph.location.column) == (3, None)
    assert isinstance(figure, Figure)
    assert (figure.location.line, figure.location.column) == (5, None)
    assert isinstance(footnote, FootnoteDefinition)
    assert (footnote.location.line, footnote.location.column) == (9, None)


def test_contract_list_locations_line_only():
    """SPEC「源码位置粒度」：ListBlock 与 ListItem 同样只有行号。"""
    doc = parse("- 甲\n  - 乙\n")

    block = doc.blocks[0]
    assert isinstance(block, ListBlock)
    assert (block.location.line, block.location.column) == (1, None)
    assert [(item.location.line, item.location.column) for item in block.items] == [
        (1, None),
        (2, None),
    ]
