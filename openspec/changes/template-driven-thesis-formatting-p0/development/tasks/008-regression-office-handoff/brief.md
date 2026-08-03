# Task Brief: 008-regression-office-handoff

## Goal

Maintainers and reviewers receive complete automated, CodeGraph and Word/WPS
evidence for A1-A10 and a valid SpecNav development handoff.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-formatting-p0/requirements.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/handoff.md`

## Vertical Slice

Complete tasks 8.1-8.7, close every acceptance assertion with direct evidence
and prepare six-domain verification.

## In Scope

- Focused and full test suites, Ruff, package build, pip check and OpenSpec.
- CodeGraph claims/impact evidence.
- Word or WPS sensory review and LibreOffice compatibility evidence.
- Task reports, reviews, ledgers, acceptance updates and handoff contract.

## Out Of Scope

- New production behavior after verification begins.
- CI pipeline repair or release deployment.

## Files Allowed

- `tests`
- `docs`
- `openspec/changes/template-driven-thesis-formatting-p0`
- generated review artifacts outside source-controlled output only when named
  by verification evidence

## Interfaces / Seams

- Validation evidence must name exact commands and artifacts.
- Sensory evidence cannot be replaced by zip/package checks.

## Components To Create

- Final verification records, acceptance evidence references and handoff.

## Components To Reuse

- Existing test suites, package validator, CodeGraph contracts and Office
  compatibility workflow.

## Components To Extract

- Reusable normalized OOXML comparison or inspection helpers remain test-only.

## API / Data Flow Contracts

- Current source and committed task baseline -> system-executed validation ->
  independent reviews -> acceptance evidence -> development handoff.

## State / Error / Empty / Loading Behavior

- Loading: long-running full tests and Office conversion record progress.
- Empty: missing sensory evidence leaves A10 failing.
- Error: failed checks remain recorded and block handoff.
- Disabled: CI status is not required; local verified behavior is authoritative.
- Permission: review artifacts stay inside allowed evidence paths.

## TDD Requirement

- No acceptance assertion changes to passing without direct executed evidence.

## Verification Commands

- `.venv/bin/python -m pytest`
- `.venv/bin/ruff check .`
- `.venv/bin/python -m build`
- `.venv/bin/python -m pip check`
- `openspec validate template-driven-thesis-formatting-p0 --no-color`
- `git diff --check`

## Stop Conditions

- Any baseline task remains unchecked or unsupported.
- A1-A10 lacks direct evidence.
- Word/WPS review cannot be performed or inspected.

## Unsafe Assumptions

- Do not treat green narrow tests, LibreOffice conversion or self-reported
  review as proof of the full objective.
