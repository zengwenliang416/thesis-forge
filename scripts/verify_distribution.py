#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import tempfile
import tomllib
import zipfile
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_WHEEL_FILES = {
    "thesis_forge/template_data/base/bachelor.yaml",
    "thesis_forge/template_data/schools/example-university/2026.yaml",
}
REQUIRED_SDIST_FILES = {
    "README.md",
    "pyproject.toml",
    "src/thesis_forge/cli.py",
    "templates/base/bachelor.yaml",
    "templates/schools/example-university/2026.yaml",
    "scripts/verify_distribution.py",
}
PROVENANCE_MODULES = (
    "thesis_forge",
    "docx",
    "lxml",
    "pydantic",
    "rich",
    "typer",
    "yaml",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return str(tomllib.load(stream)["project"]["version"])


def _distribution_paths(dist_dir: Path) -> tuple[Path, Path]:
    version = _project_version()
    wheel = dist_dir / f"thesis_forge-{version}-py3-none-any.whl"
    sdist = dist_dir / f"thesis_forge-{version}.tar.gz"
    missing = [str(path) for path in (wheel, sdist) if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing distribution artifacts: {', '.join(missing)}")
    return wheel, sdist


def _assert_no_appledouble(names: set[str], *, artifact: Path) -> None:
    polluted = sorted(name for name in names if Path(name).name.startswith("._"))
    if polluted:
        raise RuntimeError(f"{artifact.name} contains AppleDouble files: {polluted}")


def _inspect_wheel(wheel: Path) -> dict[str, object]:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        _assert_no_appledouble(names, artifact=wheel)
        missing = sorted(REQUIRED_WHEEL_FILES - names)
        if missing:
            raise RuntimeError(f"{wheel.name} misses package data: {missing}")

        entry_points = [
            name for name in names if name.endswith(".dist-info/entry_points.txt")
        ]
        if len(entry_points) != 1:
            raise RuntimeError(f"{wheel.name} has invalid entry point metadata")
        text = archive.read(entry_points[0]).decode("utf-8")
        if "thesisforge = thesis_forge.cli:app" not in text:
            raise RuntimeError(f"{wheel.name} misses the thesisforge console entry point")

    return {
        "path": str(wheel),
        "sha256": _sha256(wheel),
        "files": len(names),
    }


def _inspect_sdist(sdist: Path) -> dict[str, object]:
    with tarfile.open(sdist, "r:gz") as archive:
        names = {member.name for member in archive.getmembers() if member.isfile()}
    _assert_no_appledouble(names, artifact=sdist)
    roots = {name.split("/", 1)[0] for name in names}
    if len(roots) != 1:
        raise RuntimeError(f"{sdist.name} must contain one source root")
    root = next(iter(roots))
    relative_names = {
        name.removeprefix(f"{root}/") for name in names if name.startswith(f"{root}/")
    }
    missing = sorted(REQUIRED_SDIST_FILES - relative_names)
    if missing:
        raise RuntimeError(f"{sdist.name} misses maintenance sources: {missing}")
    return {
        "path": str(sdist),
        "sha256": _sha256(sdist),
        "files": len(names),
    }


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = "\n".join(part for part in (result.stdout, result.stderr) if part)
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return result


def _verification_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in tuple(environment):
        upper = key.upper()
        if (
            upper.endswith("_API_KEY")
            or upper in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"}
        ):
            environment.pop(key, None)
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"
    environment.pop("PYTHONPATH", None)
    return environment


def _normalize_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _runtime_distribution_names() -> tuple[str, ...]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        direct = tomllib.load(stream)["project"]["dependencies"]

    pending = list(direct)
    resolved: dict[str, str] = {}
    while pending:
        requirement = Requirement(pending.pop())
        if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
            continue
        requested = requirement.name
        normalized = _normalize_distribution_name(requested)
        if normalized in resolved:
            continue
        try:
            distribution = metadata.distribution(requested)
        except metadata.PackageNotFoundError as error:
            raise RuntimeError(
                f"Runtime dependency is not installed: {requested}"
            ) from error
        canonical = distribution.metadata["Name"] or requested
        resolved[normalized] = canonical
        for child in distribution.requires or ():
            try:
                child_requirement = Requirement(child)
                if child_requirement.marker and not child_requirement.marker.evaluate(
                    {"extra": ""}
                ):
                    continue
                metadata.distribution(child_requirement.name)
            except metadata.PackageNotFoundError:
                # Requirements behind a false environment/extra marker are not active.
                continue
            pending.append(child)
    return tuple(sorted(resolved.values(), key=str.lower))


def _copy_runtime_dependencies(target: Path) -> dict[str, object]:
    copied_files = 0
    distributions = _runtime_distribution_names()
    for name in distributions:
        distribution = metadata.distribution(name)
        source_root = Path(distribution.locate_file("")).resolve()
        for package_file in distribution.files or ():
            source = Path(distribution.locate_file(package_file))
            if not source.is_file():
                continue
            try:
                relative = source.resolve().relative_to(source_root)
            except ValueError:
                continue
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied_files += 1
    return {
        "distributions": list(distributions),
        "files": copied_files,
    }


def _write_offline_launcher(directory: Path, cli: Path) -> Path:
    launcher = directory / "offline_cli.py"
    launcher.write_text(
        "import runpy\n"
        "import socket\n"
        "import sys\n"
        "def blocked(*args, **kwargs):\n"
        "    raise RuntimeError('network access blocked by distribution verification')\n"
        "socket.create_connection = blocked\n"
        "socket.socket.connect = blocked\n"
        f"sys.argv = [{str(cli)!r}, *sys.argv[1:]]\n"
        f"runpy.run_path({str(cli)!r}, run_name='__main__')\n",
        encoding="utf-8",
    )
    return launcher


def _verify_installed_wheel(wheel: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="thesisforge-dist-") as raw_temp:
        temp = Path(raw_temp)
        install_root = temp / "install"
        scheme_vars = {
            "base": str(install_root),
            "platbase": str(install_root),
        }
        installed_site = Path(sysconfig.get_path("purelib", vars=scheme_vars))
        scripts_dir = Path(sysconfig.get_path("scripts", vars=scheme_vars))
        suffix = ".exe" if os.name == "nt" else ""
        cli = scripts_dir / f"thesisforge{suffix}"
        dependencies = _copy_runtime_dependencies(installed_site)

        base_env = _verification_environment()

        _run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                "--ignore-installed",
                "--prefix",
                str(install_root),
                str(wheel.resolve()),
            ],
            cwd=temp,
            env=base_env,
        )

        source = ROOT / "tests" / "fixtures" / "v2-project"
        workspace = temp / "workspace"
        shutil.copytree(source, workspace)
        launcher = _write_offline_launcher(temp, cli)
        offline_env = base_env | {"PYTHONPATH": str(installed_site)}

        import_result = _run(
            [
                sys.executable,
                "-S",
                "-c",
                (
                    "import importlib, json, sys; "
                    "from importlib import resources; "
                    f"names = {PROVENANCE_MODULES!r}; "
                    "modules = {name: importlib.import_module(name) for name in names}; "
                    "print(json.dumps({"
                    "'imports': {name: modules[name].__file__ for name in names}, "
                    "'sys_path': sys.path, "
                    "'templates': str(resources.files('thesis_forge') / 'template_data')"
                    "}))"
                ),
            ],
            cwd=workspace,
            env=offline_env,
        )
        installed = json.loads(import_result.stdout)
        import_paths = {
            name: Path(path).resolve() for name, path in installed["imports"].items()
        }
        escaped = {
            name: str(path)
            for name, path in import_paths.items()
            if installed_site.resolve() not in path.parents
        }
        if escaped:
            raise RuntimeError(f"Hermetic imports escaped the install prefix: {escaped}")
        checkout_paths = [
            path for path in installed["sys_path"] if ROOT == Path(path) or ROOT in Path(path).parents
        ]
        if checkout_paths:
            raise RuntimeError(f"Hermetic sys.path contains the checkout: {checkout_paths}")
        parent_sites = {
            Path(sysconfig.get_path(kind)).resolve()
            for kind in ("purelib", "platlib")
            if sysconfig.get_path(kind)
        }
        parent_leaks = [
            path
            for path in installed["sys_path"]
            if path and Path(path).resolve() in parent_sites
        ]
        if parent_leaks:
            raise RuntimeError(
                f"Hermetic sys.path contains parent site-packages: {parent_leaks}"
            )

        command = [sys.executable, "-S", str(launcher)]
        _run([*command, "inspect", str(workspace)], cwd=workspace, env=offline_env)
        _run([*command, "validate", str(workspace)], cwd=workspace, env=offline_env)
        output = workspace / "output" / "thesis.docx"
        _run(
            [*command, "build", str(workspace), "-o", str(output)],
            cwd=workspace,
            env=offline_env,
        )
        if not output.is_file() or not zipfile.is_zipfile(output):
            raise RuntimeError("Installed CLI did not produce a valid DOCX ZIP package")

        return {
            "hermetic": True,
            "dependencies": dependencies,
            "imports": {name: str(path) for name, path in import_paths.items()},
            "sys_path": installed["sys_path"],
            "templates": installed["templates"],
            "docx_bytes": output.stat().st_size,
            "docx_sha256": _sha256(output),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect ThesisForge distributions and verify the installed wheel offline."
    )
    parser.add_argument("--dist-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    wheel, sdist = _distribution_paths(args.dist_dir.resolve())
    evidence = {
        "ok": True,
        "wheel": _inspect_wheel(wheel),
        "sdist": _inspect_sdist(sdist),
        "installed": _verify_installed_wheel(wheel),
    }
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
