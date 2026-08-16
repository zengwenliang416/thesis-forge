"""Template Package v2 目录加载器（SCHEMA §1/§3/§4.3/§8.3）。

职责：
- 读取 `template.yaml`（`schema_version` 必须为 2，否则 `unsupported-schema-version`
  结构化错误并附 `template migrate` 指引，不 fallback 解释旧模板，R-026）；
- 读取 `provenance.yaml`（结构校验在 lint 层，这里容错解析）；
- 包内引用路径安全检查（§1.3，越出包目录一律 `package-path-unsafe`）；
- extends 继承解析（§4.3 决策 D-2：白名单节 map 深合并、list 一律 replace、
  禁环、链长 ≤ 8、本地模板根解析、版本区间与 sha256 锁定）。

产出 `ResolvedTemplatePackage`。加载失败抛 `PackageLoadError`，携带结构化
`ValidationIssue` 列表（码、级别、字段路径、消息），不散落 print。
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from thesis_forge import __version__ as _HOST_VERSION
from thesis_forge.core.model import ValidationIssue

from .schema import (
    ProvenanceSpec,
    TemplatePackageSpec,
    parse_semver,
    version_satisfies,
)

SCHEMA_VERSION = 2
MAX_INHERITANCE_DEPTH = 8

# §4.3 决策 D-2 第 1 条：仅这些节参与继承合并；header/compatibility/extends/
# provenance.yaml 不继承，每个包必须自带。
INHERITABLE_SECTIONS = (
    "word",
    "page",
    "fonts",
    "font_policy",
    "styles",
    "body",
    "headings",
    "regions",
    "sections",
    "numbering",
    "figures",
    "tables",
    "equations",
    "fields",
    "cross_references",
    "toc",
    "bibliography",
    "layouts",
)

# §4.3 第 3 条：文件引用按「声明方包内解析」。key → 声明定位用的点分路径。
_FILE_REF_FIELDS = (
    ("word", "reference_docx"),
    ("word", "shell_docx"),
    ("bibliography", "style_file"),
    ("bibliography", "overrides_file"),
)

_ABSOLUTE_PATH_RE = re.compile(r"^(?:/|\\|[A-Za-z]:[\\/]?)")


class PackageLoadError(ValueError):
    """包加载失败；`issues` 为结构化 ValidationIssue 元组。"""

    def __init__(self, path: Path, issues: tuple[ValidationIssue, ...]):
        self.path = path
        self.issues = issues
        detail = "; ".join(
            f"[{issue.code}] {issue.target or ''} {issue.message}".strip()
            for issue in issues[:5]
        )
        super().__init__(f"模板包无效: {path}: {detail}")


@dataclass(frozen=True, slots=True)
class InheritanceEntry:
    id: str
    version: str
    path: Path
    sha256: str


@dataclass(frozen=True, slots=True)
class ResolvedTemplatePackage:
    path: Path
    template: TemplatePackageSpec
    resolved_data: dict[str, Any]
    inheritance_chain: tuple[InheritanceEntry, ...]
    section_sources: dict[str, str]
    reference_docx: Path
    shell_docx: Path | None
    provenance: ProvenanceSpec | None
    provenance_data: dict[str, Any] | None

    def file_reference(self, dotted: str) -> Path | None:
        """解析合并后声明的包内文件引用（如 bibliography.style_file）。"""
        node: Any = self.resolved_data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        if not isinstance(node, str):
            return None
        declaring = self._file_declaring_dirs.get(dotted, self.path)
        return declaring / node

    _file_declaring_dirs: dict[str, Path] = field(default_factory=dict)


def is_safe_package_path(rel: str) -> bool:
    """§1.3 第 1–3 条：相对、无盘符/反斜杠、规范化后无 ``..`` 段。"""
    if not isinstance(rel, str) or not rel:
        return False
    if _ABSOLUTE_PATH_RE.match(rel):
        return False
    if "\\" in rel:
        return False
    parts = rel.split("/")
    return all(part not in ("", ".", "..") for part in parts)


def resolve_within_package(package_dir: Path, rel: str) -> Path | None:
    """解析包内引用并验证符号链接不越出包目录（§1.3 第 4 条）。"""
    if not is_safe_package_path(rel):
        return None
    root = package_dir.resolve()
    candidate = (root / rel).resolve()
    if candidate != root and root not in candidate.parents:
        return None
    return candidate


def package_content_hash(package_dir: Path) -> str:
    """确定性包内容哈希：按 UTF-8 字节序排序的 (relpath, 文件 sha256) 累加。"""
    root = package_dir.resolve()
    entries: list[tuple[bytes, str]] = []
    for file in root.rglob("*"):
        if not file.is_file() or file.is_symlink():
            continue
        rel = file.relative_to(root).as_posix()
        entries.append((rel.encode("utf-8"), hashlib.sha256(file.read_bytes()).hexdigest()))
    digest = hashlib.sha256()
    for rel_bytes, file_hash in sorted(entries):
        digest.update(rel_bytes)
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _issue(code: str, message: str, *, target: str | None = None) -> ValidationIssue:
    return ValidationIssue(code=code, severity="error", message=message, target=target)


def _read_template_yaml(package_dir: Path) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    template_yaml = package_dir / "template.yaml"
    try:
        text = template_yaml.read_text(encoding="utf-8")
    except OSError as error:
        return None, [
            _issue(
                "missing-package-file",
                f"无法读取 template.yaml：{error.strerror or error}",
                target="template.yaml",
            )
        ]
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        return None, [
            _issue("invalid-template", f"template.yaml YAML 语法错误：{error}", target="$yaml")
        ]
    if not isinstance(data, dict):
        return None, [
            _issue("invalid-template", "template.yaml 顶层必须是映射", target="$root")
        ]
    return data, []


def _check_schema_version(data: dict[str, Any]) -> ValidationIssue | None:
    """§8.3：非 2 一律 unsupported-schema-version，不静默解释旧模板。"""
    version = data.get("schema_version")
    if version == SCHEMA_VERSION and isinstance(version, int):
        return None
    if isinstance(version, int) and version > SCHEMA_VERSION:
        hint = "schema_version 大于宿主支持版本，请升级 ThesisForge"
    else:
        hint = (
            "schema_version 缺失或低于 2：v2 加载器不解释旧模板，请运行 "
            "`thesisforge template migrate <legacy.yaml> -o <目录>` 显式迁移（ADR-0002 D-7）"
        )
    return _issue(
        "unsupported-schema-version",
        f"template.yaml 的 schema_version 必须为 2（实际 {version!r}）：{hint}",
        target="schema_version",
    )


def _check_referenced_paths(data: dict[str, Any]) -> list[ValidationIssue]:
    """对 template.yaml 中声明的包内引用路径做 §1.3 词法检查。"""
    issues: list[ValidationIssue] = []
    refs: list[tuple[str, Any]] = []
    word = data.get("word")
    if isinstance(word, dict):
        refs.append(("word.reference_docx", word.get("reference_docx")))
        refs.append(("word.shell_docx", word.get("shell_docx")))
    bibliography = data.get("bibliography")
    if isinstance(bibliography, dict):
        refs.append(("bibliography.style_file", bibliography.get("style_file")))
        refs.append(("bibliography.overrides_file", bibliography.get("overrides_file")))
    layouts = data.get("layouts")
    if isinstance(layouts, dict):
        for region, rel in layouts.items():
            refs.append((f"layouts.{region}", rel))
    for dotted, rel in refs:
        if rel is None:
            continue
        if not isinstance(rel, str) or not is_safe_package_path(rel):
            issues.append(
                _issue(
                    "package-path-unsafe",
                    f"包内引用路径必须是相对路径、不含 .. 段、不以盘符/斜杠开头：{rel!r}",
                    target=dotted,
                )
            )
    return issues


def _merge_section(parent_value: Any, child_value: Any) -> Any:
    """§4.3 第 2 条：map 深合并（子键覆盖父键）、list 一律 replace、标量子覆盖父。"""
    if child_value is None:
        return parent_value
    if parent_value is None:
        return child_value
    if isinstance(parent_value, dict) and isinstance(child_value, dict):
        merged = dict(parent_value)
        for key, value in child_value.items():
            merged[key] = _merge_section(parent_value.get(key), value)
        return merged
    return child_value


@dataclass
class _Resolution:
    data: dict[str, Any]
    chain: list[InheritanceEntry]
    section_sources: dict[str, str]
    file_declaring_dirs: dict[str, Path]
    issues: list[ValidationIssue]


def _iter_package_candidates(search_roots: tuple[Path, ...]) -> list[Path]:
    candidates: set[Path] = set()
    for root in search_roots:
        root = Path(root).expanduser()
        if not root.is_absolute():
            root = Path.cwd() / root
        if not root.is_dir():
            continue
        for template_yaml in root.resolve().rglob("template.yaml"):
            if template_yaml.is_file() and not template_yaml.name.startswith("._"):
                candidates.add(template_yaml.parent)
    return sorted(candidates)


def _read_package_header(
    package_dir: Path,
) -> tuple[str | None, str | None]:
    """轻量读取候选包 header（id/version），解析失败返回 (None, None)。"""
    try:
        data = yaml.safe_load(
            (package_dir / "template.yaml").read_text(encoding="utf-8")
        )
    except (OSError, yaml.YAMLError):
        return None, None
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        return None, None
    package_id = data.get("id")
    version = data.get("version")
    return (
        package_id if isinstance(package_id, str) else None,
        version if isinstance(version, str) else None,
    )


def _find_parent(
    extends: dict[str, Any], search_roots: tuple[Path, ...]
) -> tuple[Path | None, ValidationIssue | None]:
    """§4.3 第 5 条：本地模板根解析满足版本区间的最高版本父包；禁止网络。"""
    parent_id = extends.get("id")
    version_range = extends.get("version")
    candidates: list[tuple[tuple[int, int, int], Path]] = []
    saw_id = False
    for package_dir in _iter_package_candidates(search_roots):
        candidate_id, candidate_version = _read_package_header(package_dir)
        if candidate_id != parent_id:
            continue
        saw_id = True
        if not isinstance(version_range, str):
            continue
        try:
            if version_satisfies(version_range, candidate_version or ""):
                candidates.append((parse_semver(candidate_version), package_dir))
        except ValueError:
            continue
    if not candidates:
        if not saw_id:
            return None, _issue(
                "missing-template",
                f"extends.id 在本地模板根中无法解析（禁止网络加载）：{parent_id!r}",
                target="extends.id",
            )
        return None, _issue(
            "unsatisfied-parent-version",
            f"父模板 {parent_id!r} 没有满足版本区间 {version_range!r} 的本地候选",
            target="extends.version",
        )
    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1], None


def _resolve_package(
    package_dir: Path,
    search_roots: tuple[Path, ...],
    stack: tuple[Path, ...],
    host_version: str,
) -> _Resolution:
    """递归解析单包；所有失败都以 issues 形式累积在返回值中。"""
    issues: list[ValidationIssue] = []
    resolved_dir = package_dir.resolve()
    if resolved_dir in stack:
        cycle = [str(path) for path in (*stack, resolved_dir)]
        return _Resolution(
            data={},
            chain=[],
            section_sources={},
            file_declaring_dirs={},
            issues=[
                _issue(
                    "template-inheritance-cycle",
                    f"extends 继承链存在环：{' -> '.join(cycle)}",
                    target="extends",
                )
            ],
        )
    if len(stack) + 1 > MAX_INHERITANCE_DEPTH:
        return _Resolution(
            data={},
            chain=[],
            section_sources={},
            file_declaring_dirs={},
            issues=[
                _issue(
                    "inheritance-depth-exceeded",
                    f"extends 继承链长度超过 {MAX_INHERITANCE_DEPTH}",
                    target="extends",
                )
            ],
        )

    data, read_issues = _read_template_yaml(resolved_dir)
    if read_issues:
        return _Resolution({}, [], {}, {}, read_issues)
    assert data is not None
    version_issue = _check_schema_version(data)
    if version_issue is not None:
        return _Resolution({}, [], {}, {}, [version_issue])
    issues.extend(_check_referenced_paths(data))

    package_id = data.get("id") if isinstance(data.get("id"), str) else ""
    package_version = data.get("version") if isinstance(data.get("version"), str) else ""
    self_entry = InheritanceEntry(
        id=package_id,
        version=package_version,
        path=resolved_dir,
        sha256=package_content_hash(resolved_dir),
    )

    parent: _Resolution | None = None
    extends = data.get("extends")
    if isinstance(extends, dict):
        parent_dir, parent_error = _find_parent(extends, search_roots)
        if parent_error is not None:
            issues.append(parent_error)
        elif parent_dir is not None:
            parent = _resolve_package(
                parent_dir, search_roots, (*stack, resolved_dir), host_version
            )
            if not any(issue.severity == "error" for issue in parent.issues):
                locked = extends.get("sha256")
                if isinstance(locked, str) and parent.chain:
                    actual = parent.chain[0].sha256
                    if locked != actual:
                        issues.append(
                            _issue(
                                "hash-mismatch",
                                f"extends.sha256 与父包内容哈希不一致：声明 {locked}，"
                                f"实际 {actual}",
                                target="extends.sha256",
                            )
                        )

    # 合并：父模板已解析为 resolved 形态，再与子模板按白名单节合并。
    merged: dict[str, Any] = {}
    sources: dict[str, str] = {}
    file_dirs: dict[str, Path] = {}
    if parent is not None:
        issues.extend(parent.issues)
        for section, value in parent.data.items():
            if section in INHERITABLE_SECTIONS:
                merged[section] = value
        sources.update(parent.section_sources)
        file_dirs.update(parent.file_declaring_dirs)
    for section, value in data.items():
        if section in INHERITABLE_SECTIONS:
            merged[section] = _merge_section(merged.get(section), value)
            sources[section] = package_id
        else:
            merged[section] = value
    for section in list(sources):
        if section not in merged:
            del sources[section]

    # §4.3 第 3 条：文件引用由「声明方包内解析」；子声明则必须解析到子包。
    for section, key in _FILE_REF_FIELDS:
        node = data.get(section)
        if isinstance(node, dict) and isinstance(node.get(key), str):
            file_dirs[f"{section}.{key}"] = resolved_dir
    layouts = data.get("layouts")
    if isinstance(layouts, dict):
        for region, rel in layouts.items():
            if isinstance(rel, str):
                file_dirs[f"layouts.{region}"] = resolved_dir

    chain = [self_entry, *(parent.chain if parent is not None else [])]

    # 宿主兼容性（§3.2）：compatibility.thesisforge 不满足 → incompatible-thesisforge
    compatibility = merged.get("compatibility")
    if isinstance(compatibility, dict):
        host_range = compatibility.get("thesisforge")
        if isinstance(host_range, str):
            try:
                if not version_satisfies(host_range, host_version):
                    issues.append(
                        _issue(
                            "incompatible-thesisforge",
                            f"宿主 ThesisForge {host_version} 不满足模板兼容区间 "
                            f"{host_range!r}",
                            target="compatibility.thesisforge",
                        )
                    )
            except ValueError:
                pass  # 区间语法错误由模型校验报 invalid-template

    return _Resolution(merged, chain, sources, file_dirs, issues)


def default_package_search_roots() -> tuple[Path, ...]:
    """v2 包默认搜索根：签出目录 templates/packages（存在时）。"""
    checkout_root = Path(__file__).resolve().parents[4] / "templates" / "packages"
    return (checkout_root,) if checkout_root.is_dir() else ()


def load_package(
    path: str | Path,
    *,
    search_roots: tuple[Path, ...] | list[Path] | None = None,
    host_version: str = _HOST_VERSION,
) -> ResolvedTemplatePackage:
    """加载并解析 Template Package v2 目录；失败抛 `PackageLoadError`。"""
    package_dir = Path(path).expanduser()
    if not package_dir.is_absolute():
        package_dir = Path.cwd() / package_dir
    package_dir = package_dir.resolve()
    roots = (
        tuple(search_roots)
        if search_roots is not None
        else default_package_search_roots()
    )
    if not package_dir.is_dir():
        raise PackageLoadError(
            package_dir,
            (
                _issue(
                    "missing-package-file",
                    f"模板包目录不存在：{package_dir}",
                    target=str(package_dir),
                ),
            ),
        )

    resolution = _resolve_package(package_dir, roots, (), host_version)
    issues = list(resolution.issues)
    if any(issue.severity == "error" for issue in issues):
        raise PackageLoadError(package_dir, tuple(issues))

    template: TemplatePackageSpec | None = None
    try:
        template = TemplatePackageSpec.model_validate(resolution.data)
    except ValidationError as error:
        issues.extend(
            _issue(
                "invalid-template",
                item["msg"],
                target=".".join(str(part) for part in item["loc"]) or "$root",
            )
            for item in error.errors()
        )
        raise PackageLoadError(package_dir, tuple(issues)) from None
    assert template is not None

    provenance: ProvenanceSpec | None = None
    provenance_data: dict[str, Any] | None = None
    provenance_path = package_dir / "provenance.yaml"
    if provenance_path.is_file():
        try:
            raw_provenance = yaml.safe_load(provenance_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            raw_provenance = None
        if isinstance(raw_provenance, dict):
            provenance_data = raw_provenance
            try:
                provenance = ProvenanceSpec.model_validate(raw_provenance)
            except ValidationError:
                provenance = None  # 结构问题由 lint L1 provenance 检查报告

    file_dirs = dict(resolution.file_declaring_dirs)
    reference_dir = file_dirs.get("word.reference_docx", package_dir)
    reference_docx = reference_dir / template.word.reference_docx
    shell_docx = None
    if template.word.shell_docx is not None:
        shell_dir = file_dirs.get("word.shell_docx", package_dir)
        shell_docx = shell_dir / template.word.shell_docx

    return ResolvedTemplatePackage(
        path=package_dir,
        template=template,
        resolved_data=resolution.data,
        inheritance_chain=tuple(resolution.chain),
        section_sources=dict(resolution.section_sources),
        reference_docx=reference_docx,
        shell_docx=shell_docx,
        provenance=provenance,
        provenance_data=provenance_data,
        _file_declaring_dirs=file_dirs,
    )
