# Acceptance Criteria: template-driven-list-layout-p1

## User-Visible Criteria

- A school template can configure ordered numbering formats, prefixes, suffixes, bullet markers,
  marker alignment, indentation and paragraph styles without changing Markdown.
- The HUT template produces editable ordered and unordered lists whose school values exist in YAML
  rather than Renderer constants.
- Two templates can produce differently formatted lists from the same Markdown while preserving
  list order, nesting and text.
- Markdown ordered lists that start at a value other than 1 retain that starting value.

## System Criteria

- Template loading rejects unsupported ordered formats, empty unordered markers, zero levels, more
  than 9 levels, relative list indentation and hanging indentation greater than left indentation.
- Existing templates that omit `list` load with a deterministic 9-level policy equivalent to the
  previous Renderer behavior.
- `ListInstruction` remains renderer neutral and continues to carry list kind, start, level,
  ordinal and inline content without template or DOCX objects.
- DOCX rendering creates true numbering definitions, selects the configured level policy and
  applies the common paragraph style to every list paragraph.
- The list renderer contains no fixed bullet tuple, fixed decimal format or fixed indentation.

## Data Criteria

- Markdown and YAML inputs are never modified.
- Repeated builds with identical inputs produce semantically equivalent list text, numbering
  definitions and paragraph properties.
- A Markdown nesting level deeper than the configured policy deterministically reuses the final
  configured level.

## Component Criteria

- Reusable components, hooks, utilities, or services named in
  `component-impact-map.json` are extracted instead of duplicated.
- List policy models contain no DOCX or OOXML objects.
- Parser, Domain and RenderPlan remain independent of the DOCX Renderer.
- List paragraph formatting uses the existing paragraph style model and translator.

## Verification Surfaces

- Facticity: compare requirements, Template Model, HUT YAML, RenderPlan and generated DOCX.
- Static: Ruff, architecture checks, strict OpenSpec validation and `git diff --check`.
- Unit: model defaults, format mapping, marker validation, level bounds and policy fallback.
- Redteam: unknown formats, empty markers, relative or invalid indentation and excessive levels.
- E2E: build one source with two templates and inspect numbering.xml plus document.xml.
- Sensory: open the HUT DOCX in Word or WPS and inspect ordered/unordered list flow.

## Unresolved Gaps

None for this slice.
