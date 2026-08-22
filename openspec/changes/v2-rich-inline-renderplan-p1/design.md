## Context

`src/thesis_forge/core/render_plan.py` is the renderer-neutral boundary between
the compiler and all output projections. It currently defines typed text,
reference, citation, and footnote runs, while the v2 capability registry also
requires distinct soft-break, hard-break, hyperlink, and inline-math semantics.
The first preparation child must establish only this shared vocabulary; later
children will update Preview, Review, DOCX body/footnote consumers, and figure
caption compilation in dependency order.

## Goals / Non-Goals

**Goals:**

- Define exactly the four capability-registered run names.
- Store hyperlink label/destination and math LaTeX as typed semantic fields.
- Represent soft and hard breaks by distinct run types, without a boolean
  compatibility flag.
- Keep `InlineRun` as the sole union used by typed paragraph, heading, list,
  table, figure-caption, and footnote inline storage.
- Provide an explicit unsupported-run failure boundary without a generic
  payload serializer.

**Non-Goals:**

- Do not change `Inline`, compiler conversion, figure caption fields, Preview,
  Review, DOCX rendering, or public output formatting.
- Do not add compatibility aliases such as `BreakRun` or `LinkRun`.
- Do not add a raw-plus-typed representation or a second caption source.

## Decisions

### Canonical names come from the capability registry

Use `SoftBreakRun`, `HardBreakRun`, `HyperlinkRun`, and `MathRun` exactly.
The registry is the contract authority; inferred names such as `BreakRun` or
`LinkRun` are rejected because they make downstream dispatch ambiguous.

### Break semantics are nominal

`SoftBreakRun` and `HardBreakRun` carry no compatibility flag. Their distinct
types make the semantic difference available to every consumer and prevent a
default value from silently changing a hard break into a soft break.

### Link and math fields remain renderer-neutral

`HyperlinkRun` stores `text` and `destination`; `MathRun` stores `latex`.
Neither type imports DOCX, OOXML, parser, or frontend implementations.

### Unknown values fail at the typed seam

The focused contract test exercises the canonical runtime boundary and expects
an explicit `TypeError` for a value outside `InlineRun`. No `None` return,
generic payload conversion, debug marker, or fallback branch is allowed.

## Risks / Trade-offs

- [Risk] Existing consumers only handle the old union → [Mitigation] keep this
  child limited to the shared model and schedule consumer updates as ordered
  dependent children.
- [Risk] A field or alias drifts from the registry → [Mitigation] assert exact
  class names, annotations, and semantic fields in the focused test.
- [Risk] Runtime type aliases alone do not reject arbitrary objects →
  [Mitigation] test the explicit seam failure directly instead of treating a
  static annotation as runtime validation.

## Migration Plan

Implement the two files named by `V2-505A1M`, run its exact focused test, and
leave all downstream consumers unchanged. The next ordered child may consume
the completed union only after an independent Checker verifies this seam.

## Open Questions

None for this preparation child. Consumer-specific display and DOCX behavior
are intentionally deferred to `V2-505A1P`, `V2-505A1R`, `V2-505A1D1`, and
`V2-505A1D2`.
