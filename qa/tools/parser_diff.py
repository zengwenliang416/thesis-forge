#!/usr/bin/env python3
"""双 parser 后端 diff 门禁脚手架（ADR-0001 Phase 2）。

把两个 ParserBackend 对同一 Markdown 输入产出的 ThesisDocument 归一化为
确定性 JSON（块类型序列、ID、inline 序列、行列号、metadata），逐字段 diff。

差异豁免机制（``--allow PATTERN=REASON``，可重复）：PATTERN 为匹配 diff
条目（``$.路径: 详情``）开头的正则，REASON 必填并逐条打印在报告中。
不允许宽泛忽略 location 等整类字段而不留记录——每条被豁免的差异都会
带着原因出现在输出里。

退出码：0 一致（含全部被豁免）/ 1 存在未豁免差异 / 2 运行错误
（未知后端、解析失败、非法 --allow 规格等）。
self-check：``--backend-a legacy --backend-b legacy`` 必须一致，
用于验证归一化的确定性。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thesis_forge.core.model import ThesisDocument
from thesis_forge.core.parser_backend import (
    get_parser_backend,
    parser_backend_names,
)

MAX_DIFF_ENTRIES = 100


def _jsonable(value: Any) -> Any:
    """递归转换为 JSON 可序列化且确定性的结构。

    非原生类型（Path、日期等 YAML 值）统一 str()，避免 default=str
    掩盖后端间的类型差异之外的排序问题；dict 键统一 str。
    """
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def normalize_document(document: ThesisDocument) -> dict[str, Any]:
    """把 ThesisDocument 归一化为确定性 JSON 结构。

    每个节点带 ``kind``（类名）+ 全部 dataclass 字段（含 id、location
    行列号、inlines 递归）；文档级带 metadata、bibliography 与
    inline_content / cross_references / citations / footnote_references 序列。
    source_path 只保留文件名，使报告跨机器稳定。
    """

    def tagged(node: Any) -> dict[str, Any]:
        return {"kind": type(node).__name__, **_jsonable(asdict(node))}

    return {
        "source_path": Path(document.source_path).name,
        "metadata": _jsonable(document.metadata),
        "bibliography": _jsonable(document.bibliography),
        "blocks": [tagged(block) for block in document.blocks],
        "inline_content": [tagged(inline) for inline in document.inline_content],
        "cross_references": [tagged(ref) for ref in document.cross_references],
        "citations": [tagged(citation) for citation in document.citations],
        "footnote_references": [tagged(ref) for ref in document.footnote_references],
    }


def dumps_normalized(normalized: dict[str, Any]) -> str:
    """确定性序列化：键排序、固定缩进、尾换行。"""
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def diff_values(a: Any, b: Any, path: str = "$", *, limit: int = MAX_DIFF_ENTRIES) -> list[str]:
    """逐字段递归 diff，返回 ``路径: 差异`` 文本列表，最多 limit 条。"""
    diffs: list[str] = []

    def walk(x: Any, y: Any, current: str) -> None:
        if len(diffs) >= limit:
            return
        if type(x) is not type(y):
            diffs.append(f"{current}: 类型不一致 {type(x).__name__} != {type(y).__name__}")
            return
        if isinstance(x, dict):
            for key in sorted(set(x) | set(y)):
                if key not in x:
                    diffs.append(f"{current}.{key}: 仅存在于后端 B: {y[key]!r}")
                elif key not in y:
                    diffs.append(f"{current}.{key}: 仅存在于后端 A: {x[key]!r}")
                else:
                    walk(x[key], y[key], f"{current}.{key}")
        elif isinstance(x, list):
            if len(x) != len(y):
                diffs.append(f"{current}: 长度不一致 {len(x)} != {len(y)}")
            for index, (item_x, item_y) in enumerate(zip(x, y)):
                walk(item_x, item_y, f"{current}[{index}]")
        elif x != y:
            diffs.append(f"{current}: {x!r} != {y!r}")

    walk(a, b, path)
    return diffs


@dataclass(frozen=True)
class AllowRule:
    """一条显式差异豁免规则。

    ``pattern`` 为匹配 diff 条目（``$.路径: 详情``）开头的正则；
    ``reason`` 必填，逐条随报告输出。豁免只应用于已知且已记录原因的
    差异（如两端位置列号策略差异），不允许宽泛吞掉整类字段而不留痕。
    """

    pattern: str
    reason: str

    def matches(self, entry: str) -> bool:
        return re.match(self.pattern, entry) is not None


@dataclass(frozen=True)
class DiffReport:
    """diff 结果：``blocking`` 为未豁免差异，``allowed`` 为（条目, 豁免原因）。"""

    blocking: list[str]
    allowed: list[tuple[str, str]]

    @property
    def ok(self) -> bool:
        return not self.blocking


def diff_documents(
    a: Any,
    b: Any,
    *,
    allow: tuple[AllowRule, ...] | list[AllowRule] = (),
    limit: int = MAX_DIFF_ENTRIES,
) -> DiffReport:
    """对归一化结果做逐字段 diff，并按显式规则分流豁免项。"""
    blocking: list[str] = []
    allowed: list[tuple[str, str]] = []
    for entry in diff_values(a, b, limit=limit):
        rule = next((item for item in allow if item.matches(entry)), None)
        if rule is None:
            blocking.append(entry)
        else:
            allowed.append((entry, rule.reason))
    return DiffReport(blocking=blocking, allowed=allowed)


def parse_allow_spec(spec: str) -> AllowRule:
    """解析 ``--allow PATTERN=REASON``；REASON 必填，杜绝无注释豁免。"""
    pattern, sep, reason = spec.partition("=")
    if not sep or not pattern.strip() or not reason.strip():
        raise ValueError(f"--allow 需要 PATTERN=REASON 形式（原因必填）: {spec!r}")
    return AllowRule(pattern=pattern.strip(), reason=reason.strip())


def _parse_with(backend_name: str, source: Path) -> ThesisDocument:
    backend = get_parser_backend(backend_name)
    return backend.parse_file(source)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="双 parser 后端 ThesisDocument diff 门禁（ADR-0001）",
    )
    parser.add_argument("source", type=Path, help="Markdown 输入文件")
    parser.add_argument("--backend-a", default="legacy", help="后端 A（默认 legacy）")
    parser.add_argument("--backend-b", default="legacy", help="后端 B（默认 legacy）")
    parser.add_argument(
        "--dump-dir",
        type=Path,
        default=None,
        help="可选：把两个后端的归一化 JSON 写入该目录",
    )
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="PATTERN=REASON",
        help="豁免匹配 PATTERN（正则，匹配 diff 条目开头）的差异；REASON 必填，"
        "逐条打印在报告中。可重复。",
    )
    args = parser.parse_args(argv)

    try:
        allow_rules = [parse_allow_spec(spec) for spec in args.allow]
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    unknown = [
        name
        for name in (args.backend_a, args.backend_b)
        if name not in parser_backend_names()
    ]
    if unknown:
        available = ", ".join(parser_backend_names())
        print(f"error: 未知 parser 后端: {', '.join(unknown)}（可用: {available}）", file=sys.stderr)
        return 2

    try:
        document_a = _parse_with(args.backend_a, args.source)
        document_b = _parse_with(args.backend_b, args.source)
    # CLI 边界：任何后端解析失败都归一为退出码 2 + stderr 诊断。
    except Exception as error:  # noqa: BLE001
        print(f"error: 解析失败（{args.source}）：{error}", file=sys.stderr)
        return 2

    normalized_a = normalize_document(document_a)
    normalized_b = normalize_document(document_b)

    if args.dump_dir is not None:
        args.dump_dir.mkdir(parents=True, exist_ok=True)
        (args.dump_dir / f"{args.backend_a}.normalized.json").write_text(
            dumps_normalized(normalized_a), encoding="utf-8"
        )
        (args.dump_dir / f"{args.backend_b}.normalized.json").write_text(
            dumps_normalized(normalized_b), encoding="utf-8"
        )

    report = diff_documents(normalized_a, normalized_b, allow=allow_rules)
    for entry, reason in report.allowed:
        print(f"  ALLOWED: {entry}（豁免原因：{reason}）")
    if report.ok:
        print(
            f"OK: {args.backend_a} 与 {args.backend_b} 输出一致"
            f"（{len(document_a.blocks)} 个块，{len(document_a.inline_content)} 个 inline"
            f"，豁免 {len(report.allowed)} 条）"
        )
        return 0

    print(
        f"DIFF: {args.backend_a} 与 {args.backend_b} 输出不一致，"
        f"共 {len(report.blocking)} 处未豁免差异（上限 {MAX_DIFF_ENTRIES} 条，"
        f"另有 {len(report.allowed)} 条已豁免）："
    )
    for line in report.blocking:
        print(f"  {line}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
