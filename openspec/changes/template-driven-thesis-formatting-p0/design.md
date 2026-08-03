## Context

The current template model has separate `BodySpec` and `HeadingLevelSpec` shapes, while captions,
TOC paragraphs, bibliography entries and headers/footers either use partial custom logic or Word
defaults. `ParagraphInstruction` has no semantic role, citations are rendered as ordinary runs,
bibliography entries are ordinary paragraphs, TOC styles are not configured, and section rendering
only writes the default header/footer with a fixed “第 X 页 / 共 Y 页” footer.

The reference thesis analysis established a concrete P0 target: Songti/Times New Roman 12 pt body,
two-character first-line indentation, zero paragraph spacing, exact 20 pt line spacing, widow
control, independent Chinese/English abstract and keyword styles, three-level dotted TOC,
superscript citations, two-character hanging bibliography entries, 15 mm/17.5 mm header/footer
distances, alternating odd/even headers, a header bottom border and centered page numbers.

The implementation must preserve:

```text
Markdown -> ThesisDocument -> Validation -> Template -> Compiler -> RenderPlan -> DOCX
```

It must also preserve existing template compatibility and must not make Word automation, network,
AI or a specific school profile part of the core build.

## Goals / Non-Goals

**Goals:**

- Introduce one reusable paragraph-style model and one DOCX paragraph-style translator.
- Add semantic paragraph/heading roles without adding Word details to Parser or Domain.
- Make body, abstracts, keywords, TOC, citations, bibliography and page headers template driven.
- Emit real OOXML for pagination, tab stops, borders, header/footer variants and page fields.
- Keep existing templates and existing Markdown sources valid.
- Add focused unit, OOXML and end-to-end coverage.

**Non-Goals:**

- Bilingual captions, list of figures/tables, advanced table geometry or equation layout.
- Componentized cover/declaration pages.
- Legacy `.doc`, EndNote or MathType import.
- Frontend template editing controls.
- Pixel-identical pagination across Word, WPS and LibreOffice.

## Decisions

### 1. Introduce `ParagraphStyleSpec` as a reusable policy object

`ParagraphStyleSpec` owns optional common properties:

- font, size, bold, italic;
- alignment;
- left/right/first-line/hanging indentation;
- space before/after and line spacing;
- widow control, keep together, keep with next, page break before;
- outline level and snap-to-grid.

`BodySpec` remains a compatibility-facing required model and either extends or delegates to this
common shape. Existing defaults remain explicit so old YAML files parse unchanged.

Alternative considered: continue adding fields independently to `BodySpec`, `HeadingLevelSpec`,
TOC and bibliography models. Rejected because it duplicates validation and OOXML conversion.

### 2. Use named semantic roles, not arbitrary user-defined Word style names

Introduce a closed renderer-neutral role enum/value set such as:

- `body`;
- `abstract.zh.title`, `abstract.zh.body`, `keywords.zh`;
- `abstract.en.title`, `abstract.en.body`, `keywords.en`;
- `toc.title`;
- `bibliography.title`, `bibliography.entry`;
- `special.acknowledgements`, `special.achievements`.

Template semantic style entries point to `ParagraphStyleSpec`; Renderer creates stable internal
Word style IDs. Users configure properties, not raw `w:styleId` values.

Alternative considered: allow arbitrary Word style IDs in YAML. Rejected because it leaks renderer
details and makes cross-renderer behavior untestable.

### 3. Resolve roles in Compiler with a small document-context state machine

Parser continues producing ordinary headings and paragraphs. Compiler observes stable heading IDs
already used by the project (`chap:abstract-zh`, `chap:abstract-en`, `chap:toc`,
`chap:bibliography`, acknowledgements/achievements IDs) and tracks the active semantic section.
Typed instructions gain a semantic role field.

Keyword paragraphs are recognized only inside the matching abstract section using documented
Chinese/English keyword labels. The original inline runs and text remain unchanged.

Alternative considered: add a new Markdown container for every role. Rejected for P0 because it
would force source migrations and expand parser syntax unnecessarily.

### 4. Keep resolved style policy on `RenderPlan`

`RenderPlan` already carries the validated `ThesisTemplate`. Typed paragraph and heading
instructions carry only semantic roles; they do not copy raw DOCX properties. The Renderer selects
the validated template style by role.

This keeps the plan renderer neutral while making semantic selection testable.

