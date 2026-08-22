# Component Seam Prototype: A1M Typed Inline RenderPlan

## Component Tree

- `core.render_plan`
  - Existing `TextRun`, `ReferenceRun`, `CitationRun`,
    `FootnoteReferenceRun`
  - New `SoftBreakRun`, `HardBreakRun`, `HyperlinkRun`, `MathRun`
  - One `InlineRun` type union consumed by typed instructions

## Cohesion Check

- One reason to change: maintain the canonical renderer-neutral inline run
  vocabulary registered by the v2 capability contract.
- State owner: none; runs are immutable semantic values and the union is a
  type-level boundary.
- Side effects: none; this seam does not parse, render, persist, or mutate
  document state.

## Coupling Check

- Allowed imports: standard typing/dataclass support and the existing
  renderer-neutral RenderPlan model.
- Forbidden imports: parser, Preview, Review, frontend, `docx`, `lxml`, and
  renderer implementation modules.
- Public API: exact run class names and the single `InlineRun` union.
- Extraction target: none; downstream consumer updates remain owned by A1P,
  A1R, A1D1, and A1D2.
