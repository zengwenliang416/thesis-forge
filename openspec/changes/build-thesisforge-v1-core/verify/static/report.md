# Static Report

## Domain

static

## Verdict

green

## Inputs Reviewed

- `plan.json`, approved test cases, domain mapping, traced diff, Python package metadata, source imports, docs, OpenSpec artifacts, and CodeGraph verification artifacts.

## Evidence

- `commands.jsonl`
- `anchor-report.json`
- `../traceability-matrix.json`
- `../../codegraph/guard-report.json`

## Commands Run

- Strict OpenSpec validation
- Ruff lint
- `pip check`
- `git diff --check`
- Banned-import, offline dependency, unsafe YAML, anchor, and CodeGraph structural checks

## Findings

- All required structural checks passed.
- Parser and Domain remain independent of DOCX/OOXML implementation types.
- Core, application, and bibliography paths contain no network or AI client dependency.

## Required Fixes

- None.

## Residual Risk

- Static analysis does not replace runtime, package, browser, or Office rendering evidence.

## Follow-up Domain Routing

- Runtime behavior is covered by unit, redteam, E2E, and sensory reports.
