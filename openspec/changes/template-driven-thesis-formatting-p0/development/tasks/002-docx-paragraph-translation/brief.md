# Task Brief: 002-docx-paragraph-translation

## Goal

Body and heading paragraphs use one tested DOCX translator for all template
font, indentation, spacing, line-spacing and pagination properties.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-formatting-p0/requirements.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/handoff.md`

## Vertical Slice

Complete tasks 2.1-2.7 and prove A1/A2 without changing semantic content.

## In Scope

- Shared style/paragraph applicator.
- Focused OOXML helpers for pagination, outline and grid properties.
- Normal and Heading 1-3 migration.
- Stable internal semantic Word style IDs.

## Out Of Scope

- Semantic role recognition, TOC tabs, citations and section variants.

## Files Allowed

- `src/thesis_forge/renderers/docx/styles.py`
- `src/thesis_forge/renderers/docx/fonts.py`
- `src/thesis_forge/renderers/docx/units.py`
- `src/thesis_forge/renderers/docx/document.py`
- `src/thesis_forge/templates/model.py`
- `tests/test_docx_renderer.py`
- `tests/test_template.py`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/002-docx-paragraph-translation`

## Interfaces / Seams

- Translator accepts validated template policy and Word style/paragraph target.
- Target font size resolves `em`; no global 12 pt shortcut.

## Components To Create

- Shared DOCX paragraph-style translator and focused paragraph OOXML helpers.

## Components To Reuse

- `apply_font`, `to_docx_length`, `to_points` and existing style configuration.

## Components To Extract

- Replace duplicated body/heading formatting with one translator.

## API / Data Flow Contracts

- `ThesisTemplate` policy -> DOCX style properties and focused OOXML.
- No school-specific constant enters renderer code.

## State / Error / Empty / Loading Behavior

- Loading: not applicable; translation is synchronous and in-memory.
- Empty: optional style fields leave deterministic defaults.
- Error: invalid policy must already be rejected by Template Model.
- Disabled: optional pagination flags omit or disable their XML property.
- Permission: not applicable until the existing atomic output layer writes.

## TDD Requirement

- Add direct XML assertions before or alongside each low-level helper.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py`
- `.venv/bin/ruff check src/thesis_forge/renderers/docx tests/test_docx_renderer.py`

## Stop Conditions

- Translator becomes an untyped option dictionary.
- A Word property is copied into Compiler or RenderPlan.
- Existing body/heading XML changes without an explicit compatibility test.

## Unsafe Assumptions

- Do not assert ideal geometric values when python-docx quantizes through twips.
