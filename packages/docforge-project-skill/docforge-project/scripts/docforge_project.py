#!/usr/bin/env python3
"""Yao-visible bridge to the canonical Node importer."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = (
    "Stable Agent Skill entrypoint delegating to the shared Node importer."
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create or install a verified DocForge project Skill.",
    )
    parser.add_argument(
        "arguments",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to docforge-project.mjs.",
    )
    args = parser.parse_args()
    script = Path(__file__).with_name("docforge-project.mjs")
    completed = subprocess.run(
        ["node", str(script), *args.arguments],
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
