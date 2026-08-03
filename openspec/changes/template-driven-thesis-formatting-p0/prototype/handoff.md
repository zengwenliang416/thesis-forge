# Prototype Handoff: template-driven-thesis-formatting-p0

## Approved Branch Variant

- Approved branch: `component-seam`.
- Approved variant: `policy-role-docx-seam-v1`.
- User approval recorded on August 3, 2026.
- Promotion remains subject to the SpecNav development entry gate.

## Screens Or Flows

- No production screen changes are included.
- `FLOW-VALIDATE`: YAML is parsed into strict template policy models and invalid
  paragraph, TOC, bibliography, page or header/footer values produce
  field-specific validation errors.
- `FLOW-BUILD`: Markdown is parsed unchanged, Compiler resolves semantic roles,
  RenderPlan carries renderer-neutral roles, and DOCX Renderer translates the
  selected template policy into Word styles and section objects.
- Existing Web/Tauri template selection and build transports remain unchanged.

## Components To Create

- `ParagraphStyleSpec` reusable template policy.
- `SemanticStylesSpec` for abstract, keywords, TOC title, bibliography and
  special headings.
- `TocSpec` / `TocLevelSpec` for TOC 1-3 formatting and tabs.
- `BibliographySpec` and citation presentation configuration.
- `HeaderFooterVariantSpec` and `PageNumberDisplaySpec`.
- Renderer-neutral `ParagraphRole`.
- Shared DOCX paragraph-style translator and stable named-style registry.
- Focused TOC, paragraph border, document-grid and header/footer variant
  helpers.

## Components To Reuse

- `FontSpec`, `LengthSpec`, `LineSpacingSpec`, `ThesisTemplate` and strict YAML
  loading.
- `HeadingInstruction`, `ParagraphInstruction`, `CitationRun`,
  `BibliographyInstruction`, `TocInstruction`, `SectionBreakInstruction` and
  `RenderPlan`.
- Existing DOCX font, unit, field, bookmark and section helpers.
- Existing bibliography database and `Gbt7714Formatter`.
- Existing application services, package validation and atomic output
  replacement.

## Extraction Targets

- Extract one common paragraph policy instead of independently extending body,
  heading, TOC, bibliography and header/footer models.
- Extract one DOCX style translator instead of duplicating indentation,
  spacing, pagination, font and alignment conversion.
- Keep semantic-section state private to Compiler and scoped to one compile.
- Keep header/footer variant selection and low-level relationship cleanup in
  the DOCX section layer.
- Keep school-specific values in YAML templates and fixtures, never renderer
  constants.

## API Contracts

- `load_template(path) -> ThesisTemplate` remains strict and backward
  compatible.
- `compile_document(document, template, bibliography) -> RenderPlan` adds
  semantic roles without adding DOCX objects.
- `HeadingInstruction.role` is optional and renderer neutral.
- `ParagraphInstruction.role` defaults to `body`.
- Paragraph style resolution returns validated template policy, not Word
  objects.
- `DocxRenderer.render(plan, output) -> Path` retains its public contract.

## Data Flows

- Existing Markdown and AST structures are unchanged.
- Stable heading IDs establish Chinese/English abstract, TOC, bibliography,
  acknowledgements and achievements context.
- Keyword labels are recognized only at paragraph start inside the matching
  abstract section.
- The validated template remains the single policy source on RenderPlan.
- DOCX Renderer resolves roles against that template and writes real styles,
  tabs, borders, fields and section relationships.
- Existing Markdown, YAML, BibTeX and image inputs remain read-only.

## State Behavior

- Legacy template: missing P0 fields normalize to prior output semantics.
- Fully configured template: every P0 role and page variant uses explicit
  policy.
- Missing semantic style: deterministic heading/body fallback applies.
- Invalid template: field-specific validation stops before compilation.
- Disabled header/footer variant: the Word part is unlinked and cleared so
  previous-section content cannot leak.
- Repeated build: equivalent RenderPlan and normalized OOXML are produced.

## Theme And Locale Policy

- Theme support: `light-only` for the existing UI.
- Theme modes shown in prototype: not applicable because this is a
  component-seam prototype with no UI.
- Theme toggle: intentionally omitted.
- Runtime internationalization: disabled.
- Fixed product/documentation locale: `zh-CN`.
- Locale switcher: intentionally omitted.

## Out Of Scope Items

- Frontend template editor or new Web/Tauri transport contracts.
- Bilingual captions and lists of figures/tables.
- Advanced table geometry and equation tab/number layout.
- Componentized cover/declaration pages.
- `.doc`, EndNote and MathType import.
- Database, account, network, AI and deployment dependencies.
- Pixel-identical pagination across Word, WPS and LibreOffice.

## Required Tests

- Pydantic defaults, invalid values and all legacy built-in template fixtures.
- Compiler semantic-role state, keyword recognition and false-positive cases.
- RenderPlan architecture and deterministic role tests.
- DOCX common style translator tests.
- OOXML assertions for `w:pStyle`, `w:spacing`, `w:ind`,
  `w:widowControl`, `w:keepNext`, `w:keepLines`, `w:outlineLvl`,
  `w:snapToGrid`, `w:tabs` and `w:pBdr`.
- TOC 1-3 style, right-tab and leader tests.
- Citation superscript and bibliography hanging-indent tests.
- First/default/even header/footer relationship, distance, border,
  `w:evenAndOddHeaders`, PAGE and NUMPAGES tests.
- Complete offline CLI build and DOCX package validation.
- Microsoft Word or WPS primary sensory review; LibreOffice compatibility
  conversion as secondary evidence.

## Open Risks

- Keyword-like prose may be misclassified; recognition must be constrained to
  the active abstract and paragraph-start label.
- Pydantic inheritance/defaults may regress legacy templates; every existing
  YAML fixture must remain covered.
- Built-in TOC style names can vary by Office locale; tests must inspect actual
  `w:styleId` values.
- Header/footer inheritance can retain stale previous-section content; every
  explicitly configured or disabled variant must be unlinked and cleared.
- `em` indentation depends on the target style font size and must not use a
  global 12 pt assumption.
- Word, WPS and LibreOffice can paginate differently; sensory acceptance is
  based on correct structure and usable layout, not pixel identity.
