# Task Report: 002-generic-document-domain

## Status

DONE

## Files Changed

- `src/thesis_forge/core/`, `src/thesis_forge/application/`, and
  `src/thesis_forge/presentation/review.py`.
- `qa/tools/parser_diff.py` and every test that directly constructed or
  annotated the parsed document aggregate.
- `tests/core/test_forge_document.py`,
  `tests/core/test_document_object_model.py`, and
  `tests/test_architecture.py`.
- The Task 002 brief/context and lifecycle evidence.

## What Changed

- Replaced the only parsed aggregate with `ForgeDocument` and removed the
  `ThesisDocument` definition and public export without an alias.
- Migrated parser, validator, symbol index, compiler, application contracts,
  Review projection, QA normalization, and direct test consumers to the same
  aggregate.
- Added public API, deterministic parsing, source-location, stable-ID, and
  general/academic profile-independence coverage.
- Extended architecture guards to inspect the production parser implementation
  and reject renderer/template/UI/AI imports or profile/template branching.

## TDD Evidence

- The initial focused test failed because neither `core.ForgeDocument` nor
  `core.model.ForgeDocument` existed.
- After the one-for-one migration, the focused semantic/type closure passed
  `278` tests and the architecture suite passed `10` tests.
- Full repository collection passed with `1324 tests collected`; production
  and QA source scans plus focused execution verify that active consumers no
  longer depend on the removed symbol.
- The first quality review required real project-profile coverage and a less
  brittle architecture guard. Both fixes were implemented and the final
  independent re-review approved the task.

## Verification Commands

- `PYTHONPATH=src .venv/bin/python -m pytest --collect-only -q`
  -> `1324 tests collected`.
- `PYTHONPATH=src .venv/bin/python -m pytest <Task 002 semantic closure> -q`
  -> `278 passed`.
- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_architecture.py -q`
  -> `10 passed`.
- `.venv/bin/ruff check <Task 002 source and test paths>`
  -> `All checks passed`.
- `rg -n '\bThesisDocument\b' src/thesis_forge qa/tools tests`
  -> only the two public-API negative assertions remain.

## Concerns

- Executing every collected regression currently reports `39` failures because
  repository-owned tests and distribution workspaces still use the
  intentionally rejected `thesisforge.yaml` contract. Those fixtures belong
  to Task 007 and are not type-migration failures; collection and the
  manifest-independent semantic closure are green.
- PR CI is expected to remain red until the repository-owned project and
  distribution fixtures are migrated later in this same breaking change.

## Scope Deviations

- The generated Task 002 allowlist named nonexistent
  `src/thesis_forge/review` and omitted the actual
  `src/thesis_forge/presentation` module, test consumers, and
  `qa/tools/parser_diff.py`. The task packet was corrected to cover the real
  direct-consumer closure without changing CLI, UI, renderer, or template
  behavior.

## Follow-up Needed

- Task 007 must convert old project fixtures, distribution verification
  workspaces, examples, and active documentation before the PR can pass the
  full test and distribution gates.

## Adjudication

Implementation evidence and final independent reviews approve items 2.1
through 2.5. The explicitly isolated Task 007 fixture failures remain a
change-level and PR blocker, not a Task 002 type-migration failure.
