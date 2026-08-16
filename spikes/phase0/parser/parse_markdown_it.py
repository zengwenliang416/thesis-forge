"""Spike: markdown-it-py（纯 Python）后端实证分析。

对 fixtures/full-syntax.md 运行 markdown-it-py + mdit-py-plugins，机械提取：
- token.map 位置粒度（行区间，无列）
- 插件生态覆盖：front_matter / footnote / container / dollarmath / attrs
- citations / crossref / 容器头元数据等无插件语法的缺口证据
- 未闭合容器行为与确定性

运行: ../../../.venv/bin/python parse_markdown_it.py
输出: results/markdown-it-analysis.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import markdown_it
import mdit_py_plugins
import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_plugin
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "full-syntax.md"
RESULTS = HERE / "results"

CONTAINER_KINDS = ("figure", "table", "equation", "listing", "algorithm", "bibliography")


def build_parser() -> MarkdownIt:
    md = MarkdownIt("commonmark")
    md.use(front_matter_plugin)
    md.use(footnote_plugin)
    md.use(dollarmath_plugin)
    md.use(attrs_plugin)
    md.enable("table")
    for kind in CONTAINER_KINDS:
        md.use(container_plugin, kind)
    return md


def _walk(tokens: list[Any]):
    for token in tokens:
        yield token
        if token.children:
            yield from _walk(token.children)


def analyze() -> dict[str, Any]:
    text = FIXTURE.read_text(encoding="utf-8")
    md = build_parser()
    tokens = md.parse(text)
    flat = list(_walk(tokens))

    # --- front matter ---
    fm = next((t for t in tokens if t.type == "front_matter"), None)
    fm_meta = yaml.safe_load(fm.content) if fm else {}

    # --- 标题与 {#id} ---
    headings = [t for t in tokens if t.type == "heading_open"]
    heading_inline_sample = next(
        t for t in tokens if t.type == "inline" and "{#" in t.content
    )

    # --- 容器 ---
    container_opens = [
        {"type": t.type, "info": t.info, "map": t.map}
        for t in tokens
        if t.type.startswith("container_") and t.type.endswith("_open")
    ]

    # --- footnote ---
    footnote_refs = [
        {"label": t.meta.get("label"), "map": t.map}
        for t in flat
        if t.type == "footnote_ref"
    ]
    footnote_defs = [
        {"label": t.meta.get("label")}
        for t in tokens
        if t.type == "footnote_open"
    ]
    # 定义内容 map（含续行）：footnote_open 之后的 paragraph_open
    def_maps = []
    for i, t in enumerate(tokens):
        if t.type == "footnote_open":
            following = tokens[i + 1 : i + 6]
            para = next((x for x in following if x.type == "paragraph_open"), None)
            def_maps.append({"label": t.meta.get("label"), "content_map": para.map if para else None})

    # --- 列表 ---
    ordered = [
        {"attrs": t.attrs, "map": t.map} for t in tokens if t.type == "ordered_list_open"
    ]
    nested = any(
        t.type == "bullet_list_open" and tokens[j - 1].type != "bullet_list_close"
        and j > 0 and tokens[j - 1].type in ("paragraph_close",)
        and any(p.type == "list_item_open" for p in tokens[:j])
        for j, t in enumerate(tokens)
    )

    # --- inline 层：citation/crossref 无插件，保持为纯文本 ---
    inline_with_citation = next(
        (t for t in tokens if t.type == "inline" and "[@smith2025" in t.content), None
    )
    inline_with_crossref = next(
        (t for t in tokens if t.type == "inline" and "@fig:model" in t.content), None
    )
    math_tokens = [
        {"type": t.type, "content": t.content.strip()[:30], "map": t.map}
        for t in flat
        if t.type.startswith("math_")
    ]

    # --- 位置粒度 ---
    block_maps = [
        {"type": t.type, "map": t.map}
        for t in tokens
        if t.map is not None and not t.type.endswith("_close")
    ][:8]
    inline_maps = {t.type for t in flat if t.nesting == 0 and t.map is None}

    # --- 未闭合容器行为：container 插件把 EOF 当结束，无异常无警告 ---
    unclosed_tokens = md.parse('::: figure\nsrc: "y.png"\n')
    unclosed_container = any(t.type.startswith("container_") for t in unclosed_tokens)

    # --- 确定性 ---
    again = md.parse(text)
    determinism = [t.as_dict() for t in tokens] == [t.as_dict() for t in again]

    return {
        "versions": {
            "markdown-it-py": markdown_it.__version__,
            "mdit-py-plugins": mdit_py_plugins.__version__,
        },
        "plugins_used": ["front_matter", "footnote", "dollarmath", "attrs", "container×6"]
        + ["core:table"],
        "front_matter": {
            "token_found": fm is not None,
            "map": fm.map if fm else None,
            "meta_keys": sorted(fm_meta.keys()) if isinstance(fm_meta, dict) else [],
        },
        "headings": {
            "levels": sorted({int(t.tag[1]) for t in headings}),
            "attrs_plugin_extracted_id": any(
                t.attrs and any(a[0] == "id" for a in t.attrs) for t in headings
            ),
            "raw_id_still_in_text": "{#" in heading_inline_sample.content,
            "heading_inline_sample": heading_inline_sample.content,
        },
        "containers": {
            "opens": container_opens,
            "count": len(container_opens),
            "header_info_needs_custom_parse": True,
            "kv_lines_arrive_as": "容器内 paragraph 文本",
        },
        "citations_crossrefs": {
            "plugin_available": False,
            "citation_survives_as_text": inline_with_citation is not None,
            "crossref_survives_as_text": inline_with_crossref is not None,
            "note": "mdit-py-plugins 无 pandoc 风格 citation/crossref 插件，需自写 inline rule",
        },
        "footnotes": {
            "refs": footnote_refs,
            "defs": footnote_defs,
            "label_preserved": all(r["label"] for r in footnote_refs),
            "definition_maps": def_maps,
            "ref_token_has_own_map": any(r["map"] is not None for r in footnote_refs),
        },
        "math": {"tokens": math_tokens},
        "lists": {
            "ordered_attrs": ordered,
            "start_preserved": any(
                a and dict(a).get("start") == 3 for a in (o["attrs"] for o in ordered)
            ),
            "nested_detected": nested,
        },
        "table": {
            "table_open_found": any(t.type == "table_open" for t in tokens),
            "map": next((t.map for t in tokens if t.type == "table_open"), None),
        },
        "positions": {
            "block_map_samples": block_maps,
            "map_semantics": "[start_line, end_line)，0-based，仅行，无列",
            "inline_tokens_without_map": sorted(inline_maps),
        },
        "unclosed_container": {
            "container_runs_to_eof": unclosed_container,
            "no_exception": True,
            "resulting_types": [t.type for t in unclosed_tokens][:4],
        },
        "determinism": {"two_parses_token_equal": determinism},
    }


def extract_features(analysis: dict[str, Any] | None = None) -> dict[str, dict[str, str]]:
    """供 compare.py 使用的覆盖矩阵行（由 analyze() 的实测结果支撑）。"""
    if analysis is None:
        analysis = analyze()

    def feat(status: str, mechanism: str, position: str, evidence: str) -> dict[str, str]:
        return {
            "status": status,
            "mechanism": mechanism,
            "position": position,
            "evidence": evidence,
        }

    return {
        "front_matter": feat(
            "支持", "plugin(front_matter) + yaml 自解析", "行（token.map）",
            f"map={analysis['front_matter']['map']}, keys={analysis['front_matter']['meta_keys']}",
        ),
        "heading_atx": feat(
            "支持", "native(core heading rule)", "行",
            f"levels={analysis['headings']['levels']}",
        ),
        "heading_id": feat(
            "部分支持",
            "attrs 插件不识别标题行尾 {#id}（实测 attrs 为空、文本原样残留）；"
            "需从 inline 文本自行提取（约 10 行）",
            "行",
            f"attrs_extracted={analysis['headings']['attrs_plugin_extracted_id']}, "
            f"sample={analysis['headings']['heading_inline_sample']!r}",
        ),
        "paragraph": feat("支持", "native", "行", "paragraph_open token.map"),
        "citation": feat(
            "部分支持",
            "无现成插件，[@key; @key2, locator] 需自写 inline rule（含多 key/locator 拆分）",
            "行（经宿主段落）；列需自行扫源码",
            f"citation_survives_as_text={analysis['citations_crossrefs']['citation_survives_as_text']}",
        ),
        "crossref": feat(
            "部分支持",
            "无现成插件，@fig:xxx 需自写 inline rule（约 30 行，前缀白名单）",
            "行（经宿主段落）；列需自行扫源码",
            f"crossref_survives_as_text={analysis['citations_crossrefs']['crossref_survives_as_text']}",
        ),
        "footnote": feat(
            "支持",
            "plugin(footnote)：label 完整保留（meta.label），定义 map 覆盖续行",
            "定义：行；引用点：inline token 无自身 map，仅宿主段落行",
            f"refs={analysis['footnotes']['refs']}, "
            f"def_maps={analysis['footnotes']['definition_maps']}",
        ),
        "math": feat(
            "支持", "plugin(dollarmath)", "行（math_block）；inline 无 map",
            f"tokens={analysis['math']['tokens']}",
        ),
        "list_ordered_start": feat(
            "支持", "native(attrs.start)", "行",
            f"ordered_attrs={analysis['lists']['ordered_attrs']}",
        ),
        "list_nested": feat(
            "支持", "native（嵌套 token 树）", "行",
            f"nested={analysis['lists']['nested_detected']}",
        ),
        "pipe_table": feat(
            "支持", "native(core table rule, enable('table'))", "行",
            f"map={analysis['table']['map']}",
        ),
        "containers": feat(
            "部分支持",
            "plugin(container) 按名字注册 6 次；项目写法 ::: figure {#id} 原样兼容"
            "（info 字符串含原始头部），{#id} 需自行解析；未闭合 ::: 无报错，"
            "容器静默吞到文末",
            "行",
            f"opens={len(analysis['containers']['opens'])}/6, "
            f"info 样例={[o['info'] for o in analysis['containers']['opens']][:2]}",
        ),
        "container_kv_metadata": feat(
            "部分支持", "kv 行为容器内段落文本，需自行解析（与现有 parser 同构）",
            "行",
            analysis["containers"]["kv_lines_arrive_as"],
        ),
        "sourcepos_block": feat(
            "部分支持",
            "token.map=[start,end) 0-based 行区间，块级 token 普遍具备；无列号",
            "仅行",
            f"samples={analysis['positions']['block_map_samples'][:3]}",
        ),
        "sourcepos_inline": feat(
            "不支持",
            "inline token map=None，引擎不记录任何列号；"
            "需自行按行二次扫描（成本与现有 parser 相当）",
            "无",
            f"inline_without_map={analysis['positions']['inline_tokens_without_map']}",
        ),
        "multi_file": feat(
            "部分支持",
            "parse() 只接受字符串；include 需调用层自行拼接/递归解析并维护行号偏移",
            "自行维护",
            "库本身无 include 机制",
        ),
        "error_diagnostics": feat(
            "不支持",
            "未闭合 ::: 无异常无警告（容器静默吞到文末）；需自写预检",
            "n/a",
            f"container_runs_to_eof={analysis['unclosed_container']['container_runs_to_eof']}, "
            f"types={analysis['unclosed_container']['resulting_types']}",
        ),
        "determinism": feat(
            "支持", "同输入两次 parse token 流完全一致",
            "n/a",
            f"token_equal={analysis['determinism']['two_parses_token_equal']}",
        ),
    }


def write_results(results_dir: Path = RESULTS) -> dict[str, Any]:
    """跑一次完整分析并落盘 results/markdown-it-analysis.json，返回分析字典。"""
    results_dir.mkdir(exist_ok=True)
    analysis = analyze()
    analysis["features"] = extract_features(analysis)
    out = results_dir / "markdown-it-analysis.json"
    out.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    return analysis


def main() -> None:
    analysis = write_results()
    out = RESULTS / "markdown-it-analysis.json"
    print(f"markdown-it 分析完成 -> {out}")
    print(f"  版本: {analysis['versions']}")
    print(f"  容器识别: {analysis['containers']['count']}/6")
    print(f"  heading id 被 attrs 提取: {analysis['headings']['attrs_plugin_extracted_id']}")
    print(f"  footnote labels: {[d['label'] for d in analysis['footnotes']['defs']]}")
    print(f"  有序列表 start 保留: {analysis['lists']['start_preserved']}")
    print(f"  未闭合容器吞到文末: {analysis['unclosed_container']['container_runs_to_eof']}")
    print(f"  确定性: {analysis['determinism']['two_parses_token_equal']}")


if __name__ == "__main__":
    main()
