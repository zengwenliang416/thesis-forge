#!/usr/bin/env python3
"""Behavior-level stop contract for the ThesisForge v2 Goal.

This script is intentionally not part of the incremental test suite. `stop-check.sh`
runs it only after LOOP.md has no Open or Blocked items. Until the Goal is complete,
this script should fail with actionable unmet requirements.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET

import yaml

ROOT = Path(__file__).resolve().parents[1]
V2_PROJECT = ROOT / "tests" / "fixtures" / "v2-project"
LEGACY_SOURCE = ROOT / "tests" / "fixtures" / "legacy-project" / "thesis.md"
CAPABILITIES = ROOT / "spec" / "format-capabilities.yaml"
BUILD_SCHEMA = ROOT / "protocol" / "build-report.v2.schema.json"
PROTOCOL_EXAMPLES = (
    ROOT / "protocol" / "examples" / "build-success.json",
    ROOT / "protocol" / "examples" / "build-failed-validation.json",
    ROOT / "protocol" / "examples" / "build-failed-render.json",
)

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
HYPERLINK_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
)
MONOSPACE_FONTS = {
    "courier",
    "courier new",
    "consolas",
    "dejavu sans mono",
    "liberation mono",
    "noto sans mono",
}
NS = {"w": W_NS, "m": M_NS, "r": R_NS, "wp": WP_NS}


@dataclass
class Result:
    name: str
    ok: bool
    detail: str


RESULTS: list[Result] = []


def record(name: str, ok: bool, detail: str) -> None:
    RESULTS.append(Result(name=name, ok=ok, detail=detail))


def require_file(path: Path, *, executable: bool = False) -> bool:
    ok = path.is_file() and (not executable or os.access(path, os.X_OK))
    try:
        display_path = path.relative_to(ROOT)
    except ValueError:
        display_path = path
    record(
        f"file:{display_path}",
        ok,
        "present" if ok else "missing or not executable",
    )
    return ok


def python_executable() -> str:
    configured = os.environ.get("PYTHON")
    if configured:
        return configured
    candidate = ROOT / ".venv" / "bin" / "python"
    if candidate.is_file():
        return str(candidate)
    return sys.executable


def run_cli(*args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    source_path = str(ROOT / "src")
    env["PYTHONPATH"] = (
        source_path
        if not env.get("PYTHONPATH")
        else source_path + os.pathsep + env["PYTHONPATH"]
    )
    command = [python_executable(), "-m", "docforge.cli", *args]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
        check=False,
    )
    ok = completed.returncode == expect
    record(
        "cli:" + " ".join(args),
        ok,
        f"exit={completed.returncode}, expected={expect}\n{completed.stdout[-4000:]}",
    )
    return completed


def basic_build_report_check(payload: Any, *, source: str) -> None:
    errors: list[str] = []
    if not isinstance(payload, dict):
        errors.append("report is not an object")
    else:
        required = {
            "schemaVersion",
            "buildId",
            "intent",
            "outcome",
            "stages",
            "failedStage",
            "primaryDiagnosticId",
            "diagnostics",
            "logs",
            "output",
        }
        missing = sorted(required - payload.keys())
        if missing:
            errors.append(f"missing fields: {missing}")
        if payload.get("schemaVersion") != "thesisforge.build-report.v2":
            errors.append("wrong schemaVersion")
        if payload.get("intent") not in {"publish", "live-preview"}:
            errors.append("invalid intent")
        if payload.get("outcome") not in {"succeeded", "failed", "canceled"}:
            errors.append("invalid outcome")
        stages = payload.get("stages")
        if not isinstance(stages, list) or not stages:
            errors.append("stages must be a non-empty array")
        else:
            seen: set[str] = set()
            allowed_names = {
                "parse",
                "validate",
                "compile",
                "render",
                "finalize",
                "postflight",
                "preview",
            }
            allowed_statuses = {
                "pending",
                "running",
                "succeeded",
                "failed",
                "skipped",
            }
            for stage in stages:
                if not isinstance(stage, dict):
                    errors.append("stage is not an object")
                    continue
                name = stage.get("name")
                status = stage.get("status")
                if name not in allowed_names:
                    errors.append(f"invalid stage name: {name!r}")
                if status not in allowed_statuses:
                    errors.append(f"invalid stage status: {status!r}")
                if name in seen:
                    errors.append(f"duplicate stage: {name}")
                seen.add(str(name))
        diagnostics = payload.get("diagnostics")
        if not isinstance(diagnostics, list):
            errors.append("diagnostics must be an array")
        else:
            ids = set()
            for diagnostic in diagnostics:
                if not isinstance(diagnostic, dict):
                    errors.append("diagnostic is not an object")
                    continue
                for field in (
                    "id",
                    "severity",
                    "category",
                    "code",
                    "stage",
                    "message",
                    "source",
                    "target",
                    "suggestion",
                    "relatedLocations",
                    "details",
                ):
                    if field not in diagnostic:
                        errors.append(f"diagnostic missing {field}")
                if diagnostic.get("id") in ids:
                    errors.append(f"duplicate diagnostic id {diagnostic.get('id')}")
                ids.add(diagnostic.get("id"))
                code = diagnostic.get("code")
                if not isinstance(code, str) or not code.startswith("TF-"):
                    errors.append(f"invalid diagnostic code {code!r}")
            primary = payload.get("primaryDiagnosticId")
            if primary is not None and primary not in ids:
                errors.append("primaryDiagnosticId does not reference diagnostics")
        logs = payload.get("logs")
        if not isinstance(logs, list) or len(logs) > 500:
            errors.append("logs must be an array with at most 500 entries")
    record(f"build-report:{source}", not errors, "; ".join(errors) or "valid")


def validate_protocol_files() -> None:
    if not require_file(BUILD_SCHEMA):
        return
    try:
        schema = json.loads(BUILD_SCHEMA.read_text(encoding="utf-8"))
        record(
            "protocol:schema-json",
            schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
            "draft 2020-12" if schema.get("$schema") else "missing $schema",
        )
    except Exception as exc:  # noqa: BLE001
        record("protocol:schema-json", False, repr(exc))
    for path in PROTOCOL_EXAMPLES:
        if not require_file(path):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            record(f"protocol:{path.name}", False, repr(exc))
            continue
        basic_build_report_check(payload, source=str(path.relative_to(ROOT)))


def validate_capability_registry() -> None:
    if not require_file(CAPABILITIES):
        return
    try:
        data = yaml.safe_load(CAPABILITIES.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        record("capabilities:yaml", False, repr(exc))
        return
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema") != "thesisforge.format-capabilities.v1":
        errors.append("invalid capability schema")
        capabilities: dict[str, Any] = {}
    else:
        capabilities = data.get("capabilities") or {}
    if not isinstance(capabilities, dict) or not capabilities:
        errors.append("capabilities must be a non-empty mapping")
        capabilities = {}
    required = {"source", "ir", "validation", "render_plan", "review", "docx", "evidence"}
    for capability_id, capability in capabilities.items():
        if not isinstance(capability, dict):
            errors.append(f"{capability_id}: not an object")
            continue
        missing = sorted(required - capability.keys())
        if missing:
            errors.append(f"{capability_id}: missing {missing}")
        evidence = capability.get("evidence")
        if isinstance(evidence, str):
            evidence_file = evidence.split("::", 1)[0]
            if not (ROOT / evidence_file).is_file():
                errors.append(f"{capability_id}: evidence file missing: {evidence_file}")
        else:
            errors.append(f"{capability_id}: evidence must be a path string")
    record(
        "capabilities:closure",
        not errors,
        "; ".join(errors[:30]) or f"{len(capabilities)} capabilities registered",
    )


def strip_fenced_code(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    fence: str | None = None
    for line in lines:
        stripped = line.lstrip()
        match = re.match(r"(```+|~~~+)", stripped)
        if fence is None and match:
            fence = match.group(1)[0]
            continue
        if fence is not None:
            if stripped.startswith(fence * 3):
                fence = None
            continue
        output.append(line)
    return "\n".join(output)


def validate_review(review_path: Path, map_path: Path) -> None:
    if not require_file(review_path):
        return
    if not require_file(map_path):
        return
    visible = strip_fenced_code(review_path.read_text(encoding="utf-8"))
    patterns = {
        "legacy container": r"(?m)^\s*:::\s*",
        "stable ID": r"\{#(?:fig|tbl|eq|alg|lst|sec|chap|region):",
        "raw citation key": r"\[@[A-Za-z0-9_.:-]+",
        "legacy cross reference": r"(?<![\w])@(?:fig|tbl|eq|alg|lst|sec|chap):",
        "absolute Unix path": r"(?<!\w)/(?:Users|home|tmp|var)/[^\s)]+",
        "absolute Windows path": r"[A-Za-z]:\\[^\s)]+",
    }
    leaks = [name for name, pattern in patterns.items() if re.search(pattern, visible)]
    starts_front_matter = visible.lstrip().startswith("---\n")
    if starts_front_matter:
        leaks.append("YAML Front Matter")
    record(
        "review:marker-free",
        not leaks,
        "no visible leaks" if not leaks else f"leaks: {', '.join(leaks)}",
    )
    try:
        mapping = json.loads(map_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        record("review:source-map", False, repr(exc))
        return
    blocks = mapping.get("blocks") if isinstance(mapping, dict) else None
    record(
        "review:source-map",
        isinstance(blocks, list) and bool(blocks),
        f"blocks={len(blocks) if isinstance(blocks, list) else 'invalid'}",
    )


def relationship_target_exists(names: set[str], rels_name: str, target: str) -> bool:
    if target.startswith("/"):
        normalized = target.lstrip("/")
    else:
        rels_path = PurePosixPath(rels_name)
        # word/_rels/document.xml.rels -> base word/
        base = rels_path.parent.parent
        normalized = str(base / target)
    parts: list[str] = []
    for part in PurePosixPath(normalized).parts:
        if part == ".":
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts) in names


def is_preformatted_paragraph(
    paragraph: ET.Element,
    style_name: str,
    text_runs: list[ET.Element],
    monospace_runs: list[ET.Element],
) -> bool:
    if any(token in style_name.lower() for token in ("code", "listing")):
        return True
    if not text_runs or len(monospace_runs) != len(text_runs):
        return False

    paragraph_properties = paragraph.find("./w:pPr", NS)
    if paragraph_properties is None:
        return False
    indentation = paragraph_properties.find("./w:ind", NS)
    spacing = paragraph_properties.find("./w:spacing", NS)
    alignment = paragraph_properties.find("./w:jc", NS)
    if indentation is None or spacing is None or alignment is None:
        return False

    return (
        (
            indentation.get(f"{{{W_NS}}}firstLine") == "0"
            or indentation.get(f"{{{W_NS}}}hanging") == "0"
        )
        and alignment.get(f"{{{W_NS}}}val") == "start"
        and spacing.get(f"{{{W_NS}}}line") == "240"
        and spacing.get(f"{{{W_NS}}}lineRule", "auto") == "auto"
    )


def validate_docx(path: Path) -> None:
    if not require_file(path):
        return
    errors: list[str] = []
    required_parts = {
        "[Content_Types].xml",
        "_rels/.rels",
        "word/document.xml",
        "word/styles.xml",
        "word/numbering.xml",
        "word/footnotes.xml",
    }
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            missing = sorted(required_parts - names)
            if missing:
                errors.append(f"missing parts: {missing}")
            xml_roots: dict[str, ET.Element] = {}
            for name in names:
                if name.endswith((".xml", ".rels")):
                    try:
                        xml_roots[name] = ET.fromstring(archive.read(name))
                    except ET.ParseError as exc:
                        errors.append(f"malformed XML {name}: {exc}")
            for name, root in xml_roots.items():
                if not name.endswith(".rels"):
                    continue
                for relationship in root.findall(f"{{{PKG_REL_NS}}}Relationship"):
                    if relationship.get("TargetMode") == "External":
                        if (
                            relationship.get("Type") == HYPERLINK_REL_TYPE
                            and (relationship.get("Target") or "").startswith(
                                ("http://", "https://")
                            )
                        ):
                            continue
                        errors.append(f"unexpected external relationship in {name}")
                        continue
                    target = relationship.get("Target")
                    if target and not relationship_target_exists(names, name, target):
                        errors.append(f"missing relationship target {target!r} from {name}")
            document = xml_roots.get("word/document.xml")
            if document is not None:
                if document.find(".//m:oMath", NS) is None and document.find(".//m:oMathPara", NS) is None:
                    errors.append("no OMML equation found")
                if document.find(".//w:bookmarkStart", NS) is None:
                    errors.append("no bookmark found")
                instr_text = " ".join(
                    (element.text or "") for element in document.findall(".//w:instrText", NS)
                )
                for field in ("TOC", "SEQ", "REF"):
                    if field not in instr_text:
                        errors.append(f"missing {field} field")
                marker_patterns = (
                    re.compile(r"\[@[A-Za-z0-9_.:-]+"),
                    re.compile(r"(?<!\w)@(?:fig|tbl|eq|alg|lst|sec|chap):"),
                    re.compile(r"\{#(?:fig|tbl|eq|alg|lst|sec|chap|region):"),
                    re.compile(r"^\s*:::", re.MULTILINE),
                )
                for paragraph in document.findall(".//w:p", NS):
                    style = paragraph.find("./w:pPr/w:pStyle", NS)
                    style_name = style.get(f"{{{W_NS}}}val", "") if style is not None else ""
                    text_runs = [
                        run
                        for run in paragraph.findall(".//w:r", NS)
                        if run.find(".//w:t", NS) is not None
                    ]
                    monospace_runs = [
                        run
                        for run in text_runs
                        if any(
                            (fonts.get(attribute) or "").strip().lower() in MONOSPACE_FONTS
                            for attribute in (
                                f"{{{W_NS}}}ascii",
                                f"{{{W_NS}}}hAnsi",
                                f"{{{W_NS}}}eastAsia",
                            )
                            for fonts in [run.find("./w:rPr/w:rFonts", NS)]
                            if fonts is not None
                        )
                    ]
                    if is_preformatted_paragraph(
                        paragraph,
                        style_name,
                        text_runs,
                        monospace_runs,
                    ):
                        continue
                    text = "".join(node.text or "" for node in paragraph.findall(".//w:t", NS))
                    if any(pattern.search(text) for pattern in marker_patterns):
                        errors.append(f"unresolved marker in normal paragraph: {text[:120]!r}")
                        break
                sections = document.findall(".//w:sectPr", NS)
                extents = document.findall(".//wp:extent", NS)
                if not sections or not extents:
                    errors.append("manifest figure width evidence is missing")
                else:
                    page_size = sections[-1].find("./w:pgSz", NS)
                    page_margin = sections[-1].find("./w:pgMar", NS)
                    if page_size is None or page_margin is None:
                        errors.append("main section page geometry is missing")
                    else:
                        page_width = int(page_size.get(f"{{{W_NS}}}w", "0"))
                        left = int(page_margin.get(f"{{{W_NS}}}left", "0"))
                        right = int(page_margin.get(f"{{{W_NS}}}right", "0"))
                        expected_width = round(
                            (page_width - left - right) * 635 * 85 / 100
                        )
                        actual_widths = {
                            int(extent.get("cx", "0")) for extent in extents
                        }
                        # LibreOffice may normalize DrawingML extents by a fraction
                        # of one twip while refreshing fields.
                        if not any(
                            abs(actual_width - expected_width) <= 635
                            for actual_width in actual_widths
                        ):
                            errors.append(
                                "manifest figure width override not applied: "
                                f"expected {expected_width}, got {sorted(actual_widths)}"
                            )
            if not any(name.startswith("word/media/") for name in names):
                errors.append("no embedded media found")
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(repr(exc))
    record("docx:structural-contract", not errors, "; ".join(errors[:30]) or "valid")


def validate_static_architecture() -> None:
    production = ROOT / "src" / "docforge"
    text_by_path: dict[Path, str] = {}
    for path in production.rglob("*.py"):
        text_by_path[path] = path.read_text(encoding="utf-8")
    combined = "\n".join(text_by_path.values())
    checks = {
        "single-parser:legacy-file-removed": not (production / "core" / "parser.py").exists(),
        "single-parser:no-LegacyParserBackend": "LegacyParserBackend" not in combined,
        "typed-render-plan:no-RenderNode": not re.search(r"\bclass\s+RenderNode\b", combined),
        "docx:no-legacy-renderer": "_render_legacy" not in combined,
        "docx:no-debug-placeholder": "[kind] {payload}" not in combined,
    }
    for name, ok in checks.items():
        record(name, ok, "satisfied" if ok else "legacy/static construct remains")

    frontend_required = (
        ROOT / "frontend" / "src" / "components" / "BuildOutputPanel.tsx",
        ROOT / "frontend" / "src" / "components" / "ReviewPanel.tsx",
    )
    for path in frontend_required:
        require_file(path)
    workspace = ROOT / "frontend" / "src" / "state" / "workspace.ts"
    if workspace.is_file():
        content = workspace.read_text(encoding="utf-8")
        ok = all(mode in content for mode in ('"review"', '"structure"', '"final-layout"'))
        record("frontend:three-preview-modes", ok, "present" if ok else "mode missing")


def main() -> int:
    required = (
        ROOT / "LOOP.md",
        ROOT / "lint-loop.sh",
        ROOT / "stop-check.sh",
        ROOT / "docs" / "THESISFORGE_V2_PRODUCT_SPEC.md",
        ROOT / "docs" / "THESISFORGE_V2_IMPLEMENTATION_PLAN.md",
        V2_PROJECT / "thesisforge.yaml",
        V2_PROJECT / "thesis.md",
        V2_PROJECT / "references.bib",
        V2_PROJECT / "assets" / "model.png",
        LEGACY_SOURCE,
    )
    for path in required:
        require_file(path, executable=path.name.endswith(".sh"))

    validate_protocol_files()
    validate_capability_registry()
    validate_static_architecture()

    with tempfile.TemporaryDirectory(prefix="thesisforge-v2-goal-") as temporary:
        temp = Path(temporary)
        review_dir = temp / "review"
        docx_path = temp / "thesis.docx"
        report_path = temp / "build-report.json"

        run_cli("inspect", str(V2_PROJECT), expect=0)
        run_cli("validate", str(V2_PROJECT), "--json", expect=0)
        run_cli("review", str(V2_PROJECT), "--output-dir", str(review_dir), expect=0)
        build = run_cli(
            "build",
            str(V2_PROJECT),
            "-o",
            str(docx_path),
            "--report-json",
            str(report_path),
            expect=0,
        )

        if build.returncode == 0:
            validate_review(
                review_dir / "thesis.review.md",
                review_dir / "thesis.review-map.json",
            )
            if report_path.is_file():
                try:
                    build_payload = json.loads(
                        report_path.read_text(encoding="utf-8")
                    )
                    basic_build_report_check(
                        build_payload.get("report", build_payload),
                        source="generated build",
                    )
                except Exception as exc:  # noqa: BLE001
                    record("build-report:generated build", False, repr(exc))
            else:
                record("build-report:generated build", False, "report file missing")
            validate_docx(docx_path)

        bare = run_cli("inspect", str(V2_PROJECT / "thesis.md"), expect=2)
        record(
            "legacy:bare-markdown-code",
            "TF-PROJECT-" in bare.stdout,
            bare.stdout[-1000:],
        )
        legacy_project = temp / "legacy-project"
        legacy_project.mkdir()
        shutil.copy2(LEGACY_SOURCE, legacy_project / "thesis.md")
        shutil.copy2(V2_PROJECT / "thesisforge.yaml", legacy_project / "thesisforge.yaml")
        legacy = run_cli("inspect", str(legacy_project), expect=2)
        record(
            "legacy:source-code",
            "TF-SOURCE-LEGACY-" in legacy.stdout,
            legacy.stdout[-1000:],
        )

    failures = [result for result in RESULTS if not result.ok]
    for result in RESULTS:
        prefix = "PASS" if result.ok else "FAIL"
        print(f"{prefix:4} {result.name}: {result.detail}")
    if failures:
        print(f"\nGOAL VERIFICATION FAILED: {len(failures)} unmet contract(s).", file=sys.stderr)
        return 1
    print("\nGOAL VERIFICATION PASSED: ThesisForge v2 behavior contract is satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
