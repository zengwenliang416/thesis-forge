from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = (
    ROOT / "openspec" / "changes" / "build-thesisforge-v1-core" / "prototype"
)
ARTIFACT = PROTOTYPE / "artifact"


def test_prototype_logic_harness_preserves_offline_safe_build_contract():
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
