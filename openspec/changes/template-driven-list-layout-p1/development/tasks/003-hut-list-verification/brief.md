# Task Brief: 003-hut-list-verification

## Goal

The HUT template explicitly owns list presentation and complete local verification proves editable,
deterministic output.

## Parent Artifacts

- `openspec/changes/template-driven-list-layout-p1/requirements.md`
- `openspec/changes/template-driven-list-layout-p1/acceptance.md`
- `openspec/changes/template-driven-list-layout-p1/prototype/handoff.md`

## Vertical Slice

Complete tasks 3.1-3.4 with HUT YAML, two-template differences, acceptance tests, full regression
and SpecNav handoff evidence.

## In Scope

- Explicit HUT ordered/unordered level policy and paragraph styles.
- HUT and generic/default template loading assertions.
- Same Markdown/two-template semantic equivalence and style difference.
- Non-1 start, depth fallback, numbering.xml/document.xml and complete offline build evidence.
- Full pytest, Ruff, OpenSpec and SpecNav development handoff.

## Out Of Scope

- UI template editor, Markdown syntax and additional document object capabilities.
- Pixel-identical pagination across every office client.

## Files Allowed

- `templates/schools/hunan-university-of-technology/master-2026.yaml`
- `templates/schools/example-university/2026.yaml`
- `tests/test_template.py`
- `tests/test_docx_renderer.py`
- `tests/test_acceptance.py`
- `docs/TEMPLATE_SPEC.md`
- `openspec/changes/template-driven-list-layout-p1/**`

## Interfaces / Seams

- All school values remain in YAML.
- Existing application service and CLI contracts remain unchanged.
- Acceptance assertions `A1`, `A2` and `A3` require direct evidence.

## Components To Create

- Focused HUT list fixtures only when existing examples are insufficient.

## Components To Reuse

- Existing HUT template, example template, application build service and DOCX package helpers.

## Components To Extract

- Reuse existing OOXML test helpers; extract only if duplicated parsing appears in multiple tests.

## API / Data Flow Contracts

- HUT YAML + Markdown -> existing validate/compile/render service -> editable DOCX.
- Inputs stay read-only; only explicit output and test temporary directories are written.

## State / Error / Empty / Loading Behavior

- Loading: local HUT and example YAML through the existing loader.
- Empty: omitted list policy is covered by generic defaults; explicit levels cannot be empty.
- Error: template or render validation fails before output replacement.
- Disabled: not applicable.
- Permission: local input read and explicit output write only.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py tests/test_acceptance.py -q`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/ruff check .`
- `OPENSPEC_TELEMETRY=0 openspec validate template-driven-list-layout-p1 --strict --no-interactive --json`
- `OPENSPEC_TELEMETRY=0 SPECNAV_CHANGE=template-driven-list-layout-p1 node /Users/wenliang_zeng/.codex/plugins/cache/specnav-marketplace/specnav-development/0.3.0/scripts/development-contract.js --mode handoff --json`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not treat one office client's pagination as proof of pixel identity everywhere.
- Do not declare completion from file existence without inspecting numbering.xml and document.xml.
- Do not reuse cover-slice CodeGraph or validation evidence for this change.
