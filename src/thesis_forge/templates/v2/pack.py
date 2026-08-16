"""Template Package v2 `.tftpl` 打包 / 校验 / 解包（SCHEMA §7，决策 D-6）。

- `pack_package`：目录形态 → `.tftpl` 确定性快照。打包前必须通过 lint
  L1+L2（失败拒绝打包，不产出文件）；entry 顺序为 `manifest.json` 居首、
  其余按 path 的 UTF-8 字节序字典序；时间戳固定 DOS 纪元
  `1980-01-01T00:00:00`；压缩固定 DEFLATE level 9；剔除 §1.2 隐藏文件、
  `__MACOSX/`、`.DS_Store` 与目录形态下误置的根 `manifest.json`/
  `signature.json`（§7.2）。
- `unpack_package`：解包到目标目录（必须不存在或为空，禁止就地覆盖），
  逐 entry 做 §1.3 Zip Slip 校验（绝对路径/盘符/反斜杠/`..` 段/符号链接
  entry 一律拒绝）、解压炸弹防护（单文件 ≤ 64 MB、总量 ≤ 512 MB、条目数
  ≤ `MAX_ENTRIES`，超限即中止）并对账 manifest 哈希（§7.4）。
- `verify_package` = 上述防护 + manifest/header 对账 + 解包后 L1–L3 全量 +
  签名检查（签名实现见 §7.3 OQ-6，当前仅提示不验证）。

所有失败以结构化 `ValidationIssue` 累积，`PackError` 携带 issues 抛出。
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from thesis_forge import __version__ as _HOST_VERSION
from thesis_forge.core.model import ValidationIssue

from . import lint as _lint
from . import package as pkg

MANIFEST_VERSION = 1
GENERATOR_NAME = "thesisforge"

# §1.3 默认阈值（与 lint.py 保持一致）
MAX_ENTRY_SIZE = 64 * 1024 * 1024  # 64 MB
MAX_TOTAL_SIZE = 512 * 1024 * 1024  # 512 MB
# §7.4 未给出条目数上限，取防御性默认值（实施记录见 ADR-0002）
MAX_ENTRIES = 10_000
# §7.4 第 3 条：压缩率超过该比值且压缩前 > 1 MB 的 entry 视为可疑，
# 流式计数解压并在超限时中止
MAX_COMPRESSION_RATIO = 100
_RATIO_PROBE_SIZE = 1 * 1024 * 1024

_FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)  # DOS 纪元（§7.2 第 2 条）
_CHUNK_SIZE = 1024 * 1024
_RESERVED_ENTRIES = frozenset({"manifest.json", "signature.json"})
_PLATFORM_JUNK_NAMES = frozenset({".DS_Store", "__MACOSX"})
_SYMLINK_MODE = 0o120000


class PackError(ValueError):
    """`.tftpl` 打包 / 校验 / 解包失败；`issues` 为结构化 ValidationIssue 元组。"""

    def __init__(self, path: Path, issues: tuple[ValidationIssue, ...]):
        self.path = path
        self.issues = issues
        detail = "; ".join(
            f"[{issue.code}] {issue.target or ''} {issue.message}".strip()
            for issue in issues[:5]
        )
        super().__init__(f".tftpl 处理失败: {path}: {detail}")


def _issue(
    code: str,
    severity: str,
    message: str,
    *,
    target: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(code=code, severity=severity, message=message, target=target)


def _error(code: str, message: str, *, target: str | None = None) -> ValidationIssue:
    return _issue(code, "error", message, target=target)


# ---------------------------------------------------------------------------
# 打包
# ---------------------------------------------------------------------------


def _iter_package_files(package_dir: Path) -> list[tuple[str, Path]]:
    """收集打包条目（§7.2 第 4 条剔除规则），按 path UTF-8 字节序排序。"""
    root = package_dir.resolve()
    entries: list[tuple[bytes, str, Path]] = []
    for file in root.rglob("*"):
        if not file.is_file() or file.is_symlink():
            continue
        rel = file.relative_to(root).as_posix()
        parts = rel.split("/")
        name = parts[-1]
        if name in _PLATFORM_JUNK_NAMES:
            continue
        if any(part.startswith(".") for part in parts):
            continue  # §1.2：隐藏文件不打包
        if rel in _RESERVED_ENTRIES:
            continue  # 根 manifest.json / signature.json 剔除重建
        entries.append((rel.encode("utf-8"), rel, file))
    entries.sort()
    return [(rel, file) for _key, rel, file in entries]


def _sha256_ref(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def build_manifest(
    resolved: pkg.ResolvedTemplatePackage,
    entries: list[tuple[str, bytes]],
) -> dict[str, Any]:
    """按 §7.1（C-10）构造 manifest 数据。"""
    template = resolved.template
    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "generator": {"name": GENERATOR_NAME, "version": _HOST_VERSION},
        "template": {
            "id": template.id,
            "version": template.version,
            "schema_version": 2,
            "language": template.language,
        },
        "compatibility": resolved.resolved_data.get("compatibility")
        or template.compatibility.model_dump(mode="json"),
        "entries": [
            {"path": rel, "sha256": _sha256_ref(data), "size": len(data)}
            for rel, data in entries
        ],
    }
    provenance_path = resolved.path / "provenance.yaml"
    manifest["provenance_hash"] = _sha256_ref(provenance_path.read_bytes())
    if len(resolved.inheritance_chain) > 1:
        # §7.1：声明 extends 时记录打包时解析的完整继承链（含自身，§4.3 第 6 条）
        manifest["inheritance"] = [
            {"id": entry.id, "version": entry.version, "sha256": entry.sha256}
            for entry in resolved.inheritance_chain
        ]
    return manifest


def manifest_bytes(manifest: dict[str, Any]) -> bytes:
    """manifest.json 规范字节：UTF-8、键排序、两空格缩进、单尾部换行。"""
    return (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=_FIXED_DATE_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3  # Unix，跨机器固定
    info.external_attr = 0o644 << 16
    return info


def pack_package(
    package_dir: str | Path,
    output_path: str | Path,
    *,
    host_version: str = _HOST_VERSION,
) -> Path:
    """把目录形态包打成 `.tftpl`；lint L1+L2 有 error 时拒绝打包。"""
    package_dir = Path(package_dir).expanduser().resolve()
    output = Path(output_path).expanduser()
    if not output.is_absolute():
        output = Path.cwd() / output

    if not package_dir.is_dir():
        raise PackError(
            package_dir,
            (
                _error(
                    "missing-package-file",
                    f"模板包目录不存在：{package_dir}",
                    target=str(package_dir),
                ),
            ),
        )
    if output.exists() and output.is_dir():
        raise PackError(
            output, (_error("invalid-package", f"输出路径是目录：{output}"),)
        )
    if package_dir == output.parent or package_dir in output.parents:
        raise PackError(
            output,
            (
                _error(
                    "invalid-package",
                    "输出文件不得位于被打包目录内（避免快照自包含）",
                    target=str(output),
                ),
            ),
        )

    # D-6 第 5 条 / 任务约束：pack 前置 lint L1+L2，失败不产出包
    issues = list(_lint.lint_l1(package_dir))
    resolved: pkg.ResolvedTemplatePackage | None = None
    if not any(issue.severity == "error" for issue in issues):
        l2_issues, resolved = _lint.lint_l2(package_dir)
        issues.extend(l2_issues)
    if any(issue.severity == "error" for issue in issues):
        raise PackError(package_dir, tuple(issues))
    assert resolved is not None

    files = _iter_package_files(package_dir)
    entries = [(rel, file.read_bytes()) for rel, file in files]
    manifest = build_manifest(resolved, entries)

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(
            _zip_info("manifest.json"), manifest_bytes(manifest), compresslevel=9
        )
        for rel, data in entries:
            archive.writestr(_zip_info(rel), data, compresslevel=9)
    return output


# ---------------------------------------------------------------------------
# 解包防护 + 校验
# ---------------------------------------------------------------------------


def _check_zip_entry(info: zipfile.ZipInfo) -> ValidationIssue | None:
    """§7.4 第 2 条：Zip Slip / 符号链接 entry / 目录 entry 检查。"""
    name = info.filename
    if name.endswith("/"):
        return None  # 目录 entry：不产出文件，容忍
    if (info.external_attr >> 16) & 0o170000 == _SYMLINK_MODE:
        return _error(
            "package-path-unsafe", f"符号链接 entry 一律拒绝：{name!r}", target=name
        )
    if not pkg.is_safe_package_path(name):
        return _error(
            "package-path-unsafe",
            f"entry 路径必须是相对路径、无盘符/反斜杠、不含 .. 段：{name!r}",
            target=name,
        )
    return None


def _check_bomb_limits(infos: list[zipfile.ZipInfo]) -> list[ValidationIssue]:
    """§7.4 第 3 条：解压炸弹静态上限（单文件/总量/条目数）。"""
    issues: list[ValidationIssue] = []
    files = [info for info in infos if not info.filename.endswith("/")]
    if len(files) > MAX_ENTRIES:
        issues.append(
            _error(
                "package-path-unsafe",
                f"entry 数量超过上限 {MAX_ENTRIES}：{len(files)}",
            )
        )
    total = 0
    for info in files:
        total += info.file_size
        if info.file_size > MAX_ENTRY_SIZE:
            issues.append(
                _error(
                    "package-path-unsafe",
                    f"单文件解压后超过 64 MB 上限：{info.filename}"
                    f"（{info.file_size} 字节）",
                    target=info.filename,
                )
            )
    if total > MAX_TOTAL_SIZE:
        issues.append(
            _error(
                "package-path-unsafe",
                f"解压总量超过 512 MB 上限（{total} 字节）",
            )
        )
    return issues


def _extract_entry_streaming(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    target: Path,
) -> tuple[str, ...] | str:
    """流式解压单 entry 并计数；超限即中止。成功返回 (sha256 hexdigest,)。"""
    digest = hashlib.sha256()
    written = 0
    target.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(info) as source, target.open("wb") as sink:
        while True:
            chunk = source.read(_CHUNK_SIZE)
            if not chunk:
                break
            written += len(chunk)
            if written > MAX_ENTRY_SIZE:
                sink.close()
                target.unlink(missing_ok=True)
                return f"单文件解压超过 64 MB 上限（流式中止）：{info.filename}"
            digest.update(chunk)
            sink.write(chunk)
    return (digest.hexdigest(),)


def _load_and_check_manifest(
    archive: zipfile.ZipFile,
    *,
    host_version: str,
) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    """§7.4 第 4 条：先读 manifest.json 校验 manifest_version 与 compatibility。"""
    issues: list[ValidationIssue] = []
    try:
        raw = archive.read("manifest.json")
    except KeyError:
        return None, [
            _error(
                "missing-package-file",
                ".tftpl 缺少 manifest.json（§7.1 必需）",
                target="manifest.json",
            )
        ]
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, [
            _error(
                "invalid-package",
                f"manifest.json 不是合法 JSON：{error}",
                target="manifest.json",
            )
        ]
    if not isinstance(manifest, dict):
        return None, [
            _error("invalid-package", "manifest.json 顶层必须是对象", target="manifest.json")
        ]
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        issues.append(
            _error(
                "unsupported-manifest-version",
                "manifest_version 必须为 "
                f"{MANIFEST_VERSION}（实际 {manifest.get('manifest_version')!r}）",
                target="manifest_version",
            )
        )
    compatibility = manifest.get("compatibility")
    if isinstance(compatibility, dict):
        host_range = compatibility.get("thesisforge")
        if isinstance(host_range, str):
            try:
                from .schema import version_satisfies

                if not version_satisfies(host_range, host_version):
                    issues.append(
                        _error(
                            "incompatible-thesisforge",
                            f"宿主 ThesisForge {host_version} 不满足模板兼容区间 "
                            f"{host_range!r}",
                            target="compatibility.thesisforge",
                        )
                    )
            except ValueError:
                issues.append(
                    _error(
                        "invalid-package",
                        f"manifest compatibility.thesisforge 区间无效：{host_range!r}",
                        target="compatibility.thesisforge",
                    )
                )
    entries = manifest.get("entries")
    if not isinstance(entries, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("path"), str)
        or not isinstance(item.get("sha256"), str)
        or not isinstance(item.get("size"), int)
        for item in entries
    ):
        issues.append(
            _error(
                "invalid-package",
                "manifest.entries 必须是 list[{path, sha256, size}]",
                target="entries",
            )
        )
    if issues:
        return None, issues
    return manifest, []


def unpack_package(
    tftpl_path: str | Path,
    dest_dir: str | Path,
    *,
    host_version: str = _HOST_VERSION,
) -> Path:
    """解包 `.tftpl` 到目标目录（§7.4 sandbox extraction）；失败抛 `PackError`。

    目标目录必须不存在或为空目录（禁止就地覆盖）。解包完成即表示通过
    Zip Slip / 炸弹防护与 manifest 哈希对账。
    """
    tftpl = Path(tftpl_path).expanduser()
    if not tftpl.is_absolute():
        tftpl = Path.cwd() / tftpl
    dest = Path(dest_dir).expanduser()
    if not dest.is_absolute():
        dest = Path.cwd() / dest
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise PackError(
            dest,
            (
                _error(
                    "invalid-package",
                    f"解包目标目录必须不存在或为空（禁止就地覆盖）：{dest}",
                    target=str(dest),
                ),
            ),
        )

    try:
        archive = zipfile.ZipFile(tftpl)
    except (OSError, zipfile.BadZipFile) as error:
        raise PackError(
            tftpl,
            (_error("invalid-package", f"不是可读的 .tftpl（ZIP）文件：{error}"),),
        ) from None

    with archive:
        infos = archive.infolist()
        issues: list[ValidationIssue] = []
        for info in infos:
            entry_issue = _check_zip_entry(info)
            if entry_issue is not None:
                issues.append(entry_issue)
        issues.extend(_check_bomb_limits(infos))
        manifest, manifest_issues = _load_and_check_manifest(
            archive, host_version=host_version
        )
        issues.extend(manifest_issues)
        if any(issue.severity == "error" for issue in issues):
            raise PackError(tftpl, tuple(issues))
        assert manifest is not None

        manifest_entries: dict[str, dict[str, Any]] = {}
        duplicate_paths: set[str] = set()
        for item in manifest["entries"]:
            if item["path"] in manifest_entries:
                duplicate_paths.add(item["path"])
            manifest_entries[item["path"]] = item
        if duplicate_paths:
            raise PackError(
                tftpl,
                (
                    _error(
                        "manifest-mismatch",
                        f"manifest.entries 含重复 path：{', '.join(sorted(duplicate_paths))}",
                        target="entries",
                    ),
                ),
            )

        zip_files = {
            info.filename: info for info in infos if not info.filename.endswith("/")
        }
        payload_names = set(zip_files) - _RESERVED_ENTRIES
        if set(manifest_entries) != payload_names:
            only_zip = sorted(payload_names - set(manifest_entries))
            only_manifest = sorted(set(manifest_entries) - payload_names)
            detail = []
            if only_zip:
                detail.append(f"ZIP 多出：{', '.join(only_zip[:5])}")
            if only_manifest:
                detail.append(f"manifest 多出：{', '.join(only_manifest[:5])}")
            raise PackError(
                tftpl,
                (
                    _error(
                        "manifest-mismatch",
                        "ZIP 条目与 manifest.entries 不一致：" + "；".join(detail),
                        target="entries",
                    ),
                ),
            )

        dest.mkdir(parents=True, exist_ok=True)
        hash_issues: list[ValidationIssue] = []
        for rel in sorted(payload_names):
            info = zip_files[rel]
            declared = manifest_entries[rel]
            # §7.4 第 3 条：高压缩率 entry 走流式计数（实现上全部流式）
            result = _extract_entry_streaming(archive, info, dest / rel)
            if isinstance(result, str):
                hash_issues.append(
                    _error("package-path-unsafe", result, target=rel)
                )
                continue
            (actual_hex,) = result
            if "sha256:" + actual_hex != declared["sha256"]:
                hash_issues.append(
                    _error(
                        "hash-mismatch",
                        f"entry 内容与 manifest 声明哈希不一致：{rel}",
                        target=rel,
                    )
                )
            elif declared["size"] != info.file_size:
                hash_issues.append(
                    _error(
                        "hash-mismatch",
                        f"entry 大小与 manifest 声明不一致：{rel}",
                        target=rel,
                    )
                )
        if hash_issues:
            raise PackError(tftpl, tuple(hash_issues))

        provenance_hash = manifest.get("provenance_hash")
        if isinstance(provenance_hash, str):
            provenance_file = dest / "provenance.yaml"
            if not provenance_file.is_file() or _sha256_ref(
                provenance_file.read_bytes()
            ) != provenance_hash:
                raise PackError(
                    tftpl,
                    (
                        _error(
                            "hash-mismatch",
                            "provenance.yaml 与 manifest.provenance_hash 不一致",
                            target="provenance_hash",
                        ),
                    ),
                )
    return dest


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class VerifyReport:
    path: Path
    issues: tuple[ValidationIssue, ...]
    package: pkg.ResolvedTemplatePackage | None

    @property
    def errors(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warnings(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)

    @property
    def has_errors(self) -> bool:
        return self.errors > 0


def _check_manifest_template_match(
    manifest: dict[str, Any], dest: Path
) -> list[ValidationIssue]:
    """§7.1：manifest.template/compatibility 必须与 template.yaml header 一致。"""
    issues: list[ValidationIssue] = []
    data, read_issues = pkg._read_template_yaml(dest)
    if read_issues:
        return list(read_issues)
    assert data is not None
    declared = manifest.get("template")
    if not isinstance(declared, dict):
        return [
            _error(
                "invalid-package",
                "manifest.template 缺失或不是对象",
                target="template",
            )
        ]
    for key in ("id", "version", "schema_version", "language"):
        if declared.get(key) != data.get(key):
            issues.append(
                _error(
                    "manifest-mismatch",
                    f"manifest.template.{key} 与 template.yaml 不一致："
                    f"{declared.get(key)!r} != {data.get(key)!r}",
                    target=f"template.{key}",
                )
            )
    yaml_compatibility = data.get("compatibility")
    if (
        isinstance(yaml_compatibility, dict)
        and isinstance(manifest.get("compatibility"), dict)
        and manifest["compatibility"] != yaml_compatibility
    ):
        issues.append(
            _error(
                "manifest-mismatch",
                "manifest.compatibility 与 template.yaml compatibility 不一致",
                target="compatibility",
            )
        )
    return issues


def verify_package(
    tftpl_path: str | Path,
    *,
    host_version: str = _HOST_VERSION,
    search_roots: tuple[Path, ...] | None = None,
) -> VerifyReport:
    """校验 `.tftpl`（§7.4 第 5 条：防护 + 哈希对账 + L1–L3 全量 + 签名检查）。"""
    tftpl = Path(tftpl_path).expanduser()
    if not tftpl.is_absolute():
        tftpl = Path.cwd() / tftpl
    if not tftpl.is_file():
        return VerifyReport(
            path=tftpl,
            issues=(
                _error(
                    "missing-package-file",
                    f".tftpl 文件不存在：{tftpl}",
                    target=str(tftpl),
                ),
            ),
            package=None,
        )

    import tempfile

    with tempfile.TemporaryDirectory(prefix="thesisforge-tftpl-") as tmp:
        dest = Path(tmp) / "package"
        try:
            unpack_package(tftpl, dest, host_version=host_version)
        except PackError as error:
            return VerifyReport(path=tftpl, issues=error.issues, package=None)

        issues: list[ValidationIssue] = []
        try:
            with zipfile.ZipFile(tftpl) as archive:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError):
            manifest = None
        if isinstance(manifest, dict):
            issues.extend(_check_manifest_template_match(manifest, dest))

        # §7.3：未签名不是错误（info）；签名存在但当前版本不做加密校验（OQ-6）
        if (dest / "signature.json").is_file():
            issues.append(
                _issue(
                    "signature-unverified",
                    "warning",
                    "signature.json 存在，但签名验证尚未实现（§7.3 OQ-6），跳过校验",
                    target="signature.json",
                )
            )
        else:
            issues.append(
                _issue(
                    "signature-absent",
                    "info",
                    "包未签名（§7.3：未签名不是错误）",
                    target="signature.json",
                )
            )

        lint_report = _lint.lint_package(dest, search_roots=search_roots)
        issues.extend(lint_report.issues)

        package: pkg.ResolvedTemplatePackage | None = None
        if not any(issue.severity == "error" for issue in issues):
            try:
                package = pkg.load_package(
                    dest, search_roots=search_roots, host_version=host_version
                )
            except pkg.PackageLoadError as error:
                issues.extend(error.issues)
        return VerifyReport(path=tftpl, issues=tuple(issues), package=package)
