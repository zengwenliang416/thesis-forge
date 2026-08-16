"""Spike: pandoc JSON AST 后端实证分析。

对 fixtures/full-syntax.md 运行多个 pandoc reader/扩展组合，机械提取：
- 项目语法到 pandoc AST 节点的映射（Div / Cite / Note / Math / data-pos 等）
- source position 的粒度与覆盖率（commonmark_x+sourcepos）
- 自定义语法（::: 容器头、@fig:xxx crossref）的扩展成本证据
- 多文件输入与确定性

运行: ../../../.venv/bin/python parse_pandoc.py
输出: results/pandoc-analysis.json
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "full-syntax.md"
INCLUDE_MAIN = HERE / "fixtures" / "include-main.md"
INCLUDE_CHAPTER = HERE / "fixtures" / "include-chapter.md"
RESULTS = HERE / "results"

# 组合 M：pandoc 原生 markdown reader（citations 等学术扩展全开，无 sourcepos 能力）
MARKDOWN_PROFILE = (
    "markdown+fenced_divs+citations+footnotes+header_attributes"
    "+yaml_metadata_block+tex_math_dollars+pipe_tables"
)
# 组合 X：commonmark_x + sourcepos（唯一能输出位置信息的路线，但无 citations 扩展）
COMMONMARK_X_PROFILE = "commonmark_x+sourcepos"

CONTAINER_KINDS = ("figure", "table", "equation", "listing", "algorithm", "bibliography")
CONTAINER_HEADER_RE = re.compile(
    r"^:::\s+(figure|table|equation|listing|algorithm|bibliography)"
    r"(?:\s+\{#([^}]+)\})?\s*$",
    re.MULTILINE,
)

CROSSREF_PREFIXES = ("fig", "tbl", "eq", "alg", "lst", "sec", "chap")


def run_pandoc_text(profile: str, text: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["pandoc", "-f", profile, "-t", "json"],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pandoc 失败({profile}): {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def run_pandoc_files(profile: str, paths: list[Path]) -> dict[str, Any]:
    proc = subprocess.run(
        ["pandoc", "-f", profile, "-t", "json", *[str(p) for p in paths]],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pandoc 失败({profile}): {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def walk_blocks(blocks: list[dict[str, Any]]):
    for block in blocks:
        yield block
        t = block["t"]
        if t == "Div":
            yield from walk_blocks(block["c"][1])
        elif t == "BlockQuote":
            yield from walk_blocks(block["c"])
        elif t == "BulletList":
            for item in block["c"]:
                yield from walk_blocks(item)
        elif t == "OrderedList":
            for item in block["c"][1]:
                yield from walk_blocks(item)
        # Table/Figure 内部行列结构对本分析无增量信息，不递归


def walk_inlines(inlines: list[dict[str, Any]]):
    for inline in inlines:
        yield inline
        t = inline["t"]
        if t == "Span":
            yield from walk_inlines(inline["c"][1])
        elif t == "Note":
            yield from walk_blocks(inline["c"])
        elif t == "Cite":
            yield from walk_inlines(inline["c"][1])


def all_inlines(blocks: list[dict[str, Any]]):
    for block in walk_blocks(blocks):
        t = block["t"]
        if t in ("Para", "Plain"):
            yield from walk_inlines(block["c"])
        elif t == "Header":
            yield from walk_inlines(block["c"][2])


def attr_of(node: dict[str, Any]) -> list[Any]:
    """返回 Header/Div/CodeBlock/Span 的 Attr 三元组，无则返回空 attr。"""
    t = node["t"]
    if t == "Header":
        return node["c"][1]
    if t in ("Div", "CodeBlock", "Span"):
        return node["c"][0]
    return ["", [], []]


def data_pos(node: dict[str, Any]) -> str | None:
    attr = attr_of(node)
    for key, value in attr[2]:
        if key == "data-pos":
            return value
    return None


def rewrite_container_headers(text: str) -> str:
    """把项目写法 `::: figure {#fig:x}` 改写为 pandoc 可识别的 `::: {.figure #fig:x}`。"""

    def repl(match: re.Match[str]) -> str:
        kind, block_id = match.group(1), match.group(2)
        inner = f".{kind}" + (f" #{block_id}" if block_id else "")
        return f"::: {{{inner}}}"

    return CONTAINER_HEADER_RE.sub(repl, text)


def _block_type_histogram(doc: dict[str, Any]) -> dict[str, int]:
    hist: dict[str, int] = {}
    for block in walk_blocks(doc["blocks"]):
        hist[block["t"]] = hist.get(block["t"], 0) + 1
    return dict(sorted(hist.items()))


def _citation_summary(doc: dict[str, Any]) -> dict[str, Any]:
    cites = [i for i in all_inlines(doc["blocks"]) if i["t"] == "Cite"]
    entries = []
    for cite in cites:
        for cit in cite["c"][0]:
            suffix_text = "".join(
                x.get("c", "") if isinstance(x.get("c"), str) else " "
                for x in cit["citationSuffix"]
            )
            entries.append(
                {
                    "id": cit["citationId"],
                    "mode": cit["citationMode"]["t"],
                    "suffix": suffix_text.strip(),
                }
            )
    return {
        "cite_node_count": len(cites),
        "citation_entries": entries,
        "crossref_as_author_in_text": [
            e["id"]
            for e in entries
            if e["mode"] == "AuthorInText" and e["id"].split(":")[0] in CROSSREF_PREFIXES
        ],
    }


def _footnote_summary(doc: dict[str, Any]) -> dict[str, Any]:
    notes = [i for i in all_inlines(doc["blocks"]) if i["t"] == "Note"]
    content_pos = None
    if notes:
        # Note 本身无 attr；其内容 inline 在 commonmark_x 下带定义点位置
        content = notes[0]["c"]
        first_inline = content[0]["c"][0] if content and content[0]["c"] else None
        if first_inline is not None:
            content_pos = data_pos(first_inline)
    return {
        "note_count": len(notes),
        "label_preserved": False,  # pandoc Note 为匿名节点，label 必然丢失
        "note_content_pos_sample": content_pos,
    }


def _sourcepos_coverage(doc: dict[str, Any]) -> dict[str, Any]:
    block_types_with_pos: dict[str, int] = {}
    block_types_without_pos: dict[str, int] = {}
    for block in walk_blocks(doc["blocks"]):
        t = block["t"]
        if t in ("Div",) and any(kv[0] == "wrapper" for kv in attr_of(block)[2]):
            t = "Div(wrapper=1)"
        if data_pos(block):
            block_types_with_pos[t] = block_types_with_pos.get(t, 0) + 1
        else:
            block_types_without_pos[t] = block_types_without_pos.get(t, 0) + 1
    inlines = list(all_inlines(doc["blocks"]))
    inline_spans_with_pos = sum(
        1 for i in inlines if i["t"] == "Span" and data_pos(i)
    )
    non_span_inlines = [i for i in inlines if i["t"] != "Span"]
    pos_samples = [p for p in (data_pos(i) for i in inlines) if p][:3]
    return {
        "block_types_with_pos": dict(sorted(block_types_with_pos.items())),
        "block_types_without_pos": dict(sorted(block_types_without_pos.items())),
        "inline_wrapper_spans_with_pos": inline_spans_with_pos,
        "non_span_inline_types": sorted({i["t"] for i in non_span_inlines}),
        "pos_format_samples": pos_samples,
    }


def analyze() -> dict[str, Any]:
    text = FIXTURE.read_text(encoding="utf-8")
    doc_m = run_pandoc_text(MARKDOWN_PROFILE, text)
    doc_x = run_pandoc_text(COMMONMARK_X_PROFILE, text)

    # --- 容器头预处理实证 ---
    rewritten = rewrite_container_headers(text)
    doc_m_rewritten = run_pandoc_text(MARKDOWN_PROFILE, rewritten)
    divs_after = [
        b for b in walk_blocks(doc_m_rewritten["blocks"]) if b["t"] == "Div"
    ]
    container_divs = [
        {
            "id": b["c"][0][0],
            "classes": b["c"][0][1],
            "inner_block_types": [c["t"] for c in b["c"][1]],
        }
        for b in divs_after
        if b["t"] == "Div" and b["c"][0][1] and b["c"][0][1][0] in CONTAINER_KINDS
    ]
    figure_div = next((d for d in container_divs if d["classes"][0] == "figure"), None)
    kv_sample = None
    if figure_div:
        for b in walk_blocks(doc_m_rewritten["blocks"]):
            if b["t"] == "Div" and b["c"][0][0] == figure_div["id"]:
                para = next((c for c in b["c"][1] if c["t"] == "Para"), None)
                if para:
                    kv_sample = "".join(
                        i.get("c", " ") if isinstance(i.get("c"), str) else " "
                        for i in para["c"]
                    )
                break

    # --- 未闭合容器行为 ---
    unclosed = run_pandoc_text(MARKDOWN_PROFILE, '::: figure {#fig:x}\nsrc: "y.png"\n')
    unclosed_blocks = [b["t"] for b in unclosed["blocks"]]

    # --- 关闭 citations 的备选路线（markdown reader） ---
    doc_no_cite = run_pandoc_text("markdown-citations", text)
    cite_nodes_no_ext = [i for i in all_inlines(doc_no_cite["blocks"]) if i["t"] == "Cite"]

    # --- 多文件 ---
    doc_multi = run_pandoc_files(COMMONMARK_X_PROFILE, [INCLUDE_MAIN, INCLUDE_CHAPTER])
    multi_positions = [
        p for p in (data_pos(b) for b in walk_blocks(doc_multi["blocks"])) if p
    ]

    # --- 确定性：同一输入跑两次逐字节比较 ---
    out1 = subprocess.run(
        ["pandoc", "-f", MARKDOWN_PROFILE, "-t", "json", str(FIXTURE)],
        capture_output=True, check=True,
    ).stdout
    out2 = subprocess.run(
        ["pandoc", "-f", MARKDOWN_PROFILE, "-t", "json", str(FIXTURE)],
        capture_output=True, check=True,
    ).stdout

    return {
        "pandoc_version": shutil.which("pandoc") and subprocess.run(
            ["pandoc", "--version"], capture_output=True, text=True, check=True
        ).stdout.splitlines()[0],
        "profiles": {
            "markdown": MARKDOWN_PROFILE,
            "commonmark_x": COMMONMARK_X_PROFILE,
        },
        "markdown_reader": {
            "meta_keys": sorted(doc_m["meta"].keys()),
            "block_histogram": _block_type_histogram(doc_m),
            "header_ids": [
                attr_of(b)[0] for b in walk_blocks(doc_m["blocks"]) if b["t"] == "Header"
            ],
            "divs": [
                {"id": b["c"][0][0], "classes": b["c"][0][1]}
                for b in walk_blocks(doc_m["blocks"])
                if b["t"] == "Div"
            ],
            "citations": _citation_summary(doc_m),
            "footnotes": _footnote_summary(doc_m),
            "math_nodes": sorted(
                {
                    f"{i['t']}({i['c'][0]['t']})"
                    for i in all_inlines(doc_m["blocks"])
                    if i["t"] == "Math"
                }
            ),
            "ordered_list_starts": [
                b["c"][0][0]
                for b in walk_blocks(doc_m["blocks"])
                if b["t"] == "OrderedList"
            ],
            "has_any_data_pos": any(
                data_pos(b) for b in walk_blocks(doc_m["blocks"])
            ),
        },
        "commonmark_x_reader": {
            "meta_keys": sorted(doc_x["meta"].keys()),
            "block_histogram": _block_type_histogram(doc_x),
            "header_ids": [
                attr_of(b)[0] for b in walk_blocks(doc_x["blocks"]) if b["t"] == "Header"
            ],
            "sourcepos": _sourcepos_coverage(doc_x),
            "citations": _citation_summary(doc_x),
            "footnotes": _footnote_summary(doc_x),
            "table_node_has_pos": any(
                data_pos(b) for b in walk_blocks(doc_x["blocks"]) if b["t"] == "Table"
            ),
        },
        "container_preprocess": {
            "rewrite_rule": "::: kind {#id} -> ::: {.kind #id}",
            "container_divs_after_rewrite": container_divs,
            "kv_lines_arrive_as": "Div 内普通 Para 文本",
            "kv_para_sample": kv_sample,
        },
        "unclosed_container_behavior": {
            "pandoc_error": False,
            "resulting_block_types": unclosed_blocks,
        },
        "no_citations_alternative": {
            "profile": "markdown-citations",
            "cite_nodes": len(cite_nodes_no_ext),
            "note": "@fig:x 与 [@key] 均保留为纯文本，可统一后处理，但仍无 sourcepos",
        },
        "multi_file": {
            "meta_keys": sorted(doc_multi["meta"].keys()),
            "data_pos_samples": multi_positions[:4],
            "per_file_tracking": any("include-main" in p for p in multi_positions)
            and any("include-chapter" in p for p in multi_positions),
        },
        "determinism": {"two_runs_byte_identical": out1 == out2},
    }


def extract_features(analysis: dict[str, Any] | None = None) -> dict[str, dict[str, str]]:
    """供 compare.py 使用的覆盖矩阵行（由 analyze() 的实测结果支撑）。"""
    if analysis is None:
        analysis = analyze()
    m = analysis["markdown_reader"]
    x = analysis["commonmark_x_reader"]
    xpos = x["sourcepos"]

    def feat(status: str, mechanism: str, position: str, evidence: str) -> dict[str, str]:
        return {
            "status": status,
            "mechanism": mechanism,
            "position": position,
            "evidence": evidence,
        }

    return {
        "front_matter": feat(
            "支持", "native(yaml_metadata_block)", "n/a",
            f"meta keys={m['meta_keys']}",
        ),
        "heading_atx": feat(
            "支持", "native(Header)", "commonmark_x: 行列; markdown: 无",
            f"Header ids={m['header_ids']}",
        ),
        "heading_id": feat(
            "支持", "native(header_attributes)", "同 heading",
            "Header attr id 原样保留 chap:/sec: 前缀（含冒号）",
        ),
        "paragraph": feat(
            "支持", "native(Para)", "commonmark_x: wrapper Div 行列",
            "Para 在 commonmark_x 下被 wrapper Div 包裹携带 data-pos",
        ),
        "citation": feat(
            "部分支持",
            "markdown reader 原生 Cite（多 key/locator 入 suffix）；"
            "commonmark_x 无 citations 扩展只能文本后处理 → sourcepos 与原生 citation 不可兼得",
            "markdown: 无; commonmark_x: 后处理可重建",
            f"Cite 数={m['citations']['cite_node_count']}, "
            f"entries={m['citations']['citation_entries'][:3]}",
        ),
        "crossref": feat(
            "部分支持",
            "无原生节点；markdown reader 下裸 @fig:x 变 AuthorInText Cite（可按前缀识别），"
            "其他路线需正则后处理",
            "取决于 reader，均需后处理",
            f"crossref_as_author_in_text={m['citations']['crossref_as_author_in_text']}",
        ),
        "footnote": feat(
            "部分支持",
            "native(Note)，但 label 丢失（Note 匿名嵌在引用点），续行被合并",
            "commonmark_x: 引用点与定义点均有行列（wrapper Span）",
            f"Note 数={m['footnotes']['note_count']}, "
            f"label_preserved={m['footnotes']['label_preserved']}",
        ),
        "math": feat(
            "支持", "native(Math InlineMath/DisplayMath, tex_math_dollars)",
            "commonmark_x: 行列",
            f"math 节点={m['math_nodes']}",
        ),
        "list_ordered_start": feat(
            "支持", "native(OrderedList start 属性)", "commonmark_x: 借 wrapper Div 行列",
            f"ordered starts={m['ordered_list_starts']}",
        ),
        "list_nested": feat(
            "支持", "native(嵌套 List)", "commonmark_x: 借 wrapper Div 行列",
            "嵌套 BulletList 正常",
        ),
        "pipe_table": feat(
            "支持", "native(Table)", "无（Table 节点无 data-pos，位置盲区）",
            f"table_node_has_pos={x['table_node_has_pos']}",
        ),
        "containers": feat(
            "部分支持",
            "项目写法 ::: figure {#id} 两种 reader 均不识别（静默退化为段落）；"
            "需源码预处理改写成 ::: {.figure #id} 后 Div 原生（id/类/位置齐全）",
            "预处理后 commonmark_x: 行列",
            f"预处理后可识别容器={len(analysis['container_preprocess']['container_divs_after_rewrite'])}/6; "
            f"未闭合 ::: 无报错, blocks={analysis['unclosed_container_behavior']['resulting_block_types']}",
        ),
        "container_kv_metadata": feat(
            "部分支持", "kv 行作为 Div 内普通段落文本，需自行解析",
            "n/a",
            f"kv_para_sample={analysis['container_preprocess']['kv_para_sample']!r}",
        ),
        "sourcepos_block": feat(
            "部分支持",
            "仅 commonmark/gfm/commonmark_x reader 的 sourcepos 扩展提供 data-pos "
            "(file@l:c-l:c)；markdown reader 完全不支持；Table 子树（含单元格）完全无位置，"
            "List/ListItem 靠外层 wrapper Div 间接定位",
            "行列",
            f"有位置: {xpos['block_types_with_pos']}; 无位置: {xpos['block_types_without_pos']}",
        ),
        "sourcepos_inline": feat(
            "部分支持",
            "commonmark_x 下每个 inline 被 wrapper Span 包裹带 data-pos（含列）；"
            "markdown reader 无任何 inline 位置",
            "行列（经 wrapper Span）",
            f"wrapper spans={xpos['inline_wrapper_spans_with_pos']}, "
            f"samples={xpos['pos_format_samples']}",
        ),
        "multi_file": feat(
            "支持", "pandoc 接受多输入文件，data-pos 带文件名前缀逐文件正确；"
            "front matter 仅首文件生效",
            "逐文件行列",
            f"per_file_tracking={analysis['multi_file']['per_file_tracking']}, "
            f"samples={analysis['multi_file']['data_pos_samples']}",
        ),
        "error_diagnostics": feat(
            "不支持",
            "pandoc 对未闭合 :::、非法属性静默退化为文本，不产生错误；需自写预检",
            "n/a",
            f"unclosed blocks={analysis['unclosed_container_behavior']['resulting_block_types']}",
        ),
        "determinism": feat(
            "支持", "同输入两次运行 JSON 逐字节一致",
            "n/a",
            f"byte_identical={analysis['determinism']['two_runs_byte_identical']}",
        ),
    }


def write_results(results_dir: Path = RESULTS) -> dict[str, Any]:
    """跑一次完整分析并落盘 results/pandoc-analysis.json，返回分析字典。"""
    results_dir.mkdir(exist_ok=True)
    analysis = analyze()
    analysis["features"] = extract_features(analysis)
    out = results_dir / "pandoc-analysis.json"
    out.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return analysis


def main() -> None:
    analysis = write_results()
    out = RESULTS / "pandoc-analysis.json"
    print(f"pandoc 分析完成 -> {out}")
    print(f"  markdown reader blocks: {analysis['markdown_reader']['block_histogram']}")
    print(f"  commonmark_x sourcepos: {analysis['commonmark_x_reader']['sourcepos']['block_types_with_pos']}")
    print(f"  容器预处理后 Div: {len(analysis['container_preprocess']['container_divs_after_rewrite'])}/6")
    print(f"  多文件逐文件定位: {analysis['multi_file']['per_file_tracking']}")
    print(f"  确定性: {analysis['determinism']['two_runs_byte_identical']}")


if __name__ == "__main__":
    main()
