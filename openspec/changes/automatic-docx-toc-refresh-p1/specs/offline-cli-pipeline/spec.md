## ADDED Requirements

### Requirement: Optionally refresh DOCX indexes before publication
The build application SHALL attempt a local Office document refresh after rendering the temporary
DOCX and before package validation and atomic replacement.

#### Scenario: Compatible LibreOffice is available
- **WHEN** a complete thesis containing headings and a TOC is built on a host with compatible LibreOffice
- **THEN** the final DOCX contains materialized TOC entries and page numbers while retaining the editable TOC field

#### Scenario: LibreOffice is unavailable
- **WHEN** executable discovery finds no compatible LibreOffice
- **THEN** build succeeds with the valid dirty-field fallback and no network or AI dependency

#### Scenario: LibreOffice refresh fails or times out
- **WHEN** the isolated Office process cannot start, connect, update, save or exit within its bounds
- **THEN** build continues from the valid rendered temporary DOCX and cleans owned process/profile state

### Requirement: Preserve finalization safety
The system SHALL validate the post-refresh DOCX package before atomically replacing the requested
output and SHALL preserve any previous valid output on mandatory finalization failure or cancellation.

#### Scenario: Refresher corrupts the temporary package
- **WHEN** an injected refresher leaves an invalid DOCX
- **THEN** package validation fails, the prior output remains unchanged and temporary files are removed
