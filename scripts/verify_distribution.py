#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import configparser
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import tomllib
import venv
import zipfile
from email.parser import BytesParser
from email.policy import default as email_policy
from importlib import metadata
from pathlib import Path
from xml.etree import ElementTree

from packaging.requirements import Requirement
from packaging.tags import Tag, sys_tags

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_WHEEL_FILES = {
    "docforge/template_data/base/bachelor.yaml",
    "docforge/template_data/base/docforge-standard.yaml",
    "docforge/template_data/schools/hunan-university-of-technology/master-2026.yaml",
    "docforge/template_data/schools/example-university/2026.yaml",
    "docforge/template_data/schools/project-proposal/2026.yaml",
}
EXPECTED_ENTRY_POINTS = {
    "console_scripts": {
        "docforge": "docforge.cli:app",
    },
}
EXPECTED_RUNTIME_DISTRIBUTIONS = {
    "lxml",
    "markdown-it-py",
    "mdit-py-plugins",
    "pydantic",
    "python-docx",
    "pyyaml",
    "rich",
    "typer",
}
REQUIRED_SDIST_FILES = {
    "README.md",
    "pyproject.toml",
    "src/docforge/cli.py",
    "templates/base/bachelor.yaml",
    "templates/base/docforge-standard.yaml",
    "templates/schools/example-university/2026.yaml",
    "scripts/verify_distribution.py",
}
PROVENANCE_MODULES = (
    "docforge",
    "docx",
    "lxml",
    "pydantic",
    "rich",
    "typer",
    "yaml",
)
OBSOLETE_WHEEL_PREFIXES = ("thesis_forge/",)
OBSOLETE_SDIST_PREFIXES = ("src/thesis_forge/",)
SUBPROCESS_TIMEOUT_SECONDS = 180
WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DISTRIBUTION_FIXTURE_EXPECTATIONS = {
    "docforge-general": {
        "required": ("DocForge 通用文档", "示例科技有限公司", "张三"),
        "forbidden": (
            "本科毕业论文",
            "硕士学位论文",
            "研究生：",
            "学号：",
            "指导教师：",
        ),
    },
    "docforge-academic": {
        "required": ("DocForge 学术文档", "示例大学", "20260001", "李教授"),
        "forbidden": (),
    },
}


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
    wheel = dist_dir / f"docforge-{version}-py3-none-any.whl"
    sdist = dist_dir / f"docforge-{version}.tar.gz"
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
        obsolete = sorted(
            name
            for name in names
            if any(name.startswith(prefix) for prefix in OBSOLETE_WHEEL_PREFIXES)
        )
        if obsolete:
            raise RuntimeError(f"{wheel.name} contains obsolete package files: {obsolete}")
        missing = sorted(REQUIRED_WHEEL_FILES - names)
        if missing:
            raise RuntimeError(f"{wheel.name} misses package data: {missing}")

        entry_points = [
            name for name in names if name.endswith(".dist-info/entry_points.txt")
        ]
        if len(entry_points) != 1:
            raise RuntimeError(f"{wheel.name} has invalid entry point metadata")
        text = archive.read(entry_points[0]).decode("utf-8")
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(text)
        actual_entry_points = {
            section: dict(parser.items(section, raw=True))
            for section in parser.sections()
        }
        if actual_entry_points != EXPECTED_ENTRY_POINTS:
            raise RuntimeError(
                f"{wheel.name} has unexpected console entry points: "
                f"{actual_entry_points}"
            )
        requirements = _wheel_requirements(archive, wheel=wheel)
        requirement_names = {
            _normalize_distribution_name(requirement.name)
            for requirement in requirements
            if _requirement_is_active(requirement)
        }
        if requirement_names != EXPECTED_RUNTIME_DISTRIBUTIONS:
            raise RuntimeError(
                f"{wheel.name} has unexpected runtime requirements: "
                f"{sorted(requirement_names)}"
            )

    return {
        "path": str(wheel),
        "sha256": _sha256(wheel),
        "files": len(names),
        "runtime_requirements": [str(requirement) for requirement in requirements],
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
    obsolete = sorted(
        name
        for name in relative_names
        if any(name.startswith(prefix) for prefix in OBSOLETE_SDIST_PREFIXES)
    )
    if obsolete:
        raise RuntimeError(f"{sdist.name} contains obsolete package files: {obsolete}")
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
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"Command timed out after {SUBPROCESS_TIMEOUT_SECONDS}s: "
            f"{' '.join(command)}"
        ) from error
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
            or upper.startswith("PIP_")
            or upper in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"}
        ):
            environment.pop(key, None)
    environment["PIP_CONFIG_FILE"] = os.devnull
    environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"
    environment.pop("PYTHONPATH", None)
    return environment


