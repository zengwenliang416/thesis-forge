## ADDED Requirements

### Requirement: Define explicit example heading colors
The example school template SHALL explicitly define black Heading 1, Heading 2, and Heading 3
colors instead of inheriting Office theme colors.

#### Scenario: Inspect example heading styles
- **WHEN** a document is rendered with the example school template
- **THEN** Heading 1, Heading 2, and Heading 3 contain `w:color w:val="000000"` without theme color attributes
