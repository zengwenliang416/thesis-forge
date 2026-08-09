# Task Brief: 003-hut-cover-verification

## Goal

The HUT template explicitly owns its cover layout and the complete offline build proves the output.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-layout-p1/requirements.md`
- `openspec/changes/template-driven-thesis-layout-p1/acceptance.md`
- `openspec/changes/template-driven-thesis-layout-p1/prototype/handoff.md`

## Vertical Slice

Complete tasks 3.1-3.4 with HUT YAML, two-template and complete-build evidence.

## In Scope

- HUT cover item policy.
- Template, acceptance and end-to-end tests.
- Full regression and SpecNav handoff evidence.

## Out Of Scope

- Lists, listings, algorithms, advanced tables and inline rich text.

## Files Allowed

- `templates/schools/hunan-university-of-technology/master-2026.yaml`
- `templates/schools/example-university/2026.yaml`
- `tests/test_template.py`
- `tests/test_docx_renderer.py`
- `tests/test_acceptance.py`
- `docs/TEMPLATE_SPEC.md`
- `openspec/changes/template-driven-thesis-layout-p1/**`

## Interfaces / Seams

- All school values remain in YAML.
- Existing build service and CLI contracts remain unchanged.

## TDD Requirement

- Add failing HUT cover and same-content/two-template assertions before final validation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py tests/test_acceptance.py -q`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/ruff check .`
- `OPENSPEC_TELEMETRY=0 openspec validate template-driven-thesis-layout-p1 --strict`

## Stop Conditions

- Acceptance needs absolute positioning or non-cover scope expansion.
