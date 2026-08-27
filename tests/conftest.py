from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def disable_automatic_office_refresh(monkeypatch):
    monkeypatch.setenv("DOCFORGE_OFFICE_REFRESH", "0")
