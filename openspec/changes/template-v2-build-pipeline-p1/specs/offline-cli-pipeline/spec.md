## ADDED Requirements

### Requirement: Accept v2 template packages across inspect, validate and build
The `--template` selection of inspect, validate and build SHALL accept a v2 package directory or `.tftpl` file in addition to the v0.3 single YAML template, resolving both to the shared compilation template model so validation and compilation semantics stay uniform.

#### Scenario: Validate and inspect with a v2 package
- **WHEN** `validate` or `inspect` runs with a v2 package directory or `.tftpl` as the template
- **THEN** template-related results are semantically consistent with the same template consumed as v0.3

#### Scenario: Build with a v2 package
- **WHEN** `build` runs with a v2 package directory or `.tftpl` as the template
- **THEN** the pipeline compiles with the mapped template and shell assets are honored when present

### Requirement: Keep the template-id registry v0.3-only
The front-matter template-id registry lookup SHALL keep resolving only v0.3 registered templates; a template id that collides with a v2 package id SHALL fail with a structured template-not-found diagnostic rather than resolving to the v2 package.

#### Scenario: Template id never resolves a v2 package
- **WHEN** `render.template_id` matches the id of a v2 package that is not in the v0.3 registry
- **THEN** validation reports a structured template-not-found error and no misleading build output is produced
