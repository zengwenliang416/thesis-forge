# Component Map

## Proposed Shared Components

- `DocumentRefresher`: application-owned protocol/callable for refreshing one temporary DOCX.
- `LibreOfficeDocumentRefresher`: best-effort default implementation.
- LibreOffice executable resolver covering macOS, Linux and Windows candidates.
- Isolated UNO refresh runner with bounded startup, update, save and cleanup.

## Reused Components

- `TocInstruction`
- `DocxRenderer`
- `add_complex_field`
- `set_update_fields`
- `ApplicationDependencies`
- `temporary_output_path`
- `validate_docx_package`
- `replace_output`

## Hooks

- `ApplicationDependencies.document_refresher`
- Build finalization sequence: refresh immediately after render and before package validation.

## Utilities / Services

- `discover_libreoffice_executable`
- isolated LibreOffice profile allocation
- private UNO endpoint allocation
- hidden document load and file URL conversion
- index/text-field update and same-file save
- timeout, process termination and profile cleanup
- no-op result for missing or failed optional runtime
