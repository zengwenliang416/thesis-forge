# Task Brief: 003-semantic-roles

## Goal

Chinese/English abstracts, keywords and special sections receive independent
template roles without changing Markdown syntax or leaking DOCX into core.

## Parent Artifacts

- `openspec/changes/template-driven-thesis-formatting-p0/requirements.md`
- `openspec/changes/template-driven-thesis-formatting-p0/acceptance.json`
- `openspec/changes/template-driven-thesis-formatting-p0/prototype/handoff.md`

## Vertical Slice

Complete tasks 3.1-3.7 and prove A3, A7 and A8 from Markdown input through
RenderPlan and semantic Word styles.

## In Scope

- Closed `ParagraphRole`.
- Compiler-owned document context state machine.
- Stable heading-ID and constrained keyword recognition.
- Renderer role lookup and deterministic fallback.

## Out Of Scope

- New Markdown containers, frontend controls and school hard-coding.

## Files Allowed

- `src/thesis_forge/core/compiler.py`
- `src/thesis_forge/core/render_plan.py`
- `src/thesis_forge/renderers/docx/renderer.py`
- `src/thesis_forge/renderers/docx/styles.py`
- `tests/test_compiler.py`
- `tests/test_render_plan.py`
- `tests/test_docx_renderer.py`
- `tests/test_architecture.py`
- `tests/test_acceptance.py`
- `openspec/changes/template-driven-thesis-formatting-p0/development/tasks/003-semantic-roles`

## Interfaces / Seams

- Compiler emits roles; Renderer resolves template policy.
- Parser and Domain remain unchanged and renderer neutral.

## Components To Create

- `ParagraphRole` and a private compiler semantic context.

## Components To Reuse

- Existing heading IDs, inline runs, typed instructions and shared translator.

## Components To Extract

- One role-resolution function/state object shared by heading and paragraph
  compilation.

## API / Data Flow Contracts

- Markdown -> ThesisDocument -> Compiler semantic context -> typed RenderPlan
  roles -> template style lookup -> DOCX style.

## State / Error / Empty / Loading Behavior

- Loading: not applicable; compile is deterministic and synchronous.
- Empty: sections without body content still emit the heading role.
- Error: unknown IDs remain ordinary headings; no guessed school mapping.
- Disabled: missing semantic policy falls back to heading/body policy.
- Permission: not applicable; no file write occurs in role resolution.

## TDD Requirement

- Test transitions, exits and false positives before relying on role state.

## Verification Commands

- `.venv/bin/python -m pytest tests/test_compiler.py tests/test_render_plan.py tests/test_docx_renderer.py tests/test_architecture.py`
- `.venv/bin/ruff check src/thesis_forge/core src/thesis_forge/renderers/docx tests/test_compiler.py tests/test_render_plan.py`

## Stop Conditions

- Stable semantic IDs are absent or ambiguous.
- Parser syntax would need to change.
- Role objects contain Word implementation details.

## Unsafe Assumptions

- Do not classify any paragraph containing a keyword label; require matching
  abstract context and a paragraph-start label.
