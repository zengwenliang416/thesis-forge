# generic-document-template Specification

## Purpose
TBD - created by archiving change docforge-project-format-v1. Update Purpose after archive.
## Requirements
### Requirement: Bundle docforge-standard
The distribution SHALL include a resolvable `docforge-standard` template that
can render a general document without an academic profile.

#### Scenario: Resolve bundled template
- **WHEN** a project declares `render.template_id: docforge-standard`
- **THEN** template resolution returns the bundled validated template package without network access

### Requirement: Avoid fabricated academic metadata
`docforge-standard` MUST NOT require or synthesize university, college, degree,
major, advisor, student ID, or completion metadata.

#### Scenario: Build general document
- **WHEN** a valid general project contains common metadata and no academic profile
- **THEN** validation and build succeed without adding academic placeholders to the DOCX

#### Scenario: Inspect rendered content
- **WHEN** the generated DOCX package and visible document text are inspected
- **THEN** no fabricated academic labels or values appear

### Requirement: Bind generic metadata through the template model
The Template Model SHALL expose title, subtitle, authors, organization,
document date, version, and keywords as typed bindings and SHALL render them only where
the selected template declares them.

#### Scenario: Render declared common metadata
- **WHEN** `docforge-standard` declares bindings for supplied common metadata
- **THEN** the compiled RenderPlan contains the resolved values in template-defined locations

#### Scenario: Omit absent optional metadata
- **WHEN** optional common metadata is absent
- **THEN** compilation omits its binding without inserting fallback prose

### Requirement: Keep document profile logic out of the renderer
Template validation and compilation SHALL resolve profile-specific bindings
before rendering. The DOCX renderer MUST consume only RenderPlan instructions
and MUST NOT branch on `general`, `academic`, or template IDs.

#### Scenario: Render general and academic plans
- **WHEN** the renderer receives valid RenderPlans from general and academic templates
- **THEN** it renders both using the same node and OOXML capabilities without inspecting document profile

### Requirement: Preserve template-driven Word behavior
The generic template SHALL use the existing typed template model and true
OOXML capabilities for styles, fields, sections, captions, equations, headers,
footers, and page numbering where configured.

#### Scenario: Validate generic template package
- **WHEN** distribution and template tests load `docforge-standard`
- **THEN** its schema, referenced files, styles, and OOXML shell resources pass the same package validation as other bundled templates
