# Task Brief: 001-archive-safe-prototype-baseline

## Goal

Maintainers can archive the completed V1 core change without breaking the
approved prototype contract tests that guard the desktop workbench baseline.

## Parent Artifacts

- `openspec/changes/build-thesisforge-desktop-ui/requirements.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.md`
- `openspec/changes/build-thesisforge-desktop-ui/acceptance.json`
- `openspec/changes/build-thesisforge-desktop-ui/spec-map.json`
- `openspec/changes/build-thesisforge-desktop-ui/component-impact-map.json`
- `openspec/changes/build-thesisforge-desktop-ui/prototype/handoff.md`

## Vertical Slice

Resolve the unique archived `build-thesisforge-v1-core` directory, run its
committed logic harness, artifact assertions, and browser-evidence assertions,
and fail explicitly when archive evidence is missing or ambiguous.

## In Scope

- Add one deterministic archived-prototype locator in
  `tests/test_prototype_acceptance.py`.
- Search only `openspec/changes/archive/` for directories ending in
  `-build-thesisforge-v1-core`.
- Require exactly one matching archive directory and a real `prototype/`
  evidence directory.
- Update the existing harness, artifact, and browser-evidence tests to consume
  the located archived prototype.
- Add focused tests for no match, multiple matches, active-change exclusion,
  missing prototype evidence, and archive immutability.

## Out Of Scope

- Creating or restoring an active `build-thesisforge-v1-core` change.
- Editing archived prototype files or the active desktop prototype.
- Implementing PySide6, workspace state, source saving, diagnostics, preview,
  build progress, or cancellation.
- Adding a production archive-discovery API.

## Files Allowed

- `tests/test_prototype_acceptance.py`

## Interfaces / Seams

- Preserve the existing Node harness invocation and JSON contract.
- Preserve the artifact and recorded browser-evidence assertions.
- Keep archive discovery test-only; production packages do not depend on
  OpenSpec directory layout.

## Components To Create

- `_locate_archived_prototype(root: Path) -> Path` in the prototype acceptance
  test module.

## Components To Reuse

- `pathlib.Path` deterministic directory inspection.
- Existing archived `prototype/logic/harness.js`.
- Existing archived artifact and browser-verification evidence.

## Components To Extract

- Centralize all archive matching and cardinality checks in the locator helper;
  existing tests must not repeat archive globbing.

## API / Data Flow Contracts

- Input: repository root containing `openspec/changes/archive/`.
- Selection: sorted archive directories whose names end with the exact V1
  change suffix; active change directories are never searched.
- Success: return the sole archive's `prototype/` path without writing.
- Failure: raise a precise exception for zero matches, multiple matches, or
  missing `prototype/` evidence.

## State / Error / Empty / Loading Behavior

- Loading: bounded synchronous filesystem inspection during test collection.
- Empty: zero matching archives fails with an explicit missing-archive message.
- Error: ambiguous archives and missing prototype evidence fail before harness
  execution.
- Disabled: active changes are outside the locator search root.
- Permission: unreadable evidence remains a normal test failure; the locator
  never changes permissions or writes.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_prototype_acceptance.py -q`
- `.venv/bin/python -m pytest tests/test_distribution.py -q`
- `OPENSPEC_TELEMETRY=0 openspec validate build-thesisforge-desktop-ui --strict --json`
- `SPECNAV_CHANGE=build-thesisforge-desktop-ui OPENSPEC_TELEMETRY=0 node /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js --mode entry --json`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.
- Discovery would need to mutate, rename, copy, or recreate archived evidence.
- More than one archive legitimately matches and the intended archive cannot be
  selected by the approved exact-suffix contract.

## Unsafe Assumptions

- Do not assume the former active-change path remains after archive.
- Do not choose the newest directory when multiple archives match.
- Do not search `openspec/changes/` broadly enough to select an active change.
- Do not treat a matching archive directory without `prototype/` as valid
  evidence.
- Do not use test execution as permission to update archive timestamps or
  contents.
