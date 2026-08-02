from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
VERIFY_DISTRIBUTION = ROOT / "scripts" / "verify_distribution.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_distribution_verifier_forces_utf8_for_isolated_cli(
    monkeypatch,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_environment")
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")
    monkeypatch.setenv("PYTHONUTF8", "0")
    monkeypatch.setenv("PYTHONPATH", "/tmp/checkout")

    environment = verifier._verification_environment()

    assert environment["PYTHONIOENCODING"] == "utf-8"
    assert environment["PYTHONUTF8"] == "1"
    assert "PYTHONPATH" not in environment


def test_distribution_verifier_decodes_subprocess_output_as_utf8(
    monkeypatch,
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_subprocess")
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        observed.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(verifier.subprocess, "run", fake_run)

    verifier._run(["thesisforge", "inspect"], cwd=tmp_path, env={})

    assert observed["encoding"] == "utf-8"


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
