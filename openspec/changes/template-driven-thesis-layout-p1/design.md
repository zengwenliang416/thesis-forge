## Context

`CoverInstruction` already contains renderer-neutral values compiled from Front Matter. The current
DOCX cover renderer ignores template policy and emits those values in a fixed order with centered
paragraphs and hard-coded blank paragraphs. P0 already provides a reusable `ParagraphStyleSpec`
and DOCX paragraph-style translator, so the new capability should compose those existing pieces
rather than introduce another formatting path.

## Goals / Non-Goals

**Goals:**

- Make cover item ordering and paragraph presentation fully template driven.
- Support both metadata-backed fields and template-owned static text.
- Preserve deterministic output and field-specific validation diagnostics.
- Reuse the common paragraph style contract and DOCX translation helpers.
- Keep cover content renderer neutral and maintain offline builds.

**Non-Goals:**

- Absolute positioning, floating text boxes, shapes, logos or signature images.
- Declaration pages, authorization forms or arbitrary additional section roles.
- Changing Front Matter syntax or moving school formatting into Markdown.
- Pixel-identical pagination across Word, WPS and LibreOffice.

## Decisions

### Ordered cover items

`CoverSpec.items` is an ordered tuple of `CoverItemSpec`. An item declares exactly one of a
supported semantic `field` or literal `text`. This is preferred over a fixed set of named style
properties because schools can reorder or omit fields without Renderer changes.

### Content and presentation remain separate

Metadata values stay in `CoverInstruction`; the template only selects a field and supplies optional
`prefix` and `suffix`. Literal template text supports labels such as degree type without requiring
school boilerplate in Markdown.

### Common paragraph policy

Each item owns a `ParagraphStyleSpec`. Spacing before and after replaces hard-coded blank
paragraphs. The renderer applies the existing shared paragraph translator to the emitted paragraph
and runs.

### Deterministic generic default

`ThesisTemplate.cover` has a generic default matching the previous semantic field order and centered
presentation. Built-in school templates declare explicit items so school rules exist only in YAML.

### Validation

An item MUST declare exactly one of `field` or `text`. Metadata field names use a closed enum.
Duplicate metadata fields are rejected because they are most likely template mistakes; literal text
items may repeat.

## Risks / Trade-offs

- [Risk] A cover requiring absolute placement cannot be represented by paragraph flow.
  -> Keep absolute positioning out of this slice and fail honestly rather than introducing DOCX
  text boxes.
- [Risk] A large `cover.items` list is verbose.
  -> Preserve a generic default and document a complete school example.
- [Risk] Direct formatting could diverge from reusable styles.
  -> Route every item through the shared paragraph-style translator and assert OOXML properties.

## Migration Plan

Existing templates continue to load through the generic default. The HUT template is updated to
declare its cover layout explicitly. Rollback removes the additive `cover` section and restores the
previous cover renderer without changing Markdown inputs.

## Open Questions

None for this slice.
