"""Shared corpus metadata for the Phase 0 citation spike.

INTENDED_TYPES maps every corpus key to the GB/T 7714-2025 type marker the
entry is designed to exercise. Used by compare.py and build_golden.py.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CSL_JSON_PATH = ROOT / "corpus" / "gbt7714-corpus.csl.json"

INTENDED_TYPES: dict[str, str] = {
    "zh-article-3": "J",
    "zh-article-etal": "J",
    "en-article-etal": "J",
    "en-article-doi": "J",
    "zh-article-no-volume": "J",
    "zh-article-no-pages": "J",
    "en-article-online-first": "J",
    "mixed-article": "J",
    "zh-book": "M",
    "en-book-edition": "M",
    "zh-book-translator": "M",
    "org-book": "M",
    "zh-incollection": "M",
    "en-incollection": "M",
    "zh-inproceedings": "C",
    "en-inproceedings": "C",
    "collection-g": "G",
    "zh-newspaper": "N",
    "zh-mastersthesis": "D",
    "zh-phdthesis": "D",
    "zh-techreport": "R",
    "standard-gb": "S",
    "zh-patent": "P",
    "zh-online": "EB/OL",
    "en-online-noauthor": "EB/OL",
    "zh-dataset": "DS",
    "zh-map": "CM",
    "zh-archive": "A",
}

TYPE_COVERAGE_NOTES: dict[str, str] = {
    "collection-g": "GB/T 7714 汇编 [G]；官方 2025 CSL 无 [G] 分支（pandoc 映射为 book → [M]）",
    "standard-gb": "GB/T 7714 标准 [S]；pandoc 将 @standard 映射为 CSL legislation → 兜底 [Z]",
    "zh-map": "GB/T 7714 舆图 [CM]；pandoc 不识别 @map（CSL type 为空）→ 兜底 [Z]",
}


def load_result(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def load_csl_json() -> dict[str, dict]:
    items = json.loads(CSL_JSON_PATH.read_text(encoding="utf-8"))
    return {str(item["id"]): item for item in items}


def corpus_keys_in_bib_order() -> list[str]:
    return list(load_csl_json().keys())
