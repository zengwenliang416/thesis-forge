## ADDED Requirements

### Requirement: Keep the TOC title outside the TOC field
The DOCX Renderer SHALL emit the visible TOC title as a standalone semantic title paragraph and
SHALL emit the real TOC complex field in the following paragraph.

#### Scenario: Inspect unrefreshed TOC OOXML
- **WHEN** a render plan contains a TOC instruction
- **THEN** `document.xml` contains a `TFTOCTitle` paragraph with literal title text followed by a different paragraph containing the TOC field

#### Scenario: Update the TOC field
- **WHEN** an Office application replaces the TOC field result
- **THEN** the standalone title paragraph remains unchanged

### Requirement: Preserve an editable dirty TOC fallback
The DOCX Renderer SHALL preserve the TOC field instruction, begin/separate/end field characters,
dirty marker and document-level update-fields setting without requiring an Office layout engine.

#### Scenario: Build without LibreOffice
- **WHEN** no compatible LibreOffice executable is installed
- **THEN** the generated DOCX contains a valid editable dirty TOC field and opens successfully
