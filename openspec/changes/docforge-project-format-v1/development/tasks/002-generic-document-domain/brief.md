# Task Brief: 002-generic-document-domain

## Goal

General and academic Markdown compile through one renderer-neutral
`ForgeDocument` aggregate without exposing thesis-only or Word implementation
details in parser and core.

## Vertical Slice

Introduce failing public-domain tests, rename the aggregate, migrate parser and
downstream type boundaries, add architecture guards, and pass focused semantic
pipeline regressions for both project profiles.

## In Scope

- Checklist items `2.1` through `2.5`.
- `ForgeDocument` public API and all direct parser, validator, compiler,
  bibliography, Review, preview, and application type consumers.
- Architecture tests for forbidden core and parser dependencies.

## Files Allowed

- `src/thesis_forge/core`
- `src/thesis_forge/application`
- `src/thesis_forge/compiler`
- `src/thesis_forge/bibliography`
- `src/thesis_forge/review`
- `tests/core`
- `tests/application`
- `tests/compiler`
- `tests/bibliography`
- `tests/review`
- `tests/test_architecture.py`
- `openspec/changes/docforge-project-format-v1/development/tasks/002-generic-document-domain`
- `openspec/changes/docforge-project-format-v1/development`

## Components To Create

- `ForgeDocument` as the only public parsed document aggregate.
- Focused architecture assertions for profile and renderer independence.

## Components To Reuse

- Existing semantic blocks, inlines, source locations, stable IDs, validation
  issues, bibliography configuration, parser backend, and RenderPlan boundary.

## Components To Extract

- No second document model or translation service is permitted; update the
  existing aggregate and shared type seams directly.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/core tests/application tests/compiler tests/bibliography tests/review tests/test_architecture.py`
- `.venv/bin/ruff check src/thesis_forge/core src/thesis_forge/application src/thesis_forge/compiler src/thesis_forge/bibliography src/thesis_forge/review tests`

## Stop Conditions

- The rename requires a second aggregate, compatibility export, or parser
  branch on document type or academic profile.
- Core or parser would import template, renderer, transport, UI, or AI code.
- A semantic behavior change lacks a focused requirement and test.

## Unsafe Assumptions

- Type renaming alone does not prove every runtime consumer was migrated.
- Existing deterministic IDs and source locations must be verified rather than
  assumed preserved.
