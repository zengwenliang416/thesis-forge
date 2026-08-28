# Task Brief: 005-template-profiles

## Goal

Ordinary documents build with `docforge-standard` and no fabricated academic
data, while academic templates retain typed profile behavior.

## Vertical Slice

Add template binding tests, extend typed common and academic bindings, package
the generic template, adapt academic templates, and verify general and academic
RenderPlans and DOCX output.

## In Scope

- Checklist items `5.1` through `5.5`.
- Generic metadata bindings, optional academic profile bindings,
  `docforge-standard`, academic template adaptation, and template-driven tests.

## Files Allowed

- `src/docforge/templates`
- `src/docforge/compiler`
- `src/docforge/project`
- `templates`
- `tests/templates`
- `tests/compiler`
- `tests/project`
- `tests/fixtures`
- `examples`
- `openspec/changes/docforge-project-format-v1/development/tasks/005-template-profiles`
- `openspec/changes/docforge-project-format-v1/development`

## Components To Create

- Bundled `docforge-standard`.
- Typed generic metadata and optional academic profile template bindings.

## Components To Reuse

- Existing typed template model, package loader, compiler binding, RenderPlan,
  template inheritance, package validation, and OOXML shell behavior.

## Components To Extract

- Profile interpretation must remain a typed project/template concern; repeated
  binding lookup belongs in a shared compiler or template utility.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/templates tests/compiler tests/project`
- `.venv/bin/ruff check src/docforge/templates src/docforge/compiler src/docforge/project tests/templates tests/compiler tests/project`

## Stop Conditions

- The renderer would need a general, academic, or template-ID branch.
- `docforge-standard` needs fabricated academic placeholders to build.
- A template schema decision is missing from the specs.

## Unsafe Assumptions

- Optional metadata omission must not generate fallback prose.
- Passing package validation does not prove visible output lacks fabricated
  academic content.
