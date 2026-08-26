from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _source_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    return environment


def test_pyproject_exposes_only_docforge_distribution_and_command() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["name"] == "docforge"
    assert pyproject["project"]["scripts"] == {"docforge": "docforge.cli:app"}
    assert pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "src/docforge"
    ]


def test_source_tree_exposes_only_docforge_import_package(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            (
                "import importlib.util, json; "
                "print(json.dumps({"
                "'docforge': importlib.util.find_spec('docforge') is not None, "
                "'thesis_forge': importlib.util.find_spec('thesis_forge') is not None"
                "}))"
            ),
        ],
        cwd=tmp_path,
        env=_source_environment(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {
        "docforge": True,
        "thesis_forge": False,
    }


def test_docforge_cli_help_is_neutral_and_lists_core_commands(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from typer.testing import CliRunner; "
                "from docforge.cli import app; "
                "result = CliRunner().invoke(app, ['--help']); "
                "print(result.stdout); "
                "raise SystemExit(result.exit_code)"
            ),
        ],
        cwd=tmp_path,
        env=_source_environment(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "DocForge" in result.stdout
    assert "ThesisForge" not in result.stdout
    for command in ("inspect", "validate", "review", "build"):
        assert command in result.stdout
