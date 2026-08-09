## Context

`ListInstruction` already carries renderer-neutral list kind, start value, item level, ordinal and
inline runs. The DOCX list helper currently ignores template policy and creates a fixed 9-level
numbering definition: decimal `%N.` for ordered lists, a three-marker cycle for bullets, left
alignment, 36pt incremental left indentation and 18pt hanging indentation. P0 already provides
`ParagraphStyleSpec` and a shared DOCX paragraph-style translator.

## Goals / Non-Goals

**Goals:**

- Make ordered and unordered list presentation fully template driven.
- Preserve Markdown list semantics and non-1 starting values.
- Keep Word numbering implementation details out of YAML, Parser, Domain and RenderPlan.
- Reuse common length and paragraph style contracts.
- Preserve current behavior as the generic default for existing templates.
- Produce real editable Word numbering definitions and deterministic output.

**Non-Goals:**

- Change Markdown list parsing, nesting semantics or preview DTOs.
- Support more than Word's 9 numbering levels.
- Support picture bullets, custom numbering fonts, checkboxes or raw OOXML.
- Maintain numbering continuity across separate Markdown list blocks.
- Guarantee pixel-identical pagination across office suites.

## Decisions

### Separate semantic policies for ordered and unordered lists

`ListSpec` owns `ordered` and `unordered` policies, each with 1 to 9 typed levels. Separate models
avoid invalid combinations such as a bullet marker on an ordered level while keeping the YAML
vocabulary independent of Word tags.

### Closed ordered format vocabulary

Ordered formats use `decimal`, `lower_letter`, `upper_letter`, `lower_roman` and `upper_roman`.
The DOCX helper maps these values to Word numbering format values. Templates never expose
`w:numFmt`, `w:lvlText` or namespace-qualified attributes.

### Numbering geometry and paragraph style compose

Each level owns marker alignment, absolute left indentation and absolute hanging indentation.
These values define numbering geometry in `numbering.xml`. A complete `ParagraphStyleSpec` is then
applied to each emitted paragraph for fonts, size, color, emphasis, paragraph alignment, additional
indentation, spacing, line spacing and pagination controls. Direct paragraph properties follow
normal Word precedence over numbering-level defaults.

### Deterministic level fallback

Policies contain at most 9 levels. A Markdown item whose zero-based level is beyond the configured
policy reuses the final configured level while its Word `ilvl` is clamped to 8. This makes concise
school templates deterministic without inventing hidden levels.

### Starting values remain semantic input

The first numbering level starts from `ListInstruction.start`, then the first item ordinal, then 1.
Deeper levels start from 1. The template controls presentation, not document content or ordinal
semantics.

### Generic default reproduces current output

The default creates 9 decimal ordered levels with empty prefix and `.` suffix, and 9 unordered
levels cycling `•`, `◦`, `▪`. Every level is left-aligned, increases left indentation by 36pt and
uses 18pt hanging indentation. Paragraph style defaults are empty.

## Risks / Trade-offs

- [Risk] Paragraph style indentation can override numbering-level indentation.
  -> Document Word precedence and keep school templates explicit about which layer owns the final
  paragraph indentation.
- [Risk] A template with fewer levels may hide an authoring mistake.
  -> Make last-level reuse deterministic and cover it with tests; document the behavior.
- [Risk] Word format names could leak into public YAML.
  -> Keep a closed semantic enum and one Renderer-local translation table.
- [Risk] Unicode bullet appearance depends on available fonts.
  -> Keep markers editable Unicode text and let paragraph style select the school font.

## Migration Plan

Existing templates continue to load through the generic default. The HUT template is updated to
declare its list policy explicitly. Rollback removes the additive `list` section and restores the
previous fixed helper without changing Markdown inputs.

## Open Questions

None for this slice.
