"""汇总 thesisforge 与 pandoc 两条链路的转换结果，生成覆盖率对照 JSON。

复跑（需先运行 convert_thesisforge.py 与 convert_pandoc.py）：
    .venv/bin/python spikes/phase0/omml/aggregate.py

输出：spikes/phase0/omml/results/coverage.json
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

SPIKE_DIR = Path(__file__).resolve().parent
CORPUS = SPIKE_DIR / "corpus" / "formulas.yaml"
RESULTS = SPIKE_DIR / "results"


def main() -> None:
    corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))["formulas"]
    thesisforge = json.loads(
        (RESULTS / "thesisforge_conversion.json").read_text(encoding="utf-8")
    )
    pandoc = json.loads(
        (RESULTS / "pandoc_conversion.json").read_text(encoding="utf-8")
    )
    tf_by_id = {entry["id"]: entry for entry in thesisforge["entries"]}
    pd_by_id = {entry["id"]: entry for entry in pandoc["entries"]}

    entries = []
    for formula in corpus:
        tf = tf_by_id[formula["id"]]
        pd = pd_by_id[formula["id"]]
        entries.append(
            {
                "id": formula["id"],
                "latex": formula["latex"],
                "category": formula["category"],
                "discipline": formula["discipline"],
                "scenario": formula["scenario"],
                "difficulty": formula["difficulty"],
                "usage": formula["usage"],
                "thesisforge": {
                    "status": tf["status"],
                    "error_type": tf["error_type"],
                    "command": tf["command"],
                    "message": tf["message"],
                },
                "pandoc": {"status": pd["status"], "stderr": pd["stderr"]},
            }
        )

    categories: dict[str, dict[str, int]] = {}
    for entry in entries:
        bucket = categories.setdefault(
            entry["category"],
            {"total": 0, "thesisforge_ok": 0, "pandoc_ok": 0},
        )
        bucket["total"] += 1
        bucket["thesisforge_ok"] += entry["thesisforge"]["status"] == "success"
        bucket["pandoc_ok"] += entry["pandoc"]["status"] == "success"

    both_fail = [
        entry["id"]
        for entry in entries
        if entry["thesisforge"]["status"] != "success"
        and entry["pandoc"]["status"] != "success"
    ]
    tf_only_fail = [
        entry["id"]
        for entry in entries
        if entry["thesisforge"]["status"] != "success"
        and entry["pandoc"]["status"] == "success"
    ]

    report = {
        "corpus_size": len(entries),
        "thesisforge": thesisforge["summary"],
        "pandoc": pandoc["summary"],
        "by_category": categories,
        "both_fail": both_fail,
        "thesisforge_fail_but_pandoc_ok": tf_only_fail,
        "entries": entries,
    }
    output = RESULTS / "coverage.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"corpus={report['corpus_size']}")
    print(
        "thesisforge: "
        f"{thesisforge['summary']['success']}/{thesisforge['summary']['total']} "
        f"({thesisforge['summary']['coverage']:.2%})"
    )
    print(
        "pandoc: "
        f"{pandoc['summary']['success']}/{pandoc['summary']['total']} "
        f"({pandoc['summary']['coverage']:.2%})"
    )
    print(f"both_fail={both_fail}")
    print(f"-> {output}")


if __name__ == "__main__":
    main()
