# Requirements: v2-rich-inline-renderplan-p1

## Summary

Establish the canonical renderer-neutral inline RenderPlan vocabulary for the
four v2 capabilities that are missing from the current `InlineRun` union:
`SoftBreakRun`, `HardBreakRun`, `HyperlinkRun`, and `MathRun`. This is the
ordered preparation seam for later Preview, Review, compiler, and DOCX
consumers.

## Users & Actors

- Compiler and renderer implementers consuming the typed RenderPlan contract.
- Review, Preview, and DOCX projections that will consume the union in ordered
  follow-up changes.
- Test and verification tooling that must detect unknown semantic runs.

## In Scope

- Add the four exact capability-registered run types to
  `src/thesis_forge/core/render_plan.py`.
- Extend one `InlineRun` union with the new variants.
- Preserve hyperlink text/destination and math LaTeX as typed fields.
- Represent soft and hard breaks as distinct nominal types.
- Establish an explicit type-error boundary for unknown inline run values.
- Add focused contract tests in
  `tests/core/test_typed_inline_render_plan.py`.

## Out of Scope

- Parser or domain `Inline` changes.
- Compiler conversion and citation numbering.
- Figure caption representation or caption compilation.
- Preview, Review, DOCX body, and DOCX footnote consumers.
- Generic payload serialization, compatibility aliases, fallback behavior, or
  UI changes.

## UI Design Impact

- Foundation spec: `openspec/specs/ui-design/design.md`
- No UI, theme, locale, or user-facing component change.

## Theme & Locale Capability Impact

- Theme support: `none`
- Theme toggle policy: `theme-toggle:none`
- Internationalization: `disabled`
- Supported locales: `locales:none`
- Default locale: `default-locale:zh-CN`
- Prototype coverage: `none`; this is a Python core seam with no UI surface.

## Architecture & Database Impact

- Foundation spec: `openspec/specs/system-architecture/design.md`
- `render_plan.py` remains renderer-neutral and imports no DOCX/OOXML,
  frontend, or parser implementation.
- The four new run classes are immutable semantic values; no database or
  persistence change is required.
- Unknown values fail explicitly at the typed boundary rather than being
  flattened or returned as `None`.

## Frontend-Backend Data Flow Impact

- Foundation spec: `openspec/specs/frontend-backend-data-flow/design.md`
- No frontend-backend or protocol data-flow change.

## Component Architecture Impact

- Foundation spec: `openspec/specs/component-architecture/design.md`
- Reuse the existing `InlineRun` seam and downstream dispatch points.
- No new shared UI component, service, hook, or extraction is introduced.
- Downstream consumers remain ordered follow-up work and are not modified here.

## Unresolved Gaps

- None. Canonical names and fields are fixed by
  `spec/format-capabilities.yaml` and the product specification.
