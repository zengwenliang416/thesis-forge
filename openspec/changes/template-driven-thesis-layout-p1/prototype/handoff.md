# Prototype Handoff: template-driven-thesis-layout-p1

## Approved Branch Variant

- Approved branch: `component-seam`.
- Approved variant: `cover-policy-docx-seam-v1`.
- User approval recorded on August 9, 2026 through the instruction to continue filling the gaps.
- Promotion remains subject to the SpecNav development entry gate.

## Screens Or Flows

- No production screen changes are included.
- `FLOW-VALIDATE`: YAML cover items become strict Template Model objects and invalid combinations
  produce field-specific errors.
- `FLOW-BUILD`: Front Matter becomes a renderer-neutral `CoverInstruction`; DOCX Renderer combines
  it with `CoverSpec.items` and emits editable styled paragraphs.

## Components To Create

- `CoverItemSpec` and `CoverSpec`.
- Closed cover metadata field enum.
- Cover item value resolver.
- Focused OOXML cover verification.

## Components To Reuse

- `ParagraphStyleSpec`, `FontSpec`, `LengthSpec` and `ThesisTemplate`.
- `CoverInstruction` and `RenderPlan`.
- Shared DOCX paragraph-style translator and font/unit helpers.
- Existing template loading, compile, render and atomic output services.

## Extraction Targets

- Keep item value resolution separate from DOCX paragraph creation.
- Reuse the common paragraph translator instead of adding cover-specific font and spacing code.
- Keep the generic default policy in Template Model and school-specific values in YAML.

## API Contracts

- `load_template(path) -> ThesisTemplate` gains an additive typed `cover` policy.
- `compile_document(...) -> RenderPlan` preserves its public signature.
- `CoverInstruction` retains renderer-neutral string fields.
- `DocxRenderer.render(plan, output) -> Path` retains its public signature.

## Data Flows

- Markdown Front Matter is parsed unchanged.
- Compiler resolves known metadata paths into `CoverInstruction`.
- Validated `CoverSpec.items` selects and orders those values or literal template text.
- Renderer applies prefixes, suffixes, empty handling and paragraph policy.
- Source Markdown and template YAML remain read-only.

## State Behavior

- Missing `cover`: deterministic generic default.
- Explicit `cover`: exact item order and styles.
- Empty field with `skip_if_empty: true`: no paragraph.
- Empty field with `skip_if_empty: false`: prefix/suffix paragraph remains available.
- Invalid field/text combination: template loading fails before compilation.

## Theme And Locale Policy

- Theme support: `light-only` for the unchanged UI.
- Theme modes in prototype: not applicable.
- Theme toggle: omitted.
- Runtime internationalization: disabled.
- Fixed documentation locale: `zh-CN`.

## Out Of Scope Items

- UI template editor.
- Absolute positioning, text boxes, shapes, Logo and signatures.
- Declaration pages and additional section roles.
- Lists, listings, algorithms, complex tables and inline rich text.
- Database, network, AI and deployment behavior.

## Required Tests

- Cover model defaults and invalid combinations.
- Duplicate metadata field rejection.
- Renderer-neutral CoverInstruction tests.
- DOCX paragraph order, text, font, size, color, alignment and spacing assertions.
- Same Front Matter with two different cover policies.
- Complete HUT offline build and package validation.

## Open Risks

- Paragraph-flow covers cannot reproduce absolute-position layouts.
- Verbose YAML can grow for complex covers; documentation must provide a complete example.
- Empty-value behavior must avoid accidental blank paragraphs.
- School values must not migrate back into Renderer constants.
