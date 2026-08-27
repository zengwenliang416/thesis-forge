#!/usr/bin/env python3
"""Check active repository surfaces for obsolete public DocForge identities.

The migration is intentionally breaking. Historical documents and explicit
obsolete-input tests may mention the old identity, but active delivery surfaces
must not. The checker reports both groups so an allowed mention cannot disappear
without review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SCAN_PATHS = (
    "README.md",
    "Makefile",
    "docs",
    "examples",
    "qa",
    "spikes/phase0/docx-template/package-sample",
    "protocol",
    "scripts",
    ".github",
    ".woodpecker",
    "src",
    "src-tauri",
    "frontend/src",
    "frontend/e2e",
    "tests/fixtures",
    "pyproject.toml",
    "package.json",
    "frontend/package.json",
)

HISTORICAL_PREFIXES = (
    "docs/update/",
    "openspec/changes/archive/",
)
HISTORICAL_FILES = frozenset(
    {
        "docs/BIBLIOGRAPHY_SPEC.md",
        "docs/MARKDOWN_SPEC.md",
        "docs/MATH_SPEC.md",
        "docs/REFERENCES.md",
        "docs/THIRD_PARTY_NOTES.md",
        "docs/TEMPLATE_SPEC.md",
        "docs/V1_PLAN.md",
        "docs/THESISFORGE_V2_PRODUCT_SPEC.md",
        "docs/THESISFORGE_V2_IMPLEMENTATION_PLAN.md",
        "examples/v2-complete-thesis.zip",
        "scripts/verify_thesisforge_v2_goal.py",
    }
)

# These files intentionally exercise or reject obsolete contracts. They are
# still reported under allowedFindings rather than silently skipped.
EXPLICIT_NEGATIVE_PREFIXES = (
    "tests/fixtures/legacy-project/",
)
EXPLICIT_NEGATIVE_FILES = frozenset(
    {
        "scripts/check_facticity.py",
        "scripts/verify_distribution.py",
        "protocol/runtime-contract.v1.json",
        "src/docforge/bibliography/bibtex.py",
        "src/docforge/core/index.py",
        "src/docforge/project/loader.py",
        "src/docforge/presentation/review_markdown.py",
        "src/docforge/ui/controller.py",
        "src-tauri/src/lib.rs",
        "src-tauri/src/project_tests.rs",
        "src-tauri/tests/protocol_contract.rs",
        "frontend/src/transport/constants.ts",
        "frontend/src/transport/WorkbenchTransport.project.test.ts",
    }
)

PATTERNS = (
    (
        "obsolete-manifest",
        re.compile(r"(?<![A-Za-z0-9_-])thesisforge\.yaml(?![A-Za-z0-9_-])"),
    ),
    (
        "obsolete-schema",
        re.compile(r"(?<![A-Za-z0-9_.-])thesisforge\.project\.v2(?![A-Za-z0-9_.-])"),
    ),
    (
        "obsolete-source",
        re.compile(r"(?<![A-Za-z0-9_-])thesis\.md(?![A-Za-z0-9_-])"),
    ),
    (
        "obsolete-default-output",
        re.compile(r"(?<![A-Za-z0-9_.-])thesis\.docx(?![A-Za-z0-9_.-])"),
    ),
    (
        "obsolete-review-output",
        re.compile(r"(?<![A-Za-z0-9_.-])thesis\.review(?:-map)?\.json?"),
    ),
    (
        "obsolete-package",
        re.compile(r"(?<![A-Za-z0-9_.-])thesis_forge(?:[./_-]|$)"),
    ),
    (
        "obsolete-environment",
        re.compile(r"(?<![A-Za-z0-9_-])THESISFORGE(?:[A-Za-z0-9_-]*)(?![A-Za-z0-9_-])"),
    ),
    (
        "obsolete-product",
        re.compile(r"(?<![A-Za-z0-9_-])(?:ThesisForge|thesisforge)(?![A-Za-z0-9_-])"),
    ),
    (
        "obsolete-domain",
        re.compile(r"(?<![A-Za-z0-9_])ThesisDocument(?![A-Za-z0-9_])"),
    ),
    (
        "obsolete-sidecar",
        re.compile(
            r"(?<![A-Za-z0-9_.-])(?:thesisforge-sidecar|ThesisForge\.app|"
            r"ThesisForge\.exe|ThesisForge_[A-Za-z0-9_.-]+)(?![A-Za-z0-9_.-])"
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    column: int
    category: str
    token: str
    text: str
    classification: str
    reason: str


@dataclass(frozen=True)
class Report:
    schema_version: str
    root: str
    scanned_files: tuple[str, ...]
    skipped_files: tuple[str, ...]
    active_findings: tuple[Finding, ...]
    allowed_findings: tuple[Finding, ...]

    @property
    def ok(self) -> bool:
        return not self.active_findings

    def as_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "root": self.root,
            "ok": self.ok,
            "activeFindingCount": len(self.active_findings),
            "allowedFindingCount": len(self.allowed_findings),
            "scannedFiles": list(self.scanned_files),
            "skippedFiles": list(self.skipped_files),
            "activeFindings": [asdict(item) for item in self.active_findings],
            "allowedFindings": [asdict(item) for item in self.allowed_findings],
        }


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _classification(relative_path: str) -> tuple[str, str]:
    if relative_path in HISTORICAL_FILES or any(
        relative_path.startswith(prefix) for prefix in HISTORICAL_PREFIXES
    ):
        return "historical", "historical specification or archived evidence"
    if relative_path in EXPLICIT_NEGATIVE_FILES or any(
        relative_path.startswith(prefix) for prefix in EXPLICIT_NEGATIVE_PREFIXES
    ):
        return "explicit-negative", "intentional obsolete-contract rejection or migration fixture"
    return "active", "active repository delivery surface"


def _iter_files(root: Path, paths: Iterable[str]) -> Iterable[Path]:
    seen: set[Path] = set()
    ignored_directories = {
        ".git",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "target",
    }
    for raw_path in paths:
        candidate = (root / raw_path).resolve()
        if not candidate.exists():
            continue
        if candidate.is_file():
            candidates = (candidate,)
        else:
            candidates = (
                path
                for path in candidate.rglob("*")
                if not any(part in ignored_directories for part in path.parts)
            )
        for path in candidates:
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            yield path


def _scan_file(root: Path, path: Path) -> tuple[list[Finding], str | None]:
    relative_path = _relative_path(root, path)
    classification, reason = _classification(relative_path)
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return [], relative_path

    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for category, pattern in PATTERNS:
            for match in pattern.finditer(line):
                findings.append(
                    Finding(
                        path=relative_path,
                        line=line_number,
                        column=match.start() + 1,
                        category=category,
                        token=match.group(0),
                        text=line.strip(),
                        classification=classification,
                        reason=reason,
                    )
                )
    return findings, None


def scan_repository(
    root: Path = ROOT,
    *,
    scan_paths: Iterable[str] = DEFAULT_SCAN_PATHS,
) -> Report:
    normalized_root = root.resolve()
    scanned_files: list[str] = []
    skipped_files: list[str] = []
    active: list[Finding] = []
    allowed: list[Finding] = []

    for path in _iter_files(normalized_root, scan_paths):
        relative_path = _relative_path(normalized_root, path)
        findings, skipped = _scan_file(normalized_root, path)
        scanned_files.append(relative_path)
        if skipped:
            skipped_files.append(skipped)
        for finding in findings:
            if finding.classification == "active":
                active.append(finding)
            else:
                allowed.append(finding)

    key = lambda finding: (finding.path, finding.line, finding.column, finding.category)
    return Report(
        schema_version="docforge.facticity.v1",
        root=str(normalized_root),
        scanned_files=tuple(sorted(scanned_files)),
        skipped_files=tuple(sorted(skipped_files)),
        active_findings=tuple(sorted(active, key=key)),
        allowed_findings=tuple(sorted(allowed, key=key)),
    )


def markdown_report(report: Report) -> str:
    status = "PASS" if report.ok else "FAIL"
    lines = [
        "# DocForge Facticity Report",
        "",
        f"- Status: `{status}`",
        f"- Scanned files: `{len(report.scanned_files)}`",
        f"- Active findings: `{len(report.active_findings)}`",
        f"- Allowed findings: `{len(report.allowed_findings)}`",
        "",
        "## Active Findings",
        "",
    ]
    if report.active_findings:
        lines.extend(
            f"- `{item.path}:{item.line}:{item.column}` `{item.category}` "
            f"`{item.token}`: {item.text}"
            for item in report.active_findings
        )
    else:
        lines.append("- None")
    lines.extend(["", "## Allowed Historical And Explicit-Negative Findings", ""])
    if report.allowed_findings:
        lines.extend(
            f"- `{item.path}:{item.line}:{item.column}` `{item.classification}` "
            f"`{item.category}` `{item.token}`: {item.reason}"
            for item in report.allowed_findings
        )
    else:
        lines.append("- None")
    if report.skipped_files:
        lines.extend(["", "## Skipped Binary Or Unreadable Files", ""])
        lines.extend(f"- `{path}`" for path in report.skipped_files)
    return "\n".join(lines) + "\n"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check active repository surfaces for obsolete DocForge identities."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--markdown", dest="markdown_path", type=Path)
    args = parser.parse_args(argv)

    report = scan_repository(args.root)
    json_text = json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n"
    markdown_text = markdown_report(report)
    if args.json_path:
        _write_text(args.json_path, json_text)
    if args.markdown_path:
        _write_text(args.markdown_path, markdown_text)
    if not args.json_path and not args.markdown_path:
        sys.stdout.write(json_text)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
