# Component Tree

```text
ThesisTemplate
└── CoverSpec
    └── CoverItemSpec[]
        ├── field | text
        ├── prefix
        ├── suffix
        ├── skip_if_empty
        └── ParagraphStyleSpec

RenderPlan
└── CoverInstruction
    └── semantic string values

DocxRenderer
└── render_cover
    ├── resolve item value
    ├── create paragraph
    └── apply_paragraph_style
```

No production UI component changes are required.
