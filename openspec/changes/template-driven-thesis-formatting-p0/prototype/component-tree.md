# Component Seam Prototype: policy-role-docx-seam-v1

## Component Tree

```text
ThesisTemplate
|-- PageSpec
|   |-- margins
|   |-- header/footer distance
|   `-- optional document grid
|-- BodySpec -> ParagraphStyleSpec-compatible policy
|-- HeadingSpec -> ParagraphStyleSpec-compatible policies
|-- SemanticStylesSpec -> role-specific ParagraphStyleSpec values
|-- TocSpec -> TocLevelSpec(ParagraphStyleSpec + tab/leader)
|-- CitationSpec -> data style + presentation mode
|-- BibliographySpec -> title/entry styles
`-- SectionsSpec
    `-- SectionSpec
        |-- default/first/even header variants
        |-- default/first/even footer variants
        `-- PageNumberSpec + PageNumberDisplaySpec

ThesisDocument
`-- Compiler semantic context
    |-- stable heading ID -> ParagraphRole
    |-- active abstract/special-section state
    |-- keyword-label recognition inside matching abstract only
    `-- typed RenderPlan instructions with roles

DocxRenderer
|-- ParagraphStyleTranslator
|   |-- font and paragraph-format properties
|   `-- focused OOXML pagination/outline/grid/tab/border helpers
|-- stable named-style registry
|-- TOC style configuration
|-- citation run presentation
|-- bibliography paragraph presentation
`-- section/header/footer variant configuration
```

## Cohesion Check

- One reason to change:
  - Template Model changes when configurable policy vocabulary changes.
  - Compiler changes when semantic-role recognition changes.
  - RenderPlan changes when renderer-neutral instruction contracts change.
  - DOCX helpers change when Word translation behavior changes.
- State owner:
  - Template policy is immutable validated `ThesisTemplate`.
  - Active semantic section is private compiler state scoped to one compile.
  - Word style and section objects are owned only by the DOCX renderer.
- Side effects:
  - Prototype has none.
  - Production template loading reads YAML.
  - Production rendering mutates an in-memory DOCX package and writes only
    through the existing atomic application service.

## Coupling Check

- Allowed imports: Template Model -> Pydantic only; Compiler -> Domain,
  Template Model and RenderPlan; DOCX Renderer -> Template Model, RenderPlan
  and DOCX libraries.
- Forbidden imports: Parser/Domain/RenderPlan -> `docx`, `lxml` or DOCX
  renderer; bibliography formatter -> Word presentation; Template Model ->
  raw OOXML.
- Public API: closed style models, closed paragraph roles and typed
  instructions. OOXML helpers remain renderer-private.
- Extraction target: one reusable common paragraph policy and one reusable
  DOCX translator, not parallel body/heading/TOC/bibliography/header
  implementations.

## Change Sequence

1. Add strict models and legacy normalization while all existing templates pass.
2. Extract common DOCX translator and migrate body/headings without regression.
3. Add semantic roles and compiler state tests.
4. Add abstract/keyword, TOC, citation and bibliography presentation.
5. Add page geometry and first/default/even header/footer variants.
6. Update template documentation and school example.
7. Verify OOXML, full offline CLI behavior and rendered Office output.
