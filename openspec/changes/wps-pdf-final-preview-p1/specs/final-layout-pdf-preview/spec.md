## ADDED Requirements

### Requirement: Present a truthful final-layout PDF
The workbench SHALL display a real PDF artifact in a final-layout preview and SHALL identify the
actual engine or source that produced it.

#### Scenario: Automatic LibreOffice preview is available
- **WHEN** a DOCX build completes and LibreOffice exports a valid PDF
- **THEN** the final-layout tab renders that PDF and labels it `LibreOffice PDF`

#### Scenario: User selects a WPS-exported PDF
- **WHEN** the user explicitly selects a valid local PDF produced by WPS
- **THEN** the final-layout tab renders the selected file and labels it `WPS PDF`

#### Scenario: No PDF is available
- **WHEN** automatic export is unavailable or fails and no WPS PDF is selected
- **THEN** the DOCX remains successful and the final-layout tab shows an actionable unavailable state

### Requirement: Mark final preview freshness
The workbench SHALL distinguish a final preview for the current saved source/template snapshot from
an older preview.

#### Scenario: Build or import current snapshot
- **WHEN** a build succeeds with PDF or the user selects a WPS PDF for a clean built workspace
- **THEN** the preview is marked current

#### Scenario: Inputs change
- **WHEN** Markdown text changes, template selection changes or a different source opens
- **THEN** the previous preview is marked stale or cleared and cannot be presented as current

### Requirement: Preserve secure runtime-specific artifact access
The system SHALL resolve PDF bytes without exposing arbitrary filesystem reads.

#### Scenario: Web reads automatic PDF
- **WHEN** the browser requests a generated preview
- **THEN** the server serves only a plain `.pdf` file inside the referenced opaque workspace

#### Scenario: Desktop reads PDF
- **WHEN** Tauri displays an automatic or selected PDF
- **THEN** the native layer reads only the authorized derived path or user-selected `.pdf`
