from __future__ import annotations

import importlib.util
import json
import os
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
BUILD_SIDECAR = ROOT / "scripts" / "build_sidecar.py"
VERIFY_DESKTOP = ROOT / "scripts" / "verify_desktop_distribution.py"
RELEASE_CONFIG = ROOT / "src-tauri" / "tauri.release.conf.json"
WORKFLOW = ROOT / ".github" / "workflows" / "distribution.yml"
REAL_HTTP_CONFIG = ROOT / "frontend" / "e2e" / "real-http.playwright.config.ts"
WINDOWS_TAURI_ACCEPTANCE = (
    ROOT / "frontend" / "e2e" / "tauri-windows.acceptance.ts"
)
FRONTEND_PACKAGE = ROOT / "frontend" / "package.json"
WINDOWS_ICON = ROOT / "src-tauri" / "icons" / "icon.ico"
TAURI_LIB = ROOT / "src-tauri" / "src" / "lib.rs"


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
    assert base_config["bundle"]["icon"] == [
        "icons/icon.png",
        "icons/icon.ico",
    ]


def test_windows_resource_icon_is_packaged() -> None:
    assert WINDOWS_ICON.is_file()
    assert WINDOWS_ICON.read_bytes()[:4] == b"\x00\x00\x01\x00"


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


def test_desktop_verifier_forces_utf8_for_frozen_sidecar(
    monkeypatch,
) -> None:
    verifier = _load_module(VERIFY_DESKTOP, "verify_desktop_distribution_environment")
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")
    monkeypatch.setenv("PYTHONUTF8", "0")

    environment = verifier._offline_environment()

    assert environment["PYTHONIOENCODING"] == "utf-8"
    assert environment["PYTHONUTF8"] == "1"


def test_desktop_verifier_decodes_sidecar_output_as_utf8(
    monkeypatch,
    tmp_path: Path,
) -> None:
    verifier = _load_module(VERIFY_DESKTOP, "verify_desktop_distribution_subprocess")
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        observed.update(kwargs)
        return SimpleNamespace(returncode=0, stdout='{"ok": true}\n', stderr="")

    monkeypatch.setattr(verifier.subprocess, "run", fake_run)

    verifier._run_sidecar(
        tmp_path / "thesisforge-sidecar.exe",
        {"operation": "inspect"},
        stream=False,
        cwd=tmp_path,
        environment={},
    )

    assert observed["encoding"] == "utf-8"


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
        ("macos-14", "aarch64-apple-darwin", "app"),
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
    dmg_step = next(
        step
        for step in desktop["steps"]
        if step.get("name") == "Build macOS DMG with diagnostics"
    )
    assert "--bundles dmg" in dmg_step["run"]
    assert "--ci" in dmg_step["run"]
    assert "-vv" in dmg_step["run"]
    assert "for attempt in 1 2 3" in dmg_step["run"]
    assert 'rm -rf "$dmg_bundle_dir"' in dmg_step["run"]
    assert 'app_bundle_dir="src-tauri/target/${{ matrix.target }}/release/bundle/macos/ThesisForge.app"' in dmg_step["run"]
    assert 'app_backup_dir="${RUNNER_TEMP}/ThesisForge.app"' in dmg_step["run"]
    assert 'ditto "$app_bundle_dir" "$app_backup_dir"' in dmg_step["run"]
    assert 'ditto "$app_backup_dir" "$app_bundle_dir"' in dmg_step["run"]


