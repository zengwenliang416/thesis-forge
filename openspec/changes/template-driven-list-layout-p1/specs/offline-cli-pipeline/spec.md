## ADDED Requirements

### Requirement: Build template-driven lists offline
The complete offline build SHALL generate the selected template's ordered and unordered list
presentation from Markdown and YAML without modifying source or template files.

#### Scenario: HUT list build
- **WHEN** the complete HUT example containing nested ordered and unordered lists is built with external network access unavailable
- **THEN** build succeeds and the DOCX contains the configured editable numbering definitions and styled list paragraphs

#### Scenario: Same source with two templates
- **WHEN** one Markdown source is built with two templates that declare different list policies
- **THEN** both DOCX files preserve semantic list content while their numbering and paragraph properties differ
