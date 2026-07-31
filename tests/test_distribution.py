from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _installed_module_path() -> str:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import pathlib, thesis_forge; print(pathlib.Path(thesis_forge.__file__).resolve())",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def test_distribution_builds_and_installed_cli_runs_offline(tmp_path: Path) -> None:
    module_before = _installed_module_path()
    dist_dir = tmp_path / "dist"
    build = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(dist_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stdout + build.stderr

    verification = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_distribution.py"),
            "--dist-dir",
            str(dist_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert verification.returncode == 0, verification.stdout + verification.stderr
    evidence = json.loads(verification.stdout)
    assert evidence["ok"] is True
    installed = evidence["installed"]
    assert installed["hermetic"] is True
    distributions = {
        name.lower().replace("_", "-")
        for name in installed["dependencies"]["distributions"]
    }
    assert {
        "lxml",
        "pydantic",
        "python-docx",
        "pyyaml",
        "rich",
        "typer",
    } <= distributions
    assert not {"build", "hatchling", "packaging", "pytest", "ruff"} & distributions
    assert all("/thesisforge-dist-" in path for path in installed["imports"].values())
    assert not any(str(ROOT) in path for path in installed["sys_path"])
    assert _installed_module_path() == module_before
