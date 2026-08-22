# Component Map: A1M Typed Inline RenderPlan

## Proposed Shared Components

- `SoftBreakRun`: nominal ordinary source-newline run with no compatibility
  flag.
- `HardBreakRun`: nominal explicit line-break run with no compatibility flag.
- `HyperlinkRun`: immutable `text` plus `destination` semantic fields.
- `MathRun`: immutable `latex` source field.
- `InlineRun`: the only union containing all canonical inline run variants.

## Reused Components

- `TextRun`
- `ReferenceRun`
- `CitationRun`
- `FootnoteReferenceRun`
- Existing typed instruction `inlines` fields.

## Hooks

- None. This core seam has no UI or lifecycle hooks.

## Utilities / Services

- No new service. The explicit unknown-run boundary is exercised by the
  focused contract test and must raise a type error rather than flattening or
  returning `None`.
