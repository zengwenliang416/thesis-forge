"""Spike 汇总：三种 parser 后端对 full-syntax fixture 的覆盖矩阵。

后端：
- existing   —— 现有手写 parser（thesis_forge.core.parser）
- pandoc     —— pandoc JSON AST（parse_pandoc.py 的实测结论）
- markdownit —— markdown-it-py + mdit-py-plugins（parse_markdown_it.py 的实测结论）

运行: ../../../.venv/bin/python compare.py
输出: results/coverage.json（并刷新 pandoc / markdown-it 两份分析 JSON）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent.parent
FIXTURE = HERE / "fixtures" / "full-syntax.md"
RESULTS = HERE / "results"

sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(HERE))

import parse_markdown_it
import parse_pandoc

FEATURES: list[tuple[str, str]] = [
    ("front_matter", "YAML front matter"),
    ("heading_atx", "ATX 标题 1–6 级"),
    ("heading_id", "标题 {#custom-id}"),
    ("paragraph", "段落"),
    ("citation", "citation [@key; @key2, locator]"),
    ("crossref", "crossref @fig:xxx"),
    ("footnote", "脚注 [^label] 引用/定义/续行"),
    ("math", "行内/块级数学"),
    ("list_ordered_start", "有序列表起始序号"),
    ("list_nested", "嵌套列表"),
    ("pipe_table", "管道表"),
    ("containers", "::: 六种语义容器"),
    ("container_kv_metadata", "容器头 key:value 元数据"),
    ("sourcepos_block", "块级 source position"),
    ("sourcepos_inline", "行内 source position（含列）"),
    ("multi_file", "多文件 include"),
    ("error_diagnostics", "语法错误诊断"),
    ("determinism", "解析确定性"),
]


def _feat(status: str, mechanism: str, position: str, evidence: str) -> dict[str, str]:
    return {
        "status": status,
        "mechanism": mechanism,
        "position": position,
        "evidence": evidence,
    }


def extract_existing_features() -> dict[str, dict[str, str]]:
    """机械检查现有 parser 对 fixture 的解析结果。"""
    from thesis_forge.core import parser as existing
    from thesis_forge.core.model import (
        Algorithm,
        BibliographyBlock,
        Equation,
        Figure,
        Heading,
        ListBlock,
        Listing,
        Paragraph,
        Table,
    )

    doc = existing.parse_markdown(FIXTURE)
    blocks = doc.blocks

    headings = [b for b in blocks if isinstance(b, Heading)]
    heading_ids = [b.id for b in headings if b.id]
    figure = next(b for b in blocks if isinstance(b, Figure))
    table = next(b for b in blocks if isinstance(b, Table))
    lists = [b for b in blocks if isinstance(b, ListBlock)]
    ordered = next(b for b in lists if b.ordered)
    footnote_defs = [b for b in blocks if type(b).__name__ == "FootnoteDefinition"]
    continuation_def = next((b for b in footnote_defs if "\n" in b.text), None)

    inline_pos = [
        (i.location.line, i.location.column)
        for i in doc.inline_content
        if i.location.line is not None
    ]
    inline_has_column = all(col is not None for _, col in inline_pos)

    # 未闭合容器应抛 ParseError 并带行号
    try:
        existing.parse_markdown_text(
            '::: figure {#fig:x}\nsrc: "y.png"\n', source_path="probe.md"
        )
        unclosed_error = None
    except existing.ParseError as error:
        unclosed_error = str(error)

    # 确定性：两次解析结构一致
    doc2 = existing.parse_markdown(FIXTURE)

    def shape(d):
        return [(type(b).__name__, b.id, b.location.line) for b in d.blocks]

    deterministic = shape(doc) == shape(doc2) and [
        (c.keys, c.locator) for c in doc.citations
    ] == [(c.keys, c.locator) for c in doc2.citations]

    container_types = {
        type(b).__name__
        for b in blocks
        if isinstance(b, Figure | Table | Equation | Listing | Algorithm | BibliographyBlock)
    }

    return {
        "front_matter": _feat(
            "支持", "native(yaml.safe_load)", "n/a",
            f"keys={sorted(doc.metadata.keys())}",
        ),
        "heading_atx": _feat(
            "支持", "native(正则逐行)", "行",
            f"levels={sorted({h.level for h in headings})}",
        ),
        "heading_id": _feat(
            "支持", "native", "行",
            f"ids={heading_ids}",
        ),
        "paragraph": _feat(
            "支持", "native", "行",
            f"Paragraph 数={sum(isinstance(b, Paragraph) for b in blocks)}",
        ),
        "citation": _feat(
            "支持", "native(INLINE_TOKEN_RE)", "行列",
            f"citations={[(c.keys, c.locator) for c in doc.citations]}",
        ),
        "crossref": _feat(
            "支持", "native(INLINE_TOKEN_RE 前缀白名单)", "行列",
            f"targets={[c.target for c in doc.cross_references]}",
        ),
        "footnote": _feat(
            "支持", "native（label 保留，续行合并）", "引用点：行列；定义：仅行",
            f"defs={[(b.label, b.location.line) for b in footnote_defs]}, "
            f"续行合并={'第二行' in (continuation_def.text if continuation_def else '')}",
        ),
        "math": _feat(
            "部分支持",
            "模型无 Math 节点：行内 $...$ 仅作普通文本；块级数学只能经 ::: equation 容器",
            "n/a",
            "model.py 无 Math 类型；fixture 行内数学未产生语义节点",
        ),
        "list_ordered_start": _feat(
            "支持", "native(start 字段)", "行",
            f"ordered.start={ordered.start}",
        ),
        "list_nested": _feat(
            "支持", "native（扁平 items + level=indent//2）", "行",
            f"levels={sorted({i.level for b in lists for i in b.items})}",
        ),
        "pipe_table": _feat(
            "支持", "native（保留原始 markdown 字符串，结构校验在编译期）", "行",
            f"table.markdown 含对齐行={'| ---' in table.markdown}",
        ),
        "containers": _feat(
            "支持", "native(CONTAINER_START_RE 逐行扫描；未闭合抛 ParseError)", "行",
            f"容器类型={sorted(container_types)}",
        ),
        "container_kv_metadata": _feat(
            "支持", "native(KV_RE 元数据阶段解析)", "行",
            f"figure: src={figure.src!r} caption={figure.caption!r} width={figure.width!r}",
        ),
        "sourcepos_block": _feat(
            "部分支持", "SourceLocation.line 全部填充；column 块级为空", "仅行",
            "所有 block.location.line 非空, column=None",
        ),
        "sourcepos_inline": _feat(
            "支持", "SourceLocation(line, column) 逐 inline 填充", "行列",
            f"inline 数={len(inline_pos)}, 全部带列={inline_has_column}",
        ),
        "multi_file": _feat(
            "不支持", "parse_markdown 只接受单文件；无 include 机制", "n/a",
            "需在调用层自行实现",
        ),
        "error_diagnostics": _feat(
            "支持", "ParseError 带行号（未闭合容器/YAML 无效等）", "n/a",
            f"unclosed -> {unclosed_error!r}",
        ),
        "determinism": _feat(
            "支持", "同输入两次解析结构一致", "n/a",
            f"deterministic={deterministic}",
        ),
    }


def _display_width(text: str) -> int:
    import unicodedata

    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _display_width(text))


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    pandoc_analysis = parse_pandoc.write_results(RESULTS)
    markdownit_analysis = parse_markdown_it.write_results(RESULTS)
    backends = {
        "existing": extract_existing_features(),
        "pandoc": pandoc_analysis["features"],
        "markdownit": markdownit_analysis["features"],
    }
    missing = {
        name: [key for key, _ in FEATURES if key not in rows]
        for name, rows in backends.items()
    }
    if any(missing.values()):
        raise SystemExit(f"feature 覆盖不全: {missing}")

    matrix = {
        key: {
            "label": label,
            **{name: backends[name][key] for name in backends},
        }
        for key, label in FEATURES
    }
    payload = {
        "fixture": str(FIXTURE.relative_to(PROJECT_ROOT)),
        "backends": {
            "existing": "src/thesis_forge/core/parser.py（手写正则+逐行扫描，396 行）",
            "pandoc": "pandoc 3.8.2.1 JSON AST（markdown / commonmark_x+sourcepos 两种 reader）",
            "markdownit": "markdown-it-py 4.2.0 + mdit-py-plugins 0.6.1",
        },
        "status_legend": {
            "支持": "原生或低成本插件即可完整获得语义",
            "部分支持": "需要预处理/后处理/自写规则，或能力有缺口",
            "不支持": "该路线基本无法获得或成本极高",
        },
        "matrix": matrix,
    }
    out = RESULTS / "coverage.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    width = max(_display_width(label) for _, label in FEATURES)
    print(f"{_pad('语法', width)} | existing | pandoc | markdown-it")
    for key, label in FEATURES:
        row = matrix[key]
        cells = [f"{row[name]['status']}({row[name]['position']})" for name in backends]
        print(f"{_pad(label, width)} | {cells[0]} | {cells[1]} | {cells[2]}")
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
