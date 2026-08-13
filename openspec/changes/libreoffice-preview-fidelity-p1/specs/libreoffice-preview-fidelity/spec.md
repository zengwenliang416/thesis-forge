## ADDED Requirements

### Requirement: Adapt fonts only inside LibreOffice preview conversion
The application SHALL use a disposable DOCX copy for platform-specific LibreOffice font adaptation
and SHALL NOT modify the input or published DOCX.

#### Scenario: Convert on macOS
- **WHEN** LibreOffice exports a DOCX containing `宋体` or `黑体` on macOS
- **THEN** the disposable copy uses the approved macOS-compatible font aliases and the source DOCX bytes remain unchanged

#### Scenario: Convert on Windows or Linux
- **WHEN** LibreOffice exports the same DOCX outside macOS
- **THEN** macOS-specific font aliases are not injected

### Requirement: Preserve safe PDF preview failure semantics
Font adaptation and LibreOffice conversion SHALL remain optional, bounded, and isolated from DOCX
build success.

#### Scenario: Adaptation fails
- **WHEN** the DOCX package cannot be copied or adapted safely
- **THEN** preview export reports unavailable without replacing a prior valid PDF or changing the DOCX

### Requirement: Verify real PDF font behavior
Verification MUST inspect the fonts embedded in a complete thesis PDF and MUST NOT infer preview
font fidelity solely from DOCX OOXML.

#### Scenario: Audit complete macOS PDF
- **WHEN** the complete thesis fixture is converted on macOS
- **THEN** the body font list contains the Songti-compatible embedded font and does not contain Arial Unicode MS
