## MODIFIED Requirements

### Requirement: Load bibliography data locally
The bibliography subsystem SHALL load the optional project-relative BibTeX file
configured by `docforge.yaml` without network access and SHALL expose records
through a renderer-neutral interface.

#### Scenario: Valid BibTeX file
- **WHEN** the confined manifest-resolved bibliography file contains valid entries
- **THEN** the loader returns records indexed by citation key

#### Scenario: General project without bibliography
- **WHEN** a general project declares no bibliography and contains no citations
- **THEN** inspect, validate, review, and build proceed without creating a bibliography dependency

### Requirement: Validate citation keys
Every citation key in the `ForgeDocument` MUST resolve to a loaded bibliography
record before build.

#### Scenario: Unknown citation
- **WHEN** a document cites a key that does not exist in the project bibliography
- **THEN** validation reports a `missing-citation` error and build does not render
