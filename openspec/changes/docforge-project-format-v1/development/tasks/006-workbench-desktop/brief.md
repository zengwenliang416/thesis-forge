# Task Brief: 006-workbench-desktop

## Goal

The installed workbench opens DocForge projects and presents neutral document
terminology while preserving the approved layout, accessibility, responsive
behavior, and Microsoft Word preview flow.

## Vertical Slice

Migrate project opening and workspace identity, replace active thesis-specific
copy, rename desktop product and sidecar identity, update UI tests, install the
macOS package, and perform sensory checks.

## In Scope

- Checklist items `6.1` through `6.5`.
- Project picker and open flows, neutral workbench copy, Tauri product identity,
  component/browser tests, installed macOS behavior, and Word final preview.

## Files Allowed

- `frontend`
- `src-tauri`
- `src/docforge`
- `tests/adapters`
- `tests/test_desktop_distribution.py`
- `scripts`
- `package.json`
- `openspec/changes/docforge-project-format-v1/development/tasks/006-workbench-desktop`
- `openspec/changes/docforge-project-format-v1/development`

## Components To Create

- No new page or layout component is planned.
- Add only DocForge identity constants or project DTO fields not already owned
  by shared transport/state modules.

## Components To Reuse

- Existing three-pane shell, project state, editor, outline, preview,
  diagnostics, template selector, build flow, final preview, and accessibility
  primitives.

## Components To Extract

- Repeated product, manifest, source, output, and sidecar identity literals
  belong in existing shared frontend or Rust identity modules.

## Verification Commands

- `pnpm --dir frontend typecheck`
- `pnpm --dir frontend test`
- `pnpm --dir frontend test:e2e`
- `cargo test --manifest-path src-tauri/Cargo.toml`
- `PYTHONPATH=src .venv/bin/python -m pytest tests/adapters tests/test_desktop_distribution.py`

## Stop Conditions

- Work requires a new screen, layout redesign, dark mode, locale switcher, or
  altered Markdown editing lifecycle.
- A desktop operation accepts bare Markdown or an obsolete project contract.
- Microsoft Word final preview cannot be exercised without changing the
  approved Office-only policy.

## Unsafe Assumptions

- Updated visible copy does not prove Tauri metadata, sidecar, file filters, and
  installer identity changed.
- Browser tests do not replace installed macOS and Microsoft Word sensory
  evidence.
