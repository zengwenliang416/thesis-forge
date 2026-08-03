# Task Brief: 004-toc-styles

## Goal

Users receive a real updateable Word TOC whose first three levels use
template-driven indentation, spacing, right tabs and dot leaders.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-formatting-p0/requirements.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/handoff.md`

## Vertical Slice

Complete tasks 4.1-4.6 and prove A4 through focused styles.xml and document.xml
assertions.

## In Scope

- TOC title and level policy resolution.
- Real TOC field preservation.
- TOC 1-3 Word styles, right tab stops and leaders.

## Out Of Scope

- Static TOC text, list of figures/tables and Office field recalculation.

## Files Allowed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/fields.py`
- `tests/test_template.py`
- `tests/test_docx_renderer.py`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/004-toc-styles`

## Interfaces / Seams

- TOC policies reuse `ParagraphStyleSpec`.
- Renderer updates built-in TOC styles and emits the existing complex field.

## Components To Create

- Focused TOC style and tab-stop configuration helper.

## Components To Reuse

- Shared paragraph translator and complex-field helper.

## Components To Extract

- Tab/leader OOXML conversion must be reusable by all TOC levels.

## API / Data Flow Contracts

- Validated `TocSpec` -> stable TOC 1-3 style XML plus real TOC field.

## State / Error / Empty / Loading Behavior

- Loading: field result is refreshed by the Office client on open.
- Empty: TOC field remains valid before Word updates entries.
- Error: invalid level/tab/leader values fail template validation.
- Disabled: omitted level policy uses deterministic defaults.
- Permission: not applicable until existing output write.

## TDD Requirement

- Assert actual style IDs, tabs and field codes in package XML.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py -k 'toc or style'`
- `.venv/bin/ruff check src/thesis_forge/templates src/thesis_forge/renderers/docx tests/test_docx_renderer.py`

## Stop Conditions

- Implementation replaces the real TOC field with static text.
- Locale-specific display names are assumed without XML evidence.

## Unsafe Assumptions

- Do not assume localized Word UI names equal package `w:styleId` values.
