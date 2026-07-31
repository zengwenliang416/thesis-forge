## Why

ThesisForge V1 core is complete, but authors still need CLI commands and manual
file inspection to understand document structure, resolve diagnostics, select a
school template, and build DOCX output. The approved desktop workbench prototype
can now be promoted because the deterministic application services and package
boundary are stable.

The archived prototype acceptance test also exposes a lifecycle defect: it
points at the removed active-change directory and fails after a correct OpenSpec
archive. The desktop milestone must begin by restoring an archive-safe baseline.

## What Changes

- Restore archived prototype contract tests without recreating or mutating the
  completed V1 change.
- Add an optional PySide6 desktop entrypoint and academic three-pane workbench.
- Add local source open, explicit atomic save, template selection, validation,
  diagnostics, renderer-neutral preview, build progress, cancellation, and
  output feedback.
- Reuse the existing inspect, validation, and build application services.
- Add headless controller/view-model tests and real desktop interaction,
  accessibility, offline, permission, and failure-path verification.
- Keep the core CLI usable without PySide6 and introduce no network, database,
  account, AI, autosave, dark mode, or runtime localization dependency.

## Capabilities

### New Capabilities

- `desktop-workbench`: Local PySide6 authoring workbench, archive-safe prototype
  contract, explicit source lifecycle, diagnostics, preview, and DOCX build
  orchestration.

### Modified Capabilities

None. Existing compiler, validation, template, rendering, bibliography, and
offline CLI requirements remain unchanged and are reused through their public
application contracts.

## Impact

- New optional UI modules under `src/thesis_forge/ui/`.
- New `thesisforge-ui` package entrypoint using the existing `ui` optional
  dependency.
- New controller, view-model, widget, accessibility, and end-to-end tests.
- Targeted repair to `tests/test_prototype_acceptance.py` so archived evidence
  remains discoverable.
- No database, migration, HTTP API, authentication, remote service, or public
  distribution change.
