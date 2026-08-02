from __future__ import annotations

import importlib.util
import json
import os
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
BUILD_SIDECAR = ROOT / "scripts" / "build_sidecar.py"
VERIFY_DESKTOP = ROOT / "scripts" / "verify_desktop_distribution.py"
RELEASE_CONFIG = ROOT / "src-tauri" / "tauri.release.conf.json"
WORKFLOW = ROOT / ".github" / "workflows" / "distribution.yml"
REAL_HTTP_CONFIG = ROOT / "frontend" / "e2e" / "real-http.playwright.config.ts"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_config_bundles_one_managed_sidecar() -> None:
    config = json.loads(RELEASE_CONFIG.read_text(encoding="utf-8"))
    base_config = json.loads(
        (ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    )

    assert config["bundle"]["externalBin"] == ["binaries/thesisforge-sidecar"]
    assert "beforeBuildCommand" not in config.get("build", {})
    assert base_config["build"]["beforeDevCommand"] == "pnpm --dir frontend dev"
    assert base_config["build"]["beforeBuildCommand"] == "pnpm --dir frontend build"


def test_sidecar_builder_uses_native_target_specific_names() -> None:
    builder = _load_module(BUILD_SIDECAR, "build_sidecar")

    assert (
        builder.sidecar_binary_name("aarch64-apple-darwin")
        == "thesisforge-sidecar-aarch64-apple-darwin"
    )
    assert (
        builder.sidecar_binary_name("x86_64-pc-windows-msvc")
        == "thesisforge-sidecar-x86_64-pc-windows-msvc.exe"
    )
    with pytest.raises(ValueError, match="must be built on its native target"):
        builder.ensure_native_target(
            "aarch64-apple-darwin",
            "x86_64-pc-windows-msvc",
        )


def test_sidecar_builder_embeds_package_data_without_wheel_runtime_leakage() -> None:
    builder = _load_module(BUILD_SIDECAR, "build_sidecar_command")
    command = builder.pyinstaller_command(
        python=Path("/tmp/python"),
        entrypoint=Path("/tmp/entry.py"),
        dist_path=Path("/tmp/dist"),
        work_path=Path("/tmp/work"),
        spec_path=Path("/tmp/spec"),
    )

    assert "--onefile" in command
    assert "--clean" in command
    assert "--paths" in command
    assert str(ROOT / "src") in command
    assert "--collect-data" in command
    assert "docx" in command
    assert command.count("--add-data") == 3
    assert any("docx/parts" in value for value in command)
    assert any("templates/base/bachelor.yaml" in value for value in command)
    assert any("templates/schools/example-university/2026.yaml" in value for value in command)
    assert "socket.socket.connect_ex = blocked" in builder._entrypoint_text()

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert not any(
        dependency.lower().startswith("pyinstaller")
        for dependency in pyproject["project"]["dependencies"]
    )
    assert any(
        dependency.lower().startswith("pyinstaller")
        for dependency in pyproject["project"]["optional-dependencies"]["dev"]
    )


def test_desktop_verifier_maps_native_bundle_artifacts() -> None:
    verifier = _load_module(VERIFY_DESKTOP, "verify_desktop_distribution")

    assert verifier.required_bundle_suffixes("macos") == (".app", ".dmg")
    assert verifier.required_bundle_suffixes("windows") == (".msi", ".exe")
    assert verifier.managed_sidecar_name("macos") == "thesisforge-sidecar"
    assert verifier.managed_sidecar_name("windows") == "thesisforge-sidecar.exe"
    with pytest.raises(ValueError, match="Unsupported desktop platform"):
        verifier.required_bundle_suffixes("linux")


def test_desktop_verifier_rejects_cross_host_targets_and_sidecar_pollution(
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DESKTOP, "verify_desktop_distribution_pollution")
    sidecar = tmp_path / "thesisforge-sidecar-aarch64-apple-darwin"
    sidecar.write_bytes(b"sidecar")
    sidecar.chmod(0o755)
    (tmp_path / "._thesisforge-sidecar-aarch64-apple-darwin").write_bytes(
        b"metadata"
    )

    with pytest.raises(ValueError, match="must be built on its native target"):
        verifier.validate_native_target(
            "x86_64-pc-windows-msvc",
            host="aarch64-apple-darwin",
        )
    with pytest.raises(RuntimeError, match="AppleDouble"):
        verifier.validate_sidecar_artifact(sidecar)


def test_windows_bundle_verifier_finds_the_managed_sidecar_in_release_directory(
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DESKTOP, "verify_desktop_distribution_windows")
    release = tmp_path / "target" / "x86_64-pc-windows-msvc" / "release"
    bundle_root = release / "bundle"
    (bundle_root / "msi").mkdir(parents=True)
    (bundle_root / "nsis").mkdir()
    (bundle_root / "msi" / "ThesisForge.msi").write_bytes(b"MSI")
    (bundle_root / "nsis" / "ThesisForge-setup.exe").write_bytes(b"MZinstaller")
    managed_sidecar = release / "thesisforge-sidecar.exe"
    managed_sidecar.write_bytes(b"MZsidecar")

    evidence = verifier.verify_native_bundles(bundle_root, "windows")

    assert evidence["artifacts"]["managedSidecar"]["path"] == str(managed_sidecar)


def test_distribution_workflow_builds_native_macos_and_windows_artifacts() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    desktop = jobs["desktop"]
    matrix = desktop["strategy"]["matrix"]["include"]

    assert {
        (
            item["os"],
            item["target"],
            item["bundles"],
        )
        for item in matrix
    } == {
        ("macos-14", "aarch64-apple-darwin", "app,dmg"),
        ("windows-2025", "x86_64-pc-windows-msvc", "msi,nsis"),
    }
    commands = "\n".join(
        step.get("run", "")
        for step in desktop["steps"]
        if isinstance(step, dict)
    )
    assert "scripts/build_sidecar.py --target-triple" in commands
    assert "tauri.release.conf.json" in commands
    assert "scripts/verify_desktop_distribution.py" in commands
    assert "dot_clean -m" in commands
    assert "dist/web" in commands
    assert "dist/python" in commands


def test_real_http_acceptance_selects_a_native_python_interpreter() -> None:
    config = REAL_HTTP_CONFIG.read_text(encoding="utf-8")

    assert "THESISFORGE_PYTHON" in config
    assert 'process.platform === "win32"' in config
    assert ".venv/Scripts/python.exe" in config
    assert ".venv/bin/python" in config


def test_tauri_uses_packaged_sidecar_without_removing_development_overrides() -> None:
    cargo = tomllib.loads(
        (ROOT / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")
    )
    rust = (ROOT / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")

    assert "tauri-plugin-shell" in cargo["dependencies"]
    assert "ShellExt" in rust
    assert '.sidecar("thesisforge-sidecar")' in rust
    assert "THESISFORGE_SIDECAR_EXECUTABLE" in rust
    assert "THESISFORGE_PYTHON" in rust


def test_makefile_keeps_web_python_and_desktop_outputs_isolated() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "WEB_DIST_DIR ?= dist/web" in makefile
    assert "PYTHON_DIST_DIR ?= dist/python" in makefile
    assert "SIDECAR_DIST_DIR ?= src-tauri/binaries" in makefile
    assert "package-web:" in makefile
    assert "package-sidecar:" in makefile
    assert "verify-desktop-dist:" in makefile


def test_release_files_do_not_embed_secrets_or_checkout_paths() -> None:
    paths = [BUILD_SIDECAR, VERIFY_DESKTOP, RELEASE_CONFIG, WORKFLOW]
    forbidden = (
        str(ROOT),
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "sk-",
    )

    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not any(value in text for value in forbidden)
        assert not any(Path(part).name.startswith("._") for part in text.split())


@pytest.mark.skipif(os.name == "nt", reason="Unix executable mode assertion")
def test_generated_sidecar_directory_is_not_tracked() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "src-tauri/binaries/" in gitignore
