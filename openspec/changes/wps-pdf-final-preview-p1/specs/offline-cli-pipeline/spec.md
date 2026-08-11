## ADDED Requirements

### Requirement: Optionally export a PDF preview after DOCX publication
The application build service SHALL attempt a local PDF preview export after a valid DOCX has been
published and SHALL report preview availability separately from DOCX success.

#### Scenario: Export succeeds
- **WHEN** a compatible local exporter creates a valid PDF
- **THEN** `BuildResult` contains engine-labelled final-preview metadata

#### Scenario: Export is unavailable or fails
- **WHEN** no compatible exporter exists or conversion fails or times out
- **THEN** the DOCX build remains successful and final-preview metadata reports no ready artifact

### Requirement: Publish only validated PDF artifacts
The PDF exporter SHALL write to bounded temporary storage and SHALL atomically publish only a
non-empty file with a valid PDF signature.

#### Scenario: Converter emits invalid output
- **WHEN** conversion exits successfully but produces an empty or non-PDF file
- **THEN** no new preview is published and any result is reported unavailable