Alternative considered: copy every resolved paragraph property into each instruction. Rejected
because it inflates plans and duplicates immutable template policy.

### 5. Centralize DOCX paragraph and style translation

Create a focused helper that applies a `ParagraphStyleSpec` to:

- a Word style's font and paragraph format;
- or a concrete paragraph when a header/footer or generated entry needs direct application.

Low-level additions not exposed by python-docx use focused OOXML helpers for:

- `w:widowControl`, `w:keepNext`, `w:keepLines`, `w:snapToGrid`;
- `w:outlineLvl`;
- tab stops and leaders;
- paragraph bottom borders.

The helper reuses existing font and unit conversion modules.

### 6. Configure TOC through real Word styles

The document keeps a real TOC field. The Renderer creates or updates `TOC 1`, `TOC 2` and `TOC 3`
styles from `TocSpec.levels`. Each level configures paragraph properties plus a right-aligned tab
stop and leader. TOC title remains a semantic heading role.

No static table-of-contents text is generated.

### 7. Separate bibliography text formatting from Word presentation

`Gbt7714Formatter` and bibliography records remain unchanged. `CitationSpec` gains a presentation
mode defaulting to `inline`. The inline renderer applies `superscript` only at DOCX run creation.
`BibliographySpec` supplies title/entry paragraph styles; `BibliographyInstruction` retains stable
entry data and order.

### 8. Model header/footer variants explicitly

Replace the single header/footer text policy with a compatible structure:

- `default` for odd/default pages;
- optional `even`;
- optional `first`;
- legacy `enabled`, `text` and `different_first_page` accepted and normalized to variants.

Each variant can define text, paragraph style, bottom border and page-number display. Page geometry
owns header/footer distances and optional document grid.

Renderer maps variants to python-docx default/even/first header/footer objects, unlinks each
configured or explicitly disabled variant, and enables `w:evenAndOddHeaders` when any even variant
is declared.

### 9. Make page-number content declarative

`PageNumberSpec` continues to own number format and restart. A nested display policy owns:

- alignment;
- PAGE prefix/suffix;
- whether NUMPAGES is included;
- separator and total-page prefix/suffix.

The default display reproduces current output for legacy templates. A P0 school template can select
a plain centered PAGE field.

### 10. Validate package structure before sensory review

Automated tests inspect:

- `word/styles.xml`;
- `word/document.xml`;
- `word/settings.xml`;
- section `w:pgMar`, `w:pgNumType` and references;
- header/footer parts and relationships;
- PAGE/NUMPAGES field codes.

Sensory review uses Microsoft Word or WPS as the primary target. LibreOffice conversion is retained
as compatibility evidence only.

## Risks / Trade-offs

- [Risk] Semantic keyword detection can misclassify prose containing “关键词” → restrict detection
  to the active abstract section and a label at paragraph start; test false positives.
- [Risk] Pydantic inheritance can produce confusing required/default fields → use explicit field
  defaults and compatibility fixtures for every built-in template.
- [Risk] Word built-in TOC style names vary by locale → address styles through stable built-in IDs
  where available and verify actual `w:styleId` values in package XML.
- [Risk] Header/footer inheritance can leak stale previous-section content → unlink and clear every
  explicitly configured or disabled variant; add regression tests.
- [Risk] `em` indentation depends on style font size → resolve it with the target style's configured
  size, not a global 12 pt assumption.
- [Risk] A broad common style helper could become an untyped catch-all → keep the Pydantic model
  closed, forbid unknown fields and split tab/border/page-number submodels.
- [Trade-off] Legacy page-number default remains the current “第/共” output for compatibility,
  while new templates can opt into plain PAGE output.
- [Trade-off] Role resolution is Compiler convention rather than new Markdown syntax; it is backward
  compatible but requires stable IDs for deterministic special-section recognition.

## Migration Plan

1. Add model types and defaults with legacy template fixtures passing.
2. Add common DOCX paragraph-style translation and migrate body/headings without output regression.
3. Add semantic roles to typed RenderPlan and compiler tests.
4. Add abstract/keywords and TOC styles.
5. Add citation/bibliography presentation.
6. Add page geometry and header/footer variants.
7. Update built-in templates, template documentation and complete example.
8. Run focused tests, full pytest, Ruff, package checks, OpenSpec validation and Office review.

Rollback is additive: remove new template usage while retaining legacy defaults. No user source or
database migration exists.

## Open Questions

None. P1/P2 capabilities remain explicitly outside this change.
