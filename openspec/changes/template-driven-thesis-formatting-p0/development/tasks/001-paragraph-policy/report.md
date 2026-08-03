# Task Report: 001-paragraph-policy

## Status

DONE

## Files Changed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/templates/__init__.py`
- `tests/test_template.py`
- `tests/test_architecture.py`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence.jsonl`
- `openspec/changes/template-driven-thesis-formatting-p0/codegraph/evidence-index.json`

## What Changed

- Added one closed `ParagraphStyleSpec` reused by body, heading, semantic,
  TOC and bibliography policy models.
- Added paragraph indentation, spacing, line-spacing, pagination, outline and
  document-grid policy fields with incompatible-value validation.
- Added page geometry, header/footer variant, border and page-number display
  policy models while preserving legacy accessors and defaults.
- Added semantic abstract/keyword/special-heading, TOC and bibliography policy
  containers with one canonical owner for each target style.
- Added one-way legacy normalization for header/footer configuration and the
  existing Chinese PAGE/NUMPAGES display default. New variants do not project
  back into fields consumed by the legacy Renderer.
- Fixed `LengthSpec.__str__` so integer values ending in zero retain their
  magnitude, such as `150mm` and `20pt`.
- Exported the new public template policy types.

## TDD Evidence

- Initial focused run failed during collection because
  `ParagraphStyleSpec` did not exist.
- First implementation run exposed the existing `LengthSpec.__str__`
  truncation defect (`150mm` became `15mm`); the implementation and regression
  assertion were corrected before acceptance.
- Added tests for full P0 YAML, all built-in templates, legacy defaults,
  mixed legacy/variant conflicts, inheritance contracts, length formatting,
  unknown fields, incompatible indentation, invalid line-spacing matrices,
  invalid enums, complete nested border paths, PAGE/NUMPAGES conflicts and
  direct Pydantic submodel construction.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_architecture.py -q`
  -> `49 passed`.
- `.venv/bin/python -m pytest -q` -> `288 passed`.
- `.venv/bin/ruff check .` -> `All checks passed`.
- `git diff --check` -> passed.
- CodeGraph evidence `ev-mscoceb1` matched the task claim.

## Concerns

- New policies are intentionally not consumed by DOCX Renderer in this task;
  one-way normalization prevents partial activation before tasks 002-006.
- A1, A7 and A8 remain partially open until DOCX emission, semantic roles and
  full offline/E2E evidence are complete.

## Scope Deviations

- `src/thesis_forge/templates/__init__.py` is explicitly included in the task
  brief/context because public policy types must be importable by tests and
  downstream components.

## Follow-up Needed

- Task 002 must translate common paragraph policy into DOCX styles and XML.
- Task 003 must add renderer-neutral semantic roles.
- Tasks 004-006 must consume TOC, bibliography and section variant policies.

## Adjudication

The task is complete at the template-model boundary. Broad acceptance
assertions remain failing until their downstream slices produce direct
evidence.
