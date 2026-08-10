# Development Migrations: template-driven-list-layout-p1

## Execution Order

- No database, seed, menu or permission migration is required for this local template and DOCX
  rendering change.

## Validation

- Validate `manifest.json` remains `required: false` and that implementation touches only local
  source, YAML templates, documentation, tests and generated DOCX output.

## Rollback

- Roll back the additive Template Model and YAML list policy plus the DOCX Renderer translation;
  no persisted data rollback is required.