def _normalize_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_is_active(requirement: Requirement) -> bool:
    return requirement.marker is None or requirement.marker.evaluate({"extra": ""})


def _wheel_requirements(
    archive: zipfile.ZipFile,
    *,
    wheel: Path,
) -> tuple[Requirement, ...]:
    metadata_files = [
        name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
    ]
    if len(metadata_files) != 1:
        raise RuntimeError(f"{wheel.name} has invalid distribution metadata")
    message = BytesParser(policy=email_policy).parsebytes(
        archive.read(metadata_files[0])
    )
    return tuple(Requirement(value) for value in message.get_all("Requires-Dist", []))


def _runtime_distributions(
    requirements: tuple[Requirement, ...],
) -> tuple[metadata.Distribution, ...]:
    pending = list(requirements)
    resolved: dict[str, metadata.Distribution] = {}
    while pending:
        requirement = pending.pop()
        if not _requirement_is_active(requirement):
            continue
        requested = requirement.name
        normalized = _normalize_distribution_name(requested)
        if normalized in resolved:
            installed = resolved[normalized]
            if installed.version not in requirement.specifier:
                raise RuntimeError(
                    f"Installed runtime dependency does not satisfy {requirement}: "
                    f"{installed.version}"
                )
            continue
        try:
            distribution = metadata.distribution(requested)
        except metadata.PackageNotFoundError as error:
            raise RuntimeError(
                f"Runtime dependency is not installed: {requested}"
            ) from error
        if distribution.version not in requirement.specifier:
            raise RuntimeError(
                f"Installed runtime dependency does not satisfy {requirement}: "
                f"{distribution.version}"
            )
        resolved[normalized] = distribution
        for child in distribution.requires or ():
            child_requirement = Requirement(child)
            if not _requirement_is_active(child_requirement):
                continue
            pending.append(child_requirement)
    return tuple(
        distribution
        for _, distribution in sorted(resolved.items(), key=lambda item: item[0])
    )


def _distribution_info_directory(distribution: metadata.Distribution) -> str:
    candidates = {
        path.parts[0]
        for path in distribution.files or ()
        if path.parts and path.parts[0].endswith(".dist-info")
    }
    if len(candidates) != 1:
        name = distribution.metadata["Name"] or "unknown"
        raise RuntimeError(f"Cannot identify dist-info directory for {name}")
    return next(iter(candidates))


def _compatible_wheel_tag(distribution: metadata.Distribution) -> str:
    wheel_metadata = distribution.read_text("WHEEL")
    if not wheel_metadata:
        name = distribution.metadata["Name"] or "unknown"
        raise RuntimeError(f"Installed distribution has no WHEEL metadata: {name}")
    compatible = set(sys_tags())
    declared = [
        value.strip()
        for line in wheel_metadata.splitlines()
        if line.startswith("Tag:")
        for value in (line.split(":", 1)[1],)
    ]
    for value in declared:
        parts = value.split("-", 2)
        if len(parts) == 3 and Tag(*parts) in compatible:
            return value
    name = distribution.metadata["Name"] or "unknown"
    raise RuntimeError(f"Installed distribution has no compatible wheel tag: {name}")


def _record_digest(data: bytes) -> str:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(data).digest())
    return encoded.rstrip(b"=").decode("ascii")


