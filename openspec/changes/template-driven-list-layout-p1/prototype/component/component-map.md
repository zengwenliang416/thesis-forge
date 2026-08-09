# Component Seam: list-policy-docx-seam-v1

## Ownership

| Component | Owns | Must Not Own |
| --- | --- | --- |
| Markdown Parser / Domain | List kind, nesting, ordinals and inline content | School formats, template models or Word objects |
| Template Model | Ordered/unordered levels, geometry and paragraph policy | Markdown content or OOXML names |
| ListInstruction | Renderer-neutral list semantics | Template models, DOCX or OOXML |
| DOCX List Renderer | Policy selection, paragraph creation and style application | Markdown parsing or school constants |
| Numbering Translator | Semantic format mapping and numbering.xml creation | School policy or document semantics |
| Paragraph Style Translator | Reusable paragraph/run property conversion | List numbering and marker selection |

## Public Seam

```text
Markdown list semantics
        |
        v
ListInstruction
        |
        +----------------------+
        |                      |
        v                      v
ListSpec policy          DOCX Renderer
        |                      |
        +---- selected level --+
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
        numbering.xml translator    paragraph style translator
                 |                           |
                 +-------------+-------------+
                               |
                               v
                    editable Word list items
```

## Level Contract

- Ordered level: semantic format, prefix, suffix, marker alignment, absolute left indentation,
  absolute hanging indentation and `ParagraphStyleSpec`.
- Unordered level: non-empty Unicode marker, marker alignment, absolute left indentation, absolute
  hanging indentation and `ParagraphStyleSpec`.
- Policy: 1 to 9 levels; deeper Markdown levels reuse the final policy level and clamp Word `ilvl`
  to 8.
- Starting value: Markdown `start`, then first item ordinal, then 1; deeper numbering levels start
  at 1.
- Generic default: 9 decimal levels, `.` suffix, `•/◦/▪` marker cycle, 36pt incremental left
  indentation and 18pt hanging indentation.

## Dependency Direction

```text
Parser -> Domain -> Compiler -> RenderPlan -> DOCX Renderer
                         ^             ^
                         |             |
                    Template Model ----+
```

Parser, Domain and RenderPlan do not import Template Model or DOCX. Semantic Word format mapping
exists only in the DOCX numbering translator.

## Reused Components

- `ParagraphStyleSpec`
- `LengthSpec`
- `ThesisTemplate`
- `ListInstruction`
- `RenderPlan`
- shared DOCX paragraph-style applicator
- shared DOCX length-to-twips conversion

## Utilities / Services

- typed list-level validation
- list policy level resolution
- semantic number format mapping
- template loading, compile and render services

## Verification Boundary

- Model tests: defaults, enum, marker, level count and indentation geometry.
- RenderPlan tests: renderer-neutral semantic payload remains unchanged.
- Numbering tests: `numFmt`, `lvlText`, `lvlJc`, `start`, `ind` and reference order.
- Paragraph tests: `numPr`, inline runs, fonts, size, color, spacing and line spacing.
- E2E tests: same Markdown with two list policies and complete HUT build.
