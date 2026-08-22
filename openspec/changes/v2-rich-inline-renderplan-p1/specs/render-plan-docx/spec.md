## MODIFIED Requirements

### Requirement: Produce renderer-neutral typed inline runs

The Compiler and typed RenderPlan model SHALL use one `InlineRun` union whose
canonical variants include text, semantic references, citations, footnote
references, soft breaks, hard breaks, hyperlinks, and inline math. The names
and semantic fields of the four rich inline variants SHALL match
`spec/format-capabilities.yaml`: `SoftBreakRun`, `HardBreakRun`,
`HyperlinkRun`, and `MathRun`.

#### Scenario: Canonical rich inline names are available

- **WHEN** the typed RenderPlan module is inspected
- **THEN** it defines `SoftBreakRun`, `HardBreakRun`, `HyperlinkRun`, and
  `MathRun`, and all four are members of the single `InlineRun` union

#### Scenario: Hyperlink and math semantics are retained

- **WHEN** a hyperlink or inline-math run is constructed
- **THEN** `HyperlinkRun` retains its readable `text` and target `destination`,
  and `MathRun` retains its source `latex` without renderer-specific objects

#### Scenario: Break semantics are not collapsed

- **WHEN** a soft break or hard break is constructed
- **THEN** its run type alone identifies the break semantics and no
  compatibility boolean or alternate break alias is required

#### Scenario: Unknown inline runs fail explicitly

- **WHEN** a value outside the canonical `InlineRun` variants reaches the typed
  seam
- **THEN** the boundary raises an explicit type error rather than returning
  `None`, flattening the value, serializing a generic payload, or emitting a
  debug marker

### Requirement: Preserve single-source typed instruction data

Typed RenderPlan preparation SHALL not add a raw-plus-typed duplicate for
figure captions or any other inline content.

#### Scenario: A1M does not create a second caption source

- **WHEN** the A1M change is applied
- **THEN** `FigureInstruction` remains outside this preparation seam and no
  `caption_inlines` field or synchronized raw/typed caption pair is introduced