def _materialize_installed_wheel(
    distribution: metadata.Distribution,
    wheelhouse: Path,
) -> Path:
    dist_info = _distribution_info_directory(distribution)
    wheel = wheelhouse / f"{dist_info.removesuffix('.dist-info')}-{_compatible_wheel_tag(distribution)}.whl"
    source_root = Path(distribution.locate_file("")).resolve()
    record_path = f"{dist_info}/RECORD"
    records: list[tuple[str, str, str]] = []
    excluded_metadata = {"INSTALLER", "REQUESTED", "direct_url.json", "RECORD"}
    with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for package_file in distribution.files or ():
            source = Path(distribution.locate_file(package_file))
            try:
                relative = source.resolve().relative_to(source_root).as_posix()
            except ValueError:
                continue
            if (
                not source.is_file()
                or (
                    relative.startswith(f"{dist_info}/")
                    and Path(relative).name in excluded_metadata
                )
            ):
                continue
            data = source.read_bytes()
            archive.writestr(relative, data)
            records.append(
                (relative, f"sha256={_record_digest(data)}", str(len(data)))
            )
        records.append((record_path, "", ""))
        record = io.StringIO(newline="")
        csv.writer(record, lineterminator="\n").writerows(records)
        archive.writestr(record_path, record.getvalue().encode("utf-8"))
    return wheel


def _build_local_wheelhouse(
    requirements: tuple[Requirement, ...],
    wheelhouse: Path,
) -> dict[str, object]:
    wheelhouse.mkdir(parents=True)
    distributions = _runtime_distributions(requirements)
    wheels = [
        _materialize_installed_wheel(distribution, wheelhouse)
        for distribution in distributions
    ]
    return {
        "source": "validated-installed-distributions",
        "distributions": [
            distribution.metadata["Name"] or "unknown"
            for distribution in distributions
        ],
        "wheels": [wheel.name for wheel in wheels],
    }


