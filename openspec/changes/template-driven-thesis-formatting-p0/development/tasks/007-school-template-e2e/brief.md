# Task Brief: 007-school-template-e2e

## Goal

Users can build one complete Hunan University of Technology P0 thesis template
into an editable DOCX covering every newly supported formatting surface.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-formatting-p0/requirements.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/handoff.md`

## Vertical Slice

Complete tasks 7.1-7.7 and prove A2-A9 through documentation, a school template,
a complete example and offline end-to-end package assertions.

## In Scope

- Full template specification update.
- HUT P0 YAML template and complete Markdown/BibTeX example.
- Offline inspect/validate/build and deterministic package checks.
- Two-template semantic equivalence test.

## Out Of Scope

- Importing the original legacy `.doc`.
- P1/P2 layout capabilities and frontend template editing.

## Files Allowed

- `docs/TEMPLATE_SPEC.md`
- `templates`
- `examples`
- `tests/test_acceptance.py`
- `tests/test_cli.py`
- `tests/test_application_services.py`
- `tests/test_docx_renderer.py`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/007-school-template-e2e`
- `openspec/changes/template-driven-thesis-formatting-p0/verification`

## Interfaces / Seams

- Existing CLI and application service contracts remain unchanged.
- School values exist only in YAML and test fixtures.

## Components To Create

- HUT P0 template, complete example and normalized OOXML test helpers as needed.

## Components To Reuse

- Existing inspect/validate/build services, package validator and atomic writer.

## Components To Extract

- Repeated DOCX package inspection belongs in reusable test helpers.

## API / Data Flow Contracts

- Read-only Markdown/YAML/BibTeX/images -> inspect/validate/build -> temporary
  DOCX -> package validation -> atomic output.

## State / Error / Empty / Loading Behavior

- Loading: CLI reads local files only.
- Empty: missing required example assets fail validation before output.
- Error: failed build preserves previous valid output and inputs.
- Disabled: no AI, network or account dependency is required.
- Permission: output permission failure retains existing atomic safety.

## TDD Requirement

- Add E2E assertions for every P0 package structure and input immutability.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_acceptance.py tests/test_cli.py tests/test_application_services.py tests/test_docx_renderer.py`
- `.venv/bin/python -m thesis_forge.cli validate examples/complete-thesis/thesis.md`
- `.venv/bin/python -m thesis_forge.cli build examples/complete-thesis/thesis.md`

## Stop Conditions

- A required school value would need a renderer constant.
- Example syntax is not documented or validated.
- E2E would mutate source inputs.

## Unsafe Assumptions

- Do not treat zip validity alone as proof of correct Word formatting.
