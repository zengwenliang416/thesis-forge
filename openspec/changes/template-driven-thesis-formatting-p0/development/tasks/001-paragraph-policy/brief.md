# Task Brief: 001-paragraph-policy

## Goal

Template maintainers can configure a complete reusable paragraph policy while
all existing YAML templates retain their prior defaults and validation quality.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-formatting-p0/requirements.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/handoff.md`

## Vertical Slice

Complete tasks 1.1-1.7 and prove A1, A2, A7 and A8 at the template-model
boundary before any DOCX rendering behavior changes.

## In Scope

- Closed paragraph, semantic, TOC, bibliography, header/footer variant and
  page-number display models.
- Legacy body, heading, header/footer and page-number normalization.
- Field-specific validation and legacy template fixtures.

## Out Of Scope

- DOCX translation, compiler role resolution and school template values.

## Files Allowed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/templates/resolver.py`
- `tests/test_template.py`
- `tests/test_architecture.py`
- `templates/base`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/001-paragraph-policy`

## Interfaces / Seams

- Preserve `load_template(path) -> ThesisTemplate`.
- Keep models renderer neutral and `extra="forbid"`.
- Existing YAML input remains valid without source migration.

## Components To Create

- `ParagraphStyleSpec`, semantic style models, TOC level models,
  bibliography presentation models, header/footer variant models and
  page-number display models.

## Components To Reuse

- `TemplateModel`, `LengthSpec`, `FontSpec`, `LineSpacingSpec`,
  `BodySpec`, `HeadingLevelSpec` and `ThesisTemplate`.

## Components To Extract

- Shared paragraph properties must be represented once rather than copied into
  each policy model.

## API / Data Flow Contracts

- YAML -> strict Pydantic models -> field-specific validation result.
- No Word object or renderer import is allowed in this flow.

## State / Error / Empty / Loading Behavior

- Loading: local YAML parsing only; no network state.
- Empty: missing required legacy fields remains a validation error.
- Error: invalid combinations report exact field paths.
- Disabled: optional P0 sections fall back to legacy behavior.
- Permission: file read failures retain existing `TemplateLoadError` behavior.

## TDD Requirement

- Add failing compatibility and validation tests before or alongside models.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_architecture.py`
- `.venv/bin/ruff check src/thesis_forge/templates tests/test_template.py tests/test_architecture.py`

## Stop Conditions

- A compatibility default is ambiguous.
- A proposed field exposes raw Word or OOXML details.
- Work requires renderer or compiler edits.

## Unsafe Assumptions

- Do not assume Pydantic inheritance preserves legacy required/default fields;
  prove each built-in template with tests.
