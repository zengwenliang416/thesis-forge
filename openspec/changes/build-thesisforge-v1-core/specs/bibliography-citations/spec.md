## ADDED Requirements

### Requirement: Load bibliography data locally
The bibliography subsystem SHALL load configured local BibTeX files without network access and
SHALL expose records through a renderer-neutral interface.

#### Scenario: Valid BibTeX file
- **WHEN** the configured bibliography file contains valid entries
- **THEN** the loader returns records indexed by citation key

### Requirement: Validate citation keys
Every citation key in the ThesisDocument MUST resolve to a loaded bibliography record before build.

#### Scenario: Unknown citation
- **WHEN** a document cites a key that does not exist in the bibliography
- **THEN** validation reports a `missing-citation` error and build does not render

### Requirement: Format inline citations deterministically
The citation formatter SHALL preserve first-use and grouped-citation semantics defined by the
selected local style and SHALL return deterministic inline citation text/instructions.

#### Scenario: Grouped citation
- **WHEN** a citation contains two valid keys in a declared order
- **THEN** repeated compilation produces the same grouped inline citation result

### Requirement: Render bibliography entries
The bibliography subsystem SHALL produce an ordered bibliography containing all and only the
records required by the configured policy, using stable output across repeated builds.

#### Scenario: Referenced-only bibliography
- **WHEN** the policy includes referenced entries only
- **THEN** uncited records are omitted and cited records appear in deterministic order

### Requirement: Provide GB/T 7714-2025 formatting contract
The system SHALL provide a GB/T 7714-2025 formatter interface and golden fixtures for supported
document types, while allowing a compliant local CSL/citeproc backend to be substituted.

#### Scenario: Golden bibliography case
- **WHEN** a supported fixture is formatted with the GB/T 7714-2025 style
- **THEN** inline citation and bibliography output match the reviewed golden result

### Requirement: Keep bibliography independent of DOCX
Bibliography loading and formatting MUST NOT create DOCX or OOXML objects; the Renderer SHALL
consume resolved citation and bibliography instructions from the Compiler.

#### Scenario: Bibliography unit test
- **WHEN** bibliography formatting is tested
- **THEN** the test runs without importing python-docx or constructing a Word document
