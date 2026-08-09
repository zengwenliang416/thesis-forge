# Acceptance Criteria: template-driven-thesis-layout-p1

## User-Visible Criteria

- A school template can choose cover metadata fields, literal text and their order without changing
  Markdown.
- Each cover item can configure prefix, suffix, empty-value behavior, font, size, color, emphasis,
  alignment, indentation, spacing, line spacing and pagination controls.
- The HUT template produces a complete editable cover whose school values exist in YAML rather than
  Renderer constants.
- Two templates can produce differently ordered and styled covers from the same Front Matter.

## System Criteria

- Template loading rejects items that provide both or neither of `field` and `text`.
- Unsupported fields, empty literal text and duplicate metadata fields fail with field-specific
  diagnostics.
- `CoverInstruction` remains renderer neutral and exposes deterministic semantic string values.
- DOCX rendering iterates `cover.items`, applies prefixes/suffixes and reuses the shared paragraph
  style translator.
- The cover renderer contains no fixed field loop, fixed centered alignment or hard-coded spacer
  paragraphs.

## Data Criteria

- Markdown and YAML inputs are never modified.
- Existing templates that omit `cover` receive a deterministic generic cover layout.
- Repeated builds with identical inputs produce semantically equivalent cover paragraph order and
  OOXML properties.

## Component Criteria

- `CoverSpec` and `CoverItemSpec` contain no DOCX or OOXML objects.
- Parser and Domain remain independent of Template Model and Renderer.
- Cover formatting uses the existing paragraph style model and DOCX translation helpers.

## Verification Surfaces

- Facticity: compare requirements, Template Model, HUT YAML, RenderPlan and generated DOCX.
- Static: Ruff, architecture checks, strict OpenSpec validation and `git diff --check`.
- Unit: model defaults, mutual exclusion, duplicate fields and cover value resolution.
- Redteam: unknown fields, empty static text, missing metadata with both empty-value policies.
- E2E: build one source with two templates and inspect cover text order and OOXML style properties.
- Sensory: open the HUT DOCX in Word or WPS and inspect the cover.

## Unresolved Gaps

None for this slice.
