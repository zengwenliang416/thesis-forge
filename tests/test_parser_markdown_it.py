"""canonical markdown-it parser 测试（ADR-0001 Phase 2）。

覆盖：协议满足、canonical factory、标准 inline typed 节点、v2 标准块消费、
legacy 输入显式拒绝、行内位置、重复解析确定性，以及 parser_diff 显式
豁免机制本身的行为。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from markdown_it import MarkdownIt

from thesis_forge.core.index import DocumentIndex
from thesis_forge.core.model import (
    BlockQuote,
    CodeBlock,
    Heading,
    InlineCode,
    InlineMath,
    Paragraph,
    Table,
    inline_plain_text,
)
from thesis_forge.core.parser_backend import (
    ParserBackend,
    create_parser_backend,
)
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend
from thesis_forge.core.parser_support import ParseError

REPO_ROOT = Path(__file__).resolve().parents[1]
PARSER_DIFF_PATH = REPO_ROOT / "qa" / "tools" / "parser_diff.py"

COMPLETE_THESIS = REPO_ROOT / "examples" / "complete-thesis" / "thesis.md"
BACHELOR_THESIS = REPO_ROOT / "examples" / "bachelor-thesis" / "thesis.md"


def _load_parser_diff():
    spec = importlib.util.spec_from_file_location("parser_diff", PARSER_DIFF_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass 处理需要模块注册在 sys.modules 中
    sys.modules["parser_diff"] = module
    spec.loader.exec_module(module)
    return module


parser_diff = _load_parser_diff()

canonical = create_parser_backend()


def _parse_with_default_preset(text: str):
    backend = MarkdownItParserBackend()
    backend._md = MarkdownIt("default")
    return backend.parse_text(text, source_path="default-preset.md")


def _assert_text_deterministic(text: str) -> None:
    """同一 canonical parser 两次解析必须产生完全一致的 normalized JSON。"""
    normalized_a = parser_diff.normalize_document(
        create_parser_backend().parse_text(text, source_path="parity.md")
    )
    normalized_b = parser_diff.normalize_document(
        create_parser_backend().parse_text(text, source_path="parity.md")
    )
    dump_a = parser_diff.dumps_normalized(normalized_a)
    dump_b = parser_diff.dumps_normalized(normalized_b)
    assert dump_a == dump_b


# ---------------------------------------------------------------------------
# 协议与注册表
# ---------------------------------------------------------------------------


def test_canonical_backend_satisfies_protocol() -> None:
    backend = create_parser_backend()
    assert isinstance(backend, ParserBackend)
    assert isinstance(backend, MarkdownItParserBackend)


# ---------------------------------------------------------------------------
# Legacy fixtures are rejected by the v2 parser before generic parsing.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [COMPLETE_THESIS, BACHELOR_THESIS],
    ids=["complete-thesis", "bachelor-thesis"],
)
def test_legacy_fixtures_are_rejected_by_canonical_backend(source: Path) -> None:
    with pytest.raises(ParseError, match=r"TF-SOURCE-LEGACY-00[1-3]"):
        canonical.parse_file(source)


def test_full_syntax_standard_inline_nodes_are_typed() -> None:
    document = canonical.parse_text(
        "a **bold** `code` $E = m c^2$.\n",
        source_path="standard-inline.md",
    )
    paragraph = next(
        block
        for block in document.blocks
        if isinstance(block, Paragraph)
        and any(isinstance(inline, InlineMath) for inline in block.inlines)
    )

    math = next(inline for inline in paragraph.inlines if isinstance(inline, InlineMath))
    assert math.latex == "E = m c^2"
    literal = next(
        inline for inline in paragraph.inlines if isinstance(inline, InlineCode)
    )
    assert literal.value == "code"


def test_full_template_standard_blocks_are_typed() -> None:
    doc = _parse_with_default_preset(
        "> quoted text\n\n"
        "| Model | AUROC |\n"
        "| --- | ---: |\n"
        "| A | 0.91 |\n\n"
        "| Model | Accuracy |\n"
        "| --- | ---: |\n"
        "| A | 0.94 |\n"
    )
    standard_tables = [block for block in doc.blocks if isinstance(block, Table)]
    assert [len(table.rows) for table in standard_tables] == [2, 2]

    standard_quote = next(
        block for block in doc.blocks if isinstance(block, BlockQuote)
    )
    assert standard_quote.location.line == 1
    assert len(standard_quote.children) == 1
    assert isinstance(standard_quote.children[0], Paragraph)


# ---------------------------------------------------------------------------
# 行内/块级语义平价（小样本，含行列位置）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        # 段落 inline 序列与行列位置（contract 基准样本）
        "已有研究给出相关结论 [@smith2025, p. 12]。[^note]\n",
        # citation 三种形态
        "单文献 [@smith2025]。\n\n多文献：[@smith2025; @wang2024]。\n\n带页码：[@smith2025, p. 12]。\n",
        # 标题内 citation 提取与 {#id}
        "## 结果 [@k1] {#sec:r}\n",
        # 列表项 inline 位置
        "- 见 [@k]\n",
        # 有序列表起始序号 / 无序嵌套层级
        "3. 从 3 开始\n4. 下一项\n\n- 第一项\n  - 第二级项目\n- 第三项\n",
        # 混合 marker 截断为两个列表块
        "1. 有序一\n2. 有序二\n- 无序一\n",
        # 有序 marker 风格变化（. → )）legacy 不截断；mdit 原生会截断，靠行扫描对齐
        "1. 甲\n2) 乙\n",
        # 无序 marker 变化（- → +）同上
        "- 甲\n+ 乙\n",
        # 松散列表（空行分隔）legacy 拆成两个列表块
        "1. 甲\n\n2. 乙\n",
        # 列表项续行：legacy 截断列表、续行成段落
        "- 第一项\n  继续内容\n- 第二项\n",
        # 脚注定义（含续行）inline 提取与位置
        "[^src]: 引用 [@fn-src]。\n    续行保留。\n",
        # 脚注引用指向未定义 label（legacy 照常产出 FootnoteReference）
        "正文引用。[^undefined]\n",
    ],
    ids=[
        "paragraph-inline-positions",
        "citation-forms",
        "heading-inline",
        "list-item-inline",
        "list-levels-and-start",
        "mixed-markers-truncate",
        "ordered-marker-style-change",
        "bullet-marker-change",
        "loose-list-splits",
        "list-item-continuation",
        "footnote-definition-inlines",
        "undefined-footnote-ref",
    ],
)
def test_canonical_parser_is_deterministic_for_samples(text: str) -> None:
    _assert_text_deterministic(text)


# ---------------------------------------------------------------------------
# legacy 输入必须显式失败，不得降级为普通文本
# ---------------------------------------------------------------------------


def test_legacy_container_error_is_explicit() -> None:
    text = '# 标题\n\n::: figure {#fig:x}\nsrc: "./a.png"\n'
    with pytest.raises(ParseError, match="TF-SOURCE-LEGACY-002"):
        canonical.parse_text(text, source_path="err.md")


@pytest.mark.parametrize(
    "text",
    [
        "---\nthesis:\n  title: 测试\n",
        "---\nthesis: [\n---\n",
        "---\n- 甲\n- 乙\n---\n",
    ],
    ids=["unclosed-front-matter", "invalid-yaml", "non-mapping"],
)
def test_front_matter_is_rejected_with_replacement(text: str) -> None:
    with pytest.raises(ParseError, match="TF-SOURCE-LEGACY-001") as captured:
        canonical.parse_text(text, source_path="err.md")
    assert "thesisforge.yaml" in str(captured.value)


@pytest.mark.parametrize(
    ("text", "expected_type"),
    [
        ("> 引用内容\n", BlockQuote),
        ("```python\nprint(1)\n```\n", CodeBlock),
        ("| 甲 | 乙 |\n| --- | ---: |\n| 1 | 2 |\n", Table),
        ("标题\n===\n", Heading),
    ],
    ids=["blockquote", "fence", "table", "setext-heading"],
)
def test_default_standard_blocks_reach_typed_consumers(
    text: str, expected_type: type
) -> None:
    doc = _parse_with_default_preset(text)
    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], expected_type)


def test_default_mixed_standard_blocks_are_consumed_in_order() -> None:
    doc = _parse_with_default_preset(
        "> 引用内容\n\n"
        "```python\nprint(1)\n```\n\n"
        "| 甲 | 乙 |\n| --- | ---: |\n| 1 | 2 |\n\n"
        "标题\n===\n"
    )
    assert [type(block) for block in doc.blocks] == [
        BlockQuote,
        CodeBlock,
        Table,
        Heading,
    ]


def test_default_list_fence_fails_explicitly_instead_of_flattening() -> None:
    with pytest.raises(ParseError, match="列表中未消费的 markdown-it 块 token: fence"):
        _parse_with_default_preset(
            "- item\n\n"
            "    ```python\n"
            "    print(1)\n"
            "    ```\n"
        )


def test_default_list_setext_heading_fails_explicitly() -> None:
    with pytest.raises(
        ParseError,
        match="列表中未消费的 markdown-it 块 token: heading_open",
    ):
        _parse_with_default_preset("- item\n\n    nested heading\n    --------------\n")


@pytest.mark.parametrize(
    "text",
    [
        "    code\n",
        "内容\n\n---\n",
    ],
    ids=["indented-code", "thematic-break"],
)
def test_default_unsupported_blocks_raise_explicit_diagnostics(text: str) -> None:
    with pytest.raises(ParseError, match="markdown-it 块 token"):
        _parse_with_default_preset(text)


def test_parse_text_preserves_logical_source_path(tmp_path: Path) -> None:
    source = tmp_path / "thesis.md"
    source.write_text("# 磁盘旧标题\n", encoding="utf-8")
    doc = canonical.parse_text("# 编辑器新标题\n", source_path=source)
    assert doc.source_path == source.resolve()
    assert inline_plain_text(doc.blocks[0].inlines) == "编辑器新标题"


def test_legacy_algorithm_container_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "algorithm.md"
    source.write_text(
        "::: algorithm {#alg:train}\n"
        'caption: "训练流程"\n'
        "\n"
        "1. 初始化参数；\n"
        "2. 读取数据 [@alg-src]。\n"
        ":::\n",
        encoding="utf-8",
    )
    with pytest.raises(ParseError, match="TF-SOURCE-LEGACY-002"):
        canonical.parse_file(source)


def test_empty_document_is_inspectable(tmp_path: Path) -> None:
    source = tmp_path / "empty.md"
    source.write_text("", encoding="utf-8")
    doc = canonical.parse_file(source)
    assert doc.metadata == {}
    assert doc.blocks == []
    assert DocumentIndex.from_document(doc).inlines == ()


# ---------------------------------------------------------------------------
# parser_diff 豁免机制（显式、逐条记录原因；不允许无注释豁免）
# ---------------------------------------------------------------------------


def test_diff_allowance_requires_reason_and_records_entries() -> None:
    normalized_a = {"blocks": [{"location": {"line": 1, "column": None}}]}
    normalized_b = {"blocks": [{"location": {"line": 1, "column": 5}}]}

    strict = parser_diff.diff_documents(normalized_a, normalized_b)
    assert not strict.ok
    assert strict.blocking == ["$.blocks[0].location.column: 类型不一致 NoneType != int"]
    assert strict.allowed == []

    rule = parser_diff.AllowRule(
        pattern=r"\$\.blocks\[\d+\]\.location\.column:",
        reason="markdown-it 块级仅行号，列号策略差异（示例）",
    )
    relaxed = parser_diff.diff_documents(normalized_a, normalized_b, allow=[rule])
    assert relaxed.ok
    assert relaxed.blocking == []
    assert relaxed.allowed == [
        ("$.blocks[0].location.column: 类型不一致 NoneType != int", rule.reason)
    ]


def test_parse_allow_spec_validation() -> None:
    rule = parser_diff.parse_allow_spec(r"\.location\.column:=列号差异")
    assert rule.pattern == r"\.location\.column:"
    assert rule.reason == "列号差异"
    with pytest.raises(ValueError, match="PATTERN=REASON"):
        parser_diff.parse_allow_spec("只有模式没有原因")
    with pytest.raises(ValueError, match="PATTERN=REASON"):
        parser_diff.parse_allow_spec("pattern=")
