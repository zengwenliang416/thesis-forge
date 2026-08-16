from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from thesis_forge.core.parser import parse_markdown, parse_markdown_text
from thesis_forge.core.parser_backend import (
    LegacyParserBackend,
    ParserBackend,
    get_parser_backend,
    parser_backend_names,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PARSER_DIFF_PATH = REPO_ROOT / "qa" / "tools" / "parser_diff.py"


def _load_parser_diff():
    spec = importlib.util.spec_from_file_location("parser_diff", PARSER_DIFF_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass 处理需要模块注册在 sys.modules 中
    sys.modules["parser_diff"] = module
    spec.loader.exec_module(module)
    return module


parser_diff = _load_parser_diff()

SAMPLE_MARKDOWN = """---
title: 示例论文
author: 张三
render:
  bibliography: refs.bib
---

# 引言 {#chap:intro}

如图 @fig:model 所示，已有研究 [@doe2020; @smith2021, p. 12] 表明……[^note1]

[^note1]: 脚注正文，含 @tbl:stats 引用。

::: figure {#fig:model}
src: assets/model.png
caption: 模型结构
width: 80%
:::

## 方法 {#sec:method}

1. 第一步
2. 第二步 [@smith2021]

::: equation {#eq:loss}
$$
L = \\sum_i y_i \\log p_i
$$
:::

::: bibliography {#bib:refs}
:::
"""


@pytest.fixture()
def sample_file(tmp_path: Path) -> Path:
    path = tmp_path / "sample.md"
    path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
    return path


def test_legacy_backend_satisfies_protocol() -> None:
    backend = LegacyParserBackend()
    assert isinstance(backend, ParserBackend)
    assert backend.name == "legacy"


def test_backend_registry() -> None:
    assert "legacy" in parser_backend_names()
    assert "markdown-it" in parser_backend_names()
    assert isinstance(get_parser_backend("legacy"), LegacyParserBackend)
    with pytest.raises(ValueError, match="未知 parser 后端"):
        get_parser_backend("no-such-backend")


def test_legacy_backend_matches_direct_parse(sample_file: Path) -> None:
    backend = LegacyParserBackend()
    direct = parse_markdown(sample_file)
    via_backend = backend.parse_file(sample_file)
    assert parser_diff.dumps_normalized(
        parser_diff.normalize_document(via_backend)
    ) == parser_diff.dumps_normalized(parser_diff.normalize_document(direct))


def test_legacy_backend_parse_text_matches_direct(tmp_path: Path) -> None:
    backend = LegacyParserBackend()
    source_path = tmp_path / "inline.md"
    direct = parse_markdown_text(SAMPLE_MARKDOWN, source_path=source_path)
    via_backend = backend.parse_text(SAMPLE_MARKDOWN, source_path=source_path)
    assert parser_diff.dumps_normalized(
        parser_diff.normalize_document(via_backend)
    ) == parser_diff.dumps_normalized(parser_diff.normalize_document(direct))


def test_normalized_json_is_deterministic(sample_file: Path) -> None:
    first = parse_markdown(sample_file)
    second = parse_markdown(sample_file)
    dump_first = parser_diff.dumps_normalized(parser_diff.normalize_document(first))
    dump_second = parser_diff.dumps_normalized(parser_diff.normalize_document(second))
    assert dump_first == dump_second
    # 同一对象重复 dump 也必须字节一致
    assert parser_diff.dumps_normalized(parser_diff.normalize_document(first)) == dump_first


def test_normalization_covers_structure(sample_file: Path) -> None:
    normalized = parser_diff.normalize_document(parse_markdown(sample_file))
    kinds = [block["kind"] for block in normalized["blocks"]]
    assert kinds == [
        "Heading",
        "Paragraph",
        "FootnoteDefinition",
        "Figure",
        "Heading",
        "ListBlock",
        "Equation",
        "BibliographyBlock",
    ]
    assert normalized["metadata"]["title"] == "示例论文"
    figure = normalized["blocks"][3]
    assert figure["id"] == "fig:model"
    assert figure["location"]["line"] == 14
    assert {inline["kind"] for inline in normalized["inline_content"]} >= {
        "Text",
        "CrossReference",
        "Citation",
        "FootnoteReference",
    }


def test_parser_diff_cli_self_check(sample_file: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PARSER_DIFF_PATH),
            str(sample_file),
            "--backend-a",
            "legacy",
            "--backend-b",
            "legacy",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("OK:")


def test_parser_diff_cli_unknown_backend(sample_file: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PARSER_DIFF_PATH),
            str(sample_file),
            "--backend-b",
            "no-such-backend",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 2
    assert "未知 parser 后端" in result.stderr