def _write_network_guard(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    guard = directory / "sitecustomize.py"
    guard.write_text(
        "import socket\n"
        "def blocked(*args, **kwargs):\n"
        "    raise RuntimeError('network access blocked by distribution verification')\n"
        "for name in (\n"
        "    'create_connection', 'getaddrinfo', 'gethostbyaddr',\n"
        "    'gethostbyname', 'gethostbyname_ex', 'getnameinfo',\n"
        "):\n"
        "    if hasattr(socket, name):\n"
        "        setattr(socket, name, blocked)\n"
        "for name in ('connect', 'connect_ex', 'send', 'sendall', 'sendmsg', 'sendto'):\n"
        "    if hasattr(socket.socket, name):\n"
        "        setattr(socket.socket, name, blocked)\n",
        encoding="utf-8",
    )
    return guard


def _docx_visible_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            document_xml = archive.read("word/document.xml")
    except (KeyError, OSError, zipfile.BadZipFile) as error:
        raise RuntimeError(f"Cannot read DOCX document text: {path}") from error
    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError as error:
        raise RuntimeError(f"DOCX document.xml is not well-formed: {path}") from error
    text_tag = f"{{{WORD_NAMESPACE}}}t"
    return "".join(node.text or "" for node in root.iter(text_tag))


def _venv_executables(
    environment: Path,
    *,
    platform_name: str = os.name,
) -> tuple[Path, Path]:
    scripts = environment / ("Scripts" if platform_name == "nt" else "bin")
    python = scripts / ("python.exe" if platform_name == "nt" else "python")
    cli = scripts / ("docforge.exe" if platform_name == "nt" else "docforge")
    return python, cli


def _pip_command(python: Path, *arguments: str) -> list[str]:
    return [str(python), "-m", "pip", "--isolated", *arguments]


def _verify_installed_wheel(wheel: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="docforge-dist-") as raw_temp:
        temp = Path(raw_temp)
        base_env = _verification_environment()
        with zipfile.ZipFile(wheel) as archive:
            requirements = _wheel_requirements(archive, wheel=wheel)
        wheelhouse = temp / "wheelhouse"
        dependencies = _build_local_wheelhouse(requirements, wheelhouse)
        environment = temp / "environment"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python, cli = _venv_executables(environment)

        _run(
            _pip_command(
                python,
                "install",
                "--no-index",
                "--find-links",
                str(wheelhouse),
                str(wheel.resolve()),
            ),
            cwd=temp,
            env=base_env,
        )
        _run(
            _pip_command(python, "check"),
            cwd=temp,
            env=base_env,
        )

        guard = _write_network_guard(temp / "network-guard")
        guarded_env = base_env | {
            "PYTHONPATH": str(guard.parent),
            "DOCFORGE_DISTRIBUTION_NETWORK_POLICY": "python-socket-denied",
        }

        import_result = _run(
            [
                str(python),
                "-c",
                (
                    "import importlib, json, sys; "
                    "from importlib import resources; "
                    f"names = {PROVENANCE_MODULES!r}; "
                    "modules = {name: importlib.import_module(name) for name in names}; "
                    "print(json.dumps({"
                    "'imports': {name: modules[name].__file__ for name in names}, "
                    "'sys_path': sys.path, "
                    "'templates': str(resources.files('docforge') / 'template_data')"
                    "}))"
                ),
            ],
            cwd=temp,
            env=guarded_env,
        )
        installed = json.loads(import_result.stdout)
        import_paths = {
            name: Path(path).resolve() for name, path in installed["imports"].items()
        }
        escaped = {
            name: str(path)
            for name, path in import_paths.items()
            if environment.resolve() not in path.parents
        }
        if escaped:
            raise RuntimeError(f"Isolated imports escaped the virtual environment: {escaped}")
        checkout_paths = [
            path for path in installed["sys_path"] if ROOT == Path(path) or ROOT in Path(path).parents
        ]
        if checkout_paths:
            raise RuntimeError(f"Isolated sys.path contains the checkout: {checkout_paths}")

        command = [str(cli)]
        fixture_flows: dict[str, dict[str, object]] = {}
        for fixture_name, expectations in DISTRIBUTION_FIXTURE_EXPECTATIONS.items():
            source = ROOT / "tests" / "fixtures" / fixture_name
            workspace = temp / fixture_name
            shutil.copytree(source, workspace)
            _run([*command, "inspect", str(workspace)], cwd=workspace, env=guarded_env)
            _run([*command, "validate", str(workspace)], cwd=workspace, env=guarded_env)
            _run([*command, "review", str(workspace)], cwd=workspace, env=guarded_env)
            review_dir = workspace / "review"
            review_markdown = review_dir / "document.review.md"
            review_map = review_dir / "document.review-map.json"
            if not review_markdown.is_file() or not review_map.is_file():
                raise RuntimeError(
                    f"Installed CLI did not produce Review artifacts for {fixture_name}"
                )
            _run([*command, "build", str(workspace)], cwd=workspace, env=guarded_env)
            output = workspace / "build" / "document.docx"
            if not output.is_file() or not zipfile.is_zipfile(output):
                raise RuntimeError(
                    f"Installed CLI did not produce a valid DOCX for {fixture_name}"
                )
            visible_text = _docx_visible_text(output)
            missing_text = [
                value for value in expectations["required"] if value not in visible_text
            ]
            forbidden_text = [
                value for value in expectations["forbidden"] if value in visible_text
            ]
            if missing_text or forbidden_text:
                raise RuntimeError(
                    f"Installed {fixture_name} visible text failed: "
                    f"missing={missing_text}, forbidden={forbidden_text}"
                )
            fixture_flows[fixture_name] = {
                "inspect": True,
                "validate": True,
                "review": True,
                "build": True,
                "review_markdown_bytes": review_markdown.stat().st_size,
                "review_map_bytes": review_map.stat().st_size,
                "docx_bytes": output.stat().st_size,
                "docx_sha256": _sha256(output),
                "visible_text_checks": {
                    "required": list(expectations["required"]),
                    "forbidden": list(expectations["forbidden"]),
                },
            }

        return {
            "isolated_install": True,
            "installer_network": "disabled-by-pip-no-index",
            "runtime_network_guard": "python-socket-apis",
            "console_launcher": str(cli),
            "dependencies": dependencies,
            "imports": {name: str(path) for name, path in import_paths.items()},
            "sys_path": installed["sys_path"],
            "templates": installed["templates"],
            "fixtures": fixture_flows,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect DocForge distributions and verify the installed wheel offline."
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
