# Task Brief: 005-citations-bibliography

## Goal

Users can select inline or superscript citations and receive template-driven
bibliography title and entry paragraphs without coupling citation data to DOCX.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-formatting-p0/requirements.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/handoff.md`

## Vertical Slice

Complete tasks 5.1-5.6 and prove A5 from compiled citation runs through
document.xml and styles.xml.

## In Scope

- Citation presentation mode with legacy inline default.
- Superscript run rendering.
- Bibliography title/entry roles, fallback and hanging indentation.
- Bibliography independence tests.

## Out Of Scope

- Citation text standard changes, CSL integration and bibliography data schema.

## Files Allowed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/inlines.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `tests/test_bibliography.py`
- `tests/test_compiler.py`
- `tests/test_docx_renderer.py`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/005-citations-bibliography`

## Interfaces / Seams

- Citation data/text remains in bibliography and Compiler layers.
- DOCX presentation is selected only when creating runs and paragraphs.

## Components To Create

- Citation presentation policy and bibliography semantic style policies.

## Components To Reuse

- `CitationRun`, `BibliographyInstruction`, `Gbt7714Formatter` and shared
  paragraph translator.

## Components To Extract

- Reuse one citation run handler and one paragraph style resolver.

## API / Data Flow Contracts

- Bibliography records -> deterministic formatted text -> renderer-neutral runs
  and entries -> template-driven DOCX presentation.

## State / Error / Empty / Loading Behavior

- Loading: local bibliography loading remains synchronous and offline.
- Empty: no citations produces no bibliography entries.
- Error: missing keys retain existing structured validation/compiler errors.
- Disabled: omitted presentation uses inline citations and body fallback.
- Permission: bibliography input is read-only.

## TDD Requirement

- Preserve golden text fixtures and add presentation-only XML assertions.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_bibliography.py tests/test_compiler.py tests/test_docx_renderer.py -k 'citation or bibliography'`
- `.venv/bin/ruff check src/thesis_forge/bibliography src/thesis_forge/renderers/docx tests/test_bibliography.py`

## Stop Conditions

- DOCX is required to run bibliography formatter tests.
- Citation ordering or formatted text changes outside this scope.

## Unsafe Assumptions

- Do not assume superscript presentation belongs in citation data or formatter
  output.
