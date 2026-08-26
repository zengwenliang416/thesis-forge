# Task Brief: 001-project-contract

## Goal

Users can open a strict DocForge v1 project with neutral defaults, generic
metadata, an optional academic profile, and unchanged path confinement.

## Vertical Slice

Add contract-first tests, implement the project model and entrypoint loader,
preserve path-security behavior, and prove minimal general and academic project
fixtures load through the application service.

## In Scope

- Checklist items `1.1` through `1.5`.
- `docforge.yaml`, `docforge.project.v1`, `document.md`, neutral output and
  Review defaults, `document.type`, generic metadata, and academic profile.
- Directory or manifest entrypoints, bare Markdown and obsolete contract
  rejection, and all current project path protections.

## Files Allowed

- `src/thesis_forge/project`
- `src/thesis_forge/application`
- `tests/project`
- `tests/application`
- `tests/fixtures`
- `examples`
- `openspec/changes/docforge-project-format-v1/development/tasks/001-project-contract`
- `openspec/changes/docforge-project-format-v1/development`

## Components To Create

- Strict DocForge v1 manifest model and Python identity constants.
- Typed common metadata and optional academic profile.
- Minimal general and academic fixtures.

## Components To Reuse

- Existing project-relative path normalization, symlink containment, project
  application service, and structured diagnostic patterns.

## Components To Extract

- Extract project identity and default filename literals into one Python module
  if they occur in more than one project boundary module.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/project tests/application/test_project_services.py`
- `.venv/bin/ruff check src/thesis_forge/project src/thesis_forge/application tests/project tests/application/test_project_services.py`

## Stop Conditions

- A required manifest, metadata, entrypoint, or path-security decision is absent.
- Implementation requires a compatibility loader, fallback manifest, or
  automatic mutation of external projects.
- A change would touch parser, renderer, frontend, Tauri, packaging, or another
  active OpenSpec change before this slice is reviewed.

## Unsafe Assumptions

- Do not assume the current thesis-named defaults are reusable public behavior.
- Do not assume a path is safe because it is syntactically relative; preserve
  realpath and symlink boundary checks.
