# Task Brief: 002-cover-rendering

## Goal

DOCX cover paragraphs follow template item order and common paragraph policy while RenderPlan stays
renderer neutral.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-layout-p1/requirements.md`
- `openspec/changes/template-driven-thesis-layout-p1/acceptance.md`
- `openspec/changes/template-driven-thesis-layout-p1/prototype/handoff.md`

## Vertical Slice

Complete tasks 2.1-2.4 and remove the fixed cover rendering path.

## In Scope

- CoverInstruction semantic field access.
- Template item value resolution and DOCX paragraph creation.
- Shared paragraph style translation and OOXML tests.

## Out Of Scope

- HUT school values and unrelated document objects.

## Files Allowed

- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/cover.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `tests/test_render_plan.py`
- `tests/test_docx_renderer.py`
- `tests/test_architecture.py`
- `openspec/changes/template-driven-thesis-layout-p1/development/tasks/002-cover-rendering/**`

## Interfaces / Seams

- `CoverInstruction` contains only strings.
- Renderer consumes `ThesisTemplate.cover`.
- Formatting uses `apply_paragraph_style`.

## TDD Requirement

- Add failing item-order, prefix/suffix, empty-policy and OOXML style tests.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_render_plan.py tests/test_docx_renderer.py tests/test_architecture.py -q`
- `.venv/bin/ruff check src/thesis_forge/core/render_plan.py src/thesis_forge/renderers/docx tests/test_render_plan.py tests/test_docx_renderer.py`

## Stop Conditions

- Rendering requires Markdown parsing or school-specific constants.
