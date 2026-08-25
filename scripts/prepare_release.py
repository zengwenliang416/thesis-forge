#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILES = {
    "python": ROOT / "pyproject.toml",
    "frontend": ROOT / "frontend" / "package.json",
    "tauri": ROOT / "src-tauri" / "tauri.conf.json",
    "rust": ROOT / "src-tauri" / "Cargo.toml",
}


def release_versions() -> dict[str, str]:
    return {
        "python": tomllib.loads(VERSION_FILES["python"].read_text(encoding="utf-8"))[
            "project"
        ]["version"],
        "frontend": json.loads(
            VERSION_FILES["frontend"].read_text(encoding="utf-8")
        )["version"],
        "tauri": json.loads(VERSION_FILES["tauri"].read_text(encoding="utf-8"))[
            "version"
        ],
        "rust": tomllib.loads(VERSION_FILES["rust"].read_text(encoding="utf-8"))[
            "package"
        ]["version"],
    }


def validate_release_tag(tag: str) -> str:
    versions = release_versions()
    unique_versions = set(versions.values())
    if len(unique_versions) != 1:
        detail = ", ".join(f"{name}={version}" for name, version in versions.items())
        raise RuntimeError(f"Release versions do not match: {detail}")
    version = unique_versions.pop()
    expected_tag = f"v{version}"
    if tag != expected_tag:
        raise RuntimeError(f"Release tag {tag!r} must match {expected_tag!r}")
    return version


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _single_artifact(root: Path, expected_name: str, label: str) -> Path:
    if root.is_symlink():
        raise RuntimeError(f"{label} root must not be a symbolic link: {root}")
    resolved_root = root.resolve(strict=True)
    matches = sorted(path for path in root.rglob(expected_name) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {label} artifact under {root}, found {matches}"
        )
    artifact = matches[0]
    if artifact.is_symlink():
        raise RuntimeError(f"{label} artifact must not be a symbolic link: {artifact}")
    resolved_artifact = artifact.resolve(strict=True)
    try:
        resolved_artifact.relative_to(resolved_root)
    except ValueError as error:
        raise RuntimeError(f"{label} artifact escapes its root: {artifact}") from error
    return resolved_artifact


def prepare_macos_release(
    *,
    tag: str,
    bundle_root: Path,
    python_dist: Path,
    output_dir: Path,
) -> list[Path]:
    version = validate_release_tag(tag)
    polluted = sorted(bundle_root.rglob("._*"))
    if polluted:
        raise RuntimeError(f"Release bundle contains AppleDouble files: {polluted}")

    dmg = _single_artifact(
        bundle_root,
        f"ThesisForge_{version}_aarch64.dmg",
        "macOS DMG",
    )
    wheel = _single_artifact(
        python_dist,
        f"thesis_forge-{version}-py3-none-any.whl",
        "Python wheel",
    )
    source_dist = _single_artifact(
        python_dist,
        f"thesis_forge-{version}.tar.gz",
        "Python source",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    if output_dir.is_symlink() or any(output_dir.iterdir()):
        raise RuntimeError(f"Release output directory must be empty: {output_dir}")
    copied: list[Path] = []
    for source in (dmg, wheel, source_dist):
        destination = output_dir / source.name
        shutil.copy2(source, destination)
        copied.append(destination)

    notes = output_dir / "RELEASE_NOTES.md"
    notes.write_text(
        "\n".join(
            [
                f"# ThesisForge {tag}",
                "",
                "本版本是供早期用户验证的未公证预发布版本。",
                "",
                "## 下载",
                "",
                f"- `ThesisForge_{version}_aarch64.dmg`: macOS Apple Silicon 安装包。",
                f"- `thesis_forge-{version}-py3-none-any.whl`: Python wheel。",
                f"- `thesis_forge-{version}.tar.gz`: Python 源码分发包。",
                "",
                "## 安全提示",
                "",
                "macOS 应用使用 ad-hoc 签名，尚未使用 Apple Developer ID 签名或公证。",
                "系统可能显示 Gatekeeper 提示；该状态不等同于正式生产发行。",
                "请使用 `SHA256SUMS` 验证下载文件完整性。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    checksum = output_dir / "SHA256SUMS"
    checksum.write_text(
        "".join(f"{_sha256(path)}  {path.name}\n" for path in sorted(copied)),
        encoding="utf-8",
    )
    return [*copied, checksum, notes]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ThesisForge release versions and collect release assets."
    )
    parser.add_argument("--tag", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--platform", choices=("macos",))
    parser.add_argument("--bundle-root", type=Path)
    parser.add_argument("--python-dist", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist" / "release")
    args = parser.parse_args()

    version = validate_release_tag(args.tag)
    if args.validate_only:
        print(json.dumps({"ok": True, "tag": args.tag, "version": version}))
        return 0

    if args.platform != "macos" or args.bundle_root is None or args.python_dist is None:
        parser.error(
            "--platform macos, --bundle-root and --python-dist are required "
            "unless --validate-only is used"
        )

    assets = prepare_macos_release(
        tag=args.tag,
        bundle_root=args.bundle_root,
        python_dist=args.python_dist,
        output_dir=args.output_dir,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "tag": args.tag,
                "version": version,
                "assets": [str(path) for path in assets],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
