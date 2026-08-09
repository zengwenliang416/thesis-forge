# Component Seam Prototype

## Component Tree

```text
ThesisTemplate
└── ListSpec
    ├── OrderedListSpec
    │   └── OrderedListLevelSpec[]
    └── UnorderedListSpec
        └── UnorderedListLevelSpec[]

RenderPlan
└── ListInstruction
    ├── ordered
    ├── start
    └── ListItemInstruction[]

DocxRenderer
└── render list instruction
    ├── resolve ordered/unordered policy
    ├── create_list_numbering
    │   └── semantic format -> Word format
    ├── apply_list_numbering
    └── apply_paragraph_style
```

## Cohesion Check

- One reason to change: Template Model changes for public YAML policy; list helper changes for Word
  numbering translation; shared style translator remains unchanged.
- State owner: `ListInstruction` owns document semantics; `ListSpec` owns presentation policy.
- Side effects: only DOCX package creation under the explicit output path.

## Coupling Check

- Allowed imports: DOCX list helper may import typed list policy and shared DOCX unit helpers.
- Forbidden imports: Parser/Domain/RenderPlan to Template Model or DOCX; Renderer to Markdown Parser;
  Template Model to python-docx/lxml/raw OOXML.
- Public API: additive `ThesisTemplate.list`; existing `ListInstruction` remains unchanged.
- Extraction target: one Renderer-local semantic numbering format mapper and one shared level
  selection helper; no duplicate paragraph-style translator.

No production UI component changes are required.
