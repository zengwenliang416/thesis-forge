"""markdown-it 后端测试（ADR-0001 Phase 2）。

覆盖：协议满足、注册表、与 legacy 后端在 full-syntax fixture 与完整示例上的
归一化平价（直接调用 qa/tools/parser_diff.py 的比较函数，不经子进程）、
未闭合容器/front matter 错误消息一致、降级行为一致、行内位置平价，
以及 parser_diff 显式豁免机制本身的行为。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from thesis_forge.core.model import Paragraph
from thesis_forge.core.parser import ParseError
from thesis_forge.core.parser_backend import (
    LegacyParserBackend,
    ParserBackend,
    get_parser_backend,
    parser_backend_names,
)
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend

REPO_ROOT = Path(__file__).resolve().parents[1]
PARSER_DIFF_PATH = REPO_ROOT / "qa" / "tools" / "parser_diff.py"

FULL_SYNTAX_FIXTURE = REPO_ROOT / "qa" / "fixtures" / "parser" / "full-syntax.md"
COMPLETE_THESIS = REPO_ROOT / "examples" / "complete-thesis" / "thesis.md"
BACHELOR_THESIS = REPO_ROOT / "examples" / "bachelor-thesis" / "thesis.md"
BACHELOR_FULL_TEMPLATE = REPO_ROOT / "examples" / "bachelor-thesis" / "thesis-full-template.md"


def _load_parser_diff():
    spec = importlib.util.spec_from_file_location("parser_diff", PARSER_DIFF_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass 处理需要模块注册在 sys.modules 中
    sys.modules["parser_diff"] = module
    spec.loader.exec_module(module)
    return module


parser_diff = _load_parser_diff()

legacy = LegacyParserBackend()
markdown_it = MarkdownItParserBackend()


def _normalized_pair(source: Path) -> tuple[dict, dict]:
    return (
        parser_diff.normalize_document(legacy.parse_file(source)),
        parser_diff.normalize_document(markdown_it.parse_file(source)),
    )


def _assert_text_parity(text: str) -> None:
    """同一文本两后端解析结果的归一化 JSON 必须逐字节一致（零豁免）。"""
    normalized_a = parser_diff.normalize_document(
        legacy.parse_text(text, source_path="parity.md")
    )
    normalized_b = parser_diff.normalize_document(
        markdown_it.parse_text(text, source_path="parity.md")
    )
    dump_a = parser_diff.dumps_normalized(normalized_a)
    dump_b = parser_diff.dumps_normalized(normalized_b)
    assert dump_a == dump_b


# ---------------------------------------------------------------------------
# 协议与注册表
# ---------------------------------------------------------------------------


def test_markdown_it_backend_satisfies_protocol() -> None:
    backend = MarkdownItParserBackend()
    assert isinstance(backend, ParserBackend)
    assert backend.name == "markdown-it"


def test_backend_registry_includes_markdown_it() -> None:
    assert "markdown-it" in parser_backend_names()
    assert isinstance(get_parser_backend("markdown-it"), MarkdownItParserBackend)


# ---------------------------------------------------------------------------
# fixture 平价（块类型序列、ID、inline 序列、citation keys、crossref target、
# 脚注、列表层级/起始序号、metadata、位置——全部逐字段一致，零豁免）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [FULL_SYNTAX_FIXTURE, COMPLETE_THESIS, BACHELOR_THESIS, BACHELOR_FULL_TEMPLATE],
    ids=["full-syntax", "complete-thesis", "bachelor-thesis", "bachelor-full-template"],
)
def test_parity_with_legacy_on_fixtures(source: Path) -> None:
    normalized_a, normalized_b = _normalized_pair(source)
    report = parser_diff.diff_documents(normalized_a, normalized_b)
    assert report.allowed == []
    assert report.blocking == []


# ---------------------------------------------------------------------------
# 行内/块级语义平价（小样本，含行列位置）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        # 段落 inline 序列与行列位置（contract 基准样本）
        "如 @fig:model 所示，已有研究给出相关结论 [@smith2025, p. 12]。[^note]\n",
        # citation 三种形态
        "单文献 [@smith2025]。\n\n多文献：[@smith2025; @wang2024]。\n\n带页码：[@smith2025, p. 12]。\n",
        # 七种 crossref 前缀
        "见 @fig:a @tbl:b @eq:c @alg:d @lst:e @sec:f @chap:g。\n",
        # 标题内 inline 提取与 {#id}
        "## 结果 [@k1] 见 @fig:x {#sec:r}\n",
        # 多行段落（softbreak 处续行缩进必须保留在 Text 内）
        "第一行\n    续行缩进保留 [@a]。\n",
        # 列表项 inline 位置
        "- 见 @fig:m 与 [@k]\n",
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
        # hr 行降级为段落
        "段落\n\n---\n",
        # 脚注定义（含续行）inline 提取与位置
        "[^src]: 引用 [@fn-src]。\n    续行见 @fig:m。\n",
        # 容器 caption / 表单元格 / 算法正文中的 citation
        "::: figure {#fig:model}\nsrc: \"./images/model.png\"\ncaption: \"模型总体结构 [@cap-src]\"\nwidth: \"85%\"\n:::\n",
        "::: table {#tbl:results}\ncaption: \"实验结果\"\n\n| 模型 | AUROC |\n| --- | ---: |\n| A [@cell-src] | 0.91 |\n:::\n",
        "::: algorithm {#alg:train}\ncaption: \"训练流程\"\n\n1. 初始化参数；\n2. 读取数据 [@alg-src]。\n:::\n",
        # listing 围栏与语言推断
        "::: listing {#lst:predict}\ncaption: \"预测函数\"\nlanguage: \"python\"\n\n```javascript\ndef predict(x):\n    return model(x)\n```\n:::\n",
        # 脚注引用指向未定义 label（legacy 照常产出 FootnoteReference）
        "正文引用。[^undefined]\n",
        # HTML 注释块按段落原文降级，内部 citation/crossref 照常提取
        "<!-- =========================\n     引用 [@k] 与 @fig:x\n     =========================\n",
    ],
    ids=[
        "paragraph-inline-positions",
        "citation-forms",
        "crossref-prefixes",
        "heading-inline",
        "multiline-paragraph-indent",
        "list-item-inline",
        "list-levels-and-start",
        "mixed-markers-truncate",
        "ordered-marker-style-change",
        "bullet-marker-change",
        "loose-list-splits",
        "list-item-continuation",
        "hr-degrades-to-paragraph",
        "footnote-definition-inlines",
        "figure-caption-inline",
        "table-cell-inline",
        "algorithm-body-inline",
        "listing-fence-language",
        "undefined-footnote-ref",
        "html-comment-degrades",
    ],
)
def test_inline_and_block_parity_samples(text: str) -> None:
    _assert_text_parity(text)


# ---------------------------------------------------------------------------
# 错误与降级行为一致
# ---------------------------------------------------------------------------


def test_unclosed_container_error_matches_legacy() -> None:
    text = '# 标题\n\n::: figure {#fig:x}\nsrc: "./a.png"\n'
    with pytest.raises(ParseError) as legacy_error:
        legacy.parse_text(text, source_path="err.md")
    with pytest.raises(ParseError) as markdown_it_error:
        markdown_it.parse_text(text, source_path="err.md")
    assert str(markdown_it_error.value) == str(legacy_error.value)
    assert "第 3 行的 figure 容器未闭合" in str(markdown_it_error.value)


@pytest.mark.parametrize(
    "text",
    [
        "---\nthesis:\n  title: 测试\n",
        "---\nthesis: [\n---\n",
        "---\n- 甲\n- 乙\n---\n",
    ],
    ids=["unclosed-front-matter", "invalid-yaml", "non-mapping"],
)
def test_front_matter_errors_match_legacy(text: str) -> None:
    with pytest.raises(ParseError) as legacy_error:
        legacy.parse_text(text, source_path="err.md")
    with pytest.raises(ParseError) as markdown_it_error:
        markdown_it.parse_text(text, source_path="err.md")
    assert str(markdown_it_error.value) == str(legacy_error.value)


@pytest.mark.parametrize(
    "text",
    [
        # 未知 ::: 容器静默降级为段落原文
        "::: unknown {#x}\n内容\n:::\n",
        # 斜体/链接/行内图片降级为段落文本
        "这是 *斜体*、[链接](https://example.com) 与 ![图片](./a.png) 的段落。\n",
        # 顶层围栏代码块降级为段落
        "```python\ndef f():\n    return 1\n```\n",
        # 引用块降级为段落原文
        "> 本节适用于需要问卷调查的论文。\n",
        # setext 标题降级为段落
        "标题\n===\n",
        # 顶层管道表降级为段落
        "| 甲 | 乙 |\n| --- | --- |\n| 1 | 2 |\n",
    ],
    ids=[
        "unknown-container",
        "unsupported-inline-constructs",
        "top-level-fence",
        "blockquote",
        "setext-heading",
        "top-level-pipe-table",
    ],
)
def test_degraded_constructs_match_legacy(text: str) -> None:
    _assert_text_parity(text)
    doc = markdown_it.parse_text(text, source_path="degrade.md")
    assert all(isinstance(block, Paragraph) for block in doc.blocks)


def test_parse_text_preserves_logical_source_path(tmp_path: Path) -> None:
    source = tmp_path / "thesis.md"
    source.write_text("# 磁盘旧标题\n", encoding="utf-8")
    doc = markdown_it.parse_text("# 编辑器新标题\n", source_path=source)
    assert doc.source_path == source.resolve()
    assert doc.blocks[0].text == "编辑器新标题"


def test_empty_document_is_inspectable(tmp_path: Path) -> None:
    source = tmp_path / "empty.md"
    source.write_text("", encoding="utf-8")
    doc = markdown_it.parse_file(source)
    assert doc.metadata == {}
    assert doc.blocks == []
    assert doc.inline_content == []


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
