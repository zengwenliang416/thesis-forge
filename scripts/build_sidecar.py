#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIDECAR_NAME = "thesisforge-sidecar"
SIDECAR_DIRECTORY = ROOT / "src-tauri" / "binaries"
PACKAGE_DATA = (
    (
        ROOT / "templates" / "base" / "bachelor.yaml",
        "docforge/template_data/base",
    ),
    (
        ROOT / "templates" / "schools" / "example-university" / "2026.yaml",
        "docforge/template_data/schools/example-university",
    ),
    (
        ROOT / "templates" / "schools" / "project-proposal" / "2026.yaml",
        "docforge/template_data/schools/project-proposal",
    ),
    (
        ROOT
        / "templates"
        / "schools"
        / "hunan-university-of-technology"
        / "master-2026.yaml",
        "docforge/template_data/schools/hunan-university-of-technology",
    ),
)


def python_docx_parts_marker() -> Path:
    spec = importlib.util.find_spec("docx.parts")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("Unable to locate python-docx package data")
    marker = Path(next(iter(spec.submodule_search_locations))) / "__init__.py"
    if not marker.is_file():
        raise RuntimeError(f"python-docx parts marker is missing: {marker}")
    return marker


def host_target_triple() -> str:
    result = subprocess.run(
        ["rustc", "--print", "host-tuple"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Unable to determine Rust host target: {detail}")
    return result.stdout.strip()


def sidecar_binary_name(target_triple: str) -> str:
    suffix = ".exe" if "windows" in target_triple else ""
    return f"{SIDECAR_NAME}-{target_triple}{suffix}"


def ensure_native_target(host: str, target: str) -> None:
    if host != target:
        raise ValueError(
            f"Sidecar target {target} must be built on its native target; host is {host}"
        )


def pyinstaller_command(
    *,
    python: Path,
    entrypoint: Path,
    dist_path: Path,
    work_path: Path,
    spec_path: Path,
) -> list[str]:
    command = [
        str(python),
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        SIDECAR_NAME,
        "--paths",
        str(ROOT / "src"),
        "--collect-data",
        "docx",
        "--distpath",
        str(dist_path),
        "--workpath",
        str(work_path),
        "--specpath",
        str(spec_path),
    ]
    for source, destination in PACKAGE_DATA:
        command.extend(["--add-data", f"{source}{os.pathsep}{destination}"])
    command.extend(
        [
            "--add-data",
            f"{python_docx_parts_marker()}{os.pathsep}docx/parts",
        ]
    )
    command.append(str(entrypoint))
    return command


def _entrypoint_text() -> str:
    return (
        "import os\n"
        "if os.environ.get('THESISFORGE_BLOCK_NETWORK') == '1':\n"
        "    import socket\n"
        "    def blocked(*args, **kwargs):\n"
        "        raise RuntimeError('network access blocked by desktop verification')\n"
        "    socket.create_connection = blocked\n"
        "    socket.socket.connect = blocked\n"
        "    socket.socket.connect_ex = blocked\n"
        "from docforge.adapters.sidecar import main\n"
        "raise SystemExit(main())\n"
    )


def build_sidecar(
    *,
    target_triple: str,
    output_directory: Path = SIDECAR_DIRECTORY,
    python: Path = Path(sys.executable),
) -> Path:
    host = host_target_triple()
    ensure_native_target(host, target_triple)
    for source, _destination in PACKAGE_DATA:
        if not source.is_file():
            raise RuntimeError(f"Required sidecar package data is missing: {source}")

    output_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="thesisforge-sidecar-") as raw_temp:
        temp = Path(raw_temp)
        entrypoint = temp / "sidecar_entry.py"
        entrypoint.write_text(_entrypoint_text(), encoding="utf-8")
        dist_path = temp / "dist"
        command = pyinstaller_command(
            python=python,
            entrypoint=entrypoint,
            dist_path=dist_path,
            work_path=temp / "work",
            spec_path=temp / "spec",
        )
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = "\n".join(part for part in (result.stdout, result.stderr) if part)
            raise RuntimeError(f"PyInstaller sidecar build failed:\n{detail}")

        built_name = f"{SIDECAR_NAME}{'.exe' if os.name == 'nt' else ''}"
        built = dist_path / built_name
        if not built.is_file():
            raise RuntimeError(f"PyInstaller did not produce the expected sidecar: {built}")
        destination = output_directory / sidecar_binary_name(target_triple)
        shutil.copy2(built, destination)
        if os.name != "nt":
            destination.chmod(destination.stat().st_mode | stat.S_IXUSR)
        return destination


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the target-native ThesisForge Python sidecar for Tauri."
    )
    parser.add_argument("--target-triple", default=None)
    parser.add_argument("--output-directory", type=Path, default=SIDECAR_DIRECTORY)
    args = parser.parse_args()

    target = args.target_triple or host_target_triple()
    output = build_sidecar(
        target_triple=target,
        output_directory=args.output_directory.resolve(),
    )
    print(
        json.dumps(
            {
                "ok": True,
                "host": host_target_triple(),
                "target": target,
                "sidecar": str(output),
                "bytes": output.stat().st_size,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
