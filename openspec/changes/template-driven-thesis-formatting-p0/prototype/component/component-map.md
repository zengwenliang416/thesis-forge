# Component Map: policy-role-docx-seam-v1

## Proposed Shared Components

- `ParagraphStyleSpec` in `thesis_forge.templates.model`
  - Closed Pydantic policy model with `extra="forbid"`.
  - Owns font, size, emphasis, alignment, indentation, spacing, pagination,
    outline and grid-alignment properties.
  - Contains no `python-docx`, `lxml`, `w:*` names or Word style IDs.
- `SemanticStylesSpec` in `thesis_forge.templates.model`
  - Owns optional styles for Chinese/English abstract titles, bodies and
    keywords; TOC title; bibliography title and entries; acknowledgements and
    achievements.
  - Missing entries fall back deterministically to heading/body policies.
- `TocSpec` and `TocLevelSpec` in `thesis_forge.templates.model`
  - Own TOC 1-3 paragraph policies plus right tab stop and dot-leader policy.
- `BibliographySpec` and citation presentation fields
  - Keep bibliography data/text formatting separate from Word presentation.
- `HeaderFooterVariantSpec`, `PageNumberDisplaySpec` and page geometry additions
  - Express first/default/even variants, borders, PAGE/NUMPAGES display,
    header/footer distances and optional document grid.
- `ParagraphRole` in `thesis_forge.core.render_plan`
  - Closed renderer-neutral role values such as `body`,
    `abstract.zh.title`, `abstract.zh.body`, `keywords.zh`,
    `abstract.en.title`, `abstract.en.body`, `keywords.en`, `toc.title`,
    `bibliography.title`, `bibliography.entry`,
    `special.acknowledgements` and `special.achievements`.
- `ParagraphStyleTranslator` in `thesis_forge.renderers.docx.styles`
  - Applies one validated `ParagraphStyleSpec` to a named Word style or a
    concrete paragraph.
  - Owns conversion to `python-docx` properties and focused OOXML for
    unsupported pagination, outline, grid, tabs and borders.

## Reused Components

- `LengthSpec`, `FontSpec`, `LineSpacingSpec` and existing strict template
  loading in `thesis_forge.templates.model`.
- `to_docx_length`, `to_points` and `apply_font` in the DOCX renderer.
- `HeadingInstruction`, `ParagraphInstruction`, `CitationRun`,
  `BibliographyInstruction`, `TocInstruction`, `SectionBreakInstruction` and
  `RenderPlan`.
- Existing real `TOC`, `PAGE`, `NUMPAGES`, bookmark, REF and SEQ field helpers.
- Existing bibliography database and `Gbt7714Formatter`; no Word behavior moves
  into bibliography formatting.
- Existing application service pipeline and atomic output replacement.

## Hooks

- No UI hooks are introduced.
- Compiler hook: a private semantic context consumes stable heading IDs and
  emits `ParagraphRole` on heading/paragraph instructions.
- Renderer hook: instruction rendering resolves `ParagraphRole` against the
  validated template before creating or selecting a Word paragraph style.
- Section hook: initial and added sections share the same variant configurator
  so explicit disabled variants are unlinked and cleared.

## Utilities / Services

- `resolve_paragraph_style(template, role, *, heading_level=None)` returns a
  validated style policy with deterministic fallback; it returns no DOCX
  object.
- `ensure_paragraph_style(document, role, spec)` creates or updates stable
  internal Word styles and delegates property application to the translator.
- `apply_paragraph_style(target, spec, *, em_size_pt)` applies the common
  policy to a style or concrete header/footer paragraph.
- `configure_toc_styles(document, toc_spec)` updates real `TOC 1` through
  `TOC 3` styles and their right tab/leader settings.
- `configure_header_footer_variants(section, section_spec)` handles default,
  first and even relationships, text, paragraph style, border and fields.

## Public Contracts

```python
ParagraphRole = Literal[
    "body",
    "abstract.zh.title",
    "abstract.zh.body",
    "keywords.zh",
    "abstract.en.title",
    "abstract.en.body",
    "keywords.en",
    "toc.title",
    "bibliography.title",
    "bibliography.entry",
    "special.acknowledgements",
    "special.achievements",
]

@dataclass(frozen=True, slots=True)
class HeadingInstruction:
    ...
    role: ParagraphRole | None = None

@dataclass(frozen=True, slots=True)
class ParagraphInstruction:
    ...
    role: ParagraphRole = "body"
```

The exact internal helper names may change during implementation, but the
ownership and dependency direction are fixed.

## Compatibility Boundary

- Existing `body` fields remain valid and preserve current defaults.
- Existing `HeadingLevelSpec` fields remain valid while delegating shared
  properties to the common policy shape.
- Legacy `header.enabled`, `header.text`, `different_first_page`, footer fields
  and current page-number output are normalized into variant/display models.
- Existing templates that omit semantic, TOC, bibliography and page-geometry
  additions must load and build without source migration.
- Unknown template fields remain rejected.

## Allowed Dependencies

```text
templates.model
    ^
    |
core.compiler -> core.render_plan
    |                 |
    +-----------------+
              |
              v
renderers.docx.styles / sections / renderer
```

- `core.parser` and `core.model` may depend only on renderer-neutral code.
- `core.compiler` may import Template Model and RenderPlan types.
- `core.render_plan` may carry Template Model values but never DOCX/OOXML
  objects.
- DOCX helpers may import Template Model and RenderPlan types.

## Forbidden Dependencies

- Parser or Domain importing `docx`, `lxml` or renderer modules.
- Template models containing raw `w:p`, `w:r`, `CT_P`, `WD_*` or Word style IDs.
- Compiler constructing `OxmlElement`, `Document`, styles, headers or footers.
- Bibliography formatter selecting superscript, indentation or Word styles.
- Renderer hard-coding 湖南工业大学 fonts, spacing, margins, borders or page text.

## Promotion Tests

- Template model and legacy YAML compatibility tests.
- Compiler role-state tests, including keyword false-positive cases.
- RenderPlan serialization/tests proving roles are renderer neutral.
- DOCX XML tests for styles, spacing, indentation, pagination, TOC tabs,
  citation superscript, bibliography hanging indent, page geometry,
  first/default/even relationships, borders and PAGE/NUMPAGES fields.
- Full offline CLI build and package validation.
- Word/WPS primary sensory review and LibreOffice compatibility conversion.
