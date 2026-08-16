"""Template Package v2 lint（SCHEMA §6，L1–L5 完整实现）。

执行模型（§6）：默认 L1→L5 顺序执行；任一层出现 error 时更高层跳过；
`--level Ln` 可单层独立运行。全部检查离线、确定性（R-020）。所有问题输出
结构化 `ValidationIssue`（码、级别、字段路径/部件路径、消息）。

- L1 Package：必需文件、路径安全（§1.3）、宏/外部关系/OLE（§5.5 纯 ZIP
  条目/Content-Types/rels 扫描，不解析 XML 正文）、header 前置解析（§8.3）、
  README/CHANGELOG/provenance 存在与完整。
- L2 Schema：template.yaml 全量 schema（extra=forbid、类型、枚举、单位上下
  文、SemverRange）+ YAML 内交叉引用 + extends 继承合法性（§4.3）。
- L3 Word assets（§6.3）：OpenXML 校验（复用 qa/tools/openxml_validate.py）、
  token 样式存在/类型（含 §3.7.3 别名与 Word 内置样式回退）、样式引用闭包、
  锚点协议（§5.2）、relationships 完整性、header/footer 部件解析（§5.2.4）、
  shell 节策略比对、A 类漂移比对（§4.2）、sectPr 子元素顺序、theme 字体引用。
- L4 Semantic（§6.4）：required region 的 section 策略、条件必需 token、
  numbering source 存在、citation style 存在、矛盾属性（防御性复检）、
  outline level 一致、body 字号绝对、兼容矩阵标注、不生效配置、能力标记。
- L5 Fixture（§6.5）：fixtures 内 markdown 可被 parser/validator 接受 +
  reference.docx 可被 python-docx 起建新文档（副本语义，D-1）。

L5 集成缺口（本切片声明）：v2 包尚未对接编译管线（Compiler 不消费 v2 包、
无 region 边界 manifest，SCHEMA C-8），因此 §6.5 的「零 error 构建」降级为
「parser + validator 接受」，`expected/manifest.json` 的 XPath 断言与
`invalid-word-asset` 产物校验待管线集成后启用。
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

import yaml
from pydantic import ValidationError

from thesis_forge.core.model import ValidationIssue

from . import package as pkg
from .schema import (
    KNOWN_FONT_ROLES,
    SEMVER_RE,
    TEMPLATE_ID_RE,
    ProvenanceSpec,
)

LEVELS = ("L1", "L2", "L3", "L4", "L5")

_SINGLE_FILE_LIMIT = 64 * 1024 * 1024  # §1.3：64 MB
_PACKAGE_TOTAL_LIMIT = 512 * 1024 * 1024  # §1.3：512 MB

_RELS_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_PLATFORM_JUNK_NAMES = {".DS_Store", "__MACOSX"}
_SEMVER_TEXT_RE = re.compile(r"\d+\.\d+\.\d+")

# L3/L4 解析 Word 资产使用的命名空间（与 qa/tools/openxml_validate.py 对齐）
_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_CT_NS = "{http://schemas.openxmlformats.org/package/2006/content-types}"

# Word 内置样式 ID：可经 w:latentStyles 机制解析，不要求 styles.xml 显式定义
# （与 qa/tools/openxml_validate.py 的 BUILTIN_STYLE_IDS 保持一致）
_BUILTIN_STYLE_IDS = frozenset(
    {
        "BalloonText",
        "CommentReference",
        "CommentSubject",
        "CommentText",
        "EndnoteReference",
        "EndnoteText",
        "FollowedHyperlink",
        "FootnoteReference",
        "FootnoteText",
        "Hyperlink",
        "LineNumber",
        "PageNumber",
    }
)

# §3.5 page.size → portrait 下的 (w, h) twips
_PAGE_SIZES_TWIPS = {
    "A3": (16838, 23811),
    "A4": (11906, 16838),
    "A5": (8391, 11906),
    "Letter": (12240, 15840),
    "Legal": (12240, 20160),
}

# §3.11 page_number.format → w:pgNumType/@w:fmt
_PGNUM_FMT = {"decimal": "decimal", "roman-lower": "lowerRoman", "roman-upper": "upperRoman"}


@dataclass(frozen=True, slots=True)
class LintReport:
    path: Path
    issues: tuple[ValidationIssue, ...]
    levels_run: tuple[str, ...]

    @property
    def errors(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warnings(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)

    @property
    def has_errors(self) -> bool:
        return self.errors > 0


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


def _warning(code: str, message: str, *, target: str | None = None) -> ValidationIssue:
    return _issue(code, "warning", message, target=target)


def _info(code: str, message: str, *, target: str | None = None) -> ValidationIssue:
    return _issue(code, "info", message, target=target)


# ---------------------------------------------------------------------------
# L1 Package
# ---------------------------------------------------------------------------


def _read_raw_template(package_dir: Path) -> tuple[dict | None, list[ValidationIssue]]:
    data, issues = pkg._read_template_yaml(package_dir)
    return data, issues


def _check_path_safety_walk(package_dir: Path) -> list[ValidationIssue]:
    """§1.3/§1.2：符号链接越界、平台垃圾、保留路径、解压尺寸上限。"""
    issues: list[ValidationIssue] = []
    root = package_dir.resolve()
    total = 0
    for entry in sorted(root.rglob("*")):
        rel = entry.relative_to(root).as_posix()
        if entry.is_symlink():
            target = entry.resolve()
            if target != root and root not in target.parents:
                issues.append(
                    _error(
                        "package-path-unsafe",
                        f"符号链接指向包外：{rel} -> {target}",
                        target=rel,
                    )
                )
            continue
        parts = rel.split("/")
        name = parts[-1]
        if name in _PLATFORM_JUNK_NAMES or name.startswith("._"):
            issues.append(
                _warning(
                    "package-path-conflict",
                    f"平台垃圾文件，打包时将剔除：{rel}",
                    target=rel,
                )
            )
            continue
        if name.startswith(".") or any(part.startswith(".") for part in parts[:-1]):
            continue  # §1.2：隐藏文件 lint 忽略、不打包
        if rel == "manifest.json":
            issues.append(
                _warning(
                    "package-path-conflict",
                    "manifest.json 是 .tftpl 打包产物保留路径，目录形态下将被剔除重建",
                    target=rel,
                )
            )
        if not entry.is_file():
            continue
        size = entry.stat().st_size
        total += size
        if size > _SINGLE_FILE_LIMIT:
            issues.append(
                _error(
                    "package-path-unsafe",
                    f"单文件超过 64 MB 上限：{rel}（{size} 字节）",
                    target=rel,
                )
            )
    if total > _PACKAGE_TOTAL_LIMIT:
        issues.append(
            _error(
                "package-path-unsafe",
                f"包总量超过 512 MB 上限（{total} 字节）",
                target=str(package_dir),
            )
        )
    return issues


def _scan_docx_security(
    docx_path: Path,
    *,
    label: str,
    policy: str,
    allowlist: list[str],
) -> list[ValidationIssue]:
    """§5.5：宏/外部关系/OLE 扫描（纯 ZIP 条目 + Content-Types + rels）。"""
    issues: list[ValidationIssue] = []
    try:
        archive = zipfile.ZipFile(docx_path)
    except (OSError, zipfile.BadZipFile):
        return issues  # 不可读由 L3 浅检查报告
    with archive:
        names = archive.namelist()
        macro = any(name.endswith("vbaProject.bin") for name in names)
        if "[Content_Types].xml" in names:
            content_types = archive.read("[Content_Types].xml").decode(
                "utf-8", errors="replace"
            )
            if "macroEnabled" in content_types:
                macro = True
        if macro:
            issues.append(
                _error(
                    "macro-detected",
                    f"{label} 含宏（vbaProject/macroEnabled），macro_policy 仅允许 forbid",
                    target=label,
                )
            )
        if any(
            name.startswith(("word/embeddings/", "word/activeX/")) for name in names
        ):
            issues.append(
                _error(
                    "ole-detected",
                    f"{label} 含 OLE/嵌入对象部件（word/embeddings/ 或 word/activeX/）",
                    target=label,
                )
            )
        for name in names:
            if not name.endswith(".rels"):
                continue
            try:
                root = ElementTree.fromstring(archive.read(name))
            except ElementTree.ParseError:
                continue
            for rel in root.iter(f"{_RELS_NS}Relationship"):
                if rel.get("TargetMode") != "External":
                    continue
                target_url = rel.get("Target") or ""
                where = f"{label}!{name}"
                if policy == "allowlist" and _in_allowlist(target_url, allowlist):
                    issues.append(
                        _info(
                            "external-relationship",
                            f"外部关系命中白名单：{target_url}",
                            target=where,
                        )
                    )
                else:
                    issues.append(
                        _error(
                            "external-relationship",
                            f"外部关系被策略 {policy} 拒绝：{target_url}",
                            target=where,
                        )
                    )
    return issues


def _in_allowlist(target_url: str, allowlist: list[str]) -> bool:
    parsed = urlparse(target_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    for entry in allowlist:
        allowed = urlparse(entry)
        allowed_origin = f"{allowed.scheme}://{allowed.netloc}"
        if allowed.scheme and origin == allowed_origin:
            return True
    return False


def _check_header_preflight(data: dict) -> list[ValidationIssue]:
    """§6.1 header 前置解析：schema_version（§8.3）+ id/version 格式。"""
    issues: list[ValidationIssue] = []
    version_issue = pkg._check_schema_version(data)
    if version_issue is not None:
        issues.append(version_issue)
    template_id = data.get("id")
    if not isinstance(template_id, str) or TEMPLATE_ID_RE.fullmatch(template_id) is None:
        issues.append(
            _error(
                "invalid-template",
                f"模板 id 缺失或格式无效：{template_id!r}（SCHEMA §3.1 正则）",
                target="id",
            )
        )
    version = data.get("version")
    if not isinstance(version, str) or SEMVER_RE.fullmatch(version) is None:
        issues.append(
            _error(
                "invalid-template",
                f"version 缺失或不是 Semver：{version!r}",
                target="version",
            )
        )
    return issues


def _check_required_files(
    package_dir: Path, data: dict
) -> tuple[list[ValidationIssue], dict[str, Path | None]]:
    """§1.1 必需性核对；返回 issues 与 docx 部件路径（供安全扫描/L3）。"""
    issues: list[ValidationIssue] = []
    word = data.get("word") if isinstance(data.get("word"), dict) else {}
    reference_rel = word.get("reference_docx", "reference.docx")
    shell_rel = word.get("shell_docx")

    reference_docx: Path | None = None
    if isinstance(reference_rel, str) and pkg.is_safe_package_path(reference_rel):
        candidate = package_dir / reference_rel
        if not candidate.is_file():
            issues.append(
                _error(
                    "missing-package-file",
                    f"必需文件缺失：{reference_rel}",
                    target=reference_rel,
                )
            )
        else:
            reference_docx = candidate
    shell_docx: Path | None = None
    if isinstance(shell_rel, str) and pkg.is_safe_package_path(shell_rel):
        candidate = package_dir / shell_rel
        if not candidate.is_file():
            issues.append(
                _error(
                    "missing-package-file",
                    f"word.shell_docx 声明的文件缺失：{shell_rel}",
                    target="word.shell_docx",
                )
            )
        else:
            shell_docx = candidate

    if not (package_dir / "provenance.yaml").is_file():
        issues.append(
            _error(
                "provenance-missing",
                "provenance.yaml 缺失（§1.1 必需，R-024）",
                target="provenance.yaml",
            )
        )
    if not (package_dir / "README.md").is_file():
        issues.append(
            _error(
                "readme-missing",
                "README.md 缺失（必须包含使用说明与「已知限制」一节）",
                target="README.md",
            )
        )
    minimal = package_dir / "fixtures" / "minimal"
    if not minimal.is_dir() or not any(minimal.iterdir()):
        issues.append(
            _error(
                "missing-package-file",
                "fixtures/minimal/ 缺失或为空（§1.1 必需）",
                target="fixtures/minimal",
            )
        )

    # CHANGELOG：目录形态开发期缺失为 warning（§1.1/§6.1）；存在时对账版本
    changelog = package_dir / "CHANGELOG.md"
    header_version = data.get("version")
    if not changelog.is_file():
        issues.append(
            _warning(
                "missing-package-file",
                "CHANGELOG.md 缺失（打包时必需，目录形态开发期为警告）",
                target="CHANGELOG.md",
            )
        )
    elif isinstance(header_version, str):
        head = changelog.read_text(encoding="utf-8", errors="replace")[:2000]
        match = _SEMVER_TEXT_RE.search(head)
        if match is None or match.group(0) != header_version:
            issues.append(
                _error(
                    "changelog-version-mismatch",
                    "CHANGELOG 顶部版本号与 header.version 不一致："
                    f"{match.group(0) if match else '未找到'} != {header_version}",
                    target="CHANGELOG.md",
                )
            )

    # 声明的包内文件引用存在性（§1.1 missing-template-asset）
    bibliography = data.get("bibliography")
    if isinstance(bibliography, dict):
        overrides = bibliography.get("overrides_file")
        if (
            isinstance(overrides, str)
            and pkg.is_safe_package_path(overrides)
            and not (package_dir / overrides).is_file()
        ):
            issues.append(
                _error(
                    "missing-template-asset",
                    f"bibliography.overrides_file 声明的文件缺失：{overrides}",
                    target="bibliography.overrides_file",
                )
            )
    layouts = data.get("layouts")
    if isinstance(layouts, dict):
        for region, rel in layouts.items():
            if (
                isinstance(rel, str)
                and pkg.is_safe_package_path(rel)
                and not (package_dir / rel).is_file()
            ):
                issues.append(
                    _error(
                        "missing-template-asset",
                        f"layouts.{region} 声明的文件缺失：{rel}",
                        target=f"layouts.{region}",
                    )
                )

    # LICENSES 条件必需（§1.1/§3.21，R-024）；目录形态 lint 记 warning，
    # 打包（未实现切片）时升级为 error
    licenses_dir = package_dir / "LICENSES"
    provenance_data = _read_provenance_raw(package_dir)
    school_assets = None
    if isinstance(provenance_data, dict):
        licenses = provenance_data.get("licenses")
        if isinstance(licenses, dict):
            school_assets = licenses.get("school_assets")
    if school_assets == "restricted" and not licenses_dir.is_dir():
        issues.append(
            _warning(
                "missing-package-file",
                "licenses.school_assets 为 restricted：LICENSES/ 必须含说明"
                "（打包时升级为 error，R-024）",
                target="LICENSES",
            )
        )
    font_policy = data.get("font_policy")
    if (
        isinstance(font_policy, dict)
        and font_policy.get("embed_fonts") is True
        and not licenses_dir.is_dir()
    ):
        issues.append(
            _error(
                "missing-package-file",
                "font_policy.embed_fonts: true 要求 LICENSES/ 含字体授权",
                target="LICENSES",
            )
        )
    return issues, {"reference_docx": reference_docx, "shell_docx": shell_docx}


def _read_provenance_raw(package_dir: Path) -> dict | None:
    try:
        raw = yaml.safe_load(
            (package_dir / "provenance.yaml").read_text(encoding="utf-8")
        )
    except (OSError, yaml.YAMLError):
        return None
    return raw if isinstance(raw, dict) else None


def _check_provenance(package_dir: Path) -> list[ValidationIssue]:
    """§3.21：provenance 存在性与完整性（必需字段缺失 → provenance-incomplete error）。"""
    provenance_path = package_dir / "provenance.yaml"
    if not provenance_path.is_file():
        return []  # provenance-missing 已在必需文件检查报告
    try:
        text = provenance_path.read_text(encoding="utf-8")
    except OSError as error:
        return [
            _error(
                "provenance-incomplete",
                f"provenance.yaml 无法读取：{error.strerror or error}",
                target="provenance.yaml",
            )
        ]
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as error:
        return [
            _error(
                "provenance-incomplete",
                f"provenance.yaml YAML 语法错误：{error}",
                target="provenance.yaml",
            )
        ]
    try:
        ProvenanceSpec.model_validate(raw)
    except ValidationError as error:
        return [
            _error(
                "provenance-incomplete",
                item["msg"],
                target=".".join(str(part) for part in item["loc"]) or "$root",
            )
            for item in error.errors()
        ]
    return []


def lint_l1(package_dir: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not (package_dir / "template.yaml").is_file():
        return [
            _error(
                "missing-package-file",
                "template.yaml 缺失（§1.1 必需）",
                target="template.yaml",
            )
        ]
    data, read_issues = _read_raw_template(package_dir)
    issues.extend(read_issues)
    issues.extend(_check_path_safety_walk(package_dir))
    docx_parts: dict[str, Path | None] = {"reference_docx": None, "shell_docx": None}
    if data is not None:
        issues.extend(_check_header_preflight(data))
        file_issues, docx_parts = _check_required_files(package_dir, data)
        issues.extend(file_issues)
    issues.extend(_check_provenance(package_dir))
    # §5.5 安全扫描（宏/外部关系/OLE）；策略取 YAML 声明，解析失败按 forbid
    policy = "forbid"
    allowlist: list[str] = []
    if data is not None and isinstance(data.get("word"), dict):
        word = data["word"]
        if word.get("external_relationships") == "allowlist":
            policy = "allowlist"
            raw_allowlist = word.get("external_relationship_allowlist")
            if isinstance(raw_allowlist, list):
                allowlist = [str(item) for item in raw_allowlist]
    for label, docx_path in (
        ("reference.docx", docx_parts["reference_docx"]),
        ("shell.docx", docx_parts["shell_docx"]),
    ):
        if docx_path is not None:
            issues.extend(
                _scan_docx_security(
                    docx_path, label=label, policy=policy, allowlist=allowlist
                )
            )
    return issues


# ---------------------------------------------------------------------------
# L2 Schema
# ---------------------------------------------------------------------------


def _collect_alias_infos(resolved_data: dict) -> list[ValidationIssue]:
    """偏差记录 C-5：sections.*.start: next_page 接受为别名并 info 提示。"""
    issues: list[ValidationIssue] = []
    sections = resolved_data.get("sections")
    if isinstance(sections, dict):
        for name, section in sections.items():
            if isinstance(section, dict) and section.get("start") == "next_page":
                issues.append(
                    _info(
                        "section-start-alias",
                        f"sections.{name}.start: next_page 是 new_page 的别名，"
                        "建议改用规范值 new_page",
                        target=f"sections.{name}.start",
                    )
                )
    return issues


def _collect_font_role_warnings(resolved_data: dict) -> list[ValidationIssue]:
    fonts = resolved_data.get("fonts")
    issues: list[ValidationIssue] = []
    if isinstance(fonts, dict):
        for role in fonts:
            if role not in KNOWN_FONT_ROLES:
                issues.append(
                    _warning(
                        "unknown-font-role",
                        f"未知字体角色 {role!r}（已知：{', '.join(KNOWN_FONT_ROLES)}）；"
                        "渲染器将忽略该角色",
                        target=f"fonts.{role}",
                    )
                )
    return issues


def _collect_layout_warnings(package_dir: Path, resolved_data: dict) -> list[ValidationIssue]:
    """§1.1：未被 template.yaml layouts 节引用的 layout 文件报 warning。"""
    issues: list[ValidationIssue] = []
    layouts_dir = package_dir / "layouts"
    if not layouts_dir.is_dir():
        return issues
    referenced = set()
    layouts = resolved_data.get("layouts")
    if isinstance(layouts, dict):
        referenced = {str(rel) for rel in layouts.values() if isinstance(rel, str)}
    for file in sorted(layouts_dir.glob("*.yaml")):
        rel = file.relative_to(package_dir).as_posix()
        if rel not in referenced:
            issues.append(
                _warning(
                    "unreferenced-layout-file",
                    f"layout 文件未被 template.yaml 的 layouts 节引用：{rel}",
                    target=rel,
                )
            )
    return issues


def lint_l2(
    package_dir: Path,
    *,
    search_roots: tuple[Path, ...] | None = None,
) -> tuple[list[ValidationIssue], pkg.ResolvedTemplatePackage | None]:
    try:
        resolved = pkg.load_package(package_dir, search_roots=search_roots)
    except pkg.PackageLoadError as error:
        return list(error.issues), None
    issues: list[ValidationIssue] = []
    issues.extend(_collect_alias_infos(resolved.resolved_data))
    issues.extend(_collect_font_role_warnings(resolved.resolved_data))
    issues.extend(_collect_layout_warnings(package_dir, resolved.resolved_data))
    # styles/aliases.yaml（§3.7.3）：键必须是已声明 token 值
    aliases_path = package_dir / "styles" / "aliases.yaml"
    if aliases_path.is_file():
        try:
            raw = yaml.safe_load(aliases_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raw = None
            issues.append(
                _error(
                    "invalid-template",
                    f"styles/aliases.yaml 解析失败：{error}",
                    target="styles/aliases.yaml",
                )
            )
        if isinstance(raw, dict):
            token_values = set(resolved.template.styles.paragraph.declared().values())
            token_values |= set(resolved.template.styles.heading.declared().values())
            token_values |= set(resolved.template.styles.character.declared().values())
            for key in raw:
                if key not in token_values:
                    issues.append(
                        _error(
                            "invalid-template",
                            f"styles/aliases.yaml 的键必须是已声明的 style token 值：{key!r}",
                            target="styles/aliases.yaml",
                        )
                    )
        elif raw is not None:
            issues.append(
                _error(
                    "invalid-template",
                    "styles/aliases.yaml 顶层必须是 map[样式名, list[别名]]",
                    target="styles/aliases.yaml",
                )
            )
    return issues, resolved


# ---------------------------------------------------------------------------
# L3 Word assets（§6.3）
# ---------------------------------------------------------------------------


def _load_openxml_validate():
    """复用 qa/tools/openxml_validate.py（§6.3「同级检查」）；缺失时返回 None。"""
    import importlib.util
    import sys

    tool = Path(__file__).resolve().parents[4] / "qa" / "tools" / "openxml_validate.py"
    if not tool.is_file():
        return None
    spec = importlib.util.spec_from_file_location("openxml_validate", tool)
    module = importlib.util.module_from_spec(spec)
    # dataclass 处理依赖 sys.modules 反查模块命名空间，exec 前必须注册
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module.validate_docx


def _read_docx_part(docx_path: Path, name: str):
    """读取并解析 docx 内 XML 部件；失败返回 None（lxml 根元素）。"""
    from lxml import etree

    try:
        with zipfile.ZipFile(docx_path) as archive:
            return etree.fromstring(archive.read(name))
    except (OSError, KeyError, zipfile.BadZipFile, etree.XMLSyntaxError):
        return None


def _docx_part_names(docx_path: Path) -> set[str]:
    try:
        with zipfile.ZipFile(docx_path) as archive:
            return set(archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return set()


def _styles_index(styles_root) -> tuple[dict[str, object], dict[str, object]]:
    """styles.xml 索引：by_name / by_id（值为 w:style 元素）。"""
    by_name: dict[str, object] = {}
    by_id: dict[str, object] = {}
    for style in styles_root.iter(f"{_W_NS}style"):
        style_id = style.get(f"{_W_NS}styleId")
        if style_id:
            by_id[style_id] = style
        name_el = style.find(f"{_W_NS}name")
        name = name_el.get(f"{_W_NS}val") if name_el is not None else None
        if name:
            by_name[name] = style
    return by_name, by_id


def _load_aliases(package_dir: Path) -> dict[str, list[str]]:
    """styles/aliases.yaml（§3.7.3）：map[样式名, list[别名]]；解析失败由 L2 报告。"""
    path = package_dir / "styles" / "aliases.yaml"
    if not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): [str(item) for item in value]
        for key, value in raw.items()
        if isinstance(value, list)
    }


def _resolve_token_style(name: str, by_name, by_id, aliases):
    """按主名 → styleId → 别名 → Word 内置样式解析 token 样式。

    返回 (元素 | "builtin" | None, 是否命中别名)。
    """
    if name in by_name:
        return by_name[name], False
    if name in by_id:
        return by_id[name], False
    for alias in aliases.get(name, ()):
        if alias in by_name:
            return by_name[alias], True
        if alias in by_id:
            return by_id[alias], True
    if name.replace(" ", "") in _BUILTIN_STYLE_IDS:
        return "builtin", False
    return None, False


def _check_token_styles(
    resolved: pkg.ResolvedTemplatePackage, package_dir: Path
) -> list[ValidationIssue]:
    """§6.3：token 样式存在/类型（missing-token-style/style-type-mismatch）。"""
    issues: list[ValidationIssue] = []
    styles_root = _read_docx_part(resolved.reference_docx, "word/styles.xml")
    if styles_root is None:
        return [
            _error(
                "missing-token-style",
                "reference.docx 缺少 word/styles.xml，全部 token 样式无法解析",
                target="reference.docx",
            )
        ]
    by_name, by_id = _styles_index(styles_root)
    aliases = _load_aliases(package_dir)
    styles = resolved.template.styles
    token_entries: list[tuple[str, str, str]] = [
        (f"styles.paragraph.{token}", name, "paragraph")
        for token, name in styles.paragraph.declared().items()
    ]
    token_entries += [
        (f"styles.heading.{level}", name, "paragraph")
        for level, name in styles.heading.declared().items()
    ]
    token_entries += [
        (f"styles.character.{token}", name, "character")
        for token, name in styles.character.declared().items()
    ]
    for target, name, expected_type in token_entries:
        element, via_alias = _resolve_token_style(name, by_name, by_id, aliases)
        if element is None:
            issues.append(
                _error(
                    "missing-token-style",
                    f"token 样式 {name!r} 在 reference.docx 的 styles.xml 中不存在"
                    "（含别名与内置样式回退均未命中）",
                    target=target,
                )
            )
            continue
        if via_alias:
            issues.append(
                _info(
                    "style-alias-hit",
                    f"token 样式 {name!r} 经别名命中：{element.get(f'{_W_NS}styleId')}",
                    target=target,
                )
            )
        if element == "builtin":
            continue
        actual_type = element.get(f"{_W_NS}type")
        if actual_type != expected_type:
            issues.append(
                _error(
                    "style-type-mismatch",
                    f"token 样式 {name!r} 类型应为 {expected_type}，实际 {actual_type}",
                    target=target,
                )
            )
        # §5.1 第 3 条：token 样式必须显式 rFonts，不得引用 theme 字体属性
        rfonts = element.find(f"{_W_NS}rPr/{_W_NS}rFonts")
        if rfonts is not None and any("Theme" in key for key in rfonts.attrib):
            issues.append(
                _warning(
                    "theme-font-reference",
                    f"token 样式 {name!r} 引用了 theme 字体属性"
                    f"（{', '.join(k for k in rfonts.attrib if 'Theme' in k)}）",
                    target=target,
                )
            )
    return issues


def _check_style_closure(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§3.7.2：style ID 重复（error）；basedOn/next/link 引用必须存在（error）。"""
    issues: list[ValidationIssue] = []
    styles_root = _read_docx_part(resolved.reference_docx, "word/styles.xml")
    if styles_root is None:
        return issues
    seen: set[str] = set()
    for style in styles_root.iter(f"{_W_NS}style"):
        style_id = style.get(f"{_W_NS}styleId")
        if style_id in seen:
            issues.append(
                _error(
                    "invalid-template",
                    f"reference.docx styles.xml 存在重复 styleId：{style_id}",
                    target=f"word/styles.xml#{style_id}",
                )
            )
        seen.add(style_id)
    for style in styles_root.iter(f"{_W_NS}style"):
        style_id = style.get(f"{_W_NS}styleId")
        for tag in ("basedOn", "next", "link"):
            link = style.find(f"{_W_NS}{tag}")
            target = link.get(f"{_W_NS}val") if link is not None else None
            if target and target not in seen:
                issues.append(
                    _error(
                        "invalid-template",
                        f"样式 {style_id} 的 {tag} 引用不存在的样式：{target}",
                        target=f"word/styles.xml#{style_id}",
                    )
                )
    return issues


