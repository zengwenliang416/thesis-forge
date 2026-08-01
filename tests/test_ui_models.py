from __future__ import annotations

import json
from pathlib import Path

import pytest

from thesis_forge import ui
from thesis_forge.core.model import ValidationIssue

FIXTURE = Path(__file__).parent / "fixtures" / "diagnostics-zh-cn-v1.json"


@pytest.mark.parametrize(
    "case",
    json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"],
)
def test_diagnostic_view_model_uses_stable_zh_cn_presentation(case: dict):
    issue = ValidationIssue(**case["input"])

    diagnostic = ui.DiagnosticViewModel.from_issue(issue)

    assert diagnostic.severity == issue.severity
    assert diagnostic.code == issue.code
    assert diagnostic.message == case["expectedMessage"]
    assert diagnostic.line == issue.line
    assert diagnostic.target == issue.target
