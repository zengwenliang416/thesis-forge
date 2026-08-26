from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
BUILD_SIDECAR = ROOT / "scripts" / "build_sidecar.py"
VERIFY_DESKTOP = ROOT / "scripts" / "verify_desktop_distribution.py"
PREPARE_RELEASE = ROOT / "scripts" / "prepare_release.py"
RELEASE_CONFIG = ROOT / "src-tauri" / "tauri.release.conf.json"
WORKFLOW = ROOT / ".github" / "workflows" / "distribution.yml"
WOODPECKER_QUALITY = ROOT / ".woodpecker" / "quality.yml"
WOODPECKER_MACOS_RELEASE = ROOT / ".woodpecker" / "release-macos.yml"
WOODPECKER_RELEASE_PUBLISH = ROOT / ".woodpecker" / "release-publish.yml"
PYTHON_CI_LOCK = ROOT / "requirements" / "ci-python312.txt"
PYTHON_CI_INPUT = ROOT / "scripts" / "ci-python312.in"
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
    assert config["bundle"]["macOS"]["signingIdentity"] == "-"
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
    assert command.count("--add-data") == 5
    assert any("docx/parts" in value for value in command)
    assert any("templates/base/bachelor.yaml" in value for value in command)
    assert any("templates/schools/example-university/2026.yaml" in value for value in command)
    assert any(
        "templates/schools/hunan-university-of-technology/master-2026.yaml" in value
        for value in command
    )
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
    force_include = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]
    package_sources = {
        source.relative_to(ROOT).as_posix()
        for source, _destination in builder.PACKAGE_DATA
    }
    assert package_sources == set(force_include)
    assert force_include[
        "templates/schools/hunan-university-of-technology/master-2026.yaml"
    ] == (
        "thesis_forge/template_data/schools/"
        "hunan-university-of-technology/master-2026.yaml"
    )


def test_sidecar_builder_keeps_pyinstaller_work_outside_checkout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    builder = _load_module(BUILD_SIDECAR, "build_sidecar_temp_root")
    observed: dict[str, Path] = {}

    def fake_run(command, **_kwargs):
        for option in ("--distpath", "--workpath", "--specpath"):
            path = Path(command[command.index(option) + 1])
            observed[option] = path
            assert not path.is_relative_to(ROOT)
        dist_path = observed["--distpath"]
        dist_path.mkdir(parents=True)
        (dist_path / "thesisforge-sidecar").write_bytes(b"sidecar")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(builder, "host_target_triple", lambda: "aarch64-apple-darwin")
    monkeypatch.setattr(builder.subprocess, "run", fake_run)

    sidecar = builder.build_sidecar(
        target_triple="aarch64-apple-darwin",
        output_directory=tmp_path / "binaries",
        python=Path("/tmp/python"),
    )

    assert sidecar.read_bytes() == b"sidecar"
    assert set(observed) == {"--distpath", "--workpath", "--specpath"}


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


def test_desktop_verifier_uses_canonical_v2_fixture_and_strict_build_reports() -> None:
    verifier = _load_module(VERIFY_DESKTOP, "verify_desktop_distribution_contract")

    assert verifier.CANONICAL_PROJECT == ROOT / "tests" / "fixtures" / "v2-project"
    assert (verifier.CANONICAL_PROJECT / "thesisforge.yaml").is_file()
    assert (verifier.CANONICAL_PROJECT / "thesis.md").read_text(
        encoding="utf-8"
    ).splitlines()[0] == "# 绪论 {#chap:introduction}"

    canceled = verifier._require_build_report(
        [
            {
                "type": "completed",
                "report": {
                    "schemaVersion": "thesisforge.build-report.v2",
                    "outcome": "canceled",
                },
            }
        ],
        outcome="canceled",
        label="canceled",
    )
    assert canceled["outcome"] == "canceled"

    succeeded = verifier._require_build_report(
        [
            {
                "type": "completed",
                "report": {
                    "schemaVersion": "thesisforge.build-report.v2",
                    "outcome": "succeeded",
                },
            }
        ],
        outcome="succeeded",
        label="succeeded",
    )
    assert succeeded["outcome"] == "succeeded"

    with pytest.raises(RuntimeError, match="legacy"):
        verifier._require_build_report(
            [{"type": "success", "result": {}}],
            outcome="succeeded",
            label="legacy",
        )


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


