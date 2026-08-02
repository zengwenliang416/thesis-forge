#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

from build_sidecar import (
    ROOT,
    SIDECAR_DIRECTORY,
    ensure_native_target,
    host_target_triple,
    sidecar_binary_name,
)

PROTOCOL_VERSION = "thesisforge.workbench.v1"
BUILD_STAGES = ("parse", "validate", "compile", "render", "finalize")


def required_bundle_suffixes(platform: str) -> tuple[str, ...]:
    if platform == "macos":
        return (".app", ".dmg")
    if platform == "windows":
        return (".msi", ".exe")
    raise ValueError(f"Unsupported desktop platform: {platform}")


def managed_sidecar_name(platform: str) -> str:
    if platform == "macos":
        return "thesisforge-sidecar"
    if platform == "windows":
        return "thesisforge-sidecar.exe"
    raise ValueError(f"Unsupported desktop platform: {platform}")


def platform_for_target(target_triple: str) -> str:
    if "apple-darwin" in target_triple:
        return "macos"
    if "windows" in target_triple:
        return "windows"
    raise ValueError(f"Unsupported desktop target: {target_triple}")


def validate_native_target(target: str, *, host: str | None = None) -> None:
    ensure_native_target(host or host_target_triple(), target)


def validate_sidecar_artifact(sidecar: Path) -> None:
    if not sidecar.is_file():
        raise RuntimeError(f"Missing target-native sidecar: {sidecar}")
    polluted = sorted(
        path for path in sidecar.parent.iterdir() if path.name.startswith("._")
    )
    if polluted:
        raise RuntimeError(f"Sidecar directory contains AppleDouble files: {polluted}")
    if os.name != "nt" and not os.access(sidecar, os.X_OK):
        raise RuntimeError(f"Sidecar is not executable: {sidecar}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in tuple(environment):
        upper = key.upper()
        if upper.endswith(("_API_KEY", "_TOKEN")) or upper in {
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "NO_PROXY",
        }:
            environment.pop(key, None)
    environment.pop("PYTHONPATH", None)
    environment["THESISFORGE_BLOCK_NETWORK"] = "1"
    return environment


def _request(
    operation: str,
    source: Path,
    *,
    output: Path | None = None,
) -> dict:
    payload: dict[str, object] = {
        "source": {
            "kind": "desktop",
            "path": str(source),
            "fileName": source.name,
        },
        "templateId": "example-university-2026",
    }
    if output is not None:
        payload["output"] = {
            "kind": "desktop",
            "path": str(output),
            "fileName": output.name,
        }
    return {
        "protocol": PROTOCOL_VERSION,
        "requestId": f"desktop-{operation}",
        "operation": operation,
        "payload": payload,
    }


def _run_sidecar(
    sidecar: Path,
    request: dict,
    *,
    stream: bool,
    cwd: Path,
    environment: dict[str, str],
) -> list[dict]:
    result = subprocess.run(
        [str(sidecar), "--stream" if stream else "--once"],
        cwd=cwd,
        env=environment,
        input=f"{json.dumps(request, ensure_ascii=False)}\n",
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Sidecar failed ({result.returncode}): {result.stdout}\n{result.stderr}"
        )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("Sidecar produced no protocol output")
    try:
        return [json.loads(line) for line in lines]
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Sidecar produced malformed JSON: {result.stdout}") from error


def verify_sidecar(sidecar: Path) -> dict[str, object]:
    validate_sidecar_artifact(sidecar)

    with tempfile.TemporaryDirectory(prefix="thesisforge-desktop-") as raw_temp:
        workspace = Path(raw_temp) / "workspace"
        shutil.copytree(ROOT / "examples" / "bachelor-thesis", workspace)
        source = workspace / "thesis.md"
        output = workspace / "output" / "thesis.docx"
        output.parent.mkdir()
        environment = _offline_environment()

        responses: dict[str, dict] = {}
        for operation in ("inspect", "validate", "preview"):
            events = _run_sidecar(
                sidecar,
                _request(operation, source),
                stream=False,
                cwd=workspace,
                environment=environment,
            )
            if len(events) != 1 or events[0].get("ok") is not True:
                raise RuntimeError(f"{operation} sidecar smoke failed: {events}")
            responses[operation] = events[0]

        prior = b"prior-valid-output"
        output.write_bytes(prior)
        cancel_file = workspace / "cancel"
        cancel_file.write_text("cancel", encoding="utf-8")
        canceled = _run_sidecar(
            sidecar,
            _request("build", source, output=output),
            stream=True,
            cwd=workspace,
            environment=environment | {"THESISFORGE_CANCEL_FILE": str(cancel_file)},
        )
        terminal = canceled[-1]
        if terminal.get("type") != "error" or terminal.get("error", {}).get("kind") != "canceled":
            raise RuntimeError(f"Sidecar cancellation smoke failed: {canceled}")
        if output.read_bytes() != prior:
            raise RuntimeError("Canceled sidecar build replaced the prior output")

        cancel_file.unlink()
        built = _run_sidecar(
            sidecar,
            _request("build", source, output=output),
            stream=True,
            cwd=workspace,
            environment=environment,
        )
        stages = tuple(
            event["stage"] for event in built if event.get("type") == "progress"
        )
        if stages != BUILD_STAGES:
            raise RuntimeError(f"Unexpected sidecar build stages: {stages}")
        if built[-1].get("type") != "success":
            raise RuntimeError(f"Sidecar build did not succeed: {built}")
        if not output.is_file() or not zipfile.is_zipfile(output):
            raise RuntimeError("Frozen sidecar did not produce a valid DOCX package")

        reopened = _run_sidecar(
            sidecar,
            _request("inspect", source),
            stream=False,
            cwd=workspace,
            environment=environment,
        )
        if reopened[0].get("ok") is not True:
            raise RuntimeError(f"Sidecar reopen smoke failed: {reopened}")

        return {
            "path": str(sidecar),
            "bytes": sidecar.stat().st_size,
            "sha256": _sha256(sidecar),
            "operations": sorted(responses),
            "canceled": True,
            "buildStages": list(stages),
            "docxBytes": output.stat().st_size,
            "docxSha256": _sha256(output),
            "reopened": True,
            "offline": True,
        }


def verify_web_distribution(web_dist: Path) -> dict[str, object]:
    index = web_dist / "index.html"
    assets = web_dist / "assets"
    if not index.is_file() or not assets.is_dir():
        raise RuntimeError(f"Invalid Web production distribution: {web_dist}")
    files = sorted(path for path in web_dist.rglob("*") if path.is_file())
    polluted = [str(path) for path in files if path.name.startswith("._")]
    if polluted:
        raise RuntimeError(f"Web distribution contains AppleDouble files: {polluted}")
    return {
        "path": str(web_dist),
        "files": len(files),
        "indexSha256": _sha256(index),
    }


def verify_native_bundles(bundle_root: Path, platform: str) -> dict[str, object]:
    suffixes = required_bundle_suffixes(platform)
    artifacts: dict[str, dict[str, object]] = {}
    for suffix in suffixes:
        candidates = sorted(
            path
            for path in bundle_root.rglob(f"*{suffix}")
            if (path.is_dir() if suffix == ".app" else path.is_file())
        )
        if not candidates:
            raise RuntimeError(f"Missing {platform} bundle artifact {suffix} in {bundle_root}")
        artifact = candidates[0]
        polluted = [
            str(path)
            for path in (
                artifact.rglob("*") if artifact.is_dir() else artifact.parent.iterdir()
            )
            if path.name.startswith("._")
        ]
        if polluted:
            raise RuntimeError(f"Bundle contains AppleDouble files: {polluted}")
        artifacts[suffix] = {
            "path": str(artifact),
            "bytes": (
                sum(path.stat().st_size for path in artifact.rglob("*") if path.is_file())
                if artifact.is_dir()
                else artifact.stat().st_size
            ),
        }
        if suffix == ".app":
            managed_sidecar = (
                artifact
                / "Contents"
                / "MacOS"
                / managed_sidecar_name(platform)
            )
            if not managed_sidecar.is_file() or not os.access(managed_sidecar, os.X_OK):
                raise RuntimeError(
                    f"macOS app does not contain an executable managed sidecar: {managed_sidecar}"
                )
            artifacts[suffix]["managedSidecar"] = str(managed_sidecar)
    if platform == "windows":
        managed_sidecar = bundle_root.parent / managed_sidecar_name(platform)
        if not managed_sidecar.is_file() or managed_sidecar.read_bytes()[:2] != b"MZ":
            raise RuntimeError(
                f"Windows release does not contain the managed sidecar: {managed_sidecar}"
            )
        artifacts["managedSidecar"] = {
            "path": str(managed_sidecar),
            "bytes": managed_sidecar.stat().st_size,
        }
    return {"platform": platform, "artifacts": artifacts}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the frozen desktop sidecar and native Tauri bundles."
    )
    parser.add_argument("--target-triple", default=None)
    parser.add_argument("--sidecar-directory", type=Path, default=SIDECAR_DIRECTORY)
    parser.add_argument("--web-dist", type=Path, default=ROOT / "dist" / "web")
    parser.add_argument("--bundle-root", type=Path)
    parser.add_argument("--platform", choices=("macos", "windows"))
    parser.add_argument("--sidecar-only", action="store_true")
    args = parser.parse_args()

    target = args.target_triple or host_target_triple()
    validate_native_target(target)
    platform = args.platform or platform_for_target(target)
    sidecar = args.sidecar_directory.resolve() / sidecar_binary_name(target)
    evidence: dict[str, object] = {
        "ok": True,
        "target": target,
        "platform": platform,
        "sidecar": verify_sidecar(sidecar),
    }
    if not args.sidecar_only:
        if args.bundle_root is None:
            parser.error("--bundle-root is required unless --sidecar-only is used")
        evidence["web"] = verify_web_distribution(args.web_dist.resolve())
        evidence["bundles"] = verify_native_bundles(
            args.bundle_root.resolve(),
            platform,
        )
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
