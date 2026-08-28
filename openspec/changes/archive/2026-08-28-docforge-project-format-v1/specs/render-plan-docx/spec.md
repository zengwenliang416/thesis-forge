## ADDED Requirements

### Requirement: Use neutral document output identity
The output pipeline SHALL use DocForge protocol identity and neutral document
filenames across compiler, renderer, finalization, postflight, preview, and
BuildReport surfaces without
changing renderer-neutral RenderPlan or true OOXML behavior.

#### Scenario: Build default output
- **WHEN** a valid DocForge project builds without an output override
- **THEN** finalization writes `build/document.docx` and the BuildReport references that neutral output

#### Scenario: Preserve renderer boundary
- **WHEN** a general or academic `ForgeDocument` is compiled and rendered
- **THEN** the renderer consumes only RenderPlan instructions and does not inspect the project manifest, document profile, Markdown source, or transport DTO

### Requirement: Preserve deterministic finalization and preview
Renaming output and protocol identities MUST preserve atomic replacement,
postflight package validation, Office finalization policy, derived PDF preview,
and last-successful-preview behavior.

#### Scenario: Finalization fails
- **WHEN** rendering succeeds but postflight or Office finalization fails
- **THEN** the previous successful DOCX and preview remain available and the new temporary output is not promoted

#### Scenario: Produce final preview
- **WHEN** Microsoft Word or the configured supported Office engine successfully derives a preview from `document.docx`
- **THEN** the authorized preview descriptor refers to the derived sibling PDF under the DocForge BuildReport contract
