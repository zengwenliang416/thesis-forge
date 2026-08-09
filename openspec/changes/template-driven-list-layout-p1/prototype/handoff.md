# Prototype Handoff: template-driven-list-layout-p1

## Approved Branch Variant

- Branch: `component-seam`
- Candidate variant pending explicit approval: `list-policy-docx-seam-v1`

## Screens Or Flows

- No UI screen change.
- `FLOW-VALIDATE`: YAML list policy -> typed validation diagnostics.
- `FLOW-BUILD`: Markdown list -> `ListInstruction` + selected `ListSpec` -> Word numbering and styled
  paragraphs.

## Components To Create

- `OrderedListLevelSpec`
- `UnorderedListLevelSpec`
- `OrderedListSpec`
- `UnorderedListSpec`
- `ListSpec`
- Renderer-local semantic number format mapper
- Deterministic list policy level resolver

## Components To Reuse

- `ParagraphStyleSpec`
- `LengthSpec`
- `ThesisTemplate`
- `ListInstruction`
- `RenderPlan`
- shared DOCX paragraph-style applicator
- shared DOCX unit conversion

## Extraction Targets

- Extract common list level selection instead of duplicating depth fallback in Renderer call sites.
- Keep one semantic-number-format translation table inside the DOCX list helper.
- Reuse the existing paragraph-style translator without a list-specific clone.

## API Contracts

- Additive `ThesisTemplate.list: ListSpec`.
- Existing `load_template(path) -> ThesisTemplate`.
- Existing `compile_document(document, template, bibliography) -> RenderPlan`.
- Existing `DocxRenderer.render(plan, output) -> Path`.
- Existing CLI `validate` and `build` contracts remain unchanged.

## Data Flows

- Template YAML -> Pydantic models -> `RenderPlan.template`.
- Markdown -> Parser -> Domain -> Compiler -> `ListInstruction`.
- `ListInstruction` + selected list policy -> numbering.xml + styled document.xml paragraphs.

## State Behavior

- Loading: not applicable; local synchronous template load and build.
- Empty: zero list levels are rejected; empty Markdown list blocks are not emitted.
- Error: field-specific template validation or structured DOCX render error.
- Disabled: not applicable.
- Permission: local input read and explicit output write only.

## Theme And Locale Policy

- Theme support: `light-only`, no UI impact.
- Theme modes shown in prototype: none; component-seam branch.
- Theme toggle: intentionally omitted.
- Internationalization: disabled.
- Locales shown in prototype: fixed `zh-CN` contract text only.
- Default locale: `zh-CN`.
- Locale switcher: intentionally omitted.

## Out Of Scope Items

- Production UI and template editor changes.
- Markdown syntax, Parser, Domain Model and RenderPlan list structure changes.
- Picture bullets, checkbox lists, custom bullet fonts, more than 9 levels and raw OOXML fields.
- Numbering continuity across separate Markdown list blocks.

## Required Tests

- List model defaults, validation and HUT explicit-policy loading.
- Renderer-neutral `ListInstruction` regression.
- numbering.xml format, marker, prefix/suffix, start, alignment, indentation and reference order.
- document.xml `numPr`, inline runs and full paragraph style properties.
- Non-1 start, configured-depth fallback, two-template differences and complete offline HUT build.

## Open Risks

- Direct paragraph indentation can override numbering-level defaults according to Word precedence.
- Unicode marker glyph shape depends on the configured font and installed office font fallback.
- Short template policies intentionally reuse their final level for deeper Markdown nesting.
