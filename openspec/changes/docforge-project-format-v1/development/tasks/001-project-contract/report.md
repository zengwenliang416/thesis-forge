# Task Report: 001-project-contract

## Status

DONE

## Files Changed

- `src/thesis_forge/project/constants.py`, `model.py`, `loader.py`, `paths.py`,
  and `__init__.py`.
- `tests/project/`, `tests/application/test_project_services.py`,
  `tests/fixtures/docforge-general/`, and
  `tests/fixtures/docforge-academic/`.
- Task 001 lifecycle records under
  `openspec/changes/docforge-project-format-v1/development/`.

## What Changed

- Centralized the Python DocForge manifest, schema, source, DOCX, and Review
  identity constants.
- Replaced `ProjectManifestV2` with the strict `DocForgeProjectManifest`,
  neutral document defaults, generic metadata, and an optional typed academic
  profile without a compatibility alias.
- Restricted project entrypoints to a directory or `docforge.yaml`, added
  actionable obsolete-contract and bare-Markdown failures, and applied the
  existing confined path resolver during load.
- Resolved `resources.root` as the confined base for assets and bibliography,
  removed the non-canonical `LoadedProject.source_path` shortcut, and covered
  symlink escapes for every source, resource, output, and Review path.
- Added minimal general and academic projects that load through the same
  `ProjectApplicationService` pipeline.

## TDD Evidence

- The first focused run failed during collection because the new constants and
  `DocForgeProjectManifest` did not exist.
- After implementation and review fixes, the focused suite passed 121 tests, including strict
  metadata, obsolete contract, neutral defaults, application service, and path
  boundary coverage.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest tests/project tests/application/test_project_services.py`
  -> `121 passed`.
- `.venv/bin/ruff check src/thesis_forge/project src/thesis_forge/application tests/project tests/application/test_project_services.py`
  -> `All checks passed`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/project/test_project_paths.py tests/project/test_manifest_loader.py -q`
  -> `31 passed`.
- `git diff --check -- <task-001 paths>` -> passed.

## Concerns

- Repository-wide consumers still use the old package, CLI, protocol, domain,
  templates, and repository fixtures until tasks 002 through 007 migrate their
  owning boundaries. This task does not claim the full suite or end-to-end
  migration is complete.

## Scope Deviations

- None. No parser, renderer, frontend, Tauri, packaging, CI, release, or
  external project migration behavior changed.

## Follow-up Needed

- Task 002 must migrate the core aggregate before downstream type boundaries.
- Task-level signed acceptance evidence is materialized only after the
  implementation is committed and the managed verification receipt authority
  is available.

## Adjudication

Implementation evidence supports tasks 1.1 through 1.5 and acceptance
assertions `A5` and `A6`. The first independent review identified incomplete
symlink coverage, a non-canonical source path shortcut, and stale evidence;
all three findings were fixed before re-review.
