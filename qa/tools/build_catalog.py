#!/usr/bin/env python3
"""用例目录索引生成工具。

扫描 qa/catalog/cases/*.yaml，结合 requirements.yaml 与 suites.yaml 生成
qa/catalog/index.json：用例总数、域分布、优先级分布、需求→用例映射与
未覆盖需求清单。输出确定性排序（不含时间戳），可入 Git 做差异审查。

用例 YAML 模型见 docs/update/QUALITY_STRATEGY.md 第 4 节。

用法：
    python qa/tools/build_catalog.py
    python qa/tools/build_catalog.py --catalog qa/catalog --output qa/catalog/index.json

退出码：0 成功；1 用例/需求/套件定义不合法；2 目录不可读。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

CASE_ID_RE = re.compile(r"^TF-D[1-6]-[A-Z]+-\d{3}$")

# QUALITY_STRATEGY 第 4 节用例模型的必备键（automation 为第 15 节要求的扩展）
CASE_REQUIRED_KEYS = (
    "id",
    "title",
    "version",
    "status",
    "domain",
    "priority",
    "requirements",
    "releases",
    "input",
    "steps",
    "expected",
    "evidence",
    "owners",
)
VALID_DOMAINS = frozenset({"D1", "D2", "D3", "D4", "D5", "D6"})
VALID_PRIORITIES = frozenset({"P0", "P1", "P2"})
VALID_STATUSES = frozenset({"active", "draft", "deprecated"})
VALID_AUTOMATION = frozenset({"automated", "manual", "planned"})


def _load_yaml(path: Path, errors: list[str]):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"{path}: 读取或解析失败: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: 顶层必须是 mapping")
        return None
    return data


def _validate_case(path: Path, case: dict, errors: list[str]) -> None:
    for key in CASE_REQUIRED_KEYS:
        if key not in case:
            errors.append(f"{path.name}: 缺少必备键 {key}")
    case_id = case.get("id")
    if isinstance(case_id, str):
        if not CASE_ID_RE.match(case_id):
            errors.append(f"{path.name}: 用例 ID 不符合 TF-D<域>-<领域>-<序号>: {case_id}")
        if case_id != path.stem:
            errors.append(f"{path.name}: 文件名必须与用例 ID 一致: {case_id}")
    domain = case.get("domain")
    if domain not in VALID_DOMAINS:
        errors.append(f"{path.name}: 非法 domain: {domain}")
    if case_id and domain in VALID_DOMAINS and f"D{case_id[4]}" != domain:
        errors.append(f"{path.name}: ID 域段与 domain 不一致: {case_id} vs {domain}")
    if case.get("priority") not in VALID_PRIORITIES:
        errors.append(f"{path.name}: 非法 priority: {case.get('priority')}")
    if case.get("status") not in VALID_STATUSES:
        errors.append(f"{path.name}: 非法 status: {case.get('status')}")
    if case.get("automation", "planned") not in VALID_AUTOMATION:
        errors.append(f"{path.name}: 非法 automation: {case.get('automation')}")
    if not isinstance(case.get("requirements"), list) or not case["requirements"]:
        errors.append(f"{path.name}: requirements 必须是非空列表")


def load_cases(cases_dir: Path, errors: list[str]) -> list[dict]:
    cases: list[dict] = []
    seen: dict[str, str] = {}
    for path in sorted(cases_dir.glob("*.yaml")):
        case = _load_yaml(path, errors)
        if case is None:
            continue
        _validate_case(path, case, errors)
        case_id = case.get("id")
        if isinstance(case_id, str):
            if case_id in seen:
                errors.append(f"{path.name}: 用例 ID 与 {seen[case_id]} 重复: {case_id}")
            seen[case_id] = path.name
        cases.append(case)
    return cases


def build_index(catalog_dir: Path) -> tuple[dict, list[str]]:
    """生成目录索引；返回 (index, errors)。"""
    errors: list[str] = []
    if not catalog_dir.is_dir():
        return {}, [f"目录不存在: {catalog_dir}"]

    requirements_doc = _load_yaml(catalog_dir / "requirements.yaml", errors) or {}
    requirements = requirements_doc.get("requirements") or []
    requirement_ids = [req.get("id") for req in requirements if isinstance(req, dict)]
    known_requirements = {req_id for req_id in requirement_ids if isinstance(req_id, str)}

    cases = load_cases(catalog_dir / "cases", errors)

    coverage: dict[str, list[str]] = {req_id: [] for req_id in sorted(known_requirements)}
    for case in cases:
        case_id = case.get("id")
        for req_id in case.get("requirements") or []:
            if req_id not in known_requirements:
                errors.append(f"{case_id}: 引用了未登记的需求 {req_id}")
            else:
                coverage[req_id].append(case_id)
    for covered in coverage.values():
        covered.sort()

    suites_doc = _load_yaml(catalog_dir / "suites.yaml", errors) or {}
    suites: dict[str, list[str]] = {}
    known_cases = {case.get("id") for case in cases}
    for suite in suites_doc.get("suites") or []:
        suite_id = suite.get("id")
        members = sorted(suite.get("cases") or [])
        for member in members:
            if member not in known_cases:
                errors.append(f"套件 {suite_id}: 引用了不存在的用例 {member}")
        if isinstance(suite_id, str):
            suites[suite_id] = members

    def _count_by(key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for case in cases:
            value = case.get(key)
            if isinstance(value, str):
                counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    index = {
        "version": 1,
        "cases": {
            "total": len(cases),
            "ids": sorted(case.get("id") for case in cases),
            "by_domain": _count_by("domain"),
            "by_priority": _count_by("priority"),
            "by_status": _count_by("status"),
            "by_automation": _count_by("automation"),
        },
        "requirements": {
            "total": len(known_requirements),
            "coverage": coverage,
            "uncovered": [req_id for req_id, covered in coverage.items() if not covered],
        },
        "suites": suites,
    }
    return index, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="用例目录索引生成工具")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "catalog",
        help="目录根（默认 qa/catalog）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="index.json 输出路径（默认 <catalog>/index.json）",
    )
    args = parser.parse_args(argv)

    if not args.catalog.is_dir():
        print(f"目录不存在: {args.catalog}", file=sys.stderr)
        return 2
    index, errors = build_index(args.catalog)
    if errors:
        for error in errors:
            print(f"错误: {error}", file=sys.stderr)
        return 1
    output = args.output or (args.catalog / "index.json")
    output.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    uncovered = index["requirements"]["uncovered"]
    print(
        f"已生成 {output}：用例 {index['cases']['total']} 个，"
        f"需求 {index['requirements']['total']} 条，未覆盖 {len(uncovered)} 条"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
