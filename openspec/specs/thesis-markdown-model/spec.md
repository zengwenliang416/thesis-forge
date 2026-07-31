# thesis-markdown-model Specification

## Purpose
TBD - created by archiving change build-thesisforge-v1-core. Update Purpose after archive.
## Requirements
### Requirement: Parse thesis front matter
The parser SHALL read optional YAML Front Matter into document metadata and SHALL report an
unclosed or invalid front matter block as a parse failure with source context.

#### Scenario: Valid front matter
- **WHEN** a thesis begins with a closed YAML Front Matter block
- **THEN** the parser stores the decoded mapping in `ThesisDocument.metadata` and continues parsing subsequent blocks

#### Scenario: Unclosed front matter
- **WHEN** a thesis starts Front Matter without a closing delimiter
- **THEN** parsing fails with an error that identifies the Front Matter problem

### Requirement: Produce semantic block types
The parser SHALL represent headings, paragraphs, lists, figures, tables, equations, algorithms,
listings and footnotes as domain objects rather than DOCX objects or renderer instructions.

#### Scenario: Semantic containers
- **WHEN** the source contains valid figure, table, equation, algorithm or listing containers
- **THEN** the resulting document contains the matching typed domain blocks with their declared content

### Requirement: Preserve stable IDs and source locations
Every referencable object MUST preserve its declared stable ID and source line, and IDs MUST use
the approved `chap:`, `sec:`, `fig:`, `tbl:`, `eq:`, `alg:` or `lst:` prefixes.

#### Scenario: Referencable figure
- **WHEN** a figure declares `{#fig:model}` on source line 20
- **THEN** the Figure has ID `fig:model` and a source location identifying line 20

### Requirement: Extract citations and cross-references
The parser SHALL extract cross-reference targets and citation keys while preserving the containing
source location and original text content.

#### Scenario: Mixed references
- **WHEN** a paragraph contains `@fig:model` and `[@smith2025; @wang2024]`
- **THEN** the document records one cross-reference target and a citation containing both keys

### Requirement: Keep parsing independent of rendering
Parser and domain modules MUST NOT import python-docx, lxml, DOCX renderer modules, UI modules or
AI providers, and the parser MUST NOT calculate final numbering.

#### Scenario: Architecture import check
- **WHEN** static architecture checks inspect Parser and Domain imports
- **THEN** no forbidden rendering, UI or AI dependency is present
