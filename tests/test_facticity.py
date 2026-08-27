from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.check_facticity import markdown_report, scan_repository

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_facticity.py"


def test_facticity_classifies_active_historical_and_negative_references(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("Use thesisforge.yaml here.\n", encoding="utf-8")
    historical = tmp_path / "docs" / "update"
    historical.mkdir(parents=True)
    (historical / "record.md").write_text("Old thesis.md contract.\n", encoding="utf-8")
    negative = tmp_path / "tests" / "fixtures" / "legacy-project"
    negative.mkdir(parents=True)
    (negative / "thesisforge.yaml").write_text(
        "schema: thesisforge.project.v2\n", encoding="utf-8"
    )

    report = scan_repository(tmp_path, scan_paths=("README.md", "docs", "tests/fixtures"))

    assert not report.ok
    assert {(item.path, item.classification) for item in report.active_findings} == {
        ("README.md", "active")
    }
    assert {item.classification for item in report.allowed_findings} == {
        "historical",
        "explicit-negative",
    }
    assert "Active findings: `2`" in markdown_report(report)


def test_facticity_classifies_obsolete_domain_identity_by_surface(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text(
        "The active model is ThesisDocument.\n", encoding="utf-8"
    )
    historical = tmp_path / "docs" / "update"
    historical.mkdir(parents=True)
    (historical / "record.md").write_text(
        "The old model was ThesisDocument.\n", encoding="utf-8"
    )

    report = scan_repository(tmp_path, scan_paths=("README.md", "docs"))

    assert not report.ok
    assert [
        (item.path, item.category, item.classification, item.token)
        for item in report.active_findings
    ] == [("README.md", "obsolete-domain", "active", "ThesisDocument")]
    assert [
        (item.path, item.category, item.classification, item.token)
        for item in report.allowed_findings
    ] == [
        (
            "docs/update/record.md",
            "obsolete-domain",
            "historical",
            "ThesisDocument",
        )
    ]


def test_facticity_cli_writes_json_and_markdown_and_fails_for_active_findings(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("thesisforge build thesis.md\n", encoding="utf-8")
    json_path = tmp_path / "evidence" / "facticity.json"
    markdown_path = tmp_path / "evidence" / "facticity.md"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(tmp_path),
            "--json",
            str(json_path),
            "--markdown",
            str(markdown_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == "docforge.facticity.v1"
    assert payload["ok"] is False
    assert payload["activeFindingCount"] >= 2
    assert "## Active Findings" in markdown_path.read_text(encoding="utf-8")


def test_facticity_cli_passes_when_only_allowlisted_references_remain(
    tmp_path: Path,
) -> None:
    historical = tmp_path / "docs" / "update"
    historical.mkdir(parents=True)
    (historical / "record.md").write_text("ThesisForge history.\n", encoding="utf-8")
    negative = tmp_path / "tests" / "fixtures" / "legacy-project"
    negative.mkdir(parents=True)
    (negative / "thesis.md").write_text("legacy source\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["activeFindingCount"] == 0
    assert payload["allowedFindingCount"] >= 1
