from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARCHIVED_CHANGE = "build-thesisforge-v1-core"
ARCHIVED_CHANGE_SUFFIX = f"-{ARCHIVED_CHANGE}"


def _locate_archived_prototype(root: Path) -> Path:
    archive_root = root / "openspec" / "changes" / "archive"
    if not archive_root.is_dir():
        raise FileNotFoundError(
            f"No archived {ARCHIVED_CHANGE} change found under {archive_root}"
        )

    matches = sorted(
        path
        for path in archive_root.iterdir()
        if path.is_dir() and path.name.endswith(ARCHIVED_CHANGE_SUFFIX)
    )
    if not matches:
        raise FileNotFoundError(
            f"No archived {ARCHIVED_CHANGE} change found under {archive_root}"
        )
    if len(matches) != 1:
        names = ", ".join(path.name for path in matches)
        raise RuntimeError(
            f"Expected exactly one archived {ARCHIVED_CHANGE} change; "
            f"found {len(matches)}: {names}"
        )

    prototype = matches[0] / "prototype"
    if not prototype.is_dir():
        raise FileNotFoundError(
            f"Archived {ARCHIVED_CHANGE} change is missing prototype evidence: "
            f"{prototype}"
        )
    return prototype


PROTOTYPE = _locate_archived_prototype(ROOT)
ARTIFACT = PROTOTYPE / "artifact"


def test_archived_prototype_locator_fails_when_archive_is_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="No archived build-thesisforge-v1-core"):
        _locate_archived_prototype(tmp_path)


def test_archived_prototype_locator_fails_when_archive_has_no_match(tmp_path: Path):
    archive_root = tmp_path / "openspec" / "changes" / "archive"
    (archive_root / "2026-07-31-unrelated-change").mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="No archived build-thesisforge-v1-core"):
        _locate_archived_prototype(tmp_path)


def test_archived_prototype_locator_rejects_ambiguous_archives(tmp_path: Path):
    archive_root = tmp_path / "openspec" / "changes" / "archive"
    for date in ("2026-07-30", "2026-07-31"):
        (archive_root / f"{date}-build-thesisforge-v1-core" / "prototype").mkdir(
            parents=True
        )

    with pytest.raises(RuntimeError, match="found 2"):
        _locate_archived_prototype(tmp_path)


def test_archived_prototype_locator_never_selects_active_change(tmp_path: Path):
    (
        tmp_path
        / "openspec"
        / "changes"
        / "build-thesisforge-v1-core"
        / "prototype"
    ).mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="No archived build-thesisforge-v1-core"):
        _locate_archived_prototype(tmp_path)


def test_archived_prototype_locator_requires_prototype_evidence(tmp_path: Path):
    (
        tmp_path
        / "openspec"
        / "changes"
        / "archive"
        / "2026-07-31-build-thesisforge-v1-core"
    ).mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="missing prototype evidence"):
        _locate_archived_prototype(tmp_path)


def test_archived_prototype_locator_does_not_mutate_evidence(tmp_path: Path):
    prototype = (
        tmp_path
        / "openspec"
        / "changes"
        / "archive"
        / "2026-07-31-build-thesisforge-v1-core"
        / "prototype"
    )
    prototype.mkdir(parents=True)
    marker = prototype / "marker.json"
    marker.write_bytes(b'{"approved":true}\n')
    before = (marker.read_bytes(), marker.stat().st_mtime_ns)

    selected = _locate_archived_prototype(tmp_path)

    assert selected == prototype
    assert (marker.read_bytes(), marker.stat().st_mtime_ns) == before


def test_prototype_logic_harness_preserves_offline_safe_build_contract():
    if shutil.which("node") is None:
        pytest.skip("node not available (prototype logic harness requires node)")
    result = subprocess.run(
        ["node", str(PROTOTYPE / "logic" / "harness.js")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert set(payload["verifiedCases"]) == {
        "inspect-is-read-only",
        "warning-only-validation-succeeds",
        "fatal-validation-stops-build",
        "successful-build-replaces-output-last",
        "render-failure-preserves-existing-output",
        "core-flows-require-no-network-or-ai-credentials",
    }


def test_prototype_artifact_exposes_workbench_panels_controls_and_review_states():
    html = (ARTIFACT / "index.html").read_text(encoding="utf-8")
    app = (ARTIFACT / "app.js").read_text(encoding="utf-8")
    styles = (ARTIFACT / "styles.css").read_text(encoding="utf-8")
    combined = f"{html}\n{app}\n{styles}"

    assert 'data-specnav-project-shell="thesisforge-workbench"' in html
    assert 'data-specnav-screen="thesisforge-workbench"' in html
    for panel in ("outline", "editor", "preview", "diagnostics"):
        assert f'data-panel="{panel}"' in html
        assert f'data-panel-target="{panel}"' in html
    for state in ("populated", "loading", "empty", "error", "disabled", "permission"):
        assert f'data-state-target="{state}"' in html
        assert f'data-state-view="{state}"' in html
    for control in (
        "template-select",
        "build-button",
        "build-progress",
    ):
        assert f'id="{control}"' in html
    assert "文档结构" in combined
    assert "诊断" in combined
    assert "@media" in styles
    assert "390px" in combined or "420px" in combined or "480px" in combined


def test_recorded_browser_evidence_covers_desktop_mobile_and_all_states():
    evidence = json.loads(
        (PROTOTYPE / "evidence" / "browser-verification.json").read_text(
            encoding="utf-8"
        )
    )

    assert evidence["ok"] is True
    assert evidence["verified_at"] == "2026-07-31"
    assert evidence["shellAnchors"] == 1
    assert evidence["screenAnchors"] == 1
    assert set(evidence["states"]) == {
        "populated",
        "loading",
        "empty",
        "error",
        "disabled",
        "permission",
    }
    assert all(state["visible"] == 1 for state in evidence["states"].values())
    assert evidence["mobilePanels"] == {
        "outline": 1,
        "editor": 1,
        "preview": 1,
        "diagnostics": 1,
    }
    assert evidence["desktopBodyWidth"] <= 1440
    assert evidence["mobileBodyWidth"] <= 390