def test_windows_workflow_installs_and_drives_the_native_tauri_package() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["desktop"]["steps"]
    workflow_text = WORKFLOW.read_text(encoding="utf-8")

    assert "cargo install tauri-driver" not in workflow_text
    assert "msiexec.exe" in workflow_text
    assert "THESISFORGE_WINDOWS_APP" in workflow_text
    assert "THESISFORGE_BLOCK_NETWORK" in workflow_text
    assert "THESISFORGE_WINDOWS_CDP_PORT" in workflow_text
    assert "e2e:tauri:windows" in workflow_text
    assert "windows-native-evidence" in workflow_text

    assert not any(
        step.get("name") == "Probe installed Windows application"
        for step in steps
    )

    diagnostics_step = next(
        step
        for step in steps
        if step.get("name") == "Collect Windows native acceptance diagnostics"
    )
    assert diagnostics_step["if"] == "runner.os == 'Windows' && always()"
    assert "Get-CimInstance Win32_Process" in diagnostics_step["run"]
    assert "Get-WinEvent" in diagnostics_step["run"]
    assert "/json/version" in diagnostics_step["run"]
    assert "windows-cdp-endpoint.json" in diagnostics_step["run"]
    assert "windows-processes.json" in diagnostics_step["run"]
    assert "windows-application-events.json" in diagnostics_step["run"]

    acceptance_step = next(
        step
        for step in steps
        if step.get("name") == "Run installed Windows native acceptance"
    )
    assert "Tee-Object" in acceptance_step["run"]
    assert "playwright-cdp.log" in acceptance_step["run"]
    assert "$LASTEXITCODE" in acceptance_step["run"]

    evidence_upload = next(
        step
        for step in steps
        if step.get("uses") == "actions/upload-artifact@v4"
        and step.get("with", {}).get("name") == "windows-native-evidence"
    )
    assert evidence_upload["if"] == "runner.os == 'Windows' && always()"
    assert "${{ runner.temp }}/windows-native-evidence" in evidence_upload["with"]["path"]
    assert "${{ runner.temp }}/thesisforge-windows-install.log" in evidence_upload["with"]["path"]


def test_windows_tauri_acceptance_uses_webview2_cdp_and_real_commands() -> None:
    acceptance = WINDOWS_TAURI_ACCEPTANCE.read_text(encoding="utf-8")

    assert "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS" not in acceptance
    assert "THESISFORGE_WINDOWS_CDP_PORT" in acceptance
    assert "chromium.connectOverCDP" in acceptance
    assert "http://127.0.0.1:" in acceptance
    assert "spawn(appBinaryPath" in acceptance
    assert "taskkill.exe" in acceptance
    assert "__TAURI_INTERNALS__" in acceptance
    assert 'command === "pick_source"' in acceptance
    assert "打开 Markdown 文稿" in acceptance
    assert "保存文稿" in acceptance
    assert "构建 DOCX" in acceptance
    assert "Markdown 文稿内容" in acceptance
    assert "构建完成" in acceptance
    assert "page.screenshot" in acceptance
    assert "prefers-reduced-motion" in acceptance
    assert "THESISFORGE_WINDOWS_EVIDENCE" in acceptance


def test_tauri_window_owner_enables_cdp_only_for_native_acceptance() -> None:
    config = json.loads(
        (ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    )
    tauri_lib = TAURI_LIB.read_text(encoding="utf-8")

    assert config["app"]["windows"][0]["create"] is False
    assert "WebviewWindowBuilder::from_config" in tauri_lib
    assert "windows_acceptance_browser_args" in tauri_lib
    assert ".additional_browser_args(&browser_args)" in tauri_lib
    assert "THESISFORGE_WINDOWS_CDP_PORT" in tauri_lib


def test_windows_tauri_acceptance_captures_processes_before_termination() -> None:
    acceptance = WINDOWS_TAURI_ACCEPTANCE.read_text(encoding="utf-8")

    snapshot = 'path.join(evidenceDirectory, "windows-processes-before-stop.json")'
    assert snapshot in acceptance
    assert "Get-CimInstance Win32_Process" in acceptance
    assert acceptance.index(snapshot) < acceptance.index("stopInstalledApp(app)")


def test_windows_tauri_acceptance_uses_existing_playwright_toolchain() -> None:
    package = json.loads(FRONTEND_PACKAGE.read_text(encoding="utf-8"))
    dev_dependencies = package["devDependencies"]
    assert package["scripts"]["e2e:tauri:windows"] == (
        "tsx e2e/tauri-windows.acceptance.ts"
    )
    assert dev_dependencies["@playwright/test"] == "1.62.1"
    assert dev_dependencies["tsx"] == "4.23.1"
    assert all("wdio" not in name for name in dev_dependencies)
    assert "webdriverio" not in dev_dependencies
    assert "pnpm" not in package


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
