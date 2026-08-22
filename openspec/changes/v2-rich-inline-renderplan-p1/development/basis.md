# Development Basis: v2-rich-inline-renderplan-p1

## Requirements Reference

- `openspec/specs/ui-design/design.md`
- `openspec/specs/system-architecture/design.md`
- `openspec/specs/frontend-backend-data-flow/design.md`
- `openspec/specs/component-architecture/design.md`
- `openspec/changes/v2-rich-inline-renderplan-p1/requirements.md`
- `openspec/changes/v2-rich-inline-renderplan-p1/acceptance.md`
- `openspec/changes/v2-rich-inline-renderplan-p1/spec-map.json`
- `openspec/changes/v2-rich-inline-renderplan-p1/component-impact-map.json`
- `openspec/changes/v2-rich-inline-renderplan-p1/tasks.md`
- `openspec/changes/v2-rich-inline-renderplan-p1/acceptance.json`
- `openspec/specs/render-plan-docx/spec.md`
- `spec/format-capabilities.yaml`

## Prototype Reference

- `openspec/changes/v2-rich-inline-renderplan-p1/prototype/handoff.md`
- `openspec/changes/v2-rich-inline-renderplan-p1/prototype/decision.json`
- `openspec/changes/v2-rich-inline-renderplan-p1/prototype/component/component-map.md`

## Handoff Reference

Development is allowed only after the requirements contract, prototype
contract, OpenSpec validation, and scope lock are valid. The approved prototype
is a component-seam decision record; production code must be reimplemented
under the development gate rather than copied from prototype text.

## Component Architecture Constraint

`core.render_plan` owns immutable renderer-neutral semantic run values. It must
not import parser, Preview, Review, frontend, DOCX, or OOXML implementations.
This slice has no shared UI component, hook, service, or extraction target.

## Files Allowed

- `src/thesis_forge/core/render_plan.py`
- `tests/core/test_typed_inline_render_plan.py`

## Verification Boundary

- `.venv/bin/python -m pytest tests/core/test_typed_inline_render_plan.py`
- `ruff check src/thesis_forge/core/render_plan.py tests/core/test_typed_inline_render_plan.py`
- `git diff --check`
