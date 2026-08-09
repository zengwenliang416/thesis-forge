## ADDED Requirements

### Requirement: Build a template-driven cover offline
The complete offline build SHALL generate the selected template's ordered cover layout from
Markdown Front Matter without modifying source or template files.

#### Scenario: HUT cover build
- **WHEN** the complete HUT example is built with external network access unavailable
- **THEN** build succeeds and the DOCX cover contains the configured fields, literal labels and styles