def _check_reference_body(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§5.1 第 1 条：reference.docx 正文应为空或仅含可清理占位段落。"""
    document = _read_docx_part(resolved.reference_docx, "word/document.xml")
    if document is None:
        return []
    body = document.find(f"{_W_NS}body")
    if body is None:
        return []
    paragraphs = body.findall(f"{_W_NS}p")
    if not paragraphs:
        return []
    has_text = any(
        "".join(paragraph.itertext()).strip() for paragraph in paragraphs
    )
    if has_text:
        return [
            _warning(
                "reference-body-not-empty",
                "reference.docx 正文含非占位内容，加载时应清理（§5.1 第 1 条）",
                target="reference.docx",
            )
        ]
    return [
        _info(
            "reference-body-not-empty",
            f"reference.docx 含 {len(paragraphs)} 个空占位段落，加载时移除并记录",
            target="reference.docx",
        )
    ]


def _check_anchors(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§5.2.1/§5.2.2 锚点协议：配对、唯一性、body 必需、未声明 tf_*、占位内容。"""
    issues: list[ValidationIssue] = []
    if resolved.shell_docx is None:
        return issues
    document = _read_docx_part(resolved.shell_docx, "word/document.xml")
    if document is None:
        return []
    declared = {
        "body": "tf_body", "toc": "tf_toc", "bibliography": "tf_bibliography",
        **resolved.template.word.anchors,
    }
    starts: dict[str, list] = {}
    end_ids: set[str] = set()
    start_ids: dict[str, str] = {}
    for el in document.iter(f"{_W_NS}bookmarkStart"):
        name = el.get(f"{_W_NS}name") or ""
        starts.setdefault(name, []).append(el)
        start_ids[name] = el.get(f"{_W_NS}id") or ""
    for el in document.iter(f"{_W_NS}bookmarkEnd"):
        end_ids.add(el.get(f"{_W_NS}id") or "")
    for name, elements in sorted(starts.items()):
        if name.startswith("tf_") and name not in declared.values():
            issues.append(
                _warning(
                    "anchor-undeclared",
                    f"shell.docx 存在未在 word.anchors 声明的 tf_* 书签：{name}",
                    target=f"shell.docx#{name}",
                )
            )
    for slot, name in sorted(declared.items()):
        elements = starts.get(name, [])
        if len(elements) > 1:
            issues.append(
                _error(
                    "anchor-duplicate",
                    f"锚点 {name}（{slot}）在 shell.docx 中出现 {len(elements)} 次，"
                    "必须恰好一次",
                    target=f"shell.docx#{name}",
                )
            )
            continue
        if not elements:
            if slot == "body":
                issues.append(
                    _error(
                        "missing-body-anchor",
                        f"shell.docx 缺少必需的 body 锚点书签 {name}（§5.2.2 阻断）",
                        target=f"shell.docx#{name}",
                    )
                )
            elif slot in resolved.template.regions.order or (
                slot == "toc" and resolved.template.toc.enabled
            ):
                issues.append(
                    _warning(
                        "anchor-fallback",
                        f"shell.docx 缺少 {slot} 锚点 {name}：对应内容将按 "
                        "regions.order 并入 body 槽投递（§5.2.2）",
                        target=f"shell.docx#{name}",
                    )
                )
            continue
        bookmark = elements[0]
        if start_ids.get(name) not in end_ids:
            issues.append(
                _error(
                    "bookmark-unpaired",
                    f"锚点 {name} 的 bookmarkStart 缺少配对 bookmarkEnd",
                    target=f"shell.docx#{name}",
                )
            )
        paragraph = bookmark.getparent()
        if (
            paragraph is not None
            and paragraph.tag == f"{_W_NS}p"
            and "".join(paragraph.itertext()).strip()
        ):
            issues.append(
                _warning(
                    "anchor-not-empty",
                    f"锚点 {name} 所在段落含内容，投递时将随锚点段落一并移除",
                    target=f"shell.docx#{name}",
                )
            )
    # §5.2.1：检测到同名 sdt → info，提示改用书签
    for sdt in document.iter(f"{_W_NS}sdt"):
        alias = sdt.find(f"{_W_NS}sdtPr/{_W_NS}alias")
        value = alias.get(f"{_W_NS}val") if alias is not None else None
        if value in declared.values():
            issues.append(
                _info(
                    "anchor-sdt",
                    f"检测到与锚点 {value} 同名的 content control（sdt）；"
                    "v2 以书签为规范实现，请改用书签",
                    target=f"shell.docx#{value}",
                )
            )
    return issues


def _check_sectpr_child_order(docx_path: Path, label: str) -> list[ValidationIssue]:
    """SPIKE §3.5：pgNumType 必须在 cols/docGrid 之前，否则 Word 修复提示。"""
    issues: list[ValidationIssue] = []
    document = _read_docx_part(docx_path, "word/document.xml")
    if document is None:
        return issues
    order = {
        f"{_W_NS}pgNumType": 0,
        f"{_W_NS}cols": 1,
        f"{_W_NS}docGrid": 2,
    }
    for index, sect_pr in enumerate(document.iter(f"{_W_NS}sectPr")):
        positions = [
            (order[child.tag], child.tag)
            for child in sect_pr
            if child.tag in order
        ]
        if positions != sorted(positions):
            issues.append(
                _error(
                    "invalid-word-asset",
                    f"{label} 第 {index + 1} 个 sectPr 子元素顺序违反 schema"
                    "（pgNumType 必须在 cols/docGrid 之前）",
                    target=f"{label}!word/document.xml",
                )
            )
    return issues


def _check_header_footer_parts(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§5.2.4：sections.*.header_footer 声明的部件名必须解析到 header/footer 部件。"""
    issues: list[ValidationIssue] = []
    candidates: dict[str, set[str]] = {}
    for label, docx_path in (
        ("shell.docx", resolved.shell_docx),
        ("reference.docx", resolved.reference_docx),
    ):
        if docx_path is None or not docx_path.is_file():
            continue
        names = _docx_part_names(docx_path)
        ct_root = _read_docx_part(docx_path, "[Content_Types].xml")
        overrides = (
            {
                (el.get("PartName") or "").lstrip("/"): el.get("ContentType") or ""
                for el in ct_root.iter(f"{_CT_NS}Override")
            }
            if ct_root is not None
            else {}
        )
        resolvable = {
            name[len("word/") : -len(".xml")]
            for name in names
            if name.startswith("word/")
            and name.endswith(".xml")
            and overrides.get(name, "").rsplit("/", 1)[-1] in ("header+xml", "footer+xml")
        }
        candidates[label] = resolvable
    all_parts = set().union(*candidates.values()) if candidates else set()
    for key in ("cover", "front_matter", "main", "back_matter"):
        section = getattr(resolved.template.sections, key)
        for slot in ("default", "first", "even"):
            value = getattr(section.header_footer, slot)
            if value == "none":
                continue
            if value not in all_parts:
                issues.append(
                    _error(
                        "unresolved-header-footer-part",
                        f"sections.{key}.header_footer.{slot} 声明的部件 {value!r} "
                        "无法解析到 shell.docx/reference.docx 的 header/footer 部件",
                        target=f"sections.{key}.header_footer.{slot}",
                    )
                )
    return issues


def _shell_sections(document) -> list:
    """shell 正文的 sectPr 序列（段落内嵌 + body 级，文档序）。"""
    return list(document.iter(f"{_W_NS}sectPr"))


def _check_section_policies(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§6.3：shell sectPr 与 §3.11 声明比对（页码格式/重启），warning 级。"""
    issues: list[ValidationIssue] = []
    if resolved.shell_docx is None:
        return issues
    document = _read_docx_part(resolved.shell_docx, "word/document.xml")
    if document is None:
        return issues
    sect_prs = _shell_sections(document)
    if not sect_prs:
        return issues
    # 约定映射：首个 sectPr ↔ front_matter，body 级（最后）sectPr ↔ main
    mapping: list[tuple[object, str]] = []
    if len(sect_prs) >= 2:
        mapping.append((sect_prs[0], "front_matter"))
    mapping.append((sect_prs[-1], "main"))
    for sect_pr, key in mapping:
        policy = getattr(resolved.template.sections, key).page_number
        pg_num = sect_pr.find(f"{_W_NS}pgNumType")
        label = f"shell.docx sectPr[{key}]"
        if not policy.display:
            continue  # display: false 时不比对格式/重启（§3.11）
        expected_fmt = _PGNUM_FMT[policy.effective_format]
        actual_fmt = pg_num.get(f"{_W_NS}fmt") if pg_num is not None else None
        if actual_fmt != expected_fmt:
            issues.append(
                _warning(
                    "section-policy-mismatch",
                    f"{label} 页码格式 {actual_fmt or '（缺省 decimal）'} 与 "
                    f"sections.{key}.page_number.format 声明的 {expected_fmt} 不一致",
                    target=f"sections.{key}.page_number.format",
                )
            )
        actual_start = pg_num.get(f"{_W_NS}start") if pg_num is not None else None
        if policy.restart is not None and actual_start != str(policy.restart):
            issues.append(
                _warning(
                    "section-policy-mismatch",
                    f"{label} 页码重启值 {actual_start or '（无）'} 与 "
                    f"sections.{key}.page_number.restart 声明的 {policy.restart} 不一致",
                    target=f"sections.{key}.page_number.restart",
                )
            )
        if policy.continue_ and actual_start is not None:
            issues.append(
                _warning(
                    "section-policy-mismatch",
                    f"{label} 声明了 w:start={actual_start}，与 "
                    f"sections.{key}.page_number.continue: true 矛盾",
                    target=f"sections.{key}.page_number.continue",
                )
            )
    return issues


def _check_template_reference_drift(
    resolved: pkg.ResolvedTemplatePackage,
) -> list[ValidationIssue]:
    """§4.2：A 类字段 YAML 值与 reference.docx sectPr 对应值漂移比对（warning）。"""
    issues: list[ValidationIssue] = []
    document = _read_docx_part(resolved.reference_docx, "word/document.xml")
    if document is None:
        return issues
    body = document.find(f"{_W_NS}body")
    sect_pr = body.find(f"{_W_NS}sectPr") if body is not None else None
    if sect_pr is None:
        return issues
    page = resolved.template.page

    def drift(field: str, expected: int | None, actual_raw: str | None) -> None:
        if expected is None or actual_raw is None:
            return  # 一侧未声明：不构成漂移证据
        try:
            actual = int(actual_raw)
        except ValueError:
            return
        if actual != expected:
            issues.append(
                _warning(
                    "template-reference-drift",
                    f"{field}：YAML 声明 {expected} twips，reference.docx sectPr 为 "
                    f"{actual} twips（A 类字段以 YAML 为准，此处仅漂移提示）",
                    target=field,
                )
            )

    size = _PAGE_SIZES_TWIPS[page.size]
    expected_w, expected_h = size if page.orientation == "portrait" else size[::-1]
    pg_sz = sect_pr.find(f"{_W_NS}pgSz")
    drift("page.size(w)", expected_w, pg_sz.get(f"{_W_NS}w") if pg_sz is not None else None)
    drift("page.size(h)", expected_h, pg_sz.get(f"{_W_NS}h") if pg_sz is not None else None)
    pg_mar = sect_pr.find(f"{_W_NS}pgMar")
    if pg_mar is not None:
        margin = page.margin
        drift(
            "page.margin.top",
            margin.top.to_twips() if margin.top else None,
            pg_mar.get(f"{_W_NS}top"),
        )
        drift(
            "page.margin.bottom",
            margin.bottom.to_twips() if margin.bottom else None,
            pg_mar.get(f"{_W_NS}bottom"),
        )
        # mirror_margins 为 false 时 inner≡left、outer≡right（§3.5）；为 true 时
        # Word 同样以 left/right 承载内外侧值，映射一致
        drift(
            "page.margin.inner",
            margin.inner.to_twips() if margin.inner else None,
            pg_mar.get(f"{_W_NS}left"),
        )
        drift(
            "page.margin.outer",
            margin.outer.to_twips() if margin.outer else None,
            pg_mar.get(f"{_W_NS}right"),
        )
        drift(
            "page.gutter",
            page.gutter.to_twips() if page.gutter else None,
            pg_mar.get(f"{_W_NS}gutter"),
        )
        drift(
            "page.header_distance",
            page.header_distance.to_twips() if page.header_distance else None,
            pg_mar.get(f"{_W_NS}header"),
        )
        drift(
            "page.footer_distance",
            page.footer_distance.to_twips() if page.footer_distance else None,
            pg_mar.get(f"{_W_NS}footer"),
        )
    grid = page.document_grid
    if grid is not None and grid.line_pitch is not None:
        doc_grid = sect_pr.find(f"{_W_NS}docGrid")
        drift(
            "page.document_grid.line_pitch",
            grid.line_pitch.to_twips(),
            doc_grid.get(f"{_W_NS}linePitch") if doc_grid is not None else None,
        )
    return issues


def lint_l3(resolved: pkg.ResolvedTemplatePackage, package_dir: Path) -> list[ValidationIssue]:
    """L3 Word assets 全量检查（§6.3）。"""
    issues: list[ValidationIssue] = []
    validate_docx = _load_openxml_validate()
    readable: dict[str, bool] = {}
    for label, docx_path in (
        ("reference.docx", resolved.reference_docx),
        ("shell.docx", resolved.shell_docx),
    ):
        if docx_path is None:
            continue
        if not docx_path.is_file():
            issues.append(
                _error(
                    "invalid-word-asset",
                    f"{label} 文件不存在：{docx_path}",
                    target=label,
                )
            )
            readable[label] = False
            continue
        try:
            with zipfile.ZipFile(docx_path) as archive:
                names = archive.namelist()
        except (OSError, zipfile.BadZipFile):
            issues.append(
                _error(
                    "invalid-word-asset",
                    f"{label} 不是可读的 OOXML OPC 包（zipfile 无法打开）",
                    target=label,
                )
            )
            readable[label] = False
            continue
        readable[label] = "[Content_Types].xml" in names
        if not readable[label]:
            issues.append(
                _error(
                    "invalid-word-asset",
                    f"{label} 缺少 [Content_Types].xml",
                    target=label,
                )
            )
            continue
        if validate_docx is not None:
            report = validate_docx(docx_path)
            for check in report["checks"]:
                if check["status"] == "pass":
                    continue
                issues.append(
                    _error(
                        "invalid-word-asset",
                        f"{label} OpenXML 校验失败（{check['name']}）："
                        f"{'；'.join(check['details']) or '见报告'}",
                        target=label,
                    )
                )
        issues.extend(_check_sectpr_child_order(docx_path, label))
    if readable.get("reference.docx"):
        issues.extend(_check_token_styles(resolved, package_dir))
        issues.extend(_check_style_closure(resolved))
        issues.extend(_check_reference_body(resolved))
        issues.extend(_check_template_reference_drift(resolved))
    if resolved.shell_docx is not None and readable.get("shell.docx"):
        issues.extend(_check_anchors(resolved))
        issues.extend(_check_section_policies(resolved))
    issues.extend(_check_header_footer_parts(resolved))
    return issues


# ---------------------------------------------------------------------------
# L4 Semantic（§6.4）
# ---------------------------------------------------------------------------


def _check_l4_region_sections(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§6.4：required region 经 §3.10 默认映射解析后必须有 section 策略。"""
    from .schema import DEFAULT_REGION_SECTION, SECTION_KEYS

    issues: list[ValidationIssue] = []
    regions = resolved.template.regions
    configs = regions.configs()
    for region in regions.order:
        config = configs.get(region)
        if config is None or not config.required:
            continue
        section = config.section or DEFAULT_REGION_SECTION[region]
        if section not in SECTION_KEYS:
            issues.append(
                _error(
                    "numbering-source-missing",
                    f"required region {region} 解析到的 section {section!r} 无策略定义",
                    target=f"regions.{region}.section",
                )
            )
    return issues


def _check_l4_conditional_tokens(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§3.7.1：启用 figures/tables/equations 时的条件必需 token。"""
    issues: list[ValidationIssue] = []
    paragraph_tokens = set(resolved.template.styles.paragraph.declared())
    requirements = (
        ("figures", "caption_figure"),
        ("tables", "caption_table"),
        ("equations", "equation"),
    )
    for section_name, token in requirements:
        if getattr(resolved.template, section_name) is not None and token not in paragraph_tokens:
            issues.append(
                _error(
                    "missing-template-style",
                    f"启用 {section_name} 时 styles.paragraph.{token} 为条件必需 token",
                    target=f"styles.paragraph.{token}",
                )
            )
    return issues


def _check_l4_numbering_source(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§3.12.1：numbering.chapter.source 指向的标题级别必须存在。"""
    source = resolved.template.numbering.chapter.source
    level = int(source.rsplit("_", 1)[1])
    if level not in resolved.template.styles.heading.declared():
        return [
            _error(
                "numbering-source-missing",
                f"numbering.chapter.source 指向 heading_{level}，但 styles.heading "
                f"未声明级别 {level}",
                target="numbering.chapter.source",
            )
        ]
    return []


def _check_l4_citation_style(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§3.19/§1.1：bibliography 声明时 citation style 文件必须存在。

    哈希对账缺口：provenance.yaml schema（§3.21）当前无 style.csl 哈希字段，
    本层只做存在性检查；哈希字段补充后接回 `hash-mismatch`。
    """
    bibliography = resolved.template.bibliography
    if bibliography is None:
        return []
    style_path = resolved.file_reference("bibliography.style_file")
    if style_path is None or not style_path.is_file():
        return [
            _error(
                "missing-template-asset",
                f"bibliography.style_file 声明的 CSL 文件缺失：{bibliography.style_file}",
                target="bibliography.style_file",
            )
        ]
    return []


def _check_l4_contradictions(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§6.4 矛盾属性（防御性复检；正常路径由 L2 pydantic 拦截）。

    注：§2.3「first_line_indent 与 hanging_indent 不得同正」在 v2 中分属
    body 与 bibliography 两个段落上下文，无同段共现字段，本层不适用。
    """
    issues: list[ValidationIssue] = []
    for key in ("cover", "front_matter", "main", "back_matter"):
        page_number = getattr(resolved.template.sections, key).page_number
        if not page_number.display and (
            page_number.format is not None or page_number.restart is not None
        ):
            issues.append(
                _error(
                    "invalid-template",
                    f"sections.{key}.page_number.display: false 时不得设置 format/restart",
                    target=f"sections.{key}.page_number",
                )
            )
    for level, heading in resolved.template.headings.levels().items():
        if heading.numbering.enabled is False and heading.numbering.pattern is not None:
            issues.append(
                _error(
                    "invalid-template",
                    f"headings.{level}.numbering.enabled: false 时不得设置 pattern",
                    target=f"headings.{level}.numbering",
                )
            )
    return issues


def _check_l4_outline_levels(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§3.7.2：heading token 样式 outline level 应与级别一致（warning）。"""
    issues: list[ValidationIssue] = []
    styles_root = _read_docx_part(resolved.reference_docx, "word/styles.xml")
    if styles_root is None:
        return issues
    by_name, by_id = _styles_index(styles_root)
    aliases: dict[str, list[str]] = {}  # L4 不重复别名解析，主名/styleId 足够
    for level, name in resolved.template.styles.heading.declared().items():
        element, _ = _resolve_token_style(name, by_name, by_id, aliases)
        if element is None or element == "builtin":
            continue
        outline = element.find(f"{_W_NS}pPr/{_W_NS}outlineLvl")
        actual = outline.get(f"{_W_NS}val") if outline is not None else None
        if actual != str(level - 1):
            issues.append(
                _warning(
                    "outline-level-mismatch",
                    f"heading token {name!r}（级别 {level}）的 outline level 为 "
                    f"{actual if actual is not None else '（未设置）'}，期望 {level - 1}",
                    target=f"styles.heading.{level}",
                )
            )
    return issues


def _check_l4_body_size(resolved: pkg.ResolvedTemplatePackage) -> list[ValidationIssue]:
    """§2.2/§6.4：body 有效字号必须最终解析为绝对值（docx 中 w:sz 恒为绝对值，
    故检查落实为：body token 样式经 basedOn 链到 docDefaults 能解析到 w:sz）。"""
    styles_root = _read_docx_part(resolved.reference_docx, "word/styles.xml")
    if styles_root is None:
        return []
    body_name = resolved.template.styles.paragraph.body
    by_name, by_id = _styles_index(styles_root)
    element, _ = _resolve_token_style(body_name, by_name, by_id, {})
    if element is None or element == "builtin":
        return []  # missing-token-style 已由 L3 报告
    visited: set[str] = set()
    current = element
    while current is not None:
        style_id = current.get(f"{_W_NS}styleId")
        if style_id in visited:
            break
        visited.add(style_id)
        if current.find(f"{_W_NS}rPr/{_W_NS}sz") is not None:
            return []
        based_on = current.find(f"{_W_NS}basedOn")
        target = based_on.get(f"{_W_NS}val") if based_on is not None else None
        current = by_id.get(target) if target else None
    doc_defaults = styles_root.find(f"{_W_NS}docDefaults")
    if doc_defaults is not None and doc_defaults.find(f".//{_W_NS}sz") is not None:
        return []
    return [
        _error(
            "non-absolute-body-size",
            f"body token 样式 {body_name!r} 经 basedOn 链与 docDefaults 均未解析到 "
            "绝对字号（w:sz）",
            target="styles.paragraph.body",
        )
    ]


def _check_l4_misc_warnings(
    resolved: pkg.ResolvedTemplatePackage,
) -> list[ValidationIssue]:
    """§6.4：兼容矩阵标注 / 不生效配置 / 能力标记（均 warning）。"""
    issues: list[ValidationIssue] = []
    template = resolved.template

    # review-incomplete：verified_with 应包含 primary 目标应用（§3.21）
    primaries = [
        app for app, level in template.compatibility.target_apps.items() if level == "primary"
    ]
    primary = primaries[0] if primaries else "word"
    if resolved.provenance is not None:
        verified = " ".join(resolved.provenance.review.verified_with).lower()
        if primary.lower() not in verified:
            issues.append(
                _warning(
                    "review-incomplete",
                    f"provenance review.verified_with 未包含 primary 目标应用 "
                    f"{primary!r} 的验证记录",
                    target="provenance.yaml#review.verified_with",
                )
            )

    # ineffective-config：toc.levels 显式键 > depth（§3.18，按 YAML 显式键判断）
    toc_raw = resolved.resolved_data.get("toc")
    if isinstance(toc_raw, dict) and isinstance(toc_raw.get("levels"), dict):
        for key in toc_raw["levels"]:
            if str(key).isdigit() and int(key) > template.toc.depth:
                issues.append(
                    _warning(
                        "ineffective-config",
                        f"toc.levels.{key} 超出 toc.depth={template.toc.depth}，不生效",
                        target=f"toc.levels.{key}",
                    )
                )
    # ineffective-config：cover/toc 类 region 开启 heading_numbering（§3.10）
    for region, config in template.regions.configs().items():
        if region in ("cover", "toc") and config.heading_numbering:
            issues.append(
                _warning(
                    "ineffective-config",
                    f"regions.{region}.heading_numbering: true 对 cover/toc 类 region "
                    "不生效",
                    target=f"regions.{region}.heading_numbering",
                )
            )

    # unsupported-capability：v2 未保证能力（§3.13、§3.11）
    if template.figures is not None and template.figures.placement == "floating":
        issues.append(
            _warning(
                "unsupported-capability",
                "figures.placement: floating 为 v2 未保证能力（渲染器仅保证 inline）",
                target="figures.placement",
            )
        )
    for key in ("cover", "front_matter", "main", "back_matter"):
        restart = getattr(template.sections, key).footnote_restart
        if restart != "continuous":
            issues.append(
                _warning(
                    "unsupported-capability",
                    f"sections.{key}.footnote_restart: {restart} 需目标应用支持，"
                    "请确认兼容矩阵",
                    target=f"sections.{key}.footnote_restart",
                )
            )
    return issues


def lint_l4(resolved: pkg.ResolvedTemplatePackage, package_dir: Path) -> list[ValidationIssue]:
    """L4 Semantic 全量检查（§6.4）。"""
    issues: list[ValidationIssue] = []
    issues.extend(_check_l4_region_sections(resolved))
    issues.extend(_check_l4_conditional_tokens(resolved))
    issues.extend(_check_l4_numbering_source(resolved))
    issues.extend(_check_l4_citation_style(resolved))
    issues.extend(_check_l4_contradictions(resolved))
    issues.extend(_check_l4_outline_levels(resolved))
    issues.extend(_check_l4_body_size(resolved))
    issues.extend(_check_l4_misc_warnings(resolved))
    return issues


# ---------------------------------------------------------------------------
# L5 Fixture（§6.5；集成缺口见模块 docstring）
# ---------------------------------------------------------------------------

_FIXTURE_DIRS = ("minimal", "full", "edge-cases")


def _lint_l5_fixture_dir(
    package_dir: Path, name: str, base_template_path: Path | None
) -> list[ValidationIssue]:
    """fixture markdown 可被 parser/validator 接受（v2 管线集成前的降级语义）。"""
    from thesis_forge.core.parser_backend import LegacyParserBackend
    from thesis_forge.core.validator import ValidationContext, validate_document
    from thesis_forge.templates.resolver import resolve_template

    issues: list[ValidationIssue] = []
    fixture_dir = package_dir / "fixtures" / name
    markdown_files = sorted(fixture_dir.glob("*.md"))
    if not markdown_files:
        return [
            _error(
                "fixture-build-failed",
                f"fixtures/{name}/ 内没有 markdown 文件",
                target=f"fixtures/{name}",
            )
        ]
    template = None
    template_path = None
    if base_template_path is not None and base_template_path.is_file():
        resolved_base = resolve_template(
            explicit_path=base_template_path, template_id=None, search_roots=()
        )
        template = resolved_base.template
        template_path = resolved_base.path
    for markdown in markdown_files:
        label = f"fixtures/{name}/{markdown.name}"
        try:
            document = LegacyParserBackend().parse_file(markdown)
        except Exception as error:  # noqa: BLE001 — parser 任意失败都转为 fixture 诊断
            issues.append(
                _error(
                    "fixture-build-failed",
                    f"{label} 解析失败：{error}",
                    target=label,
                )
            )
            continue
        if template is None:
            issues.append(
                _info(
                    "fixture-build-failed",
                    f"{label} 仅完成 parser 冒烟（base v0.3 模板不可用，跳过 validator）",
                    target=label,
                )
            )
            continue
        context = ValidationContext(
            template=template,
            template_path=template_path,
            resource_roots=(fixture_dir,),
        )
        errors = [
            issue
            for issue in validate_document(document, context)
            if issue.severity == "error"
        ]
        if errors:
            detail = "；".join(f"[{issue.code}] {issue.message}" for issue in errors[:5])
            issues.append(
                _error(
                    "fixture-build-failed",
                    f"{label} validator 报告 {len(errors)} 个 error：{detail}",
                    target=label,
                )
            )
    return issues


def lint_l5(resolved: pkg.ResolvedTemplatePackage, package_dir: Path) -> list[ValidationIssue]:
    """L5 Fixture 检查（§6.5 降级实现，集成缺口见模块 docstring）。"""
    issues: list[ValidationIssue] = []
    base_template = (
        Path(__file__).resolve().parents[4] / "templates" / "base" / "bachelor.yaml"
    )
    for name in _FIXTURE_DIRS:
        if (package_dir / "fixtures" / name).is_dir():
            issues.extend(_lint_l5_fixture_dir(package_dir, name, base_template))

    # reference.docx 可用性：python-docx 以其起建新文档（BytesIO 副本语义，D-1：
    # 禁止就地编辑模板本体）
    import io

    try:
        from docx import Document
    except ImportError:
        Document = None
    if Document is not None and resolved.reference_docx.is_file():
        try:
            probe = Document(io.BytesIO(resolved.reference_docx.read_bytes()))
            probe.add_paragraph("lint 探针", style="Normal")
            buffer = io.BytesIO()
            probe.save(buffer)
        except Exception as error:  # noqa: BLE001 — 探针的任意失败都转为资产诊断
            issues.append(
                _error(
                    "invalid-word-asset",
                    f"reference.docx 不可用：python-docx 无法以其起建新文档（{error}）",
                    target="reference.docx",
                )
            )

    # expected/manifest.json（§6.5 C-9）：结构校验；XPath 断言待管线集成
    manifest_path = package_dir / "expected" / "manifest.json"
    if manifest_path.is_file():
        import json

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            issues.append(
                _error(
                    "invalid-template",
                    f"expected/manifest.json 解析失败：{error}",
                    target="expected/manifest.json",
                )
            )
        else:
            if not isinstance(manifest, dict) or manifest.get("version") != 1:
                issues.append(
                    _error(
                        "invalid-template",
                        "expected/manifest.json 的 version 必须为 1",
                        target="expected/manifest.json",
                    )
                )
            issues.append(
                _info(
                    "fixture-assertions-skipped",
                    "expected/manifest.json 的 XPath 断言与构建产物校验待 v2 包对接"
                    "编译管线后启用（当前 L5 为 parser/validator 降级语义）",
                    target="expected/manifest.json",
                )
            )
    return issues


# ---------------------------------------------------------------------------
# 编排
# ---------------------------------------------------------------------------


def lint_package(
    path: str | Path,
    *,
    level: str | None = None,
    search_roots: tuple[Path, ...] | None = None,
) -> LintReport:
    """执行 lint；默认 L1→L5，任一层 error 后更高层跳过（§6）。"""
    package_dir = Path(path).expanduser()
    if not package_dir.is_absolute():
        package_dir = Path.cwd() / package_dir
    package_dir = package_dir.resolve()
    if not package_dir.is_dir():
        return LintReport(
            path=package_dir,
            issues=(
                _error(
                    "missing-package-file",
                    f"模板包目录不存在：{package_dir}",
                    target=str(package_dir),
                ),
            ),
            levels_run=(),
        )
    if level is not None and level not in LEVELS:
        raise ValueError(f"未知 lint 层级：{level!r}（允许 {', '.join(LEVELS)}）")

    issues: list[ValidationIssue] = []
    levels_run: list[str] = []
    resolved: pkg.ResolvedTemplatePackage | None = None

    def errored() -> bool:
        return any(issue.severity == "error" for issue in issues)

    def ensure_resolved() -> pkg.ResolvedTemplatePackage | None:
        # --level Ln 单独运行时先尝试加载以定位 docx 部件与 resolved 模型
        nonlocal resolved
        if resolved is None:
            l2_issues, resolved = lint_l2(package_dir, search_roots=search_roots)
            if resolved is None:
                issues.extend(l2_issues)
        return resolved

    if level in (None, "L1"):
        issues.extend(lint_l1(package_dir))
        levels_run.append("L1")
        if level is None and errored():
            return LintReport(package_dir, tuple(issues), tuple(levels_run))
    if level in (None, "L2") and (level is not None or not errored()):
        l2_issues, resolved = lint_l2(package_dir, search_roots=search_roots)
        issues.extend(l2_issues)
        levels_run.append("L2")
        if level is None and errored():
            return LintReport(package_dir, tuple(issues), tuple(levels_run))
    if level in (None, "L3") and (level is not None or not errored()):
        if ensure_resolved() is not None:
            issues.extend(lint_l3(resolved, package_dir))
        levels_run.append("L3")
        if level is None and errored():
            return LintReport(package_dir, tuple(issues), tuple(levels_run))
    if level in (None, "L4") and (level is not None or not errored()):
        if ensure_resolved() is not None:
            issues.extend(lint_l4(resolved, package_dir))
        levels_run.append("L4")
        if level is None and errored():
            return LintReport(package_dir, tuple(issues), tuple(levels_run))
    if level in (None, "L5") and (level is not None or not errored()):
        if ensure_resolved() is not None:
            issues.extend(lint_l5(resolved, package_dir))
        levels_run.append("L5")
    return LintReport(package_dir, tuple(issues), tuple(levels_run))
