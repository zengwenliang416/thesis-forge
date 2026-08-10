# Task Brief: 001-list-policy

## Goal

Template maintainers can declare validated ordered and unordered list policies without introducing
DOCX details or school values into the model.

## Parent Artifacts

- `openspec/changes/template-driven-list-layout-p1/requirements.md`
- `openspec/changes/template-driven-list-layout-p1/acceptance.md`
- `openspec/changes/template-driven-list-layout-p1/prototype/handoff.md`

## Vertical Slice

Complete tasks 1.1-1.4 at the Template Model, public export, focused test and documentation
boundary.

## In Scope

- Ordered format enum and typed ordered/unordered level models.
- List policy containers, generic 9-level defaults and deterministic final-level fallback.
- Marker, level count and absolute indentation geometry validation.
- Public exports, model tests and `docs/TEMPLATE_SPEC.md`.

## Out Of Scope

- DOCX numbering construction, Renderer integration and HUT-specific values.
- Markdown syntax, Parser, Domain Model, Compiler and RenderPlan changes.

## Files Allowed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/templates/__init__.py`
- `tests/test_template.py`
- `tests/test_architecture.py`
- `docs/TEMPLATE_SPEC.md`
- `openspec/changes/template-driven-list-layout-p1/development/tasks/001-list-policy/**`

## Interfaces / Seams

- Preserve `load_template(path) -> ThesisTemplate`.
- Models expose semantic names only and remain independent of python-docx, lxml and OOXML.
- Existing templates that omit `list` receive the typed generic default.

## Components To Create

- `OrderedListLevelSpec`, `UnorderedListLevelSpec`, `OrderedListSpec`,
  `UnorderedListSpec` and `ListSpec`.

## Components To Reuse

- `TemplateModel`, `LengthSpec`, `ParagraphStyleSpec` and `ThesisTemplate`.

## Components To Extract

- Shared default-level construction and level fallback helpers inside the Template Model module.

## API / Data Flow Contracts

- YAML -> Pydantic Template Model -> `RenderPlan.template`.
- No service or CLI signature changes.

## State / Error / Empty / Loading Behavior

- Loading: synchronous local YAML loading through the existing template loader.
- Empty: zero levels and blank markers are rejected; omitted `list` receives defaults.
- Error: field-specific Pydantic validation errors.
- Disabled: not applicable.
- Permission: local template read only.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_architecture.py -q`
- `.venv/bin/ruff check src/thesis_forge/templates tests/test_template.py tests/test_architecture.py`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not assume relative `em` lengths can be converted to numbering geometry.
- Do not assume a one-level school policy must be expanded to nine hidden school levels.
- Do not add Word format names such as `lowerLetter` to public YAML.
