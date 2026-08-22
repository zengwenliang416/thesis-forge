# Task Brief: 001-typed-inline-renderplan

## Goal

Compiler and renderer implementers can consume one canonical typed inline
RenderPlan vocabulary for every v2 inline capability.

## Parent Artifacts

- `openspec/changes/v2-rich-inline-renderplan-p1/requirements.md`
- `openspec/changes/v2-rich-inline-renderplan-p1/acceptance.md`
- `openspec/changes/v2-rich-inline-renderplan-p1/prototype/handoff.md`

## Vertical Slice

Implement and verify the renderer-neutral inline run seam only. The slice ends
at the typed `InlineRun` union and its explicit unknown-value error boundary;
downstream projections are separate ordered children.

## In Scope

- Add `SoftBreakRun`, `HardBreakRun`, `HyperlinkRun`, and `MathRun`.
- Extend the one `InlineRun` union.
- Add focused tests for names, fields, union membership, renderer neutrality,
  and unknown-run failure.

## Out Of Scope

- Parser/domain Inline conversion.
- Figure caption fields or caption compilation.
- Preview, Review, compiler, DOCX body, and DOCX footnote consumers.
- Generic payloads, compatibility aliases, fallback behavior, and UI.

## Files Allowed

- `src/thesis_forge/core/render_plan.py`
- `tests/core/test_typed_inline_render_plan.py`

## Interfaces / Seams

- `InlineRun` is the sole typed union.
- `HyperlinkRun` retains `text` and `destination`.
- `MathRun` retains `latex`.
- Break semantics are nominally distinct.

## Components To Create

- `SoftBreakRun`, `HardBreakRun`, `HyperlinkRun`, `MathRun`.

## Components To Reuse

- `TextRun`, `ReferenceRun`, `CitationRun`, `FootnoteReferenceRun`.

## Components To Extract

- None; the existing core seam is the correct owner.

## API / Data Flow Contracts

- `Inline` semantics flow into the compiler-owned typed run union; no renderer
  implementation detail crosses into `core.render_plan`.

## State / Error / Empty / Loading Behavior

- Loading: not applicable; runs are immutable values.
- Empty: not applicable; an empty inline tuple remains valid.
- Error: unknown inline values raise an explicit type error.
- Disabled: no feature flag or compatibility path.
- Permission: local-only; no external service or credential.

## TDD Requirement

- Write or update focused behavior tests before or alongside implementation.

## Verification Commands

- `.venv/bin/python -m pytest tests/core/test_typed_inline_render_plan.py`
- `ruff check src/thesis_forge/core/render_plan.py tests/core/test_typed_inline_render_plan.py`
- `git diff --check`

## Stop Conditions

- Scope lock mismatch.
- Missing product, architecture, data-flow, or component decision.
- Component duplication that should be extracted.

## Unsafe Assumptions

- Do not infer runtime support from a type alias alone; the focused test must
  exercise the explicit error boundary.
- Do not add fields to FigureInstruction or alter downstream consumers.
