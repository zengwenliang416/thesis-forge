## MODIFIED Requirements

### Requirement: Format inline citations deterministically
The citation formatter SHALL preserve first-use and grouped-citation semantics defined by the
selected local style and SHALL return deterministic inline citation text/instructions; the
Template Model SHALL independently select inline or superscript DOCX presentation.

#### Scenario: Superscript grouped citation
- **WHEN** a grouped citation resolves to deterministic text and the template selects superscript mode
- **THEN** the Renderer preserves the resolved text and emits superscript run formatting

#### Scenario: Inline citation compatibility
- **WHEN** a legacy template omits citation presentation mode
- **THEN** citation text remains inline as in the existing renderer behavior

### Requirement: Render bibliography entries
The bibliography subsystem SHALL produce an ordered bibliography containing all and only the
records required by the configured policy, using stable output across repeated builds; the
Renderer SHALL apply template-driven bibliography title and entry paragraph styles without
changing bibliography text or order.

#### Scenario: Referenced-only styled bibliography
- **WHEN** the policy includes referenced entries only and the template declares a two-character
  hanging indent with exact 20 pt line spacing
- **THEN** uncited records are omitted, cited records remain deterministic, and each DOCX entry uses the configured indentation and spacing

#### Scenario: Bibliography remains renderer neutral
- **WHEN** bibliography loading and formatting tests run
- **THEN** they do not import DOCX modules or construct Word objects despite the added presentation configuration
