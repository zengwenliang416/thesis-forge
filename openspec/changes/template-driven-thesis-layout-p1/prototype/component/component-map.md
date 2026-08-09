# Component Seam: cover-policy-docx-seam-v1

## Ownership

| Component | Owns | Must Not Own |
| --- | --- | --- |
| Markdown Front Matter | Thesis metadata values | School fonts, spacing or Word objects |
| Template Model | Ordered cover items and paragraph policy | Thesis content or DOCX objects |
| Compiler | Metadata-to-semantic cover value resolution | Word layout translation |
| CoverInstruction | Renderer-neutral cover strings | Template models, DOCX or OOXML |
| DOCX Cover Renderer | Paragraph creation and Word translation | School constants or Markdown parsing |
| Paragraph Style Translator | Reusable paragraph/run property conversion | Cover field ordering |

## Public Seam

```text
Front Matter metadata
        |
        v
CoverInstruction semantic strings
        |
        +--------------------+
        |                    |
        v                    v
CoverSpec.items         DOCX Renderer
        |                    |
        +---- ordered policy-+
                             |
                             v
                 editable Word paragraphs
```

## Cover Item Contract

- Exactly one of `field` or `text`.
- `field` uses a closed metadata-field enum.
- `prefix` and `suffix` are template-owned display text.
- `skip_if_empty` controls missing metadata without adding placeholder text.
- `style` reuses `ParagraphStyleSpec`.
- Metadata-backed fields are unique within one cover policy.

## Dependency Direction

```text
Parser -> Domain -> Compiler -> RenderPlan -> DOCX Renderer
                         ^             ^
                         |             |
                    Template Model ----+
```

Parser and Domain do not import Template Model or DOCX. RenderPlan does not import Template Model,
python-docx, lxml or OOXML.

## Verification Boundary

- Model tests: defaults, exact-one-of, field enum and duplicate fields.
- Compiler tests: stable renderer-neutral cover payload.
- Renderer tests: item order, empty handling, prefixes/suffixes and OOXML paragraph/run properties.
- E2E tests: same Front Matter with two cover policies.
