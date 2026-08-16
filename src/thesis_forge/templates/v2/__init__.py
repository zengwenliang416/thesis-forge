"""Template Package v2（ADR-0002）：加载器、单位解析、L1–L5 lint、
PackageEditor（shell 合并）、`.tftpl` 打包/校验/解包与 v0.3 → v2 迁移。

与 v0.3 单 YAML 模型（`templates/model.py` + `resolver.py`）完全独立；
v2 加载器不 fallback 解释旧模板（SCHEMA §8.3，R-026）。
"""

from .lint import LEVELS, LintReport, lint_package
from .migrate import (
    LEDGER_STATUSES,
    LedgerEntry,
    MigrateError,
    MigrateReport,
    migrate_template,
)
from .pack import (
    MANIFEST_VERSION,
    PackError,
    VerifyReport,
    build_manifest,
    manifest_bytes,
    pack_package,
    unpack_package,
    verify_package,
)
from .package import (
    InheritanceEntry,
    PackageLoadError,
    ResolvedTemplatePackage,
    is_safe_package_path,
    load_package,
    package_content_hash,
    resolve_within_package,
)
from .package_editor import (
    MergeLedger,
    PackageEditor,
    PackageMergeError,
    merge_into_shell,
)
from .schema import ProvenanceSpec, TemplatePackageSpec, version_satisfies
from .units import Length, LengthContext, LengthParseError, parse_length

__all__ = [
    "LEDGER_STATUSES",
    "LEVELS",
    "MANIFEST_VERSION",
    "InheritanceEntry",
    "LedgerEntry",
    "Length",
    "LengthContext",
    "LengthParseError",
    "LintReport",
    "MergeLedger",
    "MigrateError",
    "MigrateReport",
    "PackError",
    "PackageEditor",
    "PackageLoadError",
    "PackageMergeError",
    "ProvenanceSpec",
    "ResolvedTemplatePackage",
    "TemplatePackageSpec",
    "VerifyReport",
    "build_manifest",
    "is_safe_package_path",
    "lint_package",
    "load_package",
    "manifest_bytes",
    "merge_into_shell",
    "migrate_template",
    "pack_package",
    "package_content_hash",
    "parse_length",
    "resolve_within_package",
    "unpack_package",
    "verify_package",
    "version_satisfies",
]
