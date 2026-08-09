# Task Brief: 001-cover-policy

## Goal

Template maintainers can declare an ordered, validated cover policy without introducing DOCX
details or school values into the model.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-layout-p1/requirements.md`
- `openspec/changes/template-driven-thesis-layout-p1/acceptance.md`
- `openspec/changes/template-driven-thesis-layout-p1/prototype/handoff.md`

## Vertical Slice

Complete tasks 1.1-1.4 at the Template Model and documentation boundary.

## In Scope

- Cover field enum, item model, cover container, generic default and validation.
- Public exports, model tests and template documentation.

## Out Of Scope

- DOCX rendering and HUT-specific values.

## Files Allowed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/templates/__init__.py`
- `tests/test_template.py`
- `tests/test_architecture.py`
- `docs/TEMPLATE_SPEC.md`
- `openspec/changes/template-driven-thesis-layout-p1/development/tasks/001-cover-policy/**`

## Interfaces / Seams

- Preserve `load_template(path) -> ThesisTemplate`.
- Models remain renderer neutral and strict.

## TDD Requirement

- Add failing default, exact-one-of, duplicate-field and invalid-field tests.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_architecture.py -q`
- `.venv/bin/ruff check src/thesis_forge/templates tests/test_template.py tests/test_architecture.py`

## Stop Conditions

- A field requires raw Word details or absolute positioning.
