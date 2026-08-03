# Task Brief: 006-header-footer-variants

## Goal

Users can configure page geometry, first/default/even headers and footers,
header borders and declarative PAGE/NUMPAGES content without stale inheritance.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-formatting-p0/requirements.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/handoff.md`

## Vertical Slice

Complete tasks 6.1-6.9 and prove A6 with direct settings, section, relationship,
header and footer package assertions.

## In Scope

- Header/footer distances and optional document grid.
- Legacy normalization and first/default/even variants.
- Page-number display policy and fields.
- Relationship unlink/clear behavior and header bottom borders.

## Out Of Scope

- Cover componentization, absolute positioning and pixel-identical pagination.

## Files Allowed

- `src/thesis_forge/templates/model.py`
- `src/thesis_forge/renderers/docx/document.py`
- `src/thesis_forge/renderers/docx/sections.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `src/thesis_forge/renderers/docx/fields.py`
- `tests/test_template.py`
- `tests/test_docx_renderer.py`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/006-header-footer-variants`

## Interfaces / Seams

- Section model expresses variants; DOCX section helper owns relationships.
- Page-number fields remain real complex fields.

## Components To Create

- Header/footer variant selector, paragraph-border helper and declarative page
  number display renderer.

## Components To Reuse

- Existing section start, page number format/restart and field helpers.

## Components To Extract

- Initial and added sections must share one variant configuration path.

## API / Data Flow Contracts

- Validated page/section policy -> section geometry -> explicit header/footer
  parts and field codes.

## State / Error / Empty / Loading Behavior

- Loading: not applicable; section creation is synchronous.
- Empty: enabled variants with no text may still contain configured page fields.
- Error: contradictory display or variant configuration fails validation.
- Disabled: explicitly disabled variants unlink and clear inherited content.
- Permission: existing atomic writer handles output permission failures.

## TDD Requirement

- Test stale inheritance and disabled variants before accepting relationship
  logic.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_template.py tests/test_docx_renderer.py -k 'section or header or footer or page_number or grid'`
- `.venv/bin/ruff check src/thesis_forge/templates src/thesis_forge/renderers/docx tests/test_docx_renderer.py`

## Stop Conditions

- Previous-section content cannot be deterministically cleared.
- Page text is hard-coded outside compatibility defaults.
- New behavior requires cover layout expansion.

## Unsafe Assumptions

- Do not assume `different_first_page` configures even headers or unlinks all
  inherited parts.