def test_woodpecker_quality_gate_runs_for_release_tags() -> None:
    workflow = yaml.safe_load(WOODPECKER_QUALITY.read_text(encoding="utf-8"))

    assert workflow["labels"] == {
        "location": "production-80",
        "platform": "linux/amd64",
        "backend": "docker",
    }
    assert {
        condition["event"]
        for condition in workflow["when"]
        if isinstance(condition, dict)
    } >= {"pull_request", "push", "tag", "manual"}
    tag_condition = next(
        condition for condition in workflow["when"] if condition.get("event") == "tag"
    )
    assert tag_condition["ref"] == "refs/tags/v*"
    assert workflow["clone"]["git"]["image"].startswith(
        "woodpeckerci/plugin-git:2.9.2@sha256:"
    )
    assert all("@sha256:" in step["image"] for step in workflow["steps"])
    python_commands = "\n".join(
        next(step for step in workflow["steps"] if step["name"] == "python-quality")[
            "commands"
        ]
    )
    assert (
        "python -m pip install --require-hashes -r requirements/ci-python312.txt"
        in python_commands
    )
    assert (
        "python -m pip install --no-deps --no-build-isolation -e ."
        in python_commands
    )
    assert "python -m pip check" in python_commands
    assert 'pip install -e ".[dev]"' not in python_commands
    rust_commands = "\n".join(
        next(step for step in workflow["steps"] if step["name"] == "rust-quality")[
            "commands"
        ]
    )
    assert "cargo test --locked" in rust_commands
    assert "cargo check --locked" in rust_commands


