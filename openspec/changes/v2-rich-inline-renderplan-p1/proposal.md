## Why

The typed RenderPlan currently cannot represent four inline capabilities that are
already registered in `spec/format-capabilities.yaml`: ordinary breaks, explicit
hard breaks, external hyperlinks, and inline math. The missing canonical seam
forces downstream work toward incompatible names or generic payloads, so the
shared run vocabulary must be fixed before compiler and presentation consumers
are expanded.

## What Changes

- Add the canonical `SoftBreakRun`, `HardBreakRun`, `HyperlinkRun`, and `MathRun`
  types to the renderer-neutral inline model.
- Extend the single `InlineRun` union with those four exact capability names.
- Keep semantic data in typed fields: hyperlink text and destination, and math
  LaTeX source; break semantics are represented by their distinct types.
- Make unsupported inline run values fail explicitly at the typed seam rather
  than being accepted through a generic payload or silently ignored.
- Leave figure caption ownership, Preview, Review, DOCX rendering, and compiler
  projection for ordered follow-up changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `render-plan-docx`: the typed RenderPlan inline contract now includes all
  capability-registered inline run variants and rejects unknown run values.

## Impact

- Affected code: `src/thesis_forge/core/render_plan.py` and its focused contract
  test.
- Public contract: `InlineRun` gains four canonical typed variants; the names
  and fields must match `spec/format-capabilities.yaml`.
- No new dependency, parser change, renderer change, caption field, migration,
  fallback, compatibility alias, or second source of truth is introduced.
