# Acceptance Criteria: v2-rich-inline-renderplan-p1

## User-Visible Criteria

- U1: The typed RenderPlan exposes `SoftBreakRun`, `HardBreakRun`,
  `HyperlinkRun`, and `MathRun` with the exact registered names.
- U2: Hyperlink text and destination, and math LaTeX source, remain readable
  semantic fields; soft and hard breaks remain distinguishable by type.
- U3: No figure caption dual source, Preview/Review change, DOCX change, or
  compatibility alias is introduced.

## System Criteria

- S1: `InlineRun` is one union containing the existing canonical runs plus all
  four new variants.
- S2: An unsupported inline value reaches an explicit type-error boundary; it
  is not silently ignored, flattened, serialized as a generic payload, or
  returned as `None`.
- S3: The RenderPlan module remains renderer-neutral and does not import DOCX,
  OOXML, parser, or frontend implementation details.

## Data Criteria

- D1: `HyperlinkRun` retains `text` and `destination`.
- D2: `MathRun` retains `latex`.
- D3: `SoftBreakRun` and `HardBreakRun` require no compatibility boolean or
  alternate break representation.

## Component Criteria

- C1: The only production file in this slice is
  `src/thesis_forge/core/render_plan.py`.
- C2: The focused test is
  `tests/core/test_typed_inline_render_plan.py`; downstream consumer tests
  remain owned by the ordered child items.

## Verification Surfaces

- Facticity: class names, fields, and union membership match
  `spec/format-capabilities.yaml`.
- Static: `ruff check src/thesis_forge/core/render_plan.py tests/core/test_typed_inline_render_plan.py`
  and `git diff --check`.
- Unit: `.venv/bin/python -m pytest tests/core/test_typed_inline_render_plan.py`.
- Redteam: unknown inline value raises an explicit type error.
- E2E: not applicable to this renderer-neutral preparation seam.
- Sensory: not applicable; no UI or document output is changed.

## Unresolved Gaps

- None.
