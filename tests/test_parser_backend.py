from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from thesis_forge.core.parser_backend import (
    ParserBackend,
    create_parser_backend,
)
from thesis_forge.core.parser_markdown_it import MarkdownItParserBackend

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

SAMPLE_MARKDOWN = """# 绪论 {#chap:introduction}

## 研究背景 {#sec:background}

已有研究表明，**结构化编译**与*可验证反馈*能够提升论文工程的一致性 [@smith2025]。
本项目使用 `thesisforge.yaml` 作为入口，普通源码换行不应在 Word 中产生手动换行。
模型流程见[图](#fig:model)。

![模型总体结构](assets/model.png){#fig:model}

损失函数定义如下：

$$
L=-\\sum_{i=1}^{N} y_i \\log \\hat y_i
$$
{#eq:loss}

| 指标 | 实验组 | 对照组 |
|---|---:|---:|
| **准确率** | 96.2% | 91.8% |
| 召回率 | 94.1% | 89.6% |

: 模型实验结果 {#tbl:experiment}

> 内容审阅应隐藏技术标记，但保留这一引用块。

```python {#lst:training title="训练代码"}
# 代码中的 {#literal}、[@literal] 与 @fig:literal 必须保持字面量
for epoch in range(epochs):
    train_one_epoch()
```

```algorithm {#alg:training title="训练流程"}
输入：训练集 D
输出：模型 M
1. 初始化参数
2. 迭代优化
```

这里包含一个说明性脚注[^scope]。

[^scope]: Review 中显示脚注号和正文，DOCX 中生成原生脚注。
"""


@pytest.fixture()
def sample_file(tmp_path: Path) -> Path:
    path = tmp_path / "sample.md"
    path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
    return path


def test_canonical_backend_satisfies_protocol() -> None:
    backend = create_parser_backend()
    assert isinstance(backend, ParserBackend)
    assert isinstance(backend, MarkdownItParserBackend)


def test_canonical_factory_parse_file_is_deterministic(sample_file: Path) -> None:
    first = create_parser_backend().parse_file(sample_file)
    second = create_parser_backend().parse_file(sample_file)
    assert parser_diff.dumps_normalized(
        parser_diff.normalize_document(first)
    ) == parser_diff.dumps_normalized(parser_diff.normalize_document(second))


def test_canonical_factory_parse_text_matches_parse_file(sample_file: Path) -> None:
    backend = create_parser_backend()
    direct = backend.parse_file(sample_file)
    via_backend = backend.parse_text(SAMPLE_MARKDOWN, source_path=sample_file)
    assert parser_diff.dumps_normalized(
        parser_diff.normalize_document(via_backend)
    ) == parser_diff.dumps_normalized(parser_diff.normalize_document(direct))


def test_normalized_json_is_deterministic(sample_file: Path) -> None:
    backend = create_parser_backend()
    first = backend.parse_file(sample_file)
    second = backend.parse_file(sample_file)
    dump_first = parser_diff.dumps_normalized(parser_diff.normalize_document(first))
    dump_second = parser_diff.dumps_normalized(parser_diff.normalize_document(second))
    assert dump_first == dump_second
    # 同一对象重复 dump 也必须字节一致
    assert parser_diff.dumps_normalized(parser_diff.normalize_document(first)) == dump_first


def test_normalization_covers_structure(sample_file: Path) -> None:
    normalized = parser_diff.normalize_document(
        create_parser_backend().parse_file(sample_file)
    )
    kinds = [block["kind"] for block in normalized["blocks"]]
    assert kinds == [
        "Heading",
        "Heading",
        "Paragraph",
        "Figure",
        "Paragraph",
        "Equation",
        "Table",
        "BlockQuote",
        "Listing",
        "Algorithm",
        "Paragraph",
        "FootnoteDefinition",
    ]
    assert normalized["metadata"] == {}
    figure = normalized["blocks"][3]
    assert figure["id"] == "fig:model"
    assert figure["location"]["line"] == 9
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
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("OK:")