def test_woodpecker_macos_release_is_tag_only_and_quality_gated() -> None:
    workflow = yaml.safe_load(WOODPECKER_MACOS_RELEASE.read_text(encoding="utf-8"))

    assert workflow["depends_on"] == ["quality"]
    assert workflow["skip_clone"] is True
    assert workflow["labels"] == {
        "platform": "darwin/arm64",
        "backend": "local",
        "purpose": "thesisforge-release",
        "repo": "zengwenliang416/thesis-forge",
    }
    assert workflow["when"] == [{"event": "tag", "ref": "refs/tags/v*"}]

    checkout = next(
        step
        for step in workflow["steps"]
        if step["name"] == "checkout-release-source"
    )
    build = next(
        step for step in workflow["steps"] if step["name"] == "build-and-verify"
    )
    upload = next(
        step for step in workflow["steps"] if step["name"] == "upload-release-staging"
    )
    checkout_commands = "\n".join(checkout["commands"])
    build_commands = "\n".join(build["commands"])
    upload_commands = "\n".join(upload["commands"])
    tauri_build_command = next(
        command
        for command in build["commands"]
        if command.startswith("cargo tauri build ")
    )

    assert "scripts/prepare_release.py --tag" in build_commands
    assert "/Users/" not in WOODPECKER_MACOS_RELEASE.read_text(encoding="utf-8")
    assert 'test "$CI_REPO" = "zengwenliang416/thesis-forge"' in checkout_commands
    assert 'git fetch --no-tags origin "+refs/heads/main:' in checkout_commands
    assert 'git fetch --no-tags origin "+refs/tags/$CI_COMMIT_TAG:' in (
        checkout_commands
    )
    assert 'git rev-list -n 1 "$CI_COMMIT_TAG"' in checkout_commands
    assert 'git merge-base --is-ancestor "$CI_COMMIT_SHA" origin/main' in (
        checkout_commands
    )
    assert 'git checkout --detach "$CI_COMMIT_SHA"' in checkout_commands
    assert "--validate-only" in build_commands
    assert (
        "python -m pip install --require-hashes -r requirements/ci-python312.txt"
        in build_commands
    )
    assert (
        "python -m pip install --no-deps --no-build-isolation -e ."
        in build_commands
    )
    assert "python -m pip check" in build_commands
    assert 'pip install -e ".[dev]"' not in build_commands
    assert "scripts/verify_distribution.py" in build_commands
    assert "scripts/build_sidecar.py --target-triple aarch64-apple-darwin" in (
        build_commands
    )
    assert "scripts/verify_desktop_distribution.py" in build_commands
    assert "--bundles app,dmg" in build_commands
    assert "cargo tauri build --locked" not in tauri_build_command
    assert tauri_build_command.endswith(" -- --locked")
    assert "find src-tauri/target" in build_commands
    assert "codesign --verify --deep --strict" in build_commands
    assert "spctl --assess" in build_commands
    assert "hdiutil verify" in build_commands
    assert build_commands.count("find src-tauri/target") == 2

    assert "GH_TOKEN" not in WOODPECKER_MACOS_RELEASE.read_text(encoding="utf-8")
    assert upload["environment"]["AWS_ACCESS_KEY_ID"] == {
        "from_secret": "release_staging_write_access_key"
    }
    assert upload["environment"]["RELEASE_STAGING_ENDPOINT"] == {
        "from_secret": "release_staging_write_endpoint"
    }
    assert "pip install" not in upload_commands
    assert "aws-cli/2.36.30" in upload_commands
    assert 's3 cp dist/release/' in upload_commands
    assert 's3 cp dist/release-evidence/' in upload_commands
    assert "/evidence/macos/" in upload_commands


def test_woodpecker_publish_downloads_verified_assets_on_linux() -> None:
    workflow = yaml.safe_load(WOODPECKER_RELEASE_PUBLISH.read_text(encoding="utf-8"))
    quality = yaml.safe_load(WOODPECKER_QUALITY.read_text(encoding="utf-8"))

    assert workflow["depends_on"] == ["release-macos"]
    assert workflow["clone"]["git"]["image"] == quality["clone"]["git"]["image"]
    assert "@sha256:" in workflow["clone"]["git"]["image"]
    assert workflow["labels"] == {
        "location": "production-80",
        "platform": "linux/amd64",
        "backend": "docker",
    }
    assert workflow["when"] == [{"event": "tag", "ref": "refs/tags/v*"}]

    download = next(
        step
        for step in workflow["steps"]
        if step["name"] == "download-and-verify-staging"
    )
    publish = next(
        step for step in workflow["steps"] if step["name"] == "publish-prerelease"
    )
    release_guard = next(
        step for step in workflow["steps"] if step["name"] == "reject-existing-release"
    )
    download_commands = "\n".join(download["commands"])
    release_guard_commands = "\n".join(release_guard["commands"])

    assert download["image"].startswith("amazon/aws-cli:2.36.30@sha256:")
    assert download["environment"]["RELEASE_STAGING_ENDPOINT"] == {
        "from_secret": "release_staging_read_endpoint"
    }
    assert 'test -f "ThesisForge_${version}_aarch64.dmg"' in download_commands
    assert "NR == 3" in download_commands
    assert "sha256sum -c SHA256SUMS" in download_commands
    assert "find . -maxdepth 1 -type f" in download_commands
    assert release_guard["image"].startswith("curlimages/curl:8.16.0@sha256:")
    assert release_guard["environment"]["GH_TOKEN"] == {
        "from_secret": "github_release_token"
    }
    assert "releases/tags/$CI_COMMIT_TAG" in release_guard_commands
    assert '"$status" != "404"' in release_guard_commands
    assert publish["image"].startswith(
        "woodpeckerci/plugin-release:0.3.1@sha256:"
    )
    assert publish["settings"]["api_key"] == {
        "from_secret": "github_release_token"
    }
    assert publish["settings"]["prerelease"] is True
    assert publish["settings"]["file_exists"] == "fail"


