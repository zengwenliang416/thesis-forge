from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

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
            "import pathlib, docforge; print(pathlib.Path(docforge.__file__).resolve())",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def _write_test_wheel(
    path: Path,
    verifier,
    *,
    entry_points: str = "[console_scripts]\ndocforge = docforge.cli:app\n",
    omitted_file: str | None = None,
    runtime_requirements: set[str] | None = None,
    extra_files: set[str] | None = None,
) -> None:
    requirements = (
        verifier.EXPECTED_RUNTIME_DISTRIBUTIONS
        if runtime_requirements is None
        else runtime_requirements
    )
    with zipfile.ZipFile(path, "w") as archive:
        for name in verifier.REQUIRED_WHEEL_FILES:
            if name != omitted_file:
                archive.writestr(name, "")
        archive.writestr("docforge-0.1.0.dist-info/entry_points.txt", entry_points)
        metadata = "Metadata-Version: 2.4\nName: docforge\nVersion: 0.1.0\n"
        metadata += "".join(
            f"Requires-Dist: {requirement}\n" for requirement in sorted(requirements)
        )
        archive.writestr("docforge-0.1.0.dist-info/METADATA", metadata)
        for name in extra_files or ():
            archive.writestr(name, "")


def test_distribution_verifier_rejects_missing_bundled_template(
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_templates")
    wheel = tmp_path / "docforge-0.1.0-py3-none-any.whl"
    missing = (
        "docforge/template_data/schools/"
        "hunan-university-of-technology/master-2026.yaml"
    )
    _write_test_wheel(wheel, verifier, omitted_file=missing)

    with pytest.raises(RuntimeError, match="misses package data"):
        verifier._inspect_wheel(wheel)


def test_distribution_verifier_rejects_extra_console_alias(
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_entrypoints")
    wheel = tmp_path / "docforge-0.1.0-py3-none-any.whl"
    _write_test_wheel(
        wheel,
        verifier,
        entry_points=(
            "[console_scripts]\n"
            "docforge = docforge.cli:app\n"
            "thesisforge = docforge.cli:app\n"
        ),
    )

    with pytest.raises(RuntimeError, match="unexpected console entry points"):
        verifier._inspect_wheel(wheel)


def test_distribution_verifier_rejects_missing_runtime_requirement(
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_requirements")
    wheel = tmp_path / "docforge-0.1.0-py3-none-any.whl"
    requirements = verifier.EXPECTED_RUNTIME_DISTRIBUTIONS - {"lxml"}
    _write_test_wheel(wheel, verifier, runtime_requirements=requirements)

    with pytest.raises(RuntimeError, match="unexpected runtime requirements"):
        verifier._inspect_wheel(wheel)


def test_distribution_verifier_rejects_obsolete_wheel_package(
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_old_wheel")
    wheel = tmp_path / "docforge-0.1.0-py3-none-any.whl"
    _write_test_wheel(wheel, verifier, extra_files={"thesis_forge/legacy.py"})

    with pytest.raises(RuntimeError, match="obsolete package files"):
        verifier._inspect_wheel(wheel)


def test_distribution_verifier_rejects_obsolete_sdist_package(
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_old_sdist")
    sdist = tmp_path / "docforge-0.1.0.tar.gz"
    root = "docforge-0.1.0"
    with tarfile.open(sdist, "w:gz") as archive:
        for relative in verifier.REQUIRED_SDIST_FILES | {"src/thesis_forge/legacy.py"}:
            data = b""
            info = tarfile.TarInfo(f"{root}/{relative}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))

    with pytest.raises(RuntimeError, match="obsolete package files"):
        verifier._inspect_sdist(sdist)


def test_distribution_verifier_forces_utf8_for_isolated_cli(
    monkeypatch,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_environment")
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")
    monkeypatch.setenv("PYTHONUTF8", "0")
    monkeypatch.setenv("PYTHONPATH", "/tmp/checkout")
    monkeypatch.setenv("PIP_FIND_LINKS", "http://127.0.0.1:1/")
    monkeypatch.setenv("PIP_INDEX_URL", "https://example.invalid/simple")
    monkeypatch.setenv("PIP_CONFIG_FILE", "/tmp/untrusted-pip.conf")

    environment = verifier._verification_environment()

    assert environment["PYTHONIOENCODING"] == "utf-8"
    assert environment["PYTHONUTF8"] == "1"
    assert environment["PIP_CONFIG_FILE"] == verifier.os.devnull
    assert "PIP_FIND_LINKS" not in environment
    assert "PIP_INDEX_URL" not in environment
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

    verifier._run(["docforge", "inspect"], cwd=tmp_path, env={})

    assert observed["encoding"] == "utf-8"
    assert observed["timeout"] == verifier.SUBPROCESS_TIMEOUT_SECONDS


def test_distribution_verifier_reports_subprocess_timeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_timeout")

    def timeout(command, **_kwargs):
        raise subprocess.TimeoutExpired(command, verifier.SUBPROCESS_TIMEOUT_SECONDS)

    monkeypatch.setattr(verifier.subprocess, "run", timeout)

    with pytest.raises(RuntimeError, match="Command timed out after 180s"):
        verifier._run(["docforge", "inspect"], cwd=tmp_path, env={})


def test_distribution_pip_command_uses_isolated_mode(tmp_path: Path) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_pip")
    python = tmp_path / "python"

    assert verifier._pip_command(python, "check") == [
        str(python),
        "-m",
        "pip",
        "--isolated",
        "check",
    ]


@pytest.mark.parametrize(
    "probe",
    [
        "socket.socket().connect_ex(('127.0.0.1', 9))",
        "socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(b'probe', ('127.0.0.1', 9))",
        "socket.getaddrinfo('example.com', 443)",
    ],
)
def test_distribution_network_guard_blocks_python_socket_paths(
    tmp_path: Path,
    probe: str,
) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_network")
    guard = verifier._write_network_guard(tmp_path / "guard")

    result = subprocess.run(
        [sys.executable, "-c", f"import socket; {probe}"],
        cwd=tmp_path,
        env=verifier._verification_environment()
        | {"PYTHONPATH": str(guard.parent)},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "network access blocked by distribution verification" in result.stderr


def test_distribution_uses_platform_console_launcher(tmp_path: Path) -> None:
    verifier = _load_module(VERIFY_DISTRIBUTION, "verify_distribution_launcher")

    windows_python, windows_cli = verifier._venv_executables(
        tmp_path,
        platform_name="nt",
    )
    posix_python, posix_cli = verifier._venv_executables(
        tmp_path,
        platform_name="posix",
    )

    assert windows_python == tmp_path / "Scripts" / "python.exe"
    assert windows_cli == tmp_path / "Scripts" / "docforge.exe"
    assert posix_python == tmp_path / "bin" / "python"
    assert posix_cli == tmp_path / "bin" / "docforge"


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
    assert installed["isolated_install"] is True
    assert installed["installer_network"] == "disabled-by-pip-no-index"
    assert installed["runtime_network_guard"] == "python-socket-apis"
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
    assert all("/docforge-dist-" in path for path in installed["imports"].values())
    assert not any(str(ROOT) in path for path in installed["sys_path"])
    assert set(installed["fixtures"]) == {"docforge-general", "docforge-academic"}
    for fixture in installed["fixtures"].values():
        assert fixture["inspect"] is True
        assert fixture["validate"] is True
        assert fixture["review"] is True
        assert fixture["build"] is True
        assert fixture["docx_bytes"] > 0
        assert fixture["review_markdown_bytes"] > 0
        assert fixture["review_map_bytes"] > 0
    assert _installed_module_path() == module_before
