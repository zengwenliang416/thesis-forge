"""用项目现有 LaTeX 子集转换器逐条转换语料库公式，记录成功/失败与失败原因。

复跑：
    .venv/bin/python spikes/phase0/omml/convert_thesisforge.py

输出：spikes/phase0/omml/results/thesisforge_conversion.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

SPIKE_DIR = Path(__file__).resolve().parent
ROOT = SPIKE_DIR.parents[2]
SRC = ROOT / "src"

try:
    from thesis_forge.core.math import (
        LatexMathConverter,
        MathSyntaxError,
        UnsupportedMathError,
    )
except ModuleNotFoundError:  # 未安装包时退回 src 布局
    sys.path.insert(0, str(SRC))
    from thesis_forge.core.math import (
        LatexMathConverter,
        MathSyntaxError,
        UnsupportedMathError,
    )

CORPUS = SPIKE_DIR / "corpus" / "formulas.yaml"
RESULTS = SPIKE_DIR / "results"


def convert_one(converter: LatexMathConverter, latex: str) -> dict[str, object]:
    try:
        converter.convert(latex)
    except UnsupportedMathError as error:
        return {
            "status": "unsupported",
            "error_type": "UnsupportedMathError",
            "command": error.command,
            "message": str(error),
        }
    except MathSyntaxError as error:
        return {
            "status": "syntax_error",
            "error_type": "MathSyntaxError",
            "command": None,
            "message": str(error),
        }
    except Exception as error:  # noqa: BLE001 - spike 需要记录一切意外
        return {
            "status": "error",
            "error_type": type(error).__name__,
            "command": None,
            "message": str(error),
        }
    return {"status": "success", "error_type": None, "command": None, "message": None}


def main() -> None:
    corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))
    converter = LatexMathConverter()
    entries = []
    for item in corpus["formulas"]:
        result = convert_one(converter, item["latex"])
        entries.append({"id": item["id"], "latex": item["latex"], **result})

    success = sum(1 for entry in entries if entry["status"] == "success")
    failure_commands: dict[str, int] = {}
    for entry in entries:
        if entry["status"] == "unsupported":
            command = str(entry["command"])
            failure_commands[command] = failure_commands.get(command, 0) + 1
    summary = {
        "total": len(entries),
        "success": success,
        "failed": len(entries) - success,
        "coverage": round(success / len(entries), 4),
        "failure_commands": dict(
            sorted(failure_commands.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        "syntax_error_count": sum(
            1 for entry in entries if entry["status"] == "syntax_error"
        ),
    }

    RESULTS.mkdir(exist_ok=True)
    output = RESULTS / "thesisforge_conversion.json"
    output.write_text(
        json.dumps({"summary": summary, "entries": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"total={summary['total']} success={summary['success']} failed={summary['failed']}")
    print(f"coverage={summary['coverage']:.2%}")
    print(f"failure_commands={json.dumps(summary['failure_commands'], ensure_ascii=False)}")
    print(f"-> {output}")


if __name__ == "__main__":
    main()
