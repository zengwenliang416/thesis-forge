# Prototype Handoff: v2-rich-inline-renderplan-p1

## Approved Branch Variant

- Branch: `component-seam`
- Variant: `a1m-renderplan-typed-inline-seam-v1`
- Basis: the component map, component tree, normative capability registry,
  typed RenderPlan source inspection, and green verifier report.

## Screens Or Flows

- No UI screen is involved. The reviewed flow is typed inline data moving from
  the compiler-owned RenderPlan seam to later Preview, Review, and DOCX
  consumers.

## Components To Create

- `SoftBreakRun`
- `HardBreakRun`
- `HyperlinkRun`
- `MathRun`
- The focused unknown-run type boundary in the A1M test contract.

## Components To Reuse

- `TextRun`
- `ReferenceRun`
- `CitationRun`
- `FootnoteReferenceRun`
- The existing `InlineRun` annotation location and typed instruction fields.

## Extraction Targets

- None in A1M. Consumer dispatch remains in the ordered A1P, A1R, A1D1, and
  A1D2 changes.

## API Contracts

- `SoftBreakRun` and `HardBreakRun` are exact nominal class names.
- `HyperlinkRun(text, destination)` preserves both semantic strings.
- `MathRun(latex)` preserves the source formula.
- `InlineRun` is the single union containing all canonical variants.
- Values outside the union fail explicitly at the typed boundary.

## Data Flows

- Parsed `Inline` semantics are compiled into typed inline runs.
- The A1M seam only defines the run vocabulary; later consumers project those
  values without changing their ownership or meaning.

## State Behavior

- Loading: no runtime loading or external state.
- Empty: break runs carry their semantics through their nominal type.
- Error: an unknown inline value raises an explicit type error.
- Disabled: no feature flag or compatibility path exists.
- Permission: no network, credential, database, or filesystem write is needed.

## Theme And Locale Policy

- Theme support: none; this is a Python core seam.
- Theme modes: none.
- Theme toggle: intentionally omitted.
- Internationalization: disabled.
- Locales: none.
- Locale switcher: intentionally omitted; existing diagnostics remain `zh-CN`.

## Out Of Scope Items

- Production implementation outside the two A1M files.
- Figure caption fields or caption compilation.
- Preview and Review projections.
- DOCX body and footnote dispatch.
- Parser/domain model changes, generic payloads, compatibility aliases, and UI.

## Required Tests

- Exact class names and semantic field assertions.
- Single-union membership assertions for all canonical runs.
- Nominal soft versus hard break distinction.
- Unknown inline value explicit failure.
- Renderer-neutral import and no-caption-dual-source checks.

## Open Risks

- Existing consumers intentionally do not yet handle the new variants; their
  ordered child changes must land after this seam is independently verified.
- A static type alias cannot enforce runtime input by itself; the focused test
  must exercise the explicit error boundary.
