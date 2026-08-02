# Verification Domain Report: static

## Domain

static

## Verdict

green

## Inputs Reviewed

- `requirements.md`, `acceptance.md`, `acceptance.json`, `tasks.md`
- `development/handoff-to-verify.md`
- `verify/user-test-cases.json` and `verify/domain-case-matrix.json`

## Evidence

- `verify/static/commands.jsonl`
- `verify/static/anchor-report.json`
- `verify/traceability-matrix.json`
- `codegraph/guard-report.json`
- `tests/test_architecture.py`
- `tests/test_frontend_contract.py`

## Commands Run

- `make verify`
- `.venv/bin/python -m ruff check .`
- `pnpm frontend:typecheck`
- `pnpm frontend:lint`
- `cargo fmt/check`
- `OPENSPEC_TELEMETRY=0 openspec validate build-thesisforge-desktop-ui --strict --no-interactive`
- `git diff --check`

## Findings

- No blocking findings.

## Required Fixes

- None.

## Residual Risk

- Static checks do not replace runtime interaction or rendered visual review.
- The GitHub workflow file is validated structurally but remote runner billing is outside source control.

## Follow-up Domain Routing

- No unresolved issue requires routing to another verification domain.