def test_python_ci_lock_is_hashed_universal_and_covers_declared_dependencies() -> None:
    lock_text = PYTHON_CI_LOCK.read_text(encoding="utf-8")
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "--generate-hashes" in lock_text
    assert "--python-version 3.12" in lock_text
    assert "--universal" in lock_text
    assert "scripts/ci-python312.in" in lock_text
    assert "--hash=sha256:" in lock_text

    ci_requirements = [
        line
        for line in PYTHON_CI_INPUT.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    declared = [
        *pyproject["project"]["dependencies"],
        *pyproject["project"]["optional-dependencies"]["dev"],
        *pyproject["build-system"]["requires"],
        *ci_requirements,
    ]
    locked_matches = list(
        re.finditer(r"(?m)^([A-Za-z0-9_.-]+)==([^\s;\\]+)", lock_text)
    )
    locked_versions = {
        canonicalize_name(match.group(1)): Version(match.group(2))
        for match in locked_matches
    }

    for requirement_text in declared:
        requirement = Requirement(requirement_text)
        locked_version = locked_versions[canonicalize_name(requirement.name)]
        assert locked_version in requirement.specifier
    for index, match in enumerate(locked_matches):
        end = (
            locked_matches[index + 1].start()
            if index + 1 < len(locked_matches)
            else len(lock_text)
        )
        assert "--hash=sha256:" in lock_text[match.start() : end]
    assert not re.search(r"(?m)^\s*-e\s+", lock_text)
    assert "@ file:" not in lock_text
    assert "file://" not in lock_text
    assert "/Users/" not in lock_text
    assert "/Volumes/" not in lock_text


def test_release_preparer_requires_consistent_versions_and_collects_assets(
    tmp_path: Path,
) -> None:
    preparer = _load_module(PREPARE_RELEASE, "prepare_release")

    assert preparer.validate_release_tag("v0.1.0") == "0.1.0"
    with pytest.raises(RuntimeError, match="must match"):
        preparer.validate_release_tag("v0.2.0")

    bundle_root = tmp_path / "bundle"
    dmg = bundle_root / "dmg" / "ThesisForge_0.1.0_aarch64.dmg"
    dmg.parent.mkdir(parents=True)
    dmg.write_bytes(b"dmg")
    python_dist = tmp_path / "python"
    python_dist.mkdir()
    wheel = python_dist / "thesis_forge-0.1.0-py3-none-any.whl"
    source_dist = python_dist / "thesis_forge-0.1.0.tar.gz"
    wheel.write_bytes(b"wheel")
    source_dist.write_bytes(b"source")

    output_dir = tmp_path / "release"
    assets = preparer.prepare_macos_release(
        tag="v0.1.0",
        bundle_root=bundle_root,
        python_dist=python_dist,
        output_dir=output_dir,
    )

    assert {path.name for path in assets} == {
        dmg.name,
        wheel.name,
        source_dist.name,
        "SHA256SUMS",
        "RELEASE_NOTES.md",
    }
    checksums = (output_dir / "SHA256SUMS").read_text(encoding="utf-8")
    assert dmg.name in checksums
    assert wheel.name in checksums
    assert source_dist.name in checksums
    assert "未公证预发布版本" in (
        output_dir / "RELEASE_NOTES.md"
    ).read_text(encoding="utf-8")


def test_release_preparer_rejects_appledouble_metadata(tmp_path: Path) -> None:
    preparer = _load_module(PREPARE_RELEASE, "prepare_release_pollution")
    bundle_root = tmp_path / "bundle"
    bundle_root.mkdir()
    (bundle_root / "._ThesisForge.dmg").write_bytes(b"metadata")

    with pytest.raises(RuntimeError, match="AppleDouble"):
        preparer.prepare_macos_release(
            tag="v0.1.0",
            bundle_root=bundle_root,
            python_dist=tmp_path / "python",
            output_dir=tmp_path / "release",
        )


def test_release_preparer_rejects_wrong_names_symlinks_and_stale_output(
    tmp_path: Path,
) -> None:
    preparer = _load_module(PREPARE_RELEASE, "prepare_release_hardening")
    bundle_root = tmp_path / "bundle"
    dmg_dir = bundle_root / "dmg"
    dmg_dir.mkdir(parents=True)
    (dmg_dir / "ThesisForge_9.9.9_x86_64.dmg").write_bytes(b"wrong")
    python_dist = tmp_path / "python"
    python_dist.mkdir()
    (python_dist / "thesis_forge-0.1.0-py3-none-any.whl").write_bytes(b"wheel")
    (python_dist / "thesis_forge-0.1.0.tar.gz").write_bytes(b"source")

    with pytest.raises(RuntimeError, match="macOS DMG"):
        preparer.prepare_macos_release(
            tag="v0.1.0",
            bundle_root=bundle_root,
            python_dist=python_dist,
            output_dir=tmp_path / "release-wrong-name",
        )

    wrong_dmg = dmg_dir / "ThesisForge_9.9.9_x86_64.dmg"
    wrong_dmg.unlink()
    outside = tmp_path / "outside.dmg"
    outside.write_bytes(b"outside")
    (dmg_dir / "ThesisForge_0.1.0_aarch64.dmg").symlink_to(outside)
    with pytest.raises(RuntimeError, match="symbolic link"):
        preparer.prepare_macos_release(
            tag="v0.1.0",
            bundle_root=bundle_root,
            python_dist=python_dist,
            output_dir=tmp_path / "release-symlink",
        )

    (dmg_dir / "ThesisForge_0.1.0_aarch64.dmg").unlink()
    (dmg_dir / "ThesisForge_0.1.0_aarch64.dmg").write_bytes(b"dmg")
    stale_output = tmp_path / "release-stale"
    stale_output.mkdir()
    (stale_output / "stale.dmg").write_bytes(b"stale")
    with pytest.raises(RuntimeError, match="must be empty"):
        preparer.prepare_macos_release(
            tag="v0.1.0",
            bundle_root=bundle_root,
            python_dist=python_dist,
            output_dir=stale_output,
        )


def test_release_preparer_cli_does_not_resolve_away_symlink_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preparer = _load_module(PREPARE_RELEASE, "prepare_release_cli_symlinks")
    real_bundle = tmp_path / "real-bundle"
    real_bundle.mkdir()
    bundle_link = tmp_path / "bundle-link"
    bundle_link.symlink_to(real_bundle, target_is_directory=True)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(PREPARE_RELEASE),
            "--tag",
            "v0.1.0",
            "--platform",
            "macos",
            "--bundle-root",
            str(bundle_link),
            "--python-dist",
            str(tmp_path / "python"),
            "--output-dir",
            str(tmp_path / "release"),
        ],
    )

    with pytest.raises(RuntimeError, match="root must not be a symbolic link"):
        preparer.main()


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


