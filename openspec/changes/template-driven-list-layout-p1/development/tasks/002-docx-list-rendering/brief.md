# Task Brief: 002-docx-list-rendering

## Goal

DOCX ordered and unordered lists follow the selected template policy while `ListInstruction`
remains renderer neutral.

## Parent Artifacts

- `openspec/changes/template-driven-list-layout-p1/requirements.md`
- `openspec/changes/template-driven-list-layout-p1/acceptance.md`
- `openspec/changes/template-driven-list-layout-p1/prototype/handoff.md`

## Vertical Slice

Complete tasks 2.1-2.4 by replacing fixed numbering constants with typed policy translation and
shared paragraph-style application.

## In Scope

- Semantic ordered format -> Word numbering format mapping.
- Template-driven level text, marker alignment, start values and absolute indentation.
- Deterministic final-level policy reuse and valid Word `ilvl` clamping.
- Shared paragraph-style application after inline runs are created.
- Focused numbering.xml and document.xml tests.

## Out Of Scope

- HUT-specific YAML values and final complete-build acceptance.
- Markdown syntax, Parser, Domain Model, Compiler and RenderPlan changes.

## Files Allowed

- `src/thesis_forge/renderers/docx/lists.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `tests/test_docx_renderer.py`
- `tests/test_architecture.py`
- `openspec/changes/template-driven-list-layout-p1/development/tasks/002-docx-list-rendering/**`

## Interfaces / Seams

- `ListInstruction` continues to expose ordered/start/items only.
- Renderer selects `template.list.ordered` or `template.list.unordered`.
- Formatting reuses `apply_paragraph_style`; numbering translation remains inside DOCX code.

## Components To Create

- Renderer-local semantic numbering format mapping and list-level policy resolver.

## Components To Reuse

- Typed `ListSpec`, `ParagraphStyleSpec`, DOCX unit conversion and shared style applicator.

## Components To Extract

- No new shared formatter; extend `lists.py` instead of duplicating numbering logic in
  `renderer.py`.

## API / Data Flow Contracts

- `ListInstruction` + `RenderPlan.template.list` -> numbering.xml + styled document.xml paragraphs.
- Existing `DocxRenderer.render(plan, output) -> Path` remains unchanged.

## State / Error / Empty / Loading Behavior

- Loading: not applicable; rendering consumes an already validated template.
- Empty: a list block with no items is not emitted by the compiler.
- Error: unsupported internal policy fails as structured `DocxRenderError`.
- Disabled: not applicable.
- Permission: explicit output-path write only.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_docx_renderer.py tests/test_architecture.py -q`
- `.venv/bin/ruff check src/thesis_forge/renderers/docx tests/test_docx_renderer.py tests/test_architecture.py`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not assume applying a paragraph style before runs configures later run properties.
- Do not assume numbering-level indentation overrides explicit paragraph indentation.
- Do not move Word numbering values or twips into RenderPlan.
