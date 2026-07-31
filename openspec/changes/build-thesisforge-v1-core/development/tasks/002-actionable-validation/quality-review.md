# Quality Review: 002-actionable-validation

## Verdict

approved

## Separation Of Concerns

- `ValidationContext` and rules remain in core, while Chinese presentation copy
  is localized only in `src/thesis_forge/cli.py:34-75`.
- `ValidationIssue.details` at `src/thesis_forge/core/model.py:148-155` carries
  structured parameters without introducing CLI, Template or DOCX objects into
  the domain.
- Parser and Domain architecture guards still pass.

## Component Cohesion / Coupling

- Unit parsing is centralized in `templates/model.py:20-44`.
- Template selection is centralized in `templates/resolver.py:40-138`.
- Validation composition, resource policy and deterministic sorting remain in
  `core/validator.py:39-434`.
- Compiler and Renderer were not modified and receive no template or Pydantic
  implementation objects through the domain.

## Test Quality

- Tests cover rule replacement, legacy callers, metadata, IDs, references,
  images, bibliography, style coverage, deterministic ordering and path
  escapes in `tests/test_validator.py`.
- Tests cover every typed template family, field-path errors, explicit path,
  metadata ID, malformed YAML, missing templates and suffix enforcement in
  `tests/test_template.py`.
- Tests cover warning/error/source exit codes, stable target output, invalid
  templates, explicit precedence and cwd independence in `tests/test_cli.py`.
- Final result: `35 passed`.

## Error Handling

- Source parse/read failures are converted to concise exit-2 CLI errors without
  traceback.
- Template YAML/schema/unit errors retain field paths through
  `TemplateLoadError`.
- Missing, ambiguous and invalid templates remain distinct diagnostic codes.
- Path escapes are rejected before file-existence success can mask them.

## Reuse / Duplication

- Validation rules share one context and one sort function.
- Image and bibliography checks share one resource-root resolver.
- Project and packaged template lookup share one resolver.
- CLI localization has one issue-code adapter and falls back to custom rule
  messages.

## Complexity Delta

- Validator grew into focused pure rule functions rather than one monolithic
  loop.
- Template types are explicit and strict, reducing future Renderer magic-key
  growth.
- Packaging adds only two explicit template data mappings, avoiding AppleDouble
  leakage from directory-wide force inclusion.

## Required Fixes

- None. Independent quality review re-ran pytest, Ruff, repository-external CLI
  validation and isolated wheel validation before approving.
