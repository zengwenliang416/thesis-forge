# document-markdown-model Specification

## Purpose
TBD - created by archiving change docforge-project-format-v1. Update Purpose after archive.
## Requirements
### Requirement: Expose a generic ForgeDocument aggregate
The core domain SHALL expose `ForgeDocument` as the single parsed document
aggregate and SHALL NOT export `ThesisDocument`.

#### Scenario: Parse Markdown
- **WHEN** the production Markdown parser parses a valid source
- **THEN** it returns `ForgeDocument` with source path, metadata, semantic blocks, and bibliography configuration

#### Scenario: Import public core model
- **WHEN** a caller imports the public core aggregate
- **THEN** `ForgeDocument` is available and `ThesisDocument` is absent

### Requirement: Preserve stable semantic object identity
`ForgeDocument` SHALL retain the existing stable IDs, source locations, block
and inline types, citations, bibliography configuration, and cross-reference
semantics used by validation and compilation.

#### Scenario: Index referenceable blocks
- **WHEN** a parsed document contains identified headings, figures, tables, equations, algorithms, or listings
- **THEN** `ForgeDocument` returns a deterministic ID index for those blocks

#### Scenario: Preserve source locations
- **WHEN** parsing creates blocks and inline nodes
- **THEN** their source line and column information remains available to diagnostics and Review mapping

### Requirement: Keep document metadata renderer-neutral
Domain metadata MUST contain only serializable document values and MUST NOT
contain python-docx, lxml, OOXML, transport, UI, or template implementation
objects.

#### Scenario: Inspect domain aggregate
- **WHEN** a `ForgeDocument` instance is serialized for inspection
- **THEN** all metadata and semantic values can be represented without importing renderer dependencies

### Requirement: Keep parsing independent of document profiles
The Markdown parser SHALL parse the same syntax for general and academic
projects. It MUST NOT branch on `document.type`, academic profile presence, or
template identity.

#### Scenario: Parse identical Markdown in two profiles
- **WHEN** identical Markdown is used by a general project and an academic project
- **THEN** the parser produces equivalent semantic block and inline structures

### Requirement: Preserve deterministic document construction
Repeated parsing of the same source snapshot MUST produce semantically
equivalent `ForgeDocument` content, stable object IDs where source IDs are
declared, and stable source locations.

#### Scenario: Repeat parse
- **WHEN** the same Markdown snapshot is parsed twice with the same source path
- **THEN** metadata, semantic blocks, declared IDs, references, citations, and locations are equivalent