def test_distribution_workflow_retains_built_artifacts_after_acceptance_failure() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["desktop"]["steps"]
    expected_artifacts = {
        "thesisforge-web-${{ matrix.target }}",
        "thesisforge-python-${{ matrix.target }}",
        "thesisforge-sidecar-${{ matrix.target }}",
        "thesisforge-desktop-${{ matrix.target }}",
    }
    uploads = {
        step["with"]["name"]: step
        for step in steps
        if step.get("uses") == "actions/upload-artifact@v4"
        and step.get("with", {}).get("name") in expected_artifacts
    }

    assert set(uploads) == expected_artifacts
    for upload in uploads.values():
        assert upload["if"] == "always()"
        assert upload["with"]["if-no-files-found"] == "warn"


def test_distribution_workflow_pins_and_caches_the_tauri_cli() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    desktop = workflow["jobs"]["desktop"]
    steps = desktop["steps"]

    assert desktop["env"]["TAURI_CLI_VERSION"] == "2.11.4"
    restore = next(
        step
        for step in steps
        if step.get("uses") == "actions/cache/restore@v4"
    )
    install = next(
        step for step in steps if step.get("name") == "Install Tauri CLI"
    )
    save = next(
        step
        for step in steps
        if step.get("uses") == "actions/cache/save@v4"
    )
    verify = next(
        step for step in steps if step.get("name") == "Verify Tauri CLI"
    )

    assert restore["id"] == "tauri-cli-cache"
    assert "~/.cargo/bin/cargo-tauri" in restore["with"]["path"]
    assert "~/.cargo/bin/cargo-tauri.exe" in restore["with"]["path"]
    assert "${{ env.TAURI_CLI_VERSION }}" in restore["with"]["key"]
    assert install["if"] == "steps.tauri-cli-cache.outputs.cache-hit != 'true'"
    assert '--version "${{ env.TAURI_CLI_VERSION }}"' in install["run"]
    assert save["if"] == "steps.tauri-cli-cache.outputs.cache-hit != 'true'"
    assert save["with"] == restore["with"]
    assert verify["run"] == "cargo tauri --version"


