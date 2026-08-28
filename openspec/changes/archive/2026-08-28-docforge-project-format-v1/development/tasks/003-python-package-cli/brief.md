# Task Brief: 003-python-package-cli

## Goal

Users install and invoke DocForge through the `docforge` Python package and CLI
without an active ThesisForge import or command alias.

## Vertical Slice

Add distribution tests, move the import package in bounded batches, expose the
DocForge CLI over shared services, remove obsolete entrypoints, and prove a
clean wheel installation works offline.

## In Scope

- Checklist items `3.1` through `3.5`.
- Python source package, imports, resources, pyproject metadata, console
  scripts, CLI help and diagnostics, and package/distribution tests.

## Files Allowed

- `src`
- `tests`
- `pyproject.toml`
- `README.md`
- `Makefile`
- `scripts`
- `openspec/changes/docforge-project-format-v1/development/tasks/003-python-package-cli`
- `openspec/changes/docforge-project-format-v1/development`

## Components To Create

- `docforge` import package and `docforge` console entrypoint.
- Clean-install and wheel-content contract tests.

## Components To Reuse

- Existing application services, Typer command structure, local resources,
  diagnostics, and offline build pipeline.

## Components To Extract

- Centralize product and package identity rather than repeating import,
  executable, and distribution literals.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/cli tests/test_package_import.py tests/test_desktop_distribution.py`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m build`

## Stop Conditions

- A consumer requires a `thesis_forge` compatibility package or `thesisforge`
  command alias.
- The package move would mix unrelated CI, protocol, frontend, or Tauri changes
  into this slice.
- Clean installation cannot be tested without exposing credentials or network
  dependencies.

## Unsafe Assumptions

- Editable installs can hide missing wheel resources and stale package names.
- Renaming directories does not update entrypoints, imports, resource loading,
  subprocess commands, or distribution allowlists automatically.