def test_windows_tauri_acceptance_uses_webview2_cdp_and_real_commands() -> None:
    acceptance = WINDOWS_TAURI_ACCEPTANCE.read_text(encoding="utf-8")

    assert "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS" not in acceptance
    assert "THESISFORGE_WINDOWS_CDP_PORT" in acceptance
    assert "THESISFORGE_WINDOWS_ACCEPTANCE_SOURCE" in acceptance
    assert "chromium.connectOverCDP" in acceptance
    assert "http://127.0.0.1:" in acceptance
    assert "spawn(appBinaryPath" in acceptance
    assert "taskkill.exe" in acceptance
    assert "__TAURI_INTERNALS__" in acceptance
    assert 'internals.invoke = ' not in acceptance
    assert "打开 Markdown 或 DocForge 项目" in acceptance
    assert "保存文档" in acceptance
    assert "await save.isVisible()" in acceptance
    assert 'page.keyboard.press("Control+s")' in acceptance
    assert "生成 DOCX" in acceptance
    assert "Markdown 文档内容" in acceptance
    assert "构建完成" in acceptance
    assert "page.screenshot" in acceptance
    assert "windows-native-failure.png" in acceptance
    assert "windows-native-failure.html" in acceptance
    assert "windows-native-failure.json" in acceptance
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

    assert "CHANGE ?= template-v2-build-pipeline-p1" in makefile
    assert "WEB_DIST_DIR ?= dist/web" in makefile
    assert "PYTHON_DIST_DIR ?= dist/python" in makefile
    assert "SIDECAR_DIST_DIR ?= src-tauri/binaries" in makefile
    assert "package-web:" in makefile
    assert "package-sidecar:" in makefile
    assert "verify-desktop-dist:" in makefile


def test_release_files_do_not_embed_secrets_or_checkout_paths() -> None:
    paths = [
        BUILD_SIDECAR,
        VERIFY_DESKTOP,
        PREPARE_RELEASE,
        RELEASE_CONFIG,
        WORKFLOW,
        WOODPECKER_QUALITY,
        WOODPECKER_MACOS_RELEASE,
        WOODPECKER_RELEASE_PUBLISH,
        PYTHON_CI_LOCK,
        PYTHON_CI_INPUT,
    ]
    forbidden = (
        str(ROOT),
        "/Users/",
        "/Volumes/",
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
